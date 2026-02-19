"""Tests for T08: Core questions data structure + T09: LangGraph interview state."""

import json

import pytest

from app.models.schemas import InterviewQuestion, SmartDefaults
from app.prompts.interview import CORE_QUESTIONS, DYNAMIC_QUESTION_BANK, SMART_DEFAULTS
from app.services.interview_agent import (
    InterviewState,
    create_interview,
    deserialize_state,
    get_next_question,
    serialize_state,
)


def test_core_questions_count():
    """Exactly 12 core questions defined."""
    assert len(CORE_QUESTIONS) == 12


def test_core_questions_schema():
    """All core questions match InterviewQuestion schema with correct IDs."""
    for i, q in enumerate(CORE_QUESTIONS, start=1):
        assert isinstance(q, InterviewQuestion)
        assert q.question_id == f"core_{i}"
        assert q.phase == "core"
        assert q.is_required is True
        assert len(q.question_text) > 0


def test_core_questions_unique_ids():
    """No duplicate question IDs."""
    ids = [q.question_id for q in CORE_QUESTIONS]
    assert len(ids) == len(set(ids))


def test_financial_questions_have_none_option():
    """Discount, installments, interest, and penalty questions all have a 'none' option."""
    financial_ids = {"core_6", "core_7", "core_8", "core_9"}
    for q in CORE_QUESTIONS:
        if q.question_id in financial_ids:
            assert isinstance(q.options, list), f"{q.question_id} should have list options"
            values = [o.value for o in q.options]
            assert "nenhum" in values, f"{q.question_id} missing 'nenhum' option"


def test_smart_defaults_complete():
    """All 11 defaults from PRD present with correct values."""
    assert isinstance(SMART_DEFAULTS, SmartDefaults)
    assert SMART_DEFAULTS.contact_hours_weekday == "08:00-20:00"
    assert SMART_DEFAULTS.contact_hours_saturday == "08:00-14:00"
    assert SMART_DEFAULTS.contact_sunday is False
    assert SMART_DEFAULTS.follow_up_interval_days == 3
    assert SMART_DEFAULTS.max_contact_attempts == 10
    assert SMART_DEFAULTS.use_first_name is True
    assert SMART_DEFAULTS.identify_as_ai is True
    assert SMART_DEFAULTS.min_installment_value == 50.0
    assert SMART_DEFAULTS.discount_strategy == "only_when_resisted"
    assert SMART_DEFAULTS.payment_link_generation is True
    assert SMART_DEFAULTS.max_discount_installment_pct == 5.0


def test_dynamic_question_bank_categories():
    """All 8 categories present with non-empty question lists."""
    expected_categories = {
        "business_model",
        "debtor_profile",
        "negotiation_depth",
        "scenario_handling",
        "legal_judicial",
        "communication",
        "segmentation",
        "current_pain",
    }
    assert set(DYNAMIC_QUESTION_BANK.keys()) == expected_categories
    for category, questions in DYNAMIC_QUESTION_BANK.items():
        assert len(questions) >= 2, f"Category '{category}' has fewer than 2 questions"
        for q in questions:
            assert isinstance(q, str) and len(q) > 0


# ---------- T09: LangGraph interview state + basic graph ----------


@pytest.mark.asyncio
async def test_create_interview():
    """Creates interview with 12 core questions (11 remaining + 1 current)."""
    state = await create_interview()
    assert state["phase"] == "core"
    assert len(state["core_questions_remaining"]) == 11
    assert state["current_question"] is not None
    assert state["current_question"]["question_id"] == "core_1"
    assert state["answers"] == []
    assert state["dynamic_questions_asked"] == 0
    assert state["max_dynamic_questions"] == 8
    assert state["needs_follow_up"] is False
    assert state["follow_up_question"] is None
    # Total core questions: 11 remaining + 1 current = 12
    assert len(state["core_questions_remaining"]) + 1 == 12


@pytest.mark.asyncio
async def test_get_first_question():
    """Returns first core question as a valid InterviewQuestion."""
    state = await create_interview()
    question = InterviewQuestion.model_validate(state["current_question"])
    assert question.question_id == "core_1"
    assert question.question_type == "text"
    assert question.phase == "core"
    assert question.is_required is True


@pytest.mark.asyncio
async def test_state_serialization():
    """State can be dumped to JSON and loaded back identically."""
    enrichment = {"company_name": "TestCorp", "products_description": "Software"}
    state = await create_interview(enrichment_data=enrichment)

    json_str = json.dumps(serialize_state(state), ensure_ascii=False)
    loaded = deserialize_state(json.loads(json_str))

    assert loaded["phase"] == state["phase"]
    assert loaded["current_question"] == state["current_question"]
    assert len(loaded["core_questions_remaining"]) == len(state["core_questions_remaining"])
    assert loaded["enrichment_data"] == state["enrichment_data"]
    assert loaded["answers"] == state["answers"]
    assert loaded["dynamic_questions_asked"] == state["dynamic_questions_asked"]
    assert loaded["needs_follow_up"] == state["needs_follow_up"]


@pytest.mark.asyncio
async def test_pre_fill_from_enrichment():
    """If enrichment has product info, core_1 has pre_filled_value."""
    enrichment = {
        "company_name": "TestCorp",
        "products_description": "Software de gestão financeira",
        "communication_tone": "formal e profissional",
        "payment_methods_mentioned": "PIX e boleto",
    }
    state = await create_interview(enrichment_data=enrichment)
    question = InterviewQuestion.model_validate(state["current_question"])
    assert question.question_id == "core_1"
    assert question.pre_filled_value == "Software de gestão financeira"
    assert question.context_hint is not None
    assert "site" in question.context_hint.lower()


@pytest.mark.asyncio
async def test_get_next_question_advances():
    """get_next_question pops the next core question from remaining."""
    state = await create_interview()
    assert state["current_question"]["question_id"] == "core_1"

    question, new_state = await get_next_question(state)
    assert question is not None
    assert question.question_id == "core_2"
    assert len(new_state["core_questions_remaining"]) == 10


@pytest.mark.asyncio
async def test_no_enrichment_no_prefill():
    """Without enrichment data, core_1 has no pre_filled_value."""
    state = await create_interview()
    question = InterviewQuestion.model_validate(state["current_question"])
    assert question.question_id == "core_1"
    assert question.pre_filled_value is None


@pytest.mark.asyncio
async def test_enrichment_prefill_core_5_tone():
    """Enrichment tone pre-fills core_5 when it becomes the current question."""
    enrichment = {"communication_tone": "amigável e casual"}
    state = await create_interview(enrichment_data=enrichment)
    # Advance from core_1 to core_5 (4 calls to get_next_question)
    for _ in range(4):
        _, state = await get_next_question(state)
    question = InterviewQuestion.model_validate(state["current_question"])
    assert question.question_id == "core_5"
    assert question.pre_filled_value == "amigável e casual"
