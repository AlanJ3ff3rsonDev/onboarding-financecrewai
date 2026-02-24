"""End-to-end integration test: full onboarding flow with real OpenAI API."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Realistic answers for all 7 core questions
# ---------------------------------------------------------------------------

CORE_ANSWERS: dict[str, str] = {
    "core_0": "Sofia",
    "core_1": (
        "Nosso fluxo de cobranca comeca no D+5 do vencimento com envio automatico "
        "de mensagem via WhatsApp lembrando a pendencia. No D+10 enviamos uma segunda "
        "mensagem com opcoes de parcelamento. No D+15 um operador humano liga para o "
        "devedor. No D+30 enviamos notificacao formal por email. No D+60 encaminhamos "
        "para cobranca juridica. Atualmente temos 10 pessoas na operacao de cobranca "
        "e queremos reduzir para 3 com a automacao."
    ),
    "core_2": "sim",
    "core_3": "sim",
    "core_4": "sim",
    "core_5": "sim",
    "core_6": (
        "Quando o cliente e uma empresa parceira estrategica, devemos escalar para "
        "o gerente comercial. Tambem quando o devedor menciona acao judicial."
    ),
}

# Follow-up answers for policy questions answered "sim"
POLICY_FOLLOWUP_ANSWERS: dict[str, str] = {
    "followup_core_2_1": "Juros de 1% ao mes sobre o valor total da divida",
    "followup_core_3_1": "Desconto de ate 10% para pagamento a vista nos primeiros 30 dias",
    "followup_core_4_1": "Parcelamento em ate 12 vezes, parcela minima de R$50",
    "followup_core_5_1": "Multa de 2% sobre o valor da parcela vencida",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _answer_question(
    client: TestClient,
    session_id: str,
    question_id: str,
    answer: str,
) -> dict:
    """Submit an answer and handle any follow-up loop. Returns the final response."""
    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/answer",
        json={"question_id": question_id, "answer": answer, "source": "text"},
    )
    assert resp.status_code == 200, f"Failed answering {question_id}: {resp.text}"
    data = resp.json()
    assert data["received"] is True

    # Handle follow-up loop (deterministic for core_2-5, LLM for core_1)
    follow_up_count = 0
    while follow_up_count < 3:
        next_q = data.get("next_question")
        if next_q is None:
            break
        if not next_q.get("question_id", "").startswith("followup_"):
            break

        fu_id = next_q["question_id"]

        # Use specific policy follow-up answer if available, else generic
        if fu_id in POLICY_FOLLOWUP_ANSWERS:
            fu_answer = POLICY_FOLLOWUP_ANSWERS[fu_id]
        else:
            fu_answer = (
                f"Complementando: {answer[:100]}. "
                "Isso se aplica de forma padronizada a todos os nossos clientes, "
                "seguindo as politicas internas da empresa e as melhores praticas "
                "do mercado de cobranca digital no Brasil. Nosso time revisou esses "
                "processos recentemente e validou que funcionam bem para o nosso perfil."
            )
        resp = client.post(
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": fu_id, "answer": fu_answer, "source": "text"},
        )
        assert resp.status_code == 200, f"Failed follow-up {fu_id}: {resp.text}"
        data = resp.json()
        assert data["received"] is True
        follow_up_count += 1

    return data


# ---------------------------------------------------------------------------
# Main test
# ---------------------------------------------------------------------------


def test_full_onboarding_flow(client: TestClient) -> None:
    """End-to-end: session -> enrichment -> interview -> review -> agent -> simulation."""

    # ── Step 1: Create session ───────────────────────────────────────────
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "CollectAI", "website": "collectai.com.br"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert data["status"] == "created"
    session_id = data["session_id"]

    # ── Step 2: Trigger enrichment ───────────────────────────────────────
    resp = client.post(f"/api/v1/sessions/{session_id}/enrich")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "enriched"
    assert "enrichment_data" in data

    # ── Step 3: Verify enrichment ────────────────────────────────────────
    resp = client.get(f"/api/v1/sessions/{session_id}/enrichment")
    assert resp.status_code == 200
    enrichment = resp.json()
    assert enrichment["company_name"]  # non-empty
    assert len(enrichment["segment"]) > 0
    assert len(enrichment["products_description"]) > 0

    # ── Step 4: Start interview ──────────────────────────────────────────
    resp = client.get(f"/api/v1/sessions/{session_id}/interview/next")
    assert resp.status_code == 200
    first_q = resp.json()
    assert first_q["question_id"] == "core_0"
    assert first_q["phase"] == "core"

    # ── Step 5: Answer all 7 core questions ──────────────────────────────
    current_qid = "core_0"
    last_data: dict = {}
    core_answered = 0

    while current_qid in CORE_ANSWERS:
        last_data = _answer_question(
            client, session_id, current_qid, CORE_ANSWERS[current_qid],
        )
        core_answered += 1

        next_q = last_data.get("next_question")
        if next_q is None:
            break
        current_qid = next_q["question_id"]

    assert core_answered == 7, f"Expected 7 core answers, got {core_answered}"

    # Verify all 7 core questions answered
    resp = client.get(f"/api/v1/sessions/{session_id}/interview/progress")
    assert resp.status_code == 200
    progress = resp.json()
    assert progress["core_answered"] == 7

    # ── Step 6: Verify we reached review phase ───────────────────────────
    resp = client.get(f"/api/v1/sessions/{session_id}/interview/next")
    assert resp.status_code == 200
    phase_check = resp.json()
    assert phase_check["phase"] in ("review", "complete")

    # ── Step 7: Review and confirm ───────────────────────────────────────
    resp = client.get(f"/api/v1/sessions/{session_id}/interview/review")
    assert resp.status_code == 200
    review_data = resp.json()
    assert isinstance(review_data["answers"], list)
    assert len(review_data["answers"]) >= 7

    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/review",
        json={"confirmed": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confirmed"] is True
    assert data["phase"] == "complete"

    # ── Step 8: Generate onboarding report ────────────────────────────────
    resp = client.post(f"/api/v1/sessions/{session_id}/agent/generate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "generated"
    report = data["onboarding_report"]
    assert len(report["expert_recommendations"]) >= 200
    assert report["company"]["name"]
    assert report["communication"]["tone_style"] in (
        "formal", "friendly", "empathetic", "assertive",
    )

    # ── Step 9: Verify report via GET ────────────────────────────────────
    resp = client.get(f"/api/v1/sessions/{session_id}/agent")
    assert resp.status_code == 200
    stored = resp.json()
    assert len(stored["expert_recommendations"]) >= 200
    assert len(stored["collection_policies"]["payment_methods"]) > 0
    assert len(stored["collection_policies"]["discount_policy"]) > 0
    assert len(stored["collection_policies"]["installment_policy"]) > 0
    assert len(stored["guardrails"]["never_do"]) > 0
    assert len(stored["guardrails"]["never_say"]) > 0
    assert stored["metadata"]["session_id"] == session_id

    # ── Step 10: Generate simulation ─────────────────────────────────────
    resp = client.post(f"/api/v1/sessions/{session_id}/simulation/generate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert len(data["simulation_result"]["scenarios"]) == 2

    # ── Step 11: Verify simulation + final session state ─────────────────
    resp = client.get(f"/api/v1/sessions/{session_id}/simulation")
    assert resp.status_code == 200
    sim = resp.json()
    assert len(sim["scenarios"]) == 2

    for scenario in sim["scenarios"]:
        assert scenario["scenario_type"] in ("cooperative", "resistant")
        assert len(scenario["conversation"]) >= 4
        assert len(scenario["outcome"]) > 0
        assert scenario["metrics"]["resolution"] in (
            "full_payment", "installment_plan", "escalated", "no_resolution",
        )
        for msg in scenario["conversation"]:
            assert msg["role"] in ("agent", "debtor")
            assert len(msg["content"]) > 0

    # Final session state
    resp = client.get(f"/api/v1/sessions/{session_id}")
    assert resp.status_code == 200
    session = resp.json()
    assert session["status"] == "completed"
    assert session["enrichment_data"] is not None
    assert session["interview_responses"] is not None
    assert session["agent_config"] is not None
    assert session["simulation_result"] is not None
