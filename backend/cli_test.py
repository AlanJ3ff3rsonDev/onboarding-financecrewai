#!/usr/bin/env python3
"""Interactive CLI to test the full onboarding flow against a running backend."""

import sys
import textwrap

import httpx

BASE = "http://localhost:8000"
TIMEOUT = 180.0  # seconds (LLM calls can be slow)

# ── ANSI colors ──────────────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
RESET = "\033[0m"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _post(client: httpx.Client, path: str, **kwargs) -> dict:
    resp = client.post(f"{BASE}{path}", **kwargs)
    if resp.status_code >= 400:
        print(f"\n{RED}Erro {resp.status_code}: {resp.text}{RESET}")
        sys.exit(1)
    return resp.json()


def _get(client: httpx.Client, path: str) -> dict:
    resp = client.get(f"{BASE}{path}")
    if resp.status_code >= 400:
        print(f"\n{RED}Erro {resp.status_code}: {resp.text}{RESET}")
        sys.exit(1)
    return resp.json()


def _ask_text(prompt: str, prefill: str | None = None) -> str:
    """Ask user for free text. If prefill exists, Enter accepts it."""
    if prefill:
        print(f"   {DIM}[sugestao do site: \"{prefill[:120]}...\"]{RESET}")
    while True:
        if prefill:
            answer = input(f"   {CYAN}Sua resposta (Enter para aceitar sugestao): {RESET}").strip()
            if not answer:
                return prefill
        else:
            answer = input(f"   {CYAN}Sua resposta: {RESET}").strip()
        if answer:
            return answer
        print(f"   {YELLOW}Resposta nao pode ser vazia.{RESET}")


def _ask_select(options: list[dict]) -> str:
    """Show numbered options, return the value of the selected one."""
    for i, opt in enumerate(options, 1):
        print(f"   [{i}] {opt['label']}")
    while True:
        choice = input(f"   {CYAN}Escolha (numero): {RESET}").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                selected = options[idx]
                print(f"   {DIM}-> {selected['label']}{RESET}")
                return selected["value"]
        except ValueError:
            pass
        print(f"   {YELLOW}Escolha invalida. Digite um numero de 1 a {len(options)}.{RESET}")


def _ask_multiselect(options: list[dict]) -> str:
    """Show numbered options, return comma-separated values."""
    for i, opt in enumerate(options, 1):
        print(f"   [{i}] {opt['label']}")
    while True:
        choice = input(f"   {CYAN}Escolha (numeros separados por virgula, ex: 1,3,4): {RESET}").strip()
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            if all(0 <= idx < len(options) for idx in indices) and indices:
                selected = [options[idx] for idx in indices]
                labels = ", ".join(o["label"] for o in selected)
                print(f"   {DIM}-> {labels}{RESET}")
                return ",".join(o["value"] for o in selected)
        except ValueError:
            pass
        print(f"   {YELLOW}Escolha invalida. Use numeros separados por virgula.{RESET}")


def _present_question(question: dict, number: int | None = None) -> str:
    """Present a question and collect the answer. Returns answer string."""
    q_type = question.get("question_type", "text")
    q_text = question["question_text"]
    q_id = question["question_id"]
    hint = question.get("context_hint")
    prefill = question.get("pre_filled_value")
    options = question.get("options")
    phase = question.get("phase", "")

    # Header
    if phase == "follow_up":
        label = f"   Aprofundamento sobre {q_id.replace('followup_', '').rsplit('_', 1)[0]}"
    elif phase == "dynamic":
        label = "   Pergunta adicional (IA)"
    elif number:
        label = f"   Pergunta {number}/12"
    else:
        label = f"   {q_id}"

    print(f"\n{BOLD}{label}: {q_text}{RESET}")
    if hint:
        print(f"   {DIM}Dica: {hint}{RESET}")

    if q_type == "text":
        return _ask_text("", prefill)
    elif q_type == "select" and options:
        return _ask_select(options)
    elif q_type == "multiselect" and options:
        return _ask_multiselect(options)
    else:
        return _ask_text("")


def _wrap(text: str, width: int = 80, indent: str = "   ") -> str:
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


# ── Main flow ────────────────────────────────────────────────────────────────


def main() -> None:
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  CollectAI — Teste Interativo do Onboarding{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{DIM}  Certifique-se de que o backend esta rodando em {BASE}{RESET}")
    print()

    # Check server is up
    try:
        httpx.get(f"{BASE}/health", timeout=5.0)
    except httpx.ConnectError:
        print(f"{RED}Erro: Backend nao esta rodando em {BASE}{RESET}")
        print(f"{DIM}  Rode: cd backend && uv run uvicorn app.main:app --port 8000{RESET}")
        sys.exit(1)

    # ── Step 1: Collect company info ─────────────────────────────────────
    print(f"{BOLD}1. Dados da empresa{RESET}")
    company_name = ""
    while not company_name:
        company_name = input(f"   {CYAN}Nome da empresa: {RESET}").strip()
    website = ""
    while not website:
        website = input(f"   {CYAN}Site da empresa: {RESET}").strip()
    cnpj = input(f"   {CYAN}CNPJ (opcional, Enter para pular): {RESET}").strip() or None

    client = httpx.Client(timeout=TIMEOUT)

    # ── Step 2: Create session ───────────────────────────────────────────
    print(f"\n{YELLOW}Criando sessao...{RESET}")
    body: dict = {"company_name": company_name, "website": website}
    if cnpj:
        body["cnpj"] = cnpj
    data = _post(client, "/api/v1/sessions", json=body)
    session_id = data["session_id"]
    print(f"   {GREEN}Sessao criada: {session_id}{RESET}")

    # ── Step 3: Enrich ───────────────────────────────────────────────────
    print(f"\n{YELLOW}Analisando o site {website}... (pode levar ~15s){RESET}")
    data = _post(client, f"/api/v1/sessions/{session_id}/enrich")
    enrichment = data["enrichment_data"]
    print(f"   {GREEN}Dados extraidos do site:{RESET}")
    for key in ("company_name", "segment", "products_description", "target_audience",
                "communication_tone", "payment_methods_mentioned"):
        val = enrichment.get(key, "")
        if val:
            print(f"   {DIM}{key}: {val[:120]}{RESET}")

    # ── Step 4: Interview — core questions ───────────────────────────────
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  Entrevista — 12 perguntas principais{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    data = _get(client, f"/api/v1/sessions/{session_id}/interview/next")
    core_count = 0

    while True:
        # Check if we left the core phase
        if data.get("phase") in ("defaults", "complete"):
            break
        if data.get("question_id") is None and data.get("next_question") is None:
            break

        # Current question (from GET /next or from POST /answer response)
        question = data if "question_id" in data else data.get("next_question")
        if question is None:
            break
        if not question.get("question_id", "").startswith("core_") and question.get("phase") != "follow_up":
            # Entered dynamic phase
            break

        # Track core question number
        if question.get("question_id", "").startswith("core_"):
            core_count += 1

        is_followup = question.get("phase") == "follow_up" or question.get("question_id", "").startswith("followup_")
        num = core_count if not is_followup else None
        answer = _present_question(question, number=num)

        # Submit answer
        data = _post(
            client,
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": question["question_id"], "answer": answer, "source": "text"},
        )

        # If next_question exists, continue from it; otherwise fetch
        next_q = data.get("next_question")
        if next_q:
            data = next_q
        else:
            data = _get(client, f"/api/v1/sessions/{session_id}/interview/next")

    # ── Step 5: Interview — dynamic questions ────────────────────────────
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  Perguntas adicionais geradas pela IA{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{DIM}  A IA vai fazer perguntas especificas para seu negocio.{RESET}")
    print(f"{DIM}  Responda com o maximo de detalhes possivel.{RESET}")

    dynamic_count = 0
    safety = 0

    while safety < 25:
        safety += 1
        if data.get("phase") in ("defaults", "complete"):
            break

        question = data if "question_id" in data else data.get("next_question")
        if question is None:
            data = _get(client, f"/api/v1/sessions/{session_id}/interview/next")
            if data.get("phase") in ("defaults", "complete"):
                break
            question = data
            if question.get("question_id") is None:
                break

        dynamic_count += 1
        answer = _present_question(question)

        data = _post(
            client,
            f"/api/v1/sessions/{session_id}/interview/answer",
            json={"question_id": question["question_id"], "answer": answer, "source": "text"},
        )

        next_q = data.get("next_question")
        if next_q:
            data = next_q
        else:
            data = _get(client, f"/api/v1/sessions/{session_id}/interview/next")

    print(f"\n   {GREEN}Entrevista concluida! ({core_count} perguntas + {dynamic_count} adicionais){RESET}")

    # ── Step 6: Smart defaults ───────────────────────────────────────────
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  Configuracoes padrao do agente{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    defaults_data = _get(client, f"/api/v1/sessions/{session_id}/interview/defaults")
    defaults = defaults_data["defaults"]

    LABELS = {
        "follow_up_interval_days": "Intervalo entre follow-ups (dias)",
        "max_contact_attempts": "Maximo de tentativas de contato",
        "use_first_name": "Usar primeiro nome do devedor",
        "identify_as_ai": "Identificar-se como IA",
        "min_installment_value": "Valor minimo da parcela (R$)",
        "discount_strategy": "Estrategia de desconto",
        "payment_link_generation": "Gerar link de pagamento",
        "max_discount_installment_pct": "Desconto max. parcelamento (%)",
    }

    STRATEGY_LABELS = {
        "only_when_resisted": "Apenas quando devedor resiste",
        "proactive": "Proativo (oferece logo)",
        "escalating": "Escalonado (aumenta aos poucos)",
    }

    print()
    for key, label in LABELS.items():
        val = defaults.get(key)
        if isinstance(val, bool):
            display = "Sim" if val else "Nao"
        elif key == "discount_strategy":
            display = STRATEGY_LABELS.get(str(val), str(val))
        else:
            display = str(val)
        print(f"   {label}: {BOLD}{display}{RESET}")

    accept = input(f"\n   {CYAN}Aceitar todos os padroes? (s/n): {RESET}").strip().lower()

    if accept != "s":
        print(f"\n   {DIM}Edite os valores (Enter para manter o atual):{RESET}")
        edited = dict(defaults)

        # follow_up_interval_days
        v = input(f"   Intervalo follow-ups (dias) [{defaults['follow_up_interval_days']}]: ").strip()
        if v:
            edited["follow_up_interval_days"] = int(v)

        # max_contact_attempts
        v = input(f"   Max tentativas [{defaults['max_contact_attempts']}]: ").strip()
        if v:
            edited["max_contact_attempts"] = int(v)

        # use_first_name
        v = input(f"   Usar primeiro nome? (s/n) [{'s' if defaults['use_first_name'] else 'n'}]: ").strip().lower()
        if v:
            edited["use_first_name"] = v == "s"

        # identify_as_ai
        v = input(f"   Identificar como IA? (s/n) [{'s' if defaults['identify_as_ai'] else 'n'}]: ").strip().lower()
        if v:
            edited["identify_as_ai"] = v == "s"

        # min_installment_value
        v = input(f"   Valor min. parcela R$ [{defaults['min_installment_value']}]: ").strip()
        if v:
            edited["min_installment_value"] = float(v)

        # discount_strategy
        print(f"   Estrategia de desconto [{STRATEGY_LABELS.get(defaults['discount_strategy'], defaults['discount_strategy'])}]:")
        print(f"     [1] Apenas quando devedor resiste")
        print(f"     [2] Proativo")
        print(f"     [3] Escalonado")
        v = input(f"   Escolha (1/2/3 ou Enter): ").strip()
        if v == "1":
            edited["discount_strategy"] = "only_when_resisted"
        elif v == "2":
            edited["discount_strategy"] = "proactive"
        elif v == "3":
            edited["discount_strategy"] = "escalating"

        # payment_link_generation
        v = input(f"   Gerar link pagamento? (s/n) [{'s' if defaults['payment_link_generation'] else 'n'}]: ").strip().lower()
        if v:
            edited["payment_link_generation"] = v == "s"

        # max_discount_installment_pct
        v = input(f"   Desconto max. parcelamento % [{defaults['max_discount_installment_pct']}]: ").strip()
        if v:
            edited["max_discount_installment_pct"] = float(v)

        defaults = edited

    data = _post(
        client,
        f"/api/v1/sessions/{session_id}/interview/defaults",
        json=defaults,
    )
    print(f"\n   {GREEN}Padroes confirmados!{RESET}")

    # ── Step 7: Generate agent ───────────────────────────────────────────
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  Gerando agente de cobranca...{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{YELLOW}  Isso pode levar ~15 segundos...{RESET}")

    data = _post(client, f"/api/v1/sessions/{session_id}/agent/generate")
    config = data["agent_config"]

    print(f"\n   {GREEN}Agente gerado com sucesso!{RESET}\n")

    # System prompt
    print(f"   {BOLD}System Prompt:{RESET}")
    print(_wrap(config["system_prompt"], width=78))

    # Tone
    tone = config.get("tone", {})
    print(f"\n   {BOLD}Tom:{RESET} {tone.get('style', '?')}")
    if tone.get("prohibited_words"):
        print(f"   {BOLD}Palavras proibidas:{RESET} {', '.join(tone['prohibited_words'])}")

    # Negotiation
    neg = config.get("negotiation_policies", {})
    print(f"\n   {BOLD}Negociacao:{RESET}")
    print(f"   Desconto max (a vista): {neg.get('max_discount_full_payment_pct', '?')}%")
    print(f"   Desconto max (parcelado): {neg.get('max_discount_installment_pct', '?')}%")
    print(f"   Max parcelas: {neg.get('max_installments', '?')}x")
    print(f"   Metodos: {', '.join(neg.get('payment_methods', []))}")

    # Guardrails
    guard = config.get("guardrails", {})
    print(f"\n   {BOLD}Guardrails:{RESET}")
    if guard.get("never_do"):
        for item in guard["never_do"][:5]:
            print(f"   - Nunca: {item}")
    if guard.get("escalation_triggers"):
        print(f"   Escalacao: {', '.join(guard['escalation_triggers'][:5])}")

    # Scenario responses
    scenarios = config.get("scenario_responses", {})
    print(f"\n   {BOLD}Respostas para cenarios:{RESET}")
    for key in ("already_paid", "dont_recognize_debt", "cant_pay_now", "aggressive_debtor"):
        val = scenarios.get(key, "")
        label = key.replace("_", " ").title()
        if val:
            print(f"   {label}:")
            print(_wrap(val[:200], width=78, indent="      "))

    # Tools
    tools = config.get("tools", [])
    if tools:
        print(f"\n   {BOLD}Ferramentas:{RESET} {', '.join(tools)}")

    # ── Step 8: Generate simulation ──────────────────────────────────────
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  Gerando simulacao de conversas...{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{YELLOW}  Gerando 2 conversas realistas... (~20 segundos){RESET}")

    data = _post(client, f"/api/v1/sessions/{session_id}/simulation/generate")
    sim = data["simulation_result"]

    for scenario in sim["scenarios"]:
        s_type = scenario["scenario_type"]
        profile = scenario.get("debtor_profile", "")
        outcome = scenario.get("outcome", "")
        metrics = scenario.get("metrics", {})
        resolution = metrics.get("resolution", "?")

        type_label = "Devedor cooperativo" if s_type == "cooperative" else "Devedor resistente"
        print(f"\n   {BOLD}{MAGENTA}--- {type_label} ---{RESET}")
        if profile:
            print(f"   {DIM}Perfil: {profile}{RESET}")
        print()

        for msg in scenario["conversation"]:
            role = msg["role"]
            content = msg["content"]
            if role == "agent":
                print(f"   {GREEN}Agente:{RESET} {content}")
            else:
                print(f"   {CYAN}Devedor:{RESET} {content}")
            print()

        print(f"   {BOLD}Resultado:{RESET} {outcome}")
        print(f"   {BOLD}Resolucao:{RESET} {resolution}")
        if metrics.get("negotiated_discount_pct") is not None:
            print(f"   Desconto: {metrics['negotiated_discount_pct']}%")
        if metrics.get("final_installments") is not None:
            print(f"   Parcelas: {metrics['final_installments']}x")

    # ── Final status ─────────────────────────────────────────────────────
    session = _get(client, f"/api/v1/sessions/{session_id}")
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{GREEN}{BOLD}  Onboarding completo!{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"   Session ID: {session_id}")
    print(f"   Status: {session['status']}")
    print(f"   Empresa: {session['company_name']}")
    print()

    client.close()


if __name__ == "__main__":
    main()
