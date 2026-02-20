"""Core questions, dynamic question bank, and smart defaults for the interview."""

from app.models.schemas import InterviewQuestion, QuestionOption, SmartDefaults

CORE_QUESTIONS: list[InterviewQuestion] = [
    InterviewQuestion(
        question_id="core_1",
        question_text="O que sua empresa vende ou oferece?",
        question_type="text",
        phase="core",
        context_hint="Se já extraímos informações do seu site, o campo estará pré-preenchido. Confirme ou corrija.",
    ),
    InterviewQuestion(
        question_id="core_2",
        question_text="Como seus clientes normalmente pagam?",
        question_type="multiselect",
        options=[
            QuestionOption(value="pix", label="PIX"),
            QuestionOption(value="boleto", label="Boleto"),
            QuestionOption(value="cartao_credito", label="Cartão de crédito"),
            QuestionOption(value="transferencia", label="Transferência bancária"),
            QuestionOption(value="dinheiro", label="Dinheiro"),
            QuestionOption(value="outro", label="Outro"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_3",
        question_text="Quando você considera uma conta vencida?",
        question_type="select",
        options=[
            QuestionOption(value="d0", label="No dia do vencimento (D+0)"),
            QuestionOption(value="d1", label="1 dia após (D+1)"),
            QuestionOption(value="d5", label="5 dias após (D+5)"),
            QuestionOption(value="d15", label="15 dias após (D+15)"),
            QuestionOption(value="d30", label="30 dias após (D+30)"),
            QuestionOption(value="outro", label="Outro"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_4",
        question_text="Descreva seu fluxo de cobrança atual — desde o primeiro atraso até a resolução",
        question_type="text",
        phase="core",
        context_hint="Quanto mais detalhes você fornecer, melhor o agente vai replicar seu processo.",
    ),
    InterviewQuestion(
        question_id="core_5",
        question_text="Qual tom o agente deve usar?",
        question_type="select",
        options=[
            QuestionOption(value="formal", label="Formal"),
            QuestionOption(value="amigavel_firme", label="Amigável mas firme"),
            QuestionOption(value="empatico", label="Empático"),
            QuestionOption(value="direto_assertivo", label="Direto/assertivo"),
            QuestionOption(value="depende", label="Depende (explique)"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_6",
        question_text="Vocês oferecem desconto para pagamento integral imediato? Se sim, qual o máximo?",
        question_type="select",
        options=[
            QuestionOption(value="nenhum", label="Não oferecemos desconto"),
            QuestionOption(value="5", label="Até 5%"),
            QuestionOption(value="10", label="Até 10%"),
            QuestionOption(value="15", label="Até 15%"),
            QuestionOption(value="20", label="Até 20%"),
            QuestionOption(value="30", label="Até 30%"),
            QuestionOption(value="50", label="Até 50%"),
            QuestionOption(value="outro", label="Outro (especifique)"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_7",
        question_text="Vocês oferecem parcelamento? Se sim, qual o número máximo de parcelas?",
        question_type="select",
        options=[
            QuestionOption(value="nenhum", label="Não oferecemos parcelamento"),
            QuestionOption(value="2", label="2x"),
            QuestionOption(value="3", label="3x"),
            QuestionOption(value="4", label="4x"),
            QuestionOption(value="6", label="6x"),
            QuestionOption(value="10", label="10x"),
            QuestionOption(value="12", label="12x"),
            QuestionOption(value="18", label="18x"),
            QuestionOption(value="24", label="24x"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_8",
        question_text="Vocês cobram juros por atraso? Se sim, qual a taxa?",
        question_type="select",
        options=[
            QuestionOption(value="nenhum", label="Não cobramos juros"),
            QuestionOption(value="1_mes", label="1% ao mês"),
            QuestionOption(value="2_mes", label="2% ao mês"),
            QuestionOption(value="3_mes", label="3% ao mês"),
            QuestionOption(value="outro", label="Outro (especifique)"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_9",
        question_text="Vocês cobram multa por atraso? Se sim, qual o percentual?",
        question_type="select",
        options=[
            QuestionOption(value="nenhum", label="Não cobramos multa"),
            QuestionOption(value="2", label="2%"),
            QuestionOption(value="5", label="5%"),
            QuestionOption(value="10", label="10%"),
            QuestionOption(value="outro", label="Outro (especifique)"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_10",
        question_text="Quando o agente deve escalar para um humano?",
        question_type="multiselect",
        options=[
            QuestionOption(value="solicita_humano", label="Devedor solicita humano"),
            QuestionOption(value="divida_alta", label="Dívida acima de X valor"),
            QuestionOption(value="acao_judicial", label="Menção de ação judicial"),
            QuestionOption(value="tentativas_falhadas", label="Após N tentativas falhadas"),
            QuestionOption(value="agressivo", label="Devedor agressivo"),
            QuestionOption(value="fraude", label="Fraude/dívida não reconhecida"),
            QuestionOption(value="outro", label="Outro"),
        ],
        phase="core",
    ),
    InterviewQuestion(
        question_id="core_11",
        question_text="Coisas que o agente NUNCA deve fazer ou dizer",
        question_type="text",
        phase="core",
        context_hint="Exemplos: nunca ameaçar, nunca mencionar nome de outros devedores, nunca prometer algo que não pode cumprir.",
    ),
    InterviewQuestion(
        question_id="core_12",
        question_text="Quais são as razões mais comuns que os devedores dão para não pagar?",
        question_type="text",
        phase="core",
        context_hint="Exemplos: 'já paguei', 'não reconheço essa dívida', 'não tenho dinheiro agora', 'vou pagar semana que vem'.",
    ),
]

DYNAMIC_QUESTION_BANK: dict[str, list[str]] = {
    "business_model": [
        "A cobrança é recorrente (assinatura/mensalidade) ou pontual?",
        "Qual o ticket médio das dívidas que você cobra?",
        "Seus clientes são pessoas físicas (B2C) ou empresas (B2B)?",
    ],
    "debtor_profile": [
        "Existe um relacionamento contínuo com o devedor (risco de churn)?",
        "Qual o perfil típico dos seus devedores inadimplentes?",
    ],
    "negotiation_depth": [
        "Descontos devem ser oferecidos proativamente ou só quando o devedor resiste?",
        "Desconto máximo para parcelamento?",
        "Existem regras diferentes de desconto por faixa de valor da dívida?",
    ],
    "scenario_handling": [
        "Como o agente deve lidar quando o devedor diz 'já paguei'?",
        "Como o agente deve lidar quando o devedor diz 'não reconheço essa dívida'?",
        "O que fazer quando o devedor diz que não pode pagar agora?",
    ],
    "legal_judicial": [
        "Você tem um processo de cobrança judicial para dívidas maiores?",
        "Acima de qual valor a dívida vai para cobrança judicial?",
    ],
    "communication": [
        "Como o agente deve abrir a conversa?",
        "Existem palavras ou expressões que devem ser evitadas?",
        "Existem palavras ou expressões preferidas da sua marca?",
    ],
    "segmentation": [
        "Você segmenta as dívidas por valor ou tempo de atraso?",
        "Existem regras diferentes para segmentos diferentes?",
    ],
    "current_pain": [
        "O que mais frustra você no processo de cobrança atual?",
        "Como seria o cenário ideal de cobrança para você?",
    ],
}

SMART_DEFAULTS = SmartDefaults()

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

Responda EXCLUSIVAMENTE com um objeto JSON válido no formato:
{{"needs_follow_up": true/false, "follow_up_question": "pergunta de aprofundamento ou null", "reason": "motivo breve"}}

Se needs_follow_up for false, follow_up_question deve ser null.
Se needs_follow_up for true, gere uma pergunta de aprofundamento natural, específica e em \
português que ajude a extrair mais detalhes úteis para configurar o agente de cobrança.
"""

DYNAMIC_QUESTION_PROMPT = """\
Você é um especialista em onboarding de agentes de cobrança. Está conduzindo uma \
entrevista para configurar um agente de cobrança personalizado.

## Dados da empresa (extraídos do site)
{enrichment_context}

## Respostas coletadas até agora
{answers_context}

## Banco de categorias de perguntas dinâmicas
{question_bank}

## Instrução
Com base em tudo que você sabe até agora, qual é a ÚNICA pergunta mais importante que \
ainda falta ser respondida para criar um excelente agente de cobrança para esta empresa?

Considere:
- O que ainda não está claro sobre o processo de cobrança?
- Quais cenários o agente pode enfrentar que ainda não foram cobertos?
- Quais políticas ou regras estão faltando?
- NÃO repita perguntas já feitas (veja as respostas acima)
- A pergunta deve ser específica ao negócio/segmento desta empresa

Responda EXCLUSIVAMENTE com um objeto JSON válido no formato:
{{"question_text": "a pergunta em português", "category": "categoria do banco de perguntas", "reason": "motivo breve de por que esta pergunta é importante"}}
"""

INTERVIEW_COMPLETENESS_PROMPT = """\
Você é um especialista em onboarding de agentes de cobrança. Avalie se temos informações \
suficientes para gerar um agente de cobrança de alta qualidade.

## Dados da empresa (extraídos do site)
{enrichment_context}

## Todas as respostas coletadas
{answers_context}

## Perguntas dinâmicas já feitas: {dynamic_count} de {max_dynamic}

## Instrução
Avalie de 1 a 10 o quão confiante você está de que temos dados suficientes para gerar \
um agente de cobrança completo e eficaz para esta empresa.

Critérios:
- 1-3: Faltam informações críticas (processo de cobrança, políticas de desconto, tom)
- 4-6: Temos o básico mas faltam detalhes importantes para cenários específicos
- 7-8: Temos informações suficientes para um bom agente, poucos gaps
- 9-10: Cobertura excelente, agente será muito personalizado

Responda EXCLUSIVAMENTE com um objeto JSON válido no formato:
{{"confidence": 7, "reason": "motivo breve", "missing_area": "área que ainda falta ou null se confiança >= 7"}}
"""
