"""Tests for T08-T10: Core questions, LangGraph state, interview endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from app.models.schemas import InterviewQuestion
from app.prompts.interview import CORE_QUESTIONS, DYNAMIC_QUESTION_BANK
from app.services.interview_agent import (
    InterviewState,
    create_interview,
    deserialize_state,
    get_next_question,
    serialize_state,
    submit_answer,
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


def test_financial_questions_are_open_text():
    """Discount, installments, interest, and penalty questions are open text with context hints."""
    financial_ids = {"core_6", "core_7", "core_8", "core_9"}
    for q in CORE_QUESTIONS:
        if q.question_id in financial_ids:
            assert q.question_type == "text", f"{q.question_id} should be text type"
            assert q.options is None, f"{q.question_id} should have no options"
            assert q.context_hint is not None, f"{q.question_id} should have context_hint"
            assert len(q.context_hint) > 0


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


# ---------- T10: Interview "next question" endpoint ----------


def test_get_first_question_endpoint(client: TestClient) -> None:
    """New session → GET /interview/next → returns core_1, status becomes interviewing."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    resp = client.get(f"/api/v1/sessions/{session_id}/interview/next")
    assert resp.status_code == 200
    data = resp.json()
    assert data["question_id"] == "core_1"
    assert data["phase"] == "core"
    assert data["question_type"] == "text"
    assert data["is_required"] is True
    assert data["supports_audio"] is True
    assert "question_text" in data

    # Verify session status updated to interviewing
    session_resp = client.get(f"/api/v1/sessions/{session_id}")
    assert session_resp.json()["status"] == "interviewing"


def test_get_next_after_enrichment_endpoint(client: TestClient) -> None:
    """Enriched session → GET /interview/next → core_1 has pre_filled_value."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Manually set enrichment_data in DB (skip actual scraping)
    from app.database import get_db
    from app.main import app
    from app.models.orm import OnboardingSession

    db = next(app.dependency_overrides[get_db]())
    session = db.get(OnboardingSession, session_id)
    session.enrichment_data = {
        "company_name": "TestCorp",
        "products_description": "Software de cobrança inteligente",
        "payment_methods_mentioned": "PIX, boleto e cartão",
        "communication_tone": "profissional e empático",
    }
    session.status = "enriched"
    db.commit()
    db.close()

    resp = client.get(f"/api/v1/sessions/{session_id}/interview/next")
    assert resp.status_code == 200
    data = resp.json()
    assert data["question_id"] == "core_1"
    assert data["pre_filled_value"] == "Software de cobrança inteligente"
    assert data["context_hint"] is not None


def test_interview_state_persisted(client: TestClient) -> None:
    """GET /interview/next stores interview_state in DB and is idempotent."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # First call — initializes
    resp1 = client.get(f"/api/v1/sessions/{session_id}/interview/next")
    assert resp1.status_code == 200

    # Verify state stored in DB
    session_resp = client.get(f"/api/v1/sessions/{session_id}")
    assert session_resp.json()["interview_state"] is not None

    # Second call — same question (idempotent, no advancement)
    resp2 = client.get(f"/api/v1/sessions/{session_id}/interview/next")
    assert resp2.status_code == 200
    assert resp2.json()["question_id"] == resp1.json()["question_id"]


def test_interview_next_session_not_found(client: TestClient) -> None:
    """GET /interview/next for non-existent session → 404."""
    resp = client.get("/api/v1/sessions/nonexistent-id/interview/next")
    assert resp.status_code == 404


# ---------- T11: Interview "submit answer" endpoint ----------


@pytest.mark.asyncio
async def test_submit_answer_service():
    """submit_answer stores the answer and advances to next question."""
    from unittest.mock import patch, AsyncMock

    state = await create_interview()
    assert state["current_question"]["question_id"] == "core_1"

    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        next_q, new_state = await submit_answer(
            state, "core_1", "Software de gestão", "text"
        )
    assert next_q is not None
    assert next_q.question_id == "core_2"
    assert len(new_state["answers"]) == 1
    assert new_state["answers"][0]["question_id"] == "core_1"
    assert new_state["answers"][0]["answer"] == "Software de gestão"
    assert new_state["answers"][0]["source"] == "text"


@pytest.mark.asyncio
async def test_submit_answer_wrong_question_id():
    """submit_answer raises ValueError on question_id mismatch."""
    state = await create_interview()
    with pytest.raises(ValueError, match="mismatch"):
        await submit_answer(state, "core_5", "wrong question", "text")


def test_submit_answer_endpoint(client: TestClient) -> None:
    """POST /interview/answer stores answer and returns next question."""
    from unittest.mock import patch, AsyncMock

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize interview
    client.get(f"/api/v1/sessions/{session_id}/interview/next")

    # Submit answer to core_1 (mock follow-up to skip evaluation)
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        resp = client.post(
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": "core_1", "answer": "Vendemos software de cobrança", "source": "text"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["received"] is True
    assert data["next_question"]["question_id"] == "core_2"


def test_submit_answer_chain(client: TestClient) -> None:
    """Submit answers to core_1 through core_3 — each returns next question."""
    from unittest.mock import patch, AsyncMock

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize interview
    client.get(f"/api/v1/sessions/{session_id}/interview/next")

    answers = [
        ("core_1", "Software de cobrança"),
        ("core_2", "PIX e boleto"),
        ("core_3", "Pessoas físicas com dívidas"),
    ]
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        for qid, answer in answers:
            resp = client.post(
                f"/api/v1/sessions/{session_id}/interview/answer",
                json={"question_id": qid, "answer": answer, "source": "text"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["received"] is True
            assert data["next_question"] is not None

    # After core_3, next should be core_4
    assert data["next_question"]["question_id"] == "core_4"


def test_answer_stored_in_session(client: TestClient) -> None:
    """After submitting, answer appears in session's interview_responses."""
    from unittest.mock import patch, AsyncMock

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize and answer (mock follow-up to skip evaluation)
    client.get(f"/api/v1/sessions/{session_id}/interview/next")
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        client.post(
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": "core_1", "answer": "Financiamento automotivo", "source": "text"},
        )

    # Check session
    session_resp = client.get(f"/api/v1/sessions/{session_id}")
    session_data = session_resp.json()
    responses = session_data["interview_responses"]
    assert len(responses) == 1
    assert responses[0]["question_id"] == "core_1"
    assert responses[0]["answer"] == "Financiamento automotivo"
    assert responses[0]["source"] == "text"

    # Also check interview_state has the answer
    state = session_data["interview_state"]
    assert len(state["answers"]) == 1
    assert state["current_question"]["question_id"] == "core_2"


def test_wrong_question_id_endpoint(client: TestClient) -> None:
    """Submit answer for wrong question_id → 400."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize interview (current = core_1)
    client.get(f"/api/v1/sessions/{session_id}/interview/next")

    # Submit answer for core_5 instead of core_1
    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/answer",
        json={"question_id": "core_5", "answer": "wrong question", "source": "text"},
    )
    assert resp.status_code == 400
    assert "mismatch" in resp.json()["detail"].lower()


def test_submit_answer_session_not_found(client: TestClient) -> None:
    """POST /interview/answer for non-existent session → 404."""
    resp = client.post(
        "/api/v1/sessions/nonexistent-id/interview/answer",
        json={"question_id": "core_1", "answer": "test", "source": "text"},
    )
    assert resp.status_code == 404


def test_submit_answer_interview_not_started(client: TestClient) -> None:
    """POST /interview/answer before starting interview → 400."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/answer",
        json={"question_id": "core_1", "answer": "test", "source": "text"},
    )
    assert resp.status_code == 400
    assert "not started" in resp.json()["detail"].lower()


# ---------- T12: AI follow-up evaluation + generation ----------


def _mock_openai_response(content: str):
    """Build a mock OpenAI chat completion response."""
    from unittest.mock import AsyncMock, MagicMock

    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]

    client_instance = AsyncMock()
    client_instance.chat.completions.create = AsyncMock(return_value=response)
    return client_instance


@pytest.mark.asyncio
async def test_short_answer_triggers_follow_up():
    """'sim' to core_1 (text) → returns followup_core_1_1 with phase='follow_up'."""
    from unittest.mock import patch

    state = await create_interview()
    assert state["current_question"]["question_id"] == "core_1"

    mock_response = json.dumps({
        "needs_follow_up": True,
        "follow_up_question": "Pode descrever com mais detalhes os produtos ou serviços que sua empresa oferece?",
        "reason": "Resposta muito curta, precisa de mais detalhes",
    })
    mock_client = _mock_openai_response(mock_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q, new_state = await submit_answer(state, "core_1", "sim", "text")

    assert next_q is not None
    assert next_q.question_id == "followup_core_1_1"
    assert next_q.phase == "follow_up"
    assert next_q.is_required is False
    assert next_q.question_type == "text"
    assert new_state["needs_follow_up"] is True
    assert new_state["follow_up_count"] == 1
    assert len(new_state["answers"]) == 1
    assert new_state["answers"][0]["answer"] == "sim"


@pytest.mark.asyncio
async def test_detailed_answer_no_follow_up():
    """Detailed paragraph to core_1 → advances to core_2 normally."""
    from unittest.mock import patch

    state = await create_interview()

    mock_response = json.dumps({
        "needs_follow_up": False,
        "follow_up_question": None,
        "reason": "Resposta detalhada e suficiente",
    })
    mock_client = _mock_openai_response(mock_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q, new_state = await submit_answer(
                state, "core_1",
                "Vendemos software de gestão financeira para PMEs, incluindo módulos de contas a receber, fluxo de caixa e cobrança automatizada.",
                "text",
            )

    assert next_q is not None
    assert next_q.question_id == "core_2"
    assert new_state["needs_follow_up"] is False
    assert new_state["follow_up_count"] == 0


@pytest.mark.asyncio
async def test_follow_up_answer_stored():
    """Answer follow-up → both answers in state, then advances to core_2."""
    from unittest.mock import patch

    state = await create_interview()

    # First: short answer triggers follow-up
    fu_response = json.dumps({
        "needs_follow_up": True,
        "follow_up_question": "Pode descrever melhor?",
        "reason": "Muito curto",
    })
    mock_client = _mock_openai_response(fu_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q, state2 = await submit_answer(state, "core_1", "sim", "text")

    assert next_q.question_id == "followup_core_1_1"
    assert len(state2["answers"]) == 1

    # Second: answer the follow-up with detail → no more follow-up, advance to core_2
    no_fu_response = json.dumps({
        "needs_follow_up": False,
        "follow_up_question": None,
        "reason": "Agora está detalhado",
    })
    mock_client2 = _mock_openai_response(no_fu_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client2):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q2, state3 = await submit_answer(
                state2, "followup_core_1_1",
                "Vendemos software de gestão financeira com módulos de cobrança e conciliação",
                "text",
            )

    assert next_q2 is not None
    assert next_q2.question_id == "core_2"
    assert len(state3["answers"]) == 2
    assert state3["answers"][0]["question_id"] == "core_1"
    assert state3["answers"][1]["question_id"] == "followup_core_1_1"
    assert state3["follow_up_count"] == 0
    assert state3["needs_follow_up"] is False


@pytest.mark.asyncio
async def test_max_follow_ups():
    """After 2 follow-ups, third answer advances to next core (no LLM call)."""
    from unittest.mock import patch

    state = await create_interview()

    # Simulate 2 follow-ups already done
    fu_response = json.dumps({
        "needs_follow_up": True,
        "follow_up_question": "Pode detalhar mais?",
        "reason": "Curto",
    })
    mock_client = _mock_openai_response(fu_response)

    # Follow-up 1
    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q, state2 = await submit_answer(state, "core_1", "sim", "text")
    assert next_q.question_id == "followup_core_1_1"
    assert state2["follow_up_count"] == 1

    # Follow-up 2
    mock_client2 = _mock_openai_response(fu_response)
    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client2):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q2, state3 = await submit_answer(state2, "followup_core_1_1", "talvez", "text")
    assert next_q2.question_id == "followup_core_1_2"
    assert state3["follow_up_count"] == 2

    # Third answer to second follow-up — max reached, should advance to core_2 without LLM call
    # follow_up_count is already 2 (== MAX), so evaluate_and_maybe_follow_up returns (False, None)
    # No LLM call needed, but patch anyway to verify it's NOT called
    mock_client3 = _mock_openai_response(fu_response)
    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client3) as mock_cls:
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q3, state4 = await submit_answer(state3, "followup_core_1_2", "ok detalhe aqui", "text")

    assert next_q3.question_id == "core_2"
    assert state4["follow_up_count"] == 0
    assert state4["needs_follow_up"] is False
    # LLM should not have been called (max follow-ups reached)
    mock_client3.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
async def test_select_question_no_follow_up():
    """Select-type question (core_3) skips follow-up evaluation entirely."""
    from unittest.mock import patch

    state = await create_interview()

    # Advance to core_3 (select type) — answer core_1 and core_2 first without follow-ups
    no_fu = json.dumps({"needs_follow_up": False, "follow_up_question": None, "reason": "ok"})
    mock_client = _mock_openai_response(no_fu)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            _, state2 = await submit_answer(state, "core_1", "Software de gestão financeira com vários módulos", "text")

    # core_2 is multiselect — answer it (should skip evaluation)
    mock_client2 = _mock_openai_response(no_fu)
    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client2) as mock_cls:
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q, state3 = await submit_answer(state2, "core_2", "pix,boleto", "text")

    assert next_q.question_id == "core_3"
    # LLM should NOT have been called for multiselect
    mock_client2.chat.completions.create.assert_not_called()

    # core_3 is select — answer it
    mock_client3 = _mock_openai_response(no_fu)
    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client3) as mock_cls3:
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q2, state4 = await submit_answer(state3, "core_3", "d5", "text")

    assert next_q2.question_id == "core_4"
    # LLM should NOT have been called for select
    mock_client3.chat.completions.create.assert_not_called()


def test_follow_up_endpoint_response(client: TestClient) -> None:
    """POST /answer with follow-up → response has both next_question and follow_up fields."""
    from unittest.mock import AsyncMock, MagicMock, patch

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize interview
    client.get(f"/api/v1/sessions/{session_id}/interview/next")

    # Mock OpenAI to trigger follow-up
    fu_response = json.dumps({
        "needs_follow_up": True,
        "follow_up_question": "Pode descrever melhor seus produtos?",
        "reason": "Muito curto",
    })
    mock_client = _mock_openai_response(fu_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            resp = client.post(
                f"/api/v1/sessions/{session_id}/interview/answer",
                json={"question_id": "core_1", "answer": "sim", "source": "text"},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["received"] is True
    assert data["next_question"]["question_id"] == "followup_core_1_1"
    assert data["next_question"]["phase"] == "follow_up"
    # follow_up field present for follow-up responses
    assert "follow_up" in data
    assert data["follow_up"]["question_id"] == "followup_core_1_1"


@pytest.mark.asyncio
async def test_select_outro_triggers_follow_up():
    """Select question answered with 'outro' triggers follow-up evaluation."""
    from unittest.mock import patch, AsyncMock

    state = await create_interview()

    # Answer core_1 (text) without follow-up to advance
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        _, state2 = await submit_answer(state, "core_1", "Software de gestão", "text")

    # Answer core_2 (multiselect) without follow-up to advance
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        _, state3 = await submit_answer(state2, "core_2", "pix,boleto", "text")

    # core_3 is select — answer with "outro" → should trigger evaluation
    fu_response = json.dumps({
        "needs_follow_up": True,
        "follow_up_question": "Pode explicar quando exatamente você considera a conta vencida?",
        "reason": "Selecionou 'outro' sem especificar",
    })
    mock_client = _mock_openai_response(fu_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q, state4 = await submit_answer(state3, "core_3", "outro", "text")

    assert next_q is not None
    assert next_q.question_id == "followup_core_3_1"
    assert next_q.phase == "follow_up"
    assert state4["needs_follow_up"] is True
    assert state4["follow_up_count"] == 1
    # LLM WAS called because answer contained "outro"
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_multiselect_with_outro_triggers_follow_up():
    """Multiselect answer containing 'outro' triggers follow-up evaluation."""
    from unittest.mock import patch, AsyncMock

    state = await create_interview()

    # Answer core_1 (text) without follow-up to advance
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        _, state2 = await submit_answer(state, "core_1", "Software de gestão", "text")

    # core_2 is multiselect — answer with "pix,outro" → should trigger evaluation
    fu_response = json.dumps({
        "needs_follow_up": True,
        "follow_up_question": "Você mencionou 'outro' método de pagamento. Quais outros métodos seus clientes usam?",
        "reason": "Precisa especificar o método 'outro'",
    })
    mock_client = _mock_openai_response(fu_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q, state3 = await submit_answer(state2, "core_2", "pix,outro", "text")

    assert next_q is not None
    assert next_q.question_id == "followup_core_2_1"
    assert next_q.phase == "follow_up"
    assert state3["needs_follow_up"] is True
    # LLM WAS called because answer contained "outro"
    mock_client.chat.completions.create.assert_called_once()


# ---------- T13: Dynamic question generation ----------


from app.services.interview_agent import (
    evaluate_interview_completeness,
    generate_dynamic_question,
)


def _dynamic_state(**overrides) -> InterviewState:
    """Build an InterviewState in dynamic phase for testing."""
    base: dict = {
        "enrichment_data": {"company_name": "TestCo", "segment": "varejo"},
        "core_questions_remaining": [],
        "current_question": None,
        "answers": [
            {"question_id": f"core_{i}", "answer": f"Resposta {i}",
             "source": "text", "question_text": f"Pergunta {i}"}
            for i in range(1, 13)
        ],
        "dynamic_questions_asked": 0,
        "max_dynamic_questions": 8,
        "phase": "dynamic",
        "needs_follow_up": False,
        "follow_up_question": None,
        "follow_up_count": 0,
    }
    base.update(overrides)
    return InterviewState(**base)


@pytest.mark.asyncio
async def test_dynamic_phase_starts():
    """After all 12 core questions answered, get_next_question enters dynamic phase."""
    from unittest.mock import AsyncMock, patch

    # State with 1 core question remaining (core_12) — simulate answering it
    state = await create_interview()

    # Fast-forward to core_12: empty the remaining list except last
    last_q = CORE_QUESTIONS[-1].model_dump()
    state_at_core_12 = InterviewState(
        enrichment_data={},
        core_questions_remaining=[],
        current_question=last_q,
        answers=[
            {"question_id": f"core_{i}", "answer": f"Resp {i}",
             "source": "text", "question_text": f"Q{i}"}
            for i in range(1, 12)
        ],
        dynamic_questions_asked=0,
        max_dynamic_questions=8,
        phase="core",
        needs_follow_up=False,
        follow_up_question=None,
        follow_up_count=0,
    )

    # Mock follow-up eval (no follow-up) and dynamic question generation
    dyn_response = json.dumps({
        "question_text": "Qual o ticket médio das dívidas?",
        "category": "business_model",
        "reason": "Importante para calibrar descontos",
    })
    mock_client = _mock_openai_response(dyn_response)

    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up",
               new_callable=AsyncMock, return_value=(False, None)):
        with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
            with patch("app.services.interview_agent.settings") as mock_settings:
                mock_settings.OPENAI_API_KEY = "test-key"
                next_q, new_state = await submit_answer(
                    state_at_core_12, "core_12", "Já paguei, não reconheço", "text",
                )

    assert next_q is not None
    assert next_q.question_id == "dynamic_1"
    assert next_q.phase == "dynamic"
    assert new_state["phase"] == "dynamic"
    assert new_state["dynamic_questions_asked"] == 1
    assert len(new_state["answers"]) == 12


@pytest.mark.asyncio
async def test_dynamic_question_generated():
    """generate_dynamic_question returns a valid InterviewQuestion with correct format."""
    from unittest.mock import patch

    state = _dynamic_state()

    mock_response = json.dumps({
        "question_text": "Qual o ticket médio das dívidas que você cobra?",
        "category": "business_model",
        "reason": "Importante para calibrar ofertas de desconto",
    })
    mock_client = _mock_openai_response(mock_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            question, new_state = await generate_dynamic_question(state)

    assert question is not None
    assert question.question_id == "dynamic_1"
    assert question.phase == "dynamic"
    assert question.question_type == "text"
    assert question.is_required is True
    assert question.supports_audio is True
    assert "ticket" in question.question_text.lower()
    assert new_state["dynamic_questions_asked"] == 1
    assert new_state["phase"] == "dynamic"
    assert new_state["current_question"]["question_id"] == "dynamic_1"


@pytest.mark.asyncio
async def test_dynamic_question_contextual():
    """Dynamic question prompt includes business-specific context from answers."""
    from unittest.mock import patch

    state = _dynamic_state(
        enrichment_data={"company_name": "ConstrutAI", "segment": "construção civil"},
        answers=[
            {"question_id": "core_1", "answer": "Materiais de construção e acabamento",
             "source": "text", "question_text": "O que sua empresa vende?"},
            {"question_id": "core_4", "answer": "Ligamos para obras que não pagaram em 30 dias",
             "source": "text", "question_text": "Fluxo de cobrança"},
        ],
    )

    mock_response = json.dumps({
        "question_text": "As obras costumam ter um responsável financeiro diferente do engenheiro?",
        "category": "debtor_profile",
        "reason": "Na construção, quem decide e quem paga são pessoas diferentes",
    })
    mock_client = _mock_openai_response(mock_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            question, _ = await generate_dynamic_question(state)

    assert question is not None
    assert question.phase == "dynamic"

    # Verify prompt sent to LLM contains business context
    call_args = mock_client.chat.completions.create.call_args
    prompt_content = call_args.kwargs["messages"][0]["content"]
    assert "construção" in prompt_content.lower()
    assert "Materiais de construção" in prompt_content


@pytest.mark.asyncio
async def test_max_dynamic_reached():
    """After 8 dynamic questions, transitions to 'review' without LLM call."""
    state = _dynamic_state(dynamic_questions_asked=8)

    question, new_state = await generate_dynamic_question(state)

    assert question is None
    assert new_state["phase"] == "review"
    assert new_state["current_question"] is None


@pytest.mark.asyncio
async def test_early_completion():
    """If LLM rates confidence >= 7, evaluate_interview_completeness returns True."""
    from unittest.mock import patch

    state = _dynamic_state(dynamic_questions_asked=3)

    mock_response = json.dumps({
        "confidence": 8,
        "reason": "Temos informações detalhadas sobre o processo de cobrança",
        "missing_area": None,
    })
    mock_client = _mock_openai_response(mock_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            is_complete, new_state = await evaluate_interview_completeness(state)

    assert is_complete is True
    assert new_state["phase"] == "review"
    assert new_state["current_question"] is None


@pytest.mark.asyncio
async def test_low_confidence_continues():
    """If LLM rates confidence < 7, evaluate_interview_completeness returns False."""
    from unittest.mock import patch

    state = _dynamic_state(dynamic_questions_asked=2)

    mock_response = json.dumps({
        "confidence": 5,
        "reason": "Faltam detalhes sobre cenários específicos",
        "missing_area": "scenario_handling",
    })
    mock_client = _mock_openai_response(mock_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            is_complete, new_state = await evaluate_interview_completeness(state)

    assert is_complete is False
    assert new_state["phase"] == "dynamic"  # unchanged


@pytest.mark.asyncio
async def test_dynamic_answer_triggers_completeness_eval():
    """Answering a dynamic question triggers completeness evaluation."""
    from unittest.mock import AsyncMock, patch

    state = _dynamic_state(
        dynamic_questions_asked=2,
        current_question={
            "question_id": "dynamic_2",
            "question_text": "Qual o ticket médio?",
            "question_type": "text",
            "options": None,
            "pre_filled_value": None,
            "is_required": True,
            "supports_audio": True,
            "phase": "dynamic",
            "context_hint": None,
        },
    )

    # Mock: no follow-up, completeness says not done, generate next dynamic
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up",
               new_callable=AsyncMock, return_value=(False, None)):
        with patch("app.services.interview_agent.evaluate_interview_completeness",
                   new_callable=AsyncMock, return_value=(False, state)) as mock_eval:
            dyn_q_dict = {
                "question_id": "dynamic_3",
                "question_text": "Como lidar com 'já paguei'?",
                "question_type": "text",
                "options": None,
                "pre_filled_value": None,
                "is_required": True,
                "supports_audio": True,
                "phase": "dynamic",
                "context_hint": None,
            }
            gen_state = InterviewState(
                **{**dict(state),
                   "current_question": dyn_q_dict,
                   "dynamic_questions_asked": 3,
                   }
            )
            with patch("app.services.interview_agent.generate_dynamic_question",
                       new_callable=AsyncMock,
                       return_value=(InterviewQuestion.model_validate(dyn_q_dict), gen_state)) as mock_gen:
                next_q, new_state = await submit_answer(
                    state, "dynamic_2", "R$ 500 em média", "text",
                )

    # Completeness was evaluated
    mock_eval.assert_called_once()
    # Not complete → generated next dynamic question
    mock_gen.assert_called_once()
    assert next_q is not None
    assert next_q.question_id == "dynamic_3"
    assert next_q.phase == "dynamic"


# ---------- T14: Interview progress endpoint + completion ----------


def test_progress_not_started(client: TestClient) -> None:
    """No interview started → phase='not_started', all zeros."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    resp = client.get(f"/api/v1/sessions/{session_id}/interview/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "not_started"
    assert data["total_answered"] == 0
    assert data["core_answered"] == 0
    assert data["core_total"] == 12
    assert data["dynamic_answered"] == 0
    assert data["estimated_remaining"] == 12
    assert data["is_complete"] is False


def test_progress_midway(client: TestClient) -> None:
    """After answering a few core questions, progress reflects correctly."""
    from unittest.mock import AsyncMock, patch

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize interview
    client.get(f"/api/v1/sessions/{session_id}/interview/next")

    # Answer core_1 and core_2
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up",
               new_callable=AsyncMock, return_value=(False, None)):
        client.post(
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": "core_1", "answer": "Software de gestão", "source": "text"},
        )
        client.post(
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": "core_2", "answer": "PIX e boleto", "source": "text"},
        )

    resp = client.get(f"/api/v1/sessions/{session_id}/interview/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "core"
    assert data["core_answered"] == 2
    assert data["core_total"] == 12
    assert data["total_answered"] == 2
    assert data["dynamic_answered"] == 0
    assert data["estimated_remaining"] > 0
    assert data["is_complete"] is False


def test_progress_during_follow_up(client: TestClient) -> None:
    """Progress counts core_answered correctly even when current question is a follow-up."""
    from app.database import get_db
    from app.main import app
    from app.models.orm import OnboardingSession
    from app.services.interview_agent import serialize_state

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Simulate: core_1 answered, currently on followup_core_1_1 (remaining has 11 items = core_2..core_12)
    db = next(app.dependency_overrides[get_db]())
    session = db.get(OnboardingSession, session_id)
    state = {
        "enrichment_data": {},
        "core_questions_remaining": [
            {"question_id": f"core_{i}", "question_text": f"Q{i}",
             "question_type": "text", "options": None, "pre_filled_value": None,
             "is_required": True, "supports_audio": True, "phase": "core", "context_hint": None}
            for i in range(2, 13)
        ],
        "current_question": {
            "question_id": "followup_core_1_1",
            "question_text": "Pode detalhar?",
            "question_type": "text", "options": None, "pre_filled_value": None,
            "is_required": False, "supports_audio": True, "phase": "follow_up", "context_hint": None,
        },
        "answers": [
            {"question_id": "core_1", "answer": "Software", "source": "text", "question_text": "Q1"},
        ],
        "dynamic_questions_asked": 0,
        "max_dynamic_questions": 8,
        "phase": "core",
        "needs_follow_up": True,
        "follow_up_question": None,
        "follow_up_count": 1,
    }
    session.interview_state = serialize_state(state)
    session.status = "interviewing"
    db.commit()
    db.close()

    resp = client.get(f"/api/v1/sessions/{session_id}/interview/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "core"
    # core_1 was answered (popped from remaining), follow-up is current — should count as 1
    assert data["core_answered"] == 1
    assert data["total_answered"] == 1


def test_progress_review_phase(client: TestClient) -> None:
    """When phase='review', is_complete=True and session status → 'interviewed'."""
    from app.database import get_db
    from app.main import app
    from app.models.orm import OnboardingSession
    from app.services.interview_agent import serialize_state

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Manually set interview_state to review phase
    db = next(app.dependency_overrides[get_db]())
    session = db.get(OnboardingSession, session_id)
    state = {
        "enrichment_data": {},
        "core_questions_remaining": [],
        "current_question": None,
        "answers": [
            {"question_id": f"core_{i}", "answer": f"Resp {i}",
             "source": "text", "question_text": f"Q{i}"}
            for i in range(1, 13)
        ],
        "dynamic_questions_asked": 5,
        "max_dynamic_questions": 8,
        "phase": "review",
        "needs_follow_up": False,
        "follow_up_question": None,
        "follow_up_count": 0,
    }
    session.interview_state = serialize_state(state)
    session.status = "interviewing"
    db.commit()
    db.close()

    resp = client.get(f"/api/v1/sessions/{session_id}/interview/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "review"
    assert data["core_answered"] == 12
    assert data["dynamic_answered"] == 5
    assert data["total_answered"] == 12
    assert data["estimated_remaining"] == 0
    assert data["is_complete"] is True

    # Verify session status transitioned to 'interviewed'
    session_resp = client.get(f"/api/v1/sessions/{session_id}")
    assert session_resp.json()["status"] == "interviewed"


def test_progress_session_not_found(client: TestClient) -> None:
    """GET /interview/progress for non-existent session → 404."""
    resp = client.get("/api/v1/sessions/nonexistent-id/interview/progress")
    assert resp.status_code == 404


# ---------- Review endpoints (replaced SmartDefaults) ----------


def _session_in_review_phase(client: TestClient) -> str:
    """Helper: create a session with interview_state in 'review' phase. Returns session_id."""
    from app.database import get_db
    from app.main import app
    from app.models.orm import OnboardingSession
    from app.services.interview_agent import serialize_state

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    db = next(app.dependency_overrides[get_db]())
    session = db.get(OnboardingSession, session_id)
    state = {
        "enrichment_data": {},
        "core_questions_remaining": [],
        "current_question": None,
        "answers": [
            {"question_id": f"core_{i}", "answer": f"Resp {i}",
             "source": "text", "question_text": f"Q{i}"}
            for i in range(1, 13)
        ],
        "dynamic_questions_asked": 5,
        "max_dynamic_questions": 8,
        "phase": "review",
        "needs_follow_up": False,
        "follow_up_question": None,
        "follow_up_count": 0,
    }
    session.interview_state = serialize_state(state)
    session.interview_responses = [
        {"question_id": f"core_{i}", "answer": f"Resp {i}", "source": "text"}
        for i in range(1, 13)
    ]
    session.status = "interviewing"
    db.commit()
    db.close()
    return session_id


def test_get_review(client: TestClient) -> None:
    """Session in review phase → GET /interview/review returns answers summary."""
    session_id = _session_in_review_phase(client)

    resp = client.get(f"/api/v1/sessions/{session_id}/interview/review")
    assert resp.status_code == 200
    data = resp.json()
    assert data["confirmed"] is False
    assert len(data["answers"]) == 12
    assert isinstance(data["enrichment"], dict)


def test_confirm_review(client: TestClient) -> None:
    """POST /interview/review with confirmation → phase=complete, status=interviewed."""
    session_id = _session_in_review_phase(client)

    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/review",
        json={"confirmed": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confirmed"] is True
    assert data["phase"] == "complete"

    # Verify stored in DB: confirmed
    resp2 = client.get(f"/api/v1/sessions/{session_id}/interview/review")
    assert resp2.status_code == 200
    assert resp2.json()["confirmed"] is True

    # Verify session status
    session_resp = client.get(f"/api/v1/sessions/{session_id}")
    assert session_resp.json()["status"] == "interviewed"


def test_confirm_review_with_notes(client: TestClient) -> None:
    """POST /interview/review with additional_notes → notes stored as review_notes entry."""
    session_id = _session_in_review_phase(client)

    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/review",
        json={"confirmed": True, "additional_notes": "Também aceitamos cheque."},
    )
    assert resp.status_code == 200
    assert resp.json()["confirmed"] is True

    # Verify notes stored in interview_responses
    session_resp = client.get(f"/api/v1/sessions/{session_id}")
    responses = session_resp.json()["interview_responses"]
    review_notes = [r for r in responses if r["question_id"] == "review_notes"]
    assert len(review_notes) == 1
    assert review_notes[0]["answer"] == "Também aceitamos cheque."


def test_review_wrong_phase(client: TestClient) -> None:
    """POST /interview/review when phase='core' → 400."""
    from app.database import get_db
    from app.main import app
    from app.models.orm import OnboardingSession
    from app.services.interview_agent import serialize_state

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Set interview_state to core phase
    db = next(app.dependency_overrides[get_db]())
    session = db.get(OnboardingSession, session_id)
    state = {
        "enrichment_data": {},
        "core_questions_remaining": [
            {"question_id": f"core_{i}", "question_text": f"Q{i}",
             "question_type": "text", "options": None, "pre_filled_value": None,
             "is_required": True, "supports_audio": True, "phase": "core", "context_hint": None}
            for i in range(2, 13)
        ],
        "current_question": {
            "question_id": "core_1", "question_text": "Q1",
            "question_type": "text", "options": None, "pre_filled_value": None,
            "is_required": True, "supports_audio": True, "phase": "core", "context_hint": None,
        },
        "answers": [],
        "dynamic_questions_asked": 0,
        "max_dynamic_questions": 8,
        "phase": "core",
        "needs_follow_up": False,
        "follow_up_question": None,
        "follow_up_count": 0,
    }
    session.interview_state = serialize_state(state)
    session.status = "interviewing"
    db.commit()
    db.close()

    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/review",
        json={"confirmed": True},
    )
    assert resp.status_code == 400
    assert "não concluída" in resp.json()["detail"].lower()


def test_review_session_not_found(client: TestClient) -> None:
    """GET/POST on nonexistent session → 404."""
    resp = client.get("/api/v1/sessions/nonexistent-id/interview/review")
    assert resp.status_code == 404

    resp2 = client.post(
        "/api/v1/sessions/nonexistent-id/interview/review",
        json={"confirmed": True},
    )
    assert resp2.status_code == 404
