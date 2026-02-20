"""End-to-end integration test: full onboarding flow with real OpenAI API."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Realistic answers for all 12 core questions
# ---------------------------------------------------------------------------

CORE_ANSWERS: dict[str, str] = {
    "core_1": (
        "A CollectAI oferece uma plataforma SaaS de cobranca digital que utiliza "
        "agentes virtuais inteligentes via WhatsApp para automatizar o processo de "
        "recuperacao de credito. Nossos produtos incluem agentes de cobranca "
        "automatizados, painel de gestao de inadimplencia, integracao com ERPs "
        "e sistemas bancarios, e analytics de performance de cobranca."
    ),
    "core_2": "pix,boleto,cartao_credito",
    "core_3": "d5",
    "core_4": (
        "Nosso fluxo de cobranca comeca no D+5 do vencimento com envio automatico "
        "de mensagem via WhatsApp lembrando a pendencia. No D+10 enviamos uma segunda "
        "mensagem com opcoes de parcelamento. No D+15 um operador humano liga para o "
        "devedor. No D+30 enviamos notificacao formal por email. No D+60 encaminhamos "
        "para cobranca juridica. Atualmente temos 10 pessoas na operacao de cobranca "
        "e queremos reduzir para 3 com a automacao."
    ),
    "core_5": "amigavel_firme",
    "core_6": "10",
    "core_7": "12",
    "core_8": "1_mes",
    "core_9": "2",
    "core_10": "solicita_humano,divida_alta,agressivo",
    "core_11": (
        "O agente nunca deve ameacar o devedor com negativacao ou processo judicial. "
        "Nunca mencionar SPC, Serasa ou cartorio. Nunca compartilhar dados do devedor "
        "com terceiros. Nunca usar linguagem agressiva ou intimidadora. Nunca prometer "
        "descontos que nao foram autorizados. Nunca ligar fora do horario comercial "
        "(08:00-20:00 segunda a sexta)."
    ),
    "core_12": (
        "As razoes mais comuns sao: 'ja paguei essa conta' (cerca de 30% dos casos), "
        "'nao reconheco essa divida' (20%), 'nao tenho dinheiro agora mas vou pagar "
        "semana que vem' (25%), 'quero falar com um gerente/humano' (10%), "
        "'vou processar voces' (5%), e 'estou desempregado' (10%). Para cada caso "
        "temos um script especifico de tratamento."
    ),
}

SMART_DEFAULTS_BODY: dict = {
    "follow_up_interval_days": 3,
    "max_contact_attempts": 10,
    "use_first_name": True,
    "identify_as_ai": True,
    "min_installment_value": 50.0,
    "discount_strategy": "only_when_resisted",
    "payment_link_generation": True,
    "max_discount_installment_pct": 5.0,
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

    # Handle follow-up loop (server caps at 2 follow-ups per question)
    follow_up_count = 0
    while follow_up_count < 3:
        next_q = data.get("next_question")
        if next_q is None:
            break
        if not next_q.get("question_id", "").startswith("followup_"):
            break

        fu_id = next_q["question_id"]
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


def _answer_dynamic_questions(
    client: TestClient,
    session_id: str,
    initial_data: dict,
) -> dict:
    """Answer dynamic questions in a loop until phase becomes 'defaults'."""
    data = initial_data
    dynamic_count = 0
    max_safety = 20  # 8 dynamic * 2 follow-ups + margin

    while dynamic_count < max_safety:
        # Check phase transitions
        if data.get("phase") == "defaults":
            return data
        if data.get("next_question") is None:
            # No next question — check via GET
            resp = client.get(f"/api/v1/sessions/{session_id}/interview/next")
            assert resp.status_code == 200
            check = resp.json()
            if check.get("phase") in ("defaults", "complete"):
                return check
            # The GET returned a question directly
            data = {"next_question": check}

        next_q = data.get("next_question")
        if next_q is None:
            break
        if next_q.get("phase") in ("defaults", "complete"):
            return data

        q_id = next_q["question_id"]
        q_text = next_q.get("question_text", "")

        answer = (
            f"Em relacao a '{q_text[:60]}': nossa abordagem e personalizada "
            "para cada perfil de devedor. Consideramos o valor da divida, "
            "historico de pagamento, tempo de atraso e o relacionamento com "
            "o cliente. Temos scripts especificos para cada cenario, com "
            "escalacao automatica quando o devedor nao responde em 48h ou "
            "quando o valor ultrapassa R$5.000. Nossa taxa de recuperacao "
            "atual e de 68% nos primeiros 30 dias."
        )

        data = _answer_question(client, session_id, q_id, answer)
        dynamic_count += 1

    return data


# ---------------------------------------------------------------------------
# Main test
# ---------------------------------------------------------------------------


def test_full_onboarding_flow(client: TestClient) -> None:
    """End-to-end: session -> enrichment -> interview -> agent -> simulation."""

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
    assert first_q["question_id"] == "core_1"
    assert first_q["phase"] == "core"

    # ── Step 5: Answer all 12 core questions ─────────────────────────────
    current_qid = "core_1"
    last_data: dict = {}
    for i in range(1, 13):
        expected_id = f"core_{i}"
        assert current_qid == expected_id, (
            f"Expected {expected_id}, got {current_qid}"
        )
        last_data = _answer_question(
            client, session_id, current_qid, CORE_ANSWERS[expected_id],
        )

        next_q = last_data.get("next_question")
        if next_q is None:
            break
        current_qid = next_q["question_id"]

    # Verify all 12 core questions answered
    resp = client.get(f"/api/v1/sessions/{session_id}/interview/progress")
    assert resp.status_code == 200
    progress = resp.json()
    assert progress["core_answered"] == 12

    # ── Step 6: Answer dynamic questions until defaults ──────────────────
    final_data = _answer_dynamic_questions(client, session_id, last_data)

    # Verify we reached defaults phase
    resp = client.get(f"/api/v1/sessions/{session_id}/interview/next")
    assert resp.status_code == 200
    phase_check = resp.json()
    assert phase_check["phase"] in ("defaults", "complete")

    # ── Step 7: Confirm smart defaults ───────────────────────────────────
    resp = client.get(f"/api/v1/sessions/{session_id}/interview/defaults")
    assert resp.status_code == 200
    assert resp.json()["confirmed"] is False

    resp = client.post(
        f"/api/v1/sessions/{session_id}/interview/defaults",
        json=SMART_DEFAULTS_BODY,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confirmed"] is True
    assert data["phase"] == "complete"

    # ── Step 8: Generate agent config ────────────────────────────────────
    resp = client.post(f"/api/v1/sessions/{session_id}/agent/generate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "generated"
    agent_config = data["agent_config"]
    assert len(agent_config["system_prompt"]) >= 200
    assert agent_config["company_context"]["name"]
    assert agent_config["tone"]["style"] in (
        "formal", "friendly", "empathetic", "assertive",
    )

    # ── Step 9: Verify agent config via GET ──────────────────────────────
    resp = client.get(f"/api/v1/sessions/{session_id}/agent")
    assert resp.status_code == 200
    stored = resp.json()
    assert stored["agent_type"] in ("compliant", "non_compliant")
    assert len(stored["negotiation_policies"]["payment_methods"]) > 0
    assert len(stored["guardrails"]["never_do"]) > 0
    assert len(stored["guardrails"]["never_say"]) > 0
    assert len(stored["scenario_responses"]["already_paid"]) > 0
    assert len(stored["tools"]) > 0
    assert stored["metadata"]["onboarding_session_id"] == session_id

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
    assert session["smart_defaults"] is not None
    assert session["agent_config"] is not None
    assert session["simulation_result"] is not None
