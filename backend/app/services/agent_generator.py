"""Agent config generation via LLM."""

import copy
import json
import logging
from datetime import datetime, timezone
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.models.schemas import AgentConfig
from app.prompts.agent_generator import (
    ADJUSTMENT_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_adjustment_prompt,
    build_prompt,
)

logger = logging.getLogger(__name__)


def _apply_sanity_checks(
    data: dict,
    interview_responses: list[dict],
) -> list[str]:
    """Validate and auto-correct LLM output. Returns list of corrections made."""
    corrections: list[str] = []

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
    session_id: str = "",
) -> AgentConfig:
    """Generate a complete AgentConfig by calling GPT-4.1-mini.

    Args:
        company_profile: CompanyProfile dict from enrichment (or None).
        interview_responses: List of answer dicts from the interview.
        session_id: Onboarding session ID for metadata.

    Returns:
        Validated AgentConfig instance.

    Raises:
        ValueError: If LLM fails after 2 attempts or output fails sanity checks.
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    user_message = build_prompt(company_profile, interview_responses)

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
            corrections = _apply_sanity_checks(data, interview_responses)
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


def _apply_dotted_path_adjustments(
    config_dict: dict,
    adjustments: dict[str, Any],
) -> tuple[dict, list[str]]:
    """Apply dotted-path adjustments to a nested config dict.

    Args:
        config_dict: The original AgentConfig as a dict.
        adjustments: Flat dict like {"tone.style": "empathetic", ...}.

    Returns:
        (updated_dict, summary_lines) where summary_lines describes each change.

    Raises:
        ValueError: If a dotted path references a non-existent key.
    """
    result = copy.deepcopy(config_dict)
    summary_lines: list[str] = []

    for path, new_value in adjustments.items():
        parts = path.split(".")
        target = result
        for part in parts[:-1]:
            if not isinstance(target, dict) or part not in target:
                raise ValueError(
                    f"Caminho inválido: '{path}' — '{part}' não encontrado na configuração."
                )
            target = target[part]
        leaf_key = parts[-1]
        if not isinstance(target, dict):
            raise ValueError(
                f"Caminho inválido: '{path}' — o pai não é um objeto."
            )
        if leaf_key not in target:
            raise ValueError(
                f"Caminho inválido: '{path}' — '{leaf_key}' não encontrado na configuração."
            )
        old_value = target[leaf_key]
        target[leaf_key] = new_value
        summary_lines.append(f"- {path}: {old_value!r} → {new_value!r}")

    return result, summary_lines


async def adjust_agent_config(
    current_config: dict,
    adjustments: dict[str, Any],
    session_id: str = "",
) -> AgentConfig:
    """Apply user adjustments to an existing config and regenerate text fields.

    Args:
        current_config: The current agent_config dict from the DB.
        adjustments: Flat dotted-path dict of changes to apply.
        session_id: Session ID for metadata.

    Returns:
        Updated and validated AgentConfig with incremented version.

    Raises:
        ValueError: If paths are invalid, LLM fails, or validation fails.
    """
    # Step 1: Apply structural adjustments
    adjusted_dict, summary_lines = _apply_dotted_path_adjustments(
        current_config, adjustments
    )
    adjustments_summary = "\n".join(summary_lines)

    # Step 2: Increment version and update timestamp
    adjusted_dict.setdefault("metadata", {})
    adjusted_dict["metadata"]["version"] = (
        adjusted_dict["metadata"].get("version", 1) + 1
    )
    adjusted_dict["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()

    # Step 3: Regenerate system_prompt + scenario_responses via LLM
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    user_message = build_adjustment_prompt(adjusted_dict, adjustments_summary)

    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": ADJUSTMENT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            regen_data = json.loads(response.choices[0].message.content)

            adjusted_dict["system_prompt"] = regen_data["system_prompt"]
            adjusted_dict["scenario_responses"] = regen_data["scenario_responses"]

            break

        except ValueError:
            raise
        except (OpenAIError, json.JSONDecodeError, KeyError, Exception) as exc:
            logger.warning(
                "Adjustment regeneration attempt %d failed: %s", attempt + 1, exc
            )
            if attempt == 0:
                continue
            raise ValueError(
                "Falha na regeneração do agente após 2 tentativas."
            ) from exc

    # Step 4: Validate final result via Pydantic
    return AgentConfig(**adjusted_dict)
