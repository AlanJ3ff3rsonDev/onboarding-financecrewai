"""Tests for interview: core questions, LangGraph state, endpoints, follow-ups."""

import json

import pytest
from fastapi.testclient import TestClient

from app.models.schemas import InterviewQuestion
from app.prompts.interview import (
    CORE_QUESTIONS,
    DEFAULT_ESCALATION_TRIGGERS,
    DEFAULT_GUARDRAILS,
    DEFAULT_TONE,
    POLICY_FOLLOWUP_MAP,
)
from app.services.interview_agent import (
    InterviewState,
    create_interview,
    deserialize_state,
    get_next_question,
    serialize_state,
    submit_answer,
)


def test_core_questions_count():
    """Exactly 7 core questions defined."""
    assert len(CORE_QUESTIONS) == 7


def test_core_questions_schema():
    """All core questions have valid IDs, correct phase, and required fields."""
    for q in CORE_QUESTIONS:
        assert isinstance(q, InterviewQuestion)
        assert q.question_id.startswith("core_")
        assert q.phase == "core"
        assert len(q.question_text) > 0
    # All required except core_0 and core_6
    optional_ids = {"core_0", "core_6"}
    required_qs = [q for q in CORE_QUESTIONS if q.question_id not in optional_ids]
    for q in required_qs:
        assert q.is_required is True, f"{q.question_id} should be required"
    # core_0 and core_6 are optional
    for opt_id in optional_ids:
        opt_q = [q for q in CORE_QUESTIONS if q.question_id == opt_id]
        assert len(opt_q) == 1, f"{opt_id} should exist"
        assert opt_q[0].is_required is False, f"{opt_id} should be optional"


def test_core_questions_unique_ids():
    """No duplicate question IDs."""
    ids = [q.question_id for q in CORE_QUESTIONS]
    assert len(ids) == len(set(ids))


def test_select_questions_have_options():
    """core_2-5 are select type with exactly 2 options each (sim/não)."""
    select_ids = {"core_2", "core_3", "core_4", "core_5"}
    for q in CORE_QUESTIONS:
        if q.question_id in select_ids:
            assert q.question_type == "select", f"{q.question_id} should be select"
            assert q.options is not None, f"{q.question_id} should have options"
            assert len(q.options) == 2, f"{q.question_id} should have exactly 2 options"


def test_defaults_exist():
    """DEFAULT_ESCALATION_TRIGGERS and DEFAULT_GUARDRAILS are non-empty."""
    assert len(DEFAULT_ESCALATION_TRIGGERS) >= 3
    assert len(DEFAULT_GUARDRAILS) >= 3
    assert isinstance(DEFAULT_TONE, str)
    assert len(DEFAULT_TONE) > 0


def test_policy_followup_map():
    """POLICY_FOLLOWUP_MAP covers core_2-5."""
    assert set(POLICY_FOLLOWUP_MAP.keys()) == {"core_2", "core_3", "core_4", "core_5"}
    for k, v in POLICY_FOLLOWUP_MAP.items():
        assert isinstance(v, str) and len(v) > 0


# ---------- LangGraph interview state + basic graph ----------


@pytest.mark.asyncio
async def test_create_interview():
    """Creates interview with 7 core questions (6 remaining + 1 current)."""
    state = await create_interview()
    assert state["phase"] == "core"
    assert len(state["core_questions_remaining"]) == 6
    assert state["current_question"] is not None
    assert state["current_question"]["question_id"] == "core_0"
    assert state["answers"] == []
    assert state["needs_follow_up"] is False
    assert state["follow_up_question"] is None
    # Total core questions: 6 remaining + 1 current = 7
    assert len(state["core_questions_remaining"]) + 1 == 7


@pytest.mark.asyncio
async def test_get_first_question():
    """Returns first core question (core_0) as a valid InterviewQuestion."""
    state = await create_interview()
    question = InterviewQuestion.model_validate(state["current_question"])
    assert question.question_id == "core_0"
    assert question.question_type == "text"
    assert question.phase == "core"
    assert question.is_required is False


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
    assert loaded["needs_follow_up"] == state["needs_follow_up"]


@pytest.mark.asyncio
async def test_get_next_question_advances():
    """get_next_question pops the next core question from remaining."""
    state = await create_interview()
    assert state["current_question"]["question_id"] == "core_0"

    question, new_state = await get_next_question(state)
    assert question is not None
    assert question.question_id == "core_1"
    assert len(new_state["core_questions_remaining"]) == 5


# ---------- Interview "next question" endpoint ----------


def test_get_first_question_endpoint(client: TestClient) -> None:
    """New session → GET /interview/next → returns core_0, status becomes interviewing."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    resp = client.get(f"/api/v1/sessions/{session_id}/interview/next")
    assert resp.status_code == 200
    data = resp.json()
    assert data["question_id"] == "core_0"
    assert data["phase"] == "core"
    assert data["question_type"] == "text"
    assert data["is_required"] is False
    assert data["supports_audio"] is True
    assert "question_text" in data

    # Verify session status updated to interviewing
    session_resp = client.get(f"/api/v1/sessions/{session_id}")
    assert session_resp.json()["status"] == "interviewing"


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

    # Second call — same question (idempotent, no advancement)
    resp2 = client.get(f"/api/v1/sessions/{session_id}/interview/next")
    assert resp2.status_code == 200
    assert resp2.json()["question_id"] == resp1.json()["question_id"]


def test_interview_next_session_not_found(client: TestClient) -> None:
    """GET /interview/next for non-existent session → 404."""
    resp = client.get("/api/v1/sessions/nonexistent-id/interview/next")
    assert resp.status_code == 404


# ---------- Submit answer ----------


@pytest.mark.asyncio
async def test_submit_answer_service():
    """submit_answer stores the answer and advances to next question."""
    state = await create_interview()
    assert state["current_question"]["question_id"] == "core_0"

    # Answer core_0 (optional, skips follow-up) → advances to core_1
    next_q, new_state = await submit_answer(state, "core_0", "Sofia", "text")
    assert next_q is not None
    assert next_q.question_id == "core_1"
    assert len(new_state["answers"]) == 1
    assert new_state["answers"][0]["question_id"] == "core_0"


@pytest.mark.asyncio
async def test_submit_answer_wrong_question_id():
    """submit_answer raises ValueError on question_id mismatch."""
    state = await create_interview()
    with pytest.raises(ValueError, match="mismatch"):
        await submit_answer(state, "core_1", "wrong question", "text")


def test_submit_answer_endpoint(client: TestClient) -> None:
    """POST /interview/answer stores answer and returns next question."""
    from unittest.mock import patch, AsyncMock

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize interview (starts at core_0)
    client.get(f"/api/v1/sessions/{session_id}/interview/next")

    # Answer core_0 (optional, no follow-up) → core_1
    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/answer",
        json={"question_id": "core_0", "answer": "Sofia", "source": "text"},
    )
    assert resp.status_code == 200
    assert resp.json()["next_question"]["question_id"] == "core_1"

    # Submit answer to core_1 (mock follow-up to skip evaluation)
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        resp = client.post(
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": "core_1", "answer": "Mandamos WhatsApp no D+5, ligamos no D+15, judicial no D+60", "source": "text"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["received"] is True
    assert data["next_question"]["question_id"] == "core_2"


def test_submit_answer_chain(client: TestClient) -> None:
    """Submit answers to core_0 through core_3 — each returns next question."""
    from unittest.mock import patch, AsyncMock

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize interview (starts at core_0)
    client.get(f"/api/v1/sessions/{session_id}/interview/next")

    # Answer core_0 (optional, no mock needed)
    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/answer",
        json={"question_id": "core_0", "answer": "Sofia", "source": "text"},
    )
    assert resp.status_code == 200
    assert resp.json()["next_question"]["question_id"] == "core_1"

    # Answer core_1 (text, mock follow-up)
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        resp = client.post(
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": "core_1", "answer": "Processo de cobrança completo com etapas", "source": "text"},
        )
    assert resp.status_code == 200
    assert resp.json()["next_question"]["question_id"] == "core_2"

    # Answer core_2 with "nao" → no follow-up, advance to core_3
    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/answer",
        json={"question_id": "core_2", "answer": "nao", "source": "text"},
    )
    assert resp.status_code == 200
    assert resp.json()["next_question"]["question_id"] == "core_3"


def test_answer_stored_in_session(client: TestClient) -> None:
    """After submitting, answer appears in session's interview_responses."""
    from unittest.mock import patch, AsyncMock

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize and answer core_0 first (optional)
    client.get(f"/api/v1/sessions/{session_id}/interview/next")
    client.post(
        f"/api/v1/sessions/{session_id}/interview/answer",
        json={"question_id": "core_0", "answer": "Sofia", "source": "text"},
    )

    # Answer core_1 (mock follow-up to skip evaluation)
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        client.post(
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": "core_1", "answer": "Cobrança via WhatsApp e telefone", "source": "text"},
        )

    # Check session
    session_resp = client.get(f"/api/v1/sessions/{session_id}")
    session_data = session_resp.json()
    responses = session_data["interview_responses"]
    assert len(responses) == 2
    assert responses[0]["question_id"] == "core_0"
    assert responses[1]["question_id"] == "core_1"
    assert responses[1]["answer"] == "Cobrança via WhatsApp e telefone"
    assert responses[1]["source"] == "text"



def test_wrong_question_id_endpoint(client: TestClient) -> None:
    """Submit answer for wrong question_id → 400."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize interview (current = core_0)
    client.get(f"/api/v1/sessions/{session_id}/interview/next")

    # Submit answer for core_5 instead of core_0
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


# ---------- AI follow-up evaluation (core_1 only) ----------


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
    # Answer core_0 first (optional, no follow-up)
    _, state = await submit_answer(state, "core_0", "Sofia", "text")
    assert state["current_question"]["question_id"] == "core_1"

    mock_response = json.dumps({
        "needs_follow_up": True,
        "follow_up_question": "Pode descrever com mais detalhes as etapas do seu processo de cobrança?",
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
    assert len(new_state["answers"]) == 2  # core_0 + core_1
    assert new_state["answers"][1]["answer"] == "sim"


@pytest.mark.asyncio
async def test_detailed_answer_no_follow_up():
    """Detailed paragraph to core_1 → advances to core_2 normally."""
    from unittest.mock import patch

    state = await create_interview()
    # Answer core_0 first (optional, no follow-up)
    _, state = await submit_answer(state, "core_0", "Sofia", "text")

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
                "Nosso fluxo começa no D+5 com WhatsApp, D+15 ligação, D+30 notificação formal, D+60 jurídico.",
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
    # Answer core_0 first (optional, no follow-up)
    _, state = await submit_answer(state, "core_0", "Sofia", "text")

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
    assert len(state2["answers"]) == 2  # core_0 + core_1

    # Second: answer the follow-up with detail → no more follow-up (max=1), advance to core_2
    # With MAX_FOLLOW_UPS_PER_QUESTION=1, the follow-up answer is text but won't trigger
    # another LLM eval since it's a follow-up of core_1 (follow_up_count already = 1)
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
                "Nosso processo começa no D+5 com WhatsApp e vai até judicial no D+60",
                "text",
            )

    assert next_q2 is not None
    assert next_q2.question_id == "core_2"
    assert len(state3["answers"]) == 3  # core_0 + core_1 + followup
    assert state3["answers"][1]["question_id"] == "core_1"
    assert state3["answers"][2]["question_id"] == "followup_core_1_1"
    assert state3["follow_up_count"] == 0
    assert state3["needs_follow_up"] is False


def test_follow_up_endpoint_response(client: TestClient) -> None:
    """POST /answer with follow-up → response has both next_question and follow_up fields."""
    from unittest.mock import AsyncMock, MagicMock, patch

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize interview (starts at core_0)
    client.get(f"/api/v1/sessions/{session_id}/interview/next")

    # Answer core_0 first (optional, no follow-up)
    client.post(
        f"/api/v1/sessions/{session_id}/interview/answer",
        json={"question_id": "core_0", "answer": "Sofia", "source": "text"},
    )

    # Mock OpenAI to trigger follow-up on core_1
    fu_response = json.dumps({
        "needs_follow_up": True,
        "follow_up_question": "Pode descrever melhor o processo de cobrança?",
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


# ---------- Frustration detection ----------


@pytest.mark.asyncio
async def test_frustration_signal_skips_follow_up():
    """Answer with frustration signal skips follow-up without LLM call."""
    from unittest.mock import patch

    state = await create_interview()
    # Answer core_0 first (optional, no follow-up)
    _, state = await submit_answer(state, "core_0", "Sofia", "text")

    mock_response = json.dumps({
        "needs_follow_up": True,
        "follow_up_question": "Pode descrever melhor?",
        "reason": "Curto",
    })
    mock_client = _mock_openai_response(mock_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q, new_state = await submit_answer(
                state, "core_1", "isso vocês que sabem, não é meu trabalho", "text",
            )

    # Should advance to core_2 without follow-up (frustration detected)
    assert next_q is not None
    assert next_q.question_id == "core_2"
    assert new_state["needs_follow_up"] is False
    # LLM should NOT have been called (frustration short-circuited)
    mock_client.chat.completions.create.assert_not_called()


# ---------- Deterministic policy follow-ups (core_2-5) ----------


@pytest.mark.asyncio
async def test_deterministic_followup_sim():
    """core_2 answered 'sim' → deterministic follow-up about juros."""
    state = await create_interview()
    _, state = await submit_answer(state, "core_0", "Sofia", "text")
    from unittest.mock import patch, AsyncMock
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        _, state = await submit_answer(state, "core_1", "Processo completo de cobrança descrito em detalhe", "text")
    assert state["current_question"]["question_id"] == "core_2"

    # Answer core_2 with "sim" → deterministic follow-up
    next_q, new_state = await submit_answer(state, "core_2", "sim", "text")
    assert next_q is not None
    assert next_q.question_id == "followup_core_2_1"
    assert next_q.phase == "follow_up"
    assert "juros" in next_q.question_text.lower()
    assert new_state["needs_follow_up"] is True
    assert new_state["follow_up_count"] == 1


@pytest.mark.asyncio
async def test_deterministic_followup_nao():
    """core_2 answered 'nao' → no follow-up, advances to core_3."""
    state = await create_interview()
    _, state = await submit_answer(state, "core_0", "Sofia", "text")
    from unittest.mock import patch, AsyncMock
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        _, state = await submit_answer(state, "core_1", "Processo completo de cobrança descrito em detalhe", "text")
    assert state["current_question"]["question_id"] == "core_2"

    # Answer core_2 with "nao" → no follow-up
    next_q, new_state = await submit_answer(state, "core_2", "nao", "text")
    assert next_q is not None
    assert next_q.question_id == "core_3"
    assert new_state["needs_follow_up"] is False


@pytest.mark.asyncio
async def test_policy_followup_no_second_followup():
    """Answer to follow-up of core_2 does NOT generate another follow-up, advances to core_3."""
    state = await create_interview()
    _, state = await submit_answer(state, "core_0", "Sofia", "text")
    from unittest.mock import patch, AsyncMock
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        _, state = await submit_answer(state, "core_1", "Processo completo de cobrança descrito em detalhe", "text")

    # core_2 "sim" → follow-up
    next_q, state = await submit_answer(state, "core_2", "sim", "text")
    assert next_q.question_id == "followup_core_2_1"

    # Answer the follow-up → should advance to core_3, no more follow-up
    next_q2, state2 = await submit_answer(state, "followup_core_2_1", "2% ao mês", "text")
    assert next_q2 is not None
    assert next_q2.question_id == "core_3"
    assert state2["follow_up_count"] == 0
    assert state2["needs_follow_up"] is False


@pytest.mark.asyncio
async def test_all_core_exhausted_goes_to_review():
    """After answering all 7 core questions → phase='review' directly (no dynamic)."""
    from unittest.mock import patch, AsyncMock

    state = await create_interview()
    # core_0 (optional)
    _, state = await submit_answer(state, "core_0", "Sofia", "text")
    # core_1 (text, mock LLM follow-up)
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        _, state = await submit_answer(state, "core_1", "Processo completo de cobrança", "text")
    # core_2 (nao)
    _, state = await submit_answer(state, "core_2", "nao", "text")
    # core_3 (nao)
    _, state = await submit_answer(state, "core_3", "nao", "text")
    # core_4 (nao)
    _, state = await submit_answer(state, "core_4", "nao", "text")
    # core_5 (nao)
    _, state = await submit_answer(state, "core_5", "nao", "text")
    # core_6 (optional)
    next_q, state = await submit_answer(state, "core_6", "Não", "text")

    assert next_q is None
    assert state["phase"] == "review"


# ---------- core_0 agent name question ----------


@pytest.mark.asyncio
async def test_core_0_is_first_question():
    """core_0 is the very first question in the interview."""
    state = await create_interview()
    assert state["current_question"]["question_id"] == "core_0"
    assert state["current_question"]["is_required"] is False
    assert state["current_question"]["question_type"] == "text"
    # Verify it's first in CORE_QUESTIONS list
    assert CORE_QUESTIONS[0].question_id == "core_0"


@pytest.mark.asyncio
async def test_core_0_optional_skips_follow_up():
    """core_0 is optional — answering it skips follow-up evaluation (LLM not called)."""
    from unittest.mock import patch

    state = await create_interview()
    assert state["current_question"]["question_id"] == "core_0"

    mock_response = json.dumps({
        "needs_follow_up": True,
        "follow_up_question": "Pode explicar melhor o nome?",
        "reason": "Curto",
    })
    mock_client = _mock_openai_response(mock_response)

    with patch("app.services.interview_agent.AsyncOpenAI", return_value=mock_client):
        with patch("app.services.interview_agent.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            next_q, new_state = await submit_answer(state, "core_0", "Sofia", "text")

    # Should advance to core_1 without follow-up (optional question)
    assert next_q is not None
    assert next_q.question_id == "core_1"
    assert new_state["needs_follow_up"] is False
    # LLM should NOT have been called (optional question skips evaluation)
    mock_client.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
async def test_core_6_optional_skips_follow_up():
    """core_6 is optional — answering it skips follow-up evaluation."""
    from unittest.mock import patch, AsyncMock

    state = await create_interview()
    _, state = await submit_answer(state, "core_0", "Sofia", "text")
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up", new_callable=AsyncMock, return_value=(False, None)):
        _, state = await submit_answer(state, "core_1", "Processo completo", "text")
    _, state = await submit_answer(state, "core_2", "nao", "text")
    _, state = await submit_answer(state, "core_3", "nao", "text")
    _, state = await submit_answer(state, "core_4", "nao", "text")
    _, state = await submit_answer(state, "core_5", "nao", "text")

    assert state["current_question"]["question_id"] == "core_6"

    # core_6 is optional → should go to review without follow-up
    next_q, new_state = await submit_answer(state, "core_6", "Quando o cliente pede", "text")
    assert next_q is None
    assert new_state["phase"] == "review"
    assert new_state["needs_follow_up"] is False


# ---------- Progress endpoint ----------


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
    assert data["core_total"] == 7
    assert data["estimated_remaining"] == 7
    assert data["is_complete"] is False


def test_progress_midway(client: TestClient) -> None:
    """After answering a few core questions, progress reflects correctly."""
    from unittest.mock import AsyncMock, patch

    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://test.com"},
    )
    session_id = resp.json()["session_id"]

    # Initialize interview (starts at core_0)
    client.get(f"/api/v1/sessions/{session_id}/interview/next")

    # Answer core_0 (optional), core_1 and core_2
    client.post(
        f"/api/v1/sessions/{session_id}/interview/answer",
        json={"question_id": "core_0", "answer": "Sofia", "source": "text"},
    )
    with patch("app.services.interview_agent.evaluate_and_maybe_follow_up",
               new_callable=AsyncMock, return_value=(False, None)):
        client.post(
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": "core_1", "answer": "Processo de cobrança detalhado", "source": "text"},
        )
    client.post(
        f"/api/v1/sessions/{session_id}/interview/answer",
        json={"question_id": "core_2", "answer": "nao", "source": "text"},
    )

    resp = client.get(f"/api/v1/sessions/{session_id}/interview/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "core"
    assert data["core_answered"] == 3
    assert data["core_total"] == 7
    assert data["total_answered"] == 3
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

    # Simulate: core_0 + core_1 answered, currently on followup_core_1_1 (remaining has 5 items = core_2..core_6)
    db = next(app.dependency_overrides[get_db]())
    session = db.get(OnboardingSession, session_id)
    remaining = [
        {"question_id": f"core_{i}", "question_text": f"Q{i}",
         "question_type": "text", "options": None, "pre_filled_value": None,
         "is_required": True, "supports_audio": True, "phase": "core", "context_hint": None}
        for i in range(2, 7)
    ]
    state = {
        "enrichment_data": {},
        "core_questions_remaining": remaining,
        "current_question": {
            "question_id": "followup_core_1_1",
            "question_text": "Pode detalhar?",
            "question_type": "text", "options": None, "pre_filled_value": None,
            "is_required": False, "supports_audio": True, "phase": "follow_up", "context_hint": None,
        },
        "answers": [
            {"question_id": "core_0", "answer": "Sofia", "source": "text", "question_text": "Nome do agente"},
            {"question_id": "core_1", "answer": "Processo", "source": "text", "question_text": "Q1"},
        ],
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
    # core_0 + core_1 answered (popped from remaining), follow-up is current — should count as 2
    assert data["core_answered"] == 2
    assert data["total_answered"] == 2


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
    answers = [
        {"question_id": f"core_{i}", "answer": f"Resp {i}",
         "source": "text", "question_text": f"Q{i}"}
        for i in range(7)
    ]
    state = {
        "enrichment_data": {},
        "core_questions_remaining": [],
        "current_question": None,
        "answers": answers,
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
    assert data["core_answered"] == 7
    assert data["total_answered"] == 7
    assert data["estimated_remaining"] == 0
    assert data["is_complete"] is True

    # Verify session status transitioned to 'interviewed'
    session_resp = client.get(f"/api/v1/sessions/{session_id}")
    assert session_resp.json()["status"] == "interviewed"


def test_progress_session_not_found(client: TestClient) -> None:
    """GET /interview/progress for non-existent session → 404."""
    resp = client.get("/api/v1/sessions/nonexistent-id/interview/progress")
    assert resp.status_code == 404


# ---------- Review endpoints ----------


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
    answers = [
        {"question_id": f"core_{i}", "answer": f"Resp {i}",
         "source": "text", "question_text": f"Q{i}"}
        for i in range(7)
    ]
    state = {
        "enrichment_data": {},
        "core_questions_remaining": [],
        "current_question": None,
        "answers": answers,
        "phase": "review",
        "needs_follow_up": False,
        "follow_up_question": None,
        "follow_up_count": 0,
    }
    session.interview_state = serialize_state(state)
    interview_responses = [
        {"question_id": f"core_{i}", "answer": f"Resp {i}", "source": "text"}
        for i in range(7)
    ]
    session.interview_responses = interview_responses
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
    assert len(data["answers"]) == 7
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

    # Set interview_state to core phase (at core_0)
    db = next(app.dependency_overrides[get_db]())
    session = db.get(OnboardingSession, session_id)
    remaining = [
        {"question_id": f"core_{i}", "question_text": f"Q{i}",
         "question_type": "text", "options": None, "pre_filled_value": None,
         "is_required": True, "supports_audio": True, "phase": "core", "context_hint": None}
        for i in range(1, 7)
    ]
    state = {
        "enrichment_data": {},
        "core_questions_remaining": remaining,
        "current_question": {
            "question_id": "core_0", "question_text": "Nome do agente",
            "question_type": "text", "options": None, "pre_filled_value": None,
            "is_required": False, "supports_audio": True, "phase": "core", "context_hint": None,
        },
        "answers": [],
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
