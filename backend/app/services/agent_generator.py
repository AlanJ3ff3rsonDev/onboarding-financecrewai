"""Agent config generation via LLM."""

import json
import logging
import re
from datetime import datetime, timezone

from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.models.schemas import AgentConfig
from app.prompts.agent_generator import SYSTEM_PROMPT, build_prompt

logger = logging.getLogger(__name__)


def _extract_discount_limit(interview_responses: list[dict]) -> float | None:
    """Extract the max discount from core_6 answer. Returns None if not found."""
    for r in interview_responses:
        if r.get("question_id") == "core_6":
            answer = r.get("answer", "")
            if answer == "nenhum":
                return 0.0
            match = re.search(r"(\d+)", str(answer))
            if match:
                return float(match.group(1))
    return None


def _apply_sanity_checks(
    data: dict,
    interview_responses: list[dict],
    smart_defaults: dict | None,
) -> list[str]:
    """Validate and auto-correct LLM output. Returns list of corrections made."""
    corrections: list[str] = []
    defaults = smart_defaults or {}

    # --- System prompt quality ---
    system_prompt = data.get("system_prompt", "")
    if not system_prompt or len(system_prompt) < 200:
        raise ValueError(
            f"LLM gerou system_prompt com apenas {len(system_prompt)} caracteres "
            f"(mínimo: 200). Geração inválida."
        )

    # Warn if company name not in system_prompt
    company_name = ""
    if isinstance(data.get("company_context"), dict):
        company_name = data["company_context"].get("name", "")
    if company_name and company_name.lower() not in system_prompt.lower():
        logger.warning(
            "system_prompt não menciona o nome da empresa '%s'", company_name
        )

    # --- Discount caps ---
    neg = data.get("negotiation_policies", {})
    if isinstance(neg, dict):
        # Cap full-payment discount to interview answer
        interview_limit = _extract_discount_limit(interview_responses)
        if interview_limit is not None:
            current = neg.get("max_discount_full_payment_pct", 0)
            if current > interview_limit:
                corrections.append(
                    f"max_discount_full_payment_pct: {current} → {interview_limit} "
                    f"(limitado pela resposta da entrevista)"
                )
                neg["max_discount_full_payment_pct"] = interview_limit

        # Cap installment discount to smart_defaults if provided
        defaults_inst_pct = defaults.get("max_discount_installment_pct")
        if defaults_inst_pct is not None:
            current_inst = neg.get("max_discount_installment_pct", 0)
            if current_inst > defaults_inst_pct:
                corrections.append(
                    f"max_discount_installment_pct: {current_inst} → {defaults_inst_pct} "
                    f"(limitado pelos padrões confirmados)"
                )
                neg["max_discount_installment_pct"] = defaults_inst_pct

        # Clamp ranges for Pydantic validation safety
        if neg.get("max_discount_full_payment_pct", 0) > 100:
            neg["max_discount_full_payment_pct"] = 100
            corrections.append("max_discount_full_payment_pct capped to 100")
        if neg.get("max_discount_full_payment_pct", 0) < 0:
            neg["max_discount_full_payment_pct"] = 0
            corrections.append("max_discount_full_payment_pct floored to 0")

        if neg.get("max_discount_installment_pct", 0) > 50:
            neg["max_discount_installment_pct"] = 50
            corrections.append("max_discount_installment_pct capped to 50")
        if neg.get("max_discount_installment_pct", 0) < 0:
            neg["max_discount_installment_pct"] = 0
            corrections.append("max_discount_installment_pct floored to 0")

        max_inst = neg.get("max_installments", 0)
        if max_inst > 48:
            neg["max_installments"] = 48
            corrections.append(f"max_installments: {max_inst} → 48")
        elif max_inst < 0:
            neg["max_installments"] = 0
            corrections.append(f"max_installments: {max_inst} → 0")

    # --- Guardrails bounds ---
    guard = data.get("guardrails", {})
    if isinstance(guard, dict):
        fui = guard.get("follow_up_interval_days", 3)
        if fui < 1:
            guard["follow_up_interval_days"] = 1
            corrections.append(f"follow_up_interval_days: {fui} → 1")
        elif fui > 30:
            guard["follow_up_interval_days"] = 30
            corrections.append(f"follow_up_interval_days: {fui} → 30")

        ma = guard.get("max_attempts_before_stop", 10)
        if ma < 1:
            guard["max_attempts_before_stop"] = 1
            corrections.append(f"max_attempts_before_stop: {ma} → 1")
        elif ma > 30:
            guard["max_attempts_before_stop"] = 30
            corrections.append(f"max_attempts_before_stop: {ma} → 30")

    for c in corrections:
        logger.warning("Sanity check correction: %s", c)

    return corrections


async def generate_agent_config(
    company_profile: dict | None,
    interview_responses: list[dict],
    smart_defaults: dict | None,
    session_id: str = "",
) -> AgentConfig:
    """Generate a complete AgentConfig by calling GPT-4.1-mini.

    Args:
        company_profile: CompanyProfile dict from enrichment (or None).
        interview_responses: List of answer dicts from the interview.
        smart_defaults: SmartDefaults dict confirmed by user (or None).
        session_id: Onboarding session ID for metadata.

    Returns:
        Validated AgentConfig instance.

    Raises:
        ValueError: If LLM fails after 2 attempts or output fails sanity checks.
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    user_message = build_prompt(company_profile, interview_responses, smart_defaults)

    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            data = json.loads(response.choices[0].message.content)

            # Inject metadata
            if "metadata" not in data or not isinstance(data["metadata"], dict):
                data["metadata"] = {}
            data["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()
            data["metadata"]["onboarding_session_id"] = session_id
            data["metadata"]["generation_model"] = "gpt-4.1-mini"

            # Sanity checks (may raise ValueError for fatal issues)
            corrections = _apply_sanity_checks(
                data, interview_responses, smart_defaults
            )
            if corrections:
                logger.info(
                    "Applied %d sanity corrections to agent config", len(corrections)
                )

            return AgentConfig(**data)

        except ValueError:
            raise
        except (OpenAIError, json.JSONDecodeError, KeyError, Exception) as exc:
            logger.warning(
                "Agent generation attempt %d failed: %s", attempt + 1, exc
            )
            if attempt == 0:
                continue
            raise ValueError(
                "Falha na geração do agente após 2 tentativas."
            ) from exc
