"""Simulation generation via LLM."""

import json
import logging
from datetime import datetime, timezone

from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.models.schemas import AgentConfig, SimulationResult
from app.prompts.simulation import SYSTEM_PROMPT, build_simulation_prompt

logger = logging.getLogger(__name__)

MIN_MESSAGES = 8
MAX_MESSAGES = 15


def _apply_sanity_checks(data: dict) -> list[str]:
    """Validate simulation output and log warnings for issues.

    Non-fatal: logs warnings but does not raise. The conversations are still
    usable even if slightly outside bounds.

    Returns:
        List of warning messages.
    """
    warnings: list[str] = []

    scenarios = data.get("scenarios", [])
    if len(scenarios) != 2:
        warnings.append(f"Esperava 2 cenários, recebeu {len(scenarios)}")

    for i, scenario in enumerate(scenarios):
        conv = scenario.get("conversation", [])
        if len(conv) < MIN_MESSAGES:
            warnings.append(
                f"Cenário {i + 1}: {len(conv)} mensagens (mínimo: {MIN_MESSAGES})"
            )
        elif len(conv) > MAX_MESSAGES:
            warnings.append(
                f"Cenário {i + 1}: {len(conv)} mensagens (máximo: {MAX_MESSAGES})"
            )

    for w in warnings:
        logger.warning("Simulation sanity check: %s", w)

    return warnings


async def generate_simulation(
    agent_config: AgentConfig,
    session_id: str = "",
) -> SimulationResult:
    """Generate 2 simulated collection conversations from an AgentConfig.

    Args:
        agent_config: The complete agent configuration to simulate.
        session_id: Onboarding session ID for metadata.

    Returns:
        Validated SimulationResult with 2 conversation scenarios.

    Raises:
        ValueError: If LLM fails after 2 attempts or output is invalid.
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    user_message = build_simulation_prompt(agent_config)

    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            data = json.loads(response.choices[0].message.content)

            # Inject metadata
            if "metadata" not in data or not isinstance(data["metadata"], dict):
                data["metadata"] = {}
            data["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()
            data["metadata"]["onboarding_session_id"] = session_id
            data["metadata"]["generation_model"] = "gpt-4.1-mini"

            # Sanity checks (non-fatal, just logs)
            _apply_sanity_checks(data)

            return SimulationResult(**data)

        except ValueError:
            raise
        except (OpenAIError, json.JSONDecodeError, KeyError, Exception) as exc:
            logger.warning(
                "Simulation generation attempt %d failed: %s", attempt + 1, exc
            )
            if attempt == 0:
                continue
            raise ValueError(
                "Falha na geração da simulação após 2 tentativas."
            ) from exc
