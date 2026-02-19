"""Website scraping and LLM extraction service."""

import json
import logging
from urllib.parse import urlparse

from openai import AsyncOpenAI, OpenAIError
from playwright.async_api import async_playwright, Error as PlaywrightError

from app.config import settings
from app.models.schemas import CompanyProfile
from app.prompts.enrichment import SYSTEM_PROMPT, build_prompt

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 15_000
NAVIGATION_TIMEOUT_MS = 30_000


async def scrape_website(url: str) -> str:
    """Scrape visible text content from a website using headless Chromium.

    Returns clean text or empty string on any failure.
    """
    # Ensure URL has a scheme
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                # Use domcontentloaded + short wait — networkidle hangs on sites
                # with persistent connections (analytics, chat widgets, etc.)
                await page.goto(url, timeout=NAVIGATION_TIMEOUT_MS, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                text = await page.inner_text("body")
            finally:
                await browser.close()
    except (PlaywrightError, TimeoutError, Exception) as exc:
        logger.warning("Failed to scrape %s: %s", url, exc)
        return ""

    text = text.strip()
    if not text:
        return ""

    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    return text


async def extract_company_profile(company_name: str, website_text: str) -> CompanyProfile:
    """Extract structured company profile from website text using LLM.

    Returns minimal profile (company_name only) if text is empty or LLM fails.
    """
    if not website_text.strip():
        return CompanyProfile(company_name=company_name)

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    user_message = build_prompt(company_name, website_text)

    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            data = json.loads(response.choices[0].message.content)
            data["company_name"] = company_name
            return CompanyProfile(**data)
        except (OpenAIError, json.JSONDecodeError, KeyError) as exc:
            logger.warning(
                "LLM extraction attempt %d failed: %s", attempt + 1, exc
            )
            if attempt == 0:
                continue
            return CompanyProfile(company_name=company_name)
