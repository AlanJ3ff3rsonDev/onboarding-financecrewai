"""Core questions, policy follow-up map, and defaults for the interview."""

from app.models.schemas import InterviewQuestion, QuestionOption

CORE_QUESTIONS: list[InterviewQuestion] = [
    InterviewQuestion(
        question_id="core_0",
        question_text="Quer dar um nome ao seu agente de cobrança?",
        question_type="text",
        is_required=False,
        phase="core",
        context_hint="Exemplos: Sofia, Carlos, Ana. Dê um nome que represente sua marca. Se preferir, pode pular.",
    ),
    InterviewQuestion(
        question_id="core_1",
        question_text="Como funciona o processo de cobrança na sua empresa hoje? Descreva do início ao fim, passo a passo.",
        question_type="text",
        phase="core",
        context_hint="Quanto mais detalhes você fornecer, melhor o agente vai replicar seu processo.",
    ),
    InterviewQuestion(
        question_id="core_2",
        question_text="Vocês cobram juros por atraso?",
        question_type="select",
        options=[
            QuestionOption(value="sim", label="Sim"),
            QuestionOption(value="nao", label="Não"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_3",
        question_text="Vocês oferecem desconto para pagamento?",
        question_type="select",
        options=[
            QuestionOption(value="sim", label="Sim"),
            QuestionOption(value="nao", label="Não"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_4",
        question_text="Vocês permitem parcelamento da dívida?",
        question_type="select",
        options=[
            QuestionOption(value="sim", label="Sim"),
            QuestionOption(value="nao", label="Não"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_5",
        question_text="Vocês cobram multa por atraso?",
        question_type="select",
        options=[
            QuestionOption(value="sim", label="Sim"),
            QuestionOption(value="nao", label="Não"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_6",
        question_text="Tem alguma situação específica em que o agente deve passar a conversa para um atendente humano?",
        question_type="text",
        is_required=False,
        phase="core",
        context_hint="Exemplos: dívida acima de certo valor, cliente muito irritado, pedido de cancelamento. Se não houver, pode pular.",
    ),
]

# Deterministic follow-up questions for policy questions (core_2-5) when answered "sim"
POLICY_FOLLOWUP_MAP: dict[str, str] = {
    "core_2": "Como funciona a cobrança de juros? (percentual, periodicidade, etc.)",
    "core_3": "Como funciona o desconto? (percentual, condições, prazo, etc.)",
    "core_4": "Como funciona o parcelamento? (número máximo de parcelas, valor mínimo, etc.)",
    "core_5": "Como funciona a multa? (percentual, quando é aplicada, etc.)",
}

# Hardcoded defaults (previously collected via core_7, core_8)
DEFAULT_ESCALATION_TRIGGERS: list[str] = [
    "Devedor agressivo ou ameaçador",
    "Devedor solicitou falar com humano",
    "Menção de ação judicial",
    "Fraude ou dívida não reconhecida",
]

DEFAULT_GUARDRAILS: list[str] = [
    "Nunca ameaçar o devedor",
    "Nunca prometer algo que não pode cumprir",
    "Nunca mencionar outros devedores",
    "Nunca usar linguagem agressiva",
    "Nunca contatar fora do horário comercial",
]

DEFAULT_TONE: str = "amigável mas firme"

FOLLOW_UP_EVALUATION_PROMPT = """\
Você é um especialista em onboarding de agentes de cobrança. Está avaliando se a resposta \
de um cliente a uma pergunta é detalhada o suficiente para configurar um agente de cobrança \
de qualidade.

## Pergunta feita
{question_text}

## Resposta do cliente
{answer}

## Contexto (respostas anteriores)
{answers_context}

## Instrução
Avalie se a resposta é suficientemente detalhada para configurar um bom agente de cobrança. \
Respostas curtas ou vagas (como "sim", "normal", "não sei", "talvez") geralmente precisam \
de aprofundamento. Respostas com detalhes específicos, exemplos ou explicações claras são \
suficientes.

REGRAS CRÍTICAS:
- NÃO aprofunde conhecimento padrão de cobrança. O agente JÁ É ESPECIALISTA em cobrança. \
Não peça mais detalhes sobre como lidar com objeções genéricas ("já paguei", "não reconheço"), \
como abrir conversa, como lidar com devedor agressivo, etc. Esses cenários o agente já domina.
- Se o cliente sinalizar frustração, impaciência ou irritação (ex: "isso vocês que sabem", \
"isso é óbvio", "já respondi isso"), retorne needs_follow_up: false imediatamente.
- Só peça aprofundamento para informações ESPECÍFICAS DA EMPRESA que o agente não tem como saber \
sozinho (ex: políticas internas, valores, processos, exceções do negócio).

Responda EXCLUSIVAMENTE com um objeto JSON válido no formato:
{{"needs_follow_up": true/false, "follow_up_question": "pergunta de aprofundamento ou null", "reason": "motivo breve"}}

Se needs_follow_up for false, follow_up_question deve ser null.
Se needs_follow_up for true, gere uma pergunta de aprofundamento natural, específica e em \
português que ajude a extrair mais detalhes ESPECÍFICOS DA EMPRESA para configurar o agente.
"""
