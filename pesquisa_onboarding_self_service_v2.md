# Pesquisa: Onboarding Self-Service CollectAI

## Finance Crew AI / CollectAI

**Data:** 18 de Fevereiro de 2026
**Versão:** 2.0
**Classificação:** Documento Interno — Estratégico

---

# Sumário Executivo

## O Problema

O crescimento da CollectAI está limitado pela capacidade de onboarding manual. Hoje, cada novo cliente passa por uma call individual com o fundador, onde são coletados dados sobre a empresa, fluxo de cobrança, políticas e preferências. Com isso, o agente de cobrança é criado manualmente — prompt, tools, guardrails, políticas de desconto e tom de voz.

Esse processo limita a aquisição a **5-10 calls por semana**, criando um gargalo direto no crescimento. O time fundador trabalha 1-2 horas por dia (todos têm empregos paralelos), o que torna o modelo atual insustentável para escalar além de poucos clientes por mês.

## A Solução Proposta

Criar um **onboarding self-service** onde o cliente:

1. **Se cadastra** e informa CNPJ/site da empresa
2. **Tem seus dados enriquecidos automaticamente** (site da empresa via scraping + LLM, CNPJ básico via BrasilAPI gratuito)
3. **Responde perguntas** via wizard híbrido (formulários estruturados + chat com IA que gera follow-ups inteligentes), podendo responder por texto ou áudio
4. **Escolhe o tipo de agente** (cobrança adimplente ou inadimplente)
5. **Vê o agente gerado em ação** — simulação agent-to-agent (agente de cobrança vs. devedor simulado) como AHA Moment
6. **Revisa, ajusta e aprova** o agente
7. **Cadastra pagamento** e lança a primeira campanha

## Impacto Esperado

- **Time-to-value**: de dias (agendamento + call + criação manual) para **15-30 minutos**
- **Escalabilidade**: de 5-10 clientes/semana para self-service ilimitado
- **Custo de aquisição**: redução significativa ao eliminar horas de call por cliente
- **Experiência**: AHA Moment imediato com simulação do agente em ação

## Decisões Estratégicas Chave

1. **Padrão de UX**: Wizard híbrido + chat conversacional
2. **Frontend**: Construído no Lovable, conectado ao backend via API REST
3. **Backend**: FastAPI como API-first, independente do frontend
4. **Enriquecimento**: Foco no que importa — wizard/SOP (80%+ da qualidade) + site scraping + CNPJ gratuito
5. **Geração de agentes**: Context engineering com structured output (JSON)
6. **Guardrails**: Camada separada (não mais in-prompt)
7. **Simulação**: Agent-to-agent com debtor simulator calibrado por segmento
8. **Monetização**: Modelo híbrido (base mensal + créditos por uso)
9. **Framework de agentes**: Avaliação LangGraph vs. OpenAI Agents SDK vs. alternativas

---

# PARTE 1: Contexto de Mercado e Benchmarks

## 1.1 Panorama da Inadimplência no Brasil

### Números Gerais (2025)

O Brasil encerrou 2025 com níveis recordes de inadimplência, consolidando um cenário de oportunidade massiva para soluções de cobrança automatizada.

**Dados Serasa Experian:**
- **81,2 milhões de pessoas inadimplentes** em dezembro de 2025 — o maior número da história
- Isso representa aproximadamente **50% da população adulta** do país
- Total de dívidas de consumidores: estimado em **R$ 518 bilhões+**
- Média de **4 dívidas por pessoa**
- O ano começou com 74,6 milhões e cresceu 8,85% ao longo de 12 meses

**Dados CNDL/SPC Brasil:**
- 73,49 milhões de consumidores inadimplentes (metodologia diferente da Serasa)
- Crescimento de 5,29% ano a ano
- Taxa de reincidência: **83,81%** — ou seja, a cada 10 consumidores que entram em inadimplência, mais de 8 já foram inadimplentes antes

**Perfil Demográfico:**
- Mulheres representam 50,4% dos inadimplentes
- Faixa etária mais afetada: 41-60 anos (35,6%)
- Comprometimento da renda familiar com dívidas: **28,5%** em setembro/2025 — recorde desde 2005 (dados Banco Central)

### Inadimplência por Setor (Dívidas de Consumidores)

Dados Serasa dezembro/2025:
- **Bancos e cartões de crédito**: 26,1%
- **Serviços básicos** (água, luz, gás): 22,1%
- **Instituições financeiras**: 19,6%
- **Serviços**: 11,9%

Destaque para cartão de crédito rotativo: inadimplência atingiu **recorde histórico de 64,7%** em dezembro/2025, com juros de **438% ao ano**.

### Inadimplência Corporativa

**Dados Serasa Experian:**
- **8,9 milhões de empresas inadimplentes** em novembro/2025 — recorde desde o início da série em 2016
- Total de dívidas corporativas: **R$ 210,8 bilhões**
- **31,6%** de todos os CNPJs ativos estavam inadimplentes
- 8,2 milhões eram micro, pequenas e médias empresas

**Por setor:**
- Serviços: 54,9% (maior fatia)
- Comércio: 33%
- Indústria: 8%
- Outros: 3,1%
- Setor primário: 0,9%

### Taxas de Recuperação e Tendências

A recuperação de crédito está em queda acentuada:
- **Queda de 12,57%** na recuperação nos 12 meses encerrados em junho/2025
- **Queda de 12,61%** no número de consumidores que limparam o nome
- Em dezembro/2025: 5,2 milhões de acordos de renegociação, com R$ 14,3 bilhões em descontos concedidos

**Taxas de recuperação por aging da dívida** — dados críticos para a CollectAI:
- 1-10 dias de atraso: recuperação de até **98%**
- 31-60 dias: cai para **56-60%**
- 6 meses a 1 ano: despenca para **20%**

> **Insight estratégico**: A velocidade do contato é a variável mais importante na recuperação. Cada dia de atraso reduz drasticamente a probabilidade de pagamento. Isso favorece fortemente a automação via IA, que pode agir imediatamente após a identificação do atraso.

### Projeções 2026

**Pesquisa Febraban (dezembro/2025, 20 bancos):**
- Taxa de inadimplência do crédito livre: projetada em **5,2% para 2026** (vs. 5,1% em 2025)
- Crescimento do crédito: desaceleração gradual para **8,2% em 2026**
- 73,7% dos analistas esperam desaceleração do crédito
- 70% dos bancos projetam início do ciclo de corte da Selic no **Q1 2026**
- Selic projetada: **12,25% em dezembro/2026** (vs. 15,25% atual)
- Alívio nas condições de crédito esperado apenas no **final de 2026** (lag de 6-9 meses)

**Fontes:**
- Serasa Mapa da Inadimplência (serasa.com.br)
- CNDL/SPC Brasil — Recorde de inadimplentes
- Febraban — Pesquisa economia bancária dez/2025
- ANBC — Perspectivas 2026

---

## 1.2 Mercado de Cobrança Digital e IA

### Tamanho do Mercado Global

| Segmento | Valor 2024 | Projeção | CAGR |
|----------|-----------|----------|------|
| **IA para Cobrança** | USD 3,34 bi | USD 15,9 bi (2034) | 16,90% |
| **Software de Cobrança** | USD 3,30 bi | USD 7,74 bi (2033) | 9,95% |
| **Serviços de Cobrança** | USD 47,7 bi | USD 69,1 bi (2035) | 3,70% |

**Mercado brasileiro de software de cobrança**: CAGR de **11,8%** entre 2025-2031.

### Impacto Comprovado da IA na Cobrança

- **McKinsey**: IA melhora taxas de recuperação em **até 25%**; segmentação por IA pode elevar a recuperação em **15-25%** enquanto reduz custos em **até 70%**
- **Juniper Research**: Instituições financeiras com IA agentic viram **31% de melhoria** nas taxas de recuperação
- **Dado geral**: IA pode quadruplicar a produtividade dos cobradores (2-4x) e reduzir custos operacionais em **30-50%**
- **Adoção**: 61% das empresas adotaram analytics preditivo e 55% comunicação automatizada com consumidores

### Tendências-Chave do Mercado

**1. IA Conversacional**
- Até 2025, chatbots com IA esperados para lidar com **75% das interações** em cobrança
- Gartner projeta que **90% das funções financeiras** usarão IA até 2026
- Agentes autônomos (negociam, decidem, adaptam) vs. chatbots simples (respostas fixas)

**2. WhatsApp-First**
- WhatsApp: **3,2 bilhões de usuários** globalmente em 2025
- No Brasil: **76% dos consumidores** preferem comunicar com empresas via WhatsApp para negociação de dívidas
- Taxas de entrega: **95%+**; taxas de engajamento: **78-90%**
- Tempos de resolução **30-40% mais rápidos** via WhatsApp

**Fontes:**
- Market.us — AI for Debt Collection Market
- Mordor Intelligence — Debt Collection Software Market
- 6W Research — Brazil Debt Collection Software Market

---

## 1.3 Análise Competitiva: Uma Avaliação Honesta

### Premissa

Esta seção não repete os diferenciais que a CollectAI já afirma ter. Em vez disso, analisa criticamente se esses diferenciais são reais, se são únicos, e o que os competidores já fazem.

### Panorama: Competidores por Nível de Ameaça

| Empresa | Ameaça | Motivo |
|---------|--------|--------|
| **Neofin** | MUITO ALTA | R$ 35M captados, 300+ clientes, régua IA + WhatsApp, plataforma completa |
| **Monest (MIA)** | MUITO ALTA | Mesma tech (GPT-4), R$ 500M em acordos, 6M+ conversas, IA de voz lançando |
| **EaseCob.ai** | ALTA | Arquitetura multi-agente idêntica (agente de serviço + supervisor + auditor de risco), WhatsApp + voz |
| **O2OBOTS** | ALTA | Já tem onboarding self-service em 5 minutos + free trial + cliente bancário (BMG) |
| **Fintalk** | MÉDIA-ALTA | IA conversacional no WhatsApp, 12M+ usuários atendidos, resultados comprovados |
| **Moveo.AI** | MÉDIA | LLM proprietário otimizado para português, 200K+ usuários/mês, parceiro LatAm |
| **YKP** | MÉDIA | Agente IA para WhatsApp, entende regionalismos e gírias |
| **Assertiva** | MÉDIA-BAIXA | 6.000 clientes + 200M CPFs — pode adicionar IA a qualquer momento |
| **Acordo Certo** | BAIXA | Marketplace B2C, não concorre diretamente |
| **Players globais** | BAIXA | C&R, HighRadius, Sedric, Vodex — enterprise, fora do Brasil |

### Fichas dos Competidores Mais Relevantes

**Neofin — O competidor mais perigoso**
- Fundada em jan/2023. **Captou R$ 35 milhões** em rodada seed (jan/2025), liderada por Quona e Upload
- Produto: sistema inteligente de cobrança automatizada com "régua de cobrança" por IA
- Features: regras multi-canal automatizadas (email, WhatsApp, SMS), segmentação por perfil, dashboards, integração Serasa, integrações ERP (Omie, Protheus, Nomus)
- Mais de 300 clientes ativos
- Roadmap: portal de renegociação 100% automático, CRM avançado de cobrança, conversas via WhatsApp com IA
- **Ameaça direta**: Quando Neofin decidir ir para o downmarket com self-service (e com R$ 35M, vão), ataca exatamente o nicho da CollectAI

**Monest (MIA) — Mesma tecnologia, escala comprovada**
- Baseada em Curitiba, PR. Investimento de R$ 3,2M da Nestal
- **MIA**: assistente virtual com GPT-4 para recuperação de crédito — mesma base tecnológica da CollectAI
- Resultados impressionantes: **R$ 500M em acordos facilitados**, **6M+ conversas realizadas**
- Custo por acordo: **R$ 15,95** (vs. R$ 21-25 por call center humano)
- **Mia Voz** (lançamento 2025): IA de voz que converteu **36% dos inadimplentes em acordo** em piloto com Midway (Riachuelo)
- Modelo white-label para bancos e fintechs
- Clientes: Adiante Recebíveis, Arco Educação, Grupo Marista

**EaseCob.ai — Arquitetura quase idêntica**
- Usa arquitetura multi-agente explícita: agente de serviço, supervisor de estratégia e auditor de risco
- Isso é essencialmente a mesma arquitetura que a CollectAI
- WhatsApp + voz, modelos preditivos de probabilidade de pagamento
- Roteamento inteligente: melhor número, canal e horário para cada devedor

**O2OBOTS — Já tem o que a CollectAI está planejando**
- SaaS plug-and-play para renegociação via WhatsApp com IA generativa
- **Ativação em 5 minutos**: Upload de planilha → configura regras → ativa no WhatsApp
- **Free trial de 10 dias** sem necessidade de integração técnica
- Pricing: **R$ 4,99 a R$ 9,90 por renegociação** com IA
- Cliente: Banco BMG. Resultado: **40% de aumento nos acordos**, **79% de conversão de boletos emitidos**

### A Verdade Sobre os Diferenciais da CollectAI

| Diferencial Alegado | Realidade | Veredicto |
|---------------------|-----------|-----------|
| "IA nativa, não aparafusada" | Monest, EaseCob, O2OBOTS, Fintalk também são IA nativa | **NÃO É ÚNICO** |
| "WhatsApp-first" | Neofin, Monest, EaseCob, O2OBOTS, Fintalk, YKP — todos usam WhatsApp como canal principal | **NÃO É ÚNICO** |
| "Arquitetura multi-agente (GPT-4)" | EaseCob usa multi-agente explícito. Monest usa GPT-4. Floatbot usa Agent M multi-LLM | **NÃO É ÚNICO** |
| "Estratégias personalizadas por devedor" | Neofin, Monest, Symend, TrueAccord — todos fazem isso. Feature padrão | **NÃO É ÚNICO** |
| "Onboarding self-service" | O2OBOTS já tem ativação em 5 min com free trial. Zaia oferece self-service a R$ 99/mês | **NÃO É PRIMEIRO** |
| "Foco em PMEs no Brasil" | Neofin também foca em PMEs. O2OBOTS tem free trial acessível | **VANTAGEM MODERADA** |

### Onde a CollectAI PODE ter Vantagem Real

A vantagem da CollectAI não está em nenhum diferencial tecnológico isolado. Está na **combinação e execução**:

1. **Combinação completa em um pacote acessível para PMEs**: Nenhum competidor combina perfeitamente multi-agente + WhatsApp + self-service onboarding sofisticado (com enrichment + wizard + simulação) + preço transparente para PME
2. **AHA Moment com simulação agent-to-agent**: Nenhum competidor oferece uma simulação personalizada onde o cliente vê SEU agente em ação antes de pagar
3. **Profundidade da geração automática de agentes**: Auto-gerar agentes com context engineering completo (enrichment → wizard → generation → simulation) é mais sofisticado que o "upload planilha em 5 min" do O2OBOTS
4. **Precificação transparente** (R$ 497-1.497/mês): Enquanto Neofin e Monest são "solicite uma demo", CollectAI pode atrair PMEs com preço claro

### Fraquezas Reais da CollectAI

1. **Gap de funding**: Neofin tem R$ 35M. Monest tem R$ 3,2M + receita forte. CollectAI provavelmente tem muito menos capital
2. **Sem escala comprovada**: Monest processou R$ 500M em acordos e 6M+ conversas. Credibilidade importa em serviços financeiros
3. **Sem canal de voz**: Monest lançou Mia Voz com 36% de conversão. Voz ainda é o canal dominante de cobrança no Brasil
4. **Produto incompleto vs. plataforma**: Neofin oferece CRM, protesto, negativação, integração ERP. CollectAI aparenta ser "só a conversa IA"
5. **Dependência do GPT-4/OpenAI**: Margens pressionadas por custos de API, qualquer concorrente pode usar o mesmo modelo, risco de mudança de termos
6. **Sem data moat**: Assertiva tem 200M CPFs. Neofin tem 300+ clientes de dados. CollectAI começa quase do zero em dados proprietários
7. **Reconhecimento de marca = zero**: Em um mercado de confiança (dados financeiros sensíveis), ser desconhecido é uma desvantagem real

### Implicações Estratégicas

> **O mercado de IA para cobrança no Brasil NÃO é um oceano azul. É um oceano vermelho cada vez mais concorrido — mas com um mercado endereçável gigante** (6,8M de micro/pequenas empresas inadimplentes, R$ 141,6 bilhões em dívidas).

**O caminho para vencer não é ter tecnologia única — é ter:**
1. **Onboarding mais rápido** (self-service sofisticado, AGORA — antes que Neofin construa)
2. **Melhor custo por acordo** (provar unit economics vs. alternativas)
3. **Especialização vertical** (escolher 2-3 verticais e dominar: e-commerce, SaaS, clínicas)
4. **Flywheel de dados** (cada conversa treina o produto — vantagem composta)
5. **Pricing mais transparente** (vantagem real vs. "solicite uma demo")

**A janela de oportunidade está aberta mas se fechando. Velocidade de execução vai determinar se a CollectAI vira um player relevante ou fica espremida entre Neofin (vindo para baixo com R$ 35M) e O2OBOTS (já na base com self-service + free trial).**

**Fontes:**
- Neofin.com.br / Finsiders Brasil — Neofin R$ 35M
- Monest.com.br / Finsiders — Monest MIA
- TI Inside — Mia Voz piloto Midway
- EaseCob.com / EaseAndTrust.ai
- O2OBOTS — Blog sobre renegociação com IA
- Fintalk.ai / YKP.com.br
- Assertiva.com.br / Acerto.com.br
- C&R Software, HighRadius, Sedric AI, Vodex AI
- TrueAccord.com, Symend.com
- Market.us — AI for Debt Collection Market

---

## 1.4 Persona e Jornada do Usuário

### Persona Principal

**Nome**: Ana Paula (arquétipo)
**Cargo**: Analista/Gestora de Cobrança ou do Setor Financeiro
**Idade**: 28-45 anos
**Perfil técnico**: Baixo a médio — usa ERPs e planilhas, não é desenvolvedora
**Empresa**: PME ou mid-market (R$ 5M-100M de faturamento), 11-500 funcionários
**Verticais**: Construtora/incorporadora, varejo a prazo, healthcare, SaaS B2B

**Contexto**: Ana Paula está sobrecarregada. A inadimplência cresce, o time de cobrança é pequeno (ou não existe um time dedicado), e ela perde horas do dia ligando para devedores ou mandando mensagens manuais. Ela pesquisa soluções no Google ou LinkedIn e encontra a CollectAI.

### Jobs to be Done (JTBD)

1. **Funcional**: "Quero recuperar mais dívidas com menos esforço manual"
2. **Emocional**: "Quero parar de me estressar com cobrança todos os dias"
3. **Social**: "Quero mostrar para meu chefe que trouxe uma solução moderna que funciona"

### Jornada Completa

| Etapa | Ação | Pain Point | Solução |
|-------|------|-----------|---------|
| **Descoberta** | Pesquisa "cobrança automatizada" no Google | Não sabe que existe IA para cobrança | SEO + LinkedIn content |
| **Avaliação** | Visita o site, lê sobre a solução | "Será que funciona pra minha empresa?" | Case studies, ROI calculator |
| **Cadastro** | Cria conta, informa CNPJ | "Vai ser complicado de configurar?" | Registro simples, 30 segundos |
| **Enriquecimento** | Sistema busca dados automaticamente | "Vou ter que preencher 50 campos?" | Auto-fill com dados do CNPJ |
| **Entrevista** | Responde perguntas no wizard | "Não sei termos técnicos" | Linguagem simples, áudio, IA adapta |
| **Geração** | Sistema gera o agente | "Será que o agente entende meu negócio?" | Simulação mostra agente em ação |
| **AHA Moment** | Vê simulação agent-to-agent | "Uau, ele realmente negocia como eu faria!" | Conversa realista personalizada |
| **Ajuste** | Revisa e ajusta tom/regras | "E se ele fizer algo errado?" | Controle total das regras + guardrails |
| **Pagamento** | Escolhe plano e cadastra cartão | "Quanto vai custar?" | Pricing transparente + trial grátis |
| **Ativação** | Upload de lista e lança campanha | "E agora, como começo?" | Wizard guiado de campanha |

### Benchmarks de Time-to-Value

- **Média SaaS**: 1 dia, 12 horas, 23 minutos até primeiro valor percebido
- **Meta CollectAI**: **15-30 minutos** do cadastro até o AHA Moment (simulação)
- Usuários que experienciam valor core **em 5-15 minutos** são **3x mais propensos a reter**
- Produtos que entregam AHA Moment **em 5 minutos** mostram **40% mais retenção em 30 dias**
- **Cada minuto extra** de time-to-value **reduz conversão em 3%**

**Fontes:**
- Userpilot — Time-to-Value Benchmark Report 2024
- ProductLed — PLG Metrics
- High Alpha — 2025 SaaS Benchmarks

---

# PARTE 2: UX/UI e Design do Onboarding

## 2.1 Fundamentos de UX para Onboarding Self-Service B2B

### Por que Onboarding é Crítico

Dado de mercado: **66% dos clientes B2B param de comprar** após uma experiência de onboarding ruim. O onboarding é o momento mais crítico da jornada do cliente — é onde a percepção de valor se forma (ou morre).

### Princípios de Design

**1. Progressive Disclosure (Revelação Progressiva)**
Mostrar informações apenas quando o usuário precisa delas, não todas de uma vez. Em vez de um formulário com 50 campos, dividir em steps com 3-5 campos cada. Pesquisa do Nielsen Norman Group mostra que progressive disclosure pode **reduzir tempo de conclusão em 20-40%**.

**2. Redução de Carga Cognitiva**
- Limitar escolhas simultâneas (Lei de Hick: mais opções = mais tempo para decidir)
- Usar defaults inteligentes (pré-preenchidos pelo enriquecimento)
- Agrupar informações relacionadas
- Indicar progresso claro (progress bar)

**3. Orientação a Resultado**
Focar no que o usuário vai conseguir ("Seu agente estará pronto em 15 minutos") em vez do que ele precisa fazer ("Preencha 10 seções de configuração").

**4. IA como Redutora de Fricção**
- Auto-fill: preencher campos automaticamente com dados do CNPJ/site
- Inferência de intenção: sugerir tipo de agente baseado no segmento da empresa
- Pular etapas irrelevantes: se a empresa é construtora, não perguntar sobre assinaturas SaaS
- Adaptar linguagem: se o usuário responde de forma simples, simplificar as próximas perguntas

### Padrões de UX para Onboarding B2B SaaS 2025-2026

| Padrão | Quando Usar | Exemplo |
|--------|------------|---------|
| **Wizard Flow** | Apps data-heavy que precisam coleta estruturada | Configuração de agente (CollectAI) |
| **Product Tour** | Familiarizar com interface existente | Primeiro acesso ao dashboard |
| **Checklist** | Múltiplas tarefas independentes | Setup pós-onboarding |
| **Tooltip** | Orientação contextual in-place | Campos complexos do wizard |
| **Empty State** | Motivar primeira ação | Dashboard vazio → "Crie seu primeiro agente" |

**Referências de mercado:**
- **Slack**: SSO com um clique → convite de equipe → tutorial interativo. AHA moment: quando equipe envia **2.000 mensagens**
- **HubSpot**: Self-serve extensivo com progress bars em todo o onboarding
- **Intercom**: Segmentação por role no signup — cada persona vê uma experiência diferente
- **Calendly**: Sign in com Google (1 step para conectar calendário) → auto-teste

### Para Usuários Não-Técnicos

A persona da CollectAI (analista financeiro) não é técnica. Princípios essenciais:

- **Não remover complexidade, mas gerenciar quando e como o usuário a experiencia**
- Orientação contextual > documentação extensa
- Focar em ajudar o usuário a ter sucesso cedo, não em explicar tudo
- Gamificação leve: progress bars, indicadores visuais de conquista
- Experiências orientadas a resultado reduzem ansiedade e constroem confiança

**Dado crítico sobre tours de produto**: Tours com **mais de 4 steps** tiveram taxa de conclusão abaixo da média. Tours de **4 steps** foram concluídos 40,5% das vezes; adicionar **apenas 1 step extra (5 total) reduziu para ~21%** — quase pela metade com um step a mais.

**Fontes:**
- Insaim Design — SaaS Onboarding Best Practices for 2025
- NN/g — New Users Need Support with Gen-AI Tools
- UserGuiding — B2B SaaS Onboarding
- Userpilot — Progressive Disclosure Examples
- Appcues — AHA Moment Guide

---

## 2.2 O Padrão Híbrido: Wizard + Chat Conversacional

### O Conceito

O padrão híbrido combina dois modelos de interação:

1. **Wizard estruturado**: Steps pré-definidos com campos específicos — garante que todos os dados necessários sejam coletados
2. **Chat conversacional com IA**: Agente observa as respostas e gera perguntas de follow-up inteligentes — captura nuances e detalhes que um formulário fixo não pegaria

Este é um padrão emergente em 2025-2026, documentado como "AI-Powered Form Wizards": assistentes dinâmicos que guiam o usuário step-by-step, validam input em tempo real, e usam RAG para oferecer ajuda contextual.

### Como Funciona na CollectAI

Cada step do wizard tem duas áreas:
- **Área superior**: Formulário estruturado com campos pré-definidos (alguns pré-preenchidos pelo enriquecimento)
- **Área inferior**: Chat IA que observa as respostas e gera follow-ups contextuais

**Fluxo:**
1. Wizard step aparece com campos pré-definidos
2. Cliente preenche os campos (texto) ou grava áudio (botão de microfone)
3. IA observa as respostas e analisa lacunas/oportunidades de aprofundamento
4. IA gera follow-ups contextuais: "Você mencionou X. Pode me contar mais sobre Y?"
5. Cliente responde os follow-ups (texto ou áudio)
6. Dados estruturados são salvos em tempo real no backend
7. Progress bar atualiza mostrando avanço
8. Próximo step é liberado quando os dados mínimos foram coletados

### Referências de Mercado

- **boost.ai Get Started Wizard**: Onboarding co-pilot com interface de diálogo que guia enterprises na configuração de novas instâncias de agentes IA, gerando fundação funcional em minutos
- **OpenAI ChatKit**: Framework drop-in de chat UI com streaming, attachments, e workflows de agentes
- **Sendbird Conversational Forms**: Formulários conversacionais integrados a chat

**Fontes:**
- JavaPro — AI-Powered Form Wizards: Chat, Click, Done
- boost.ai — Introducing Get Started Wizard
- Sendbird — AI Conversational Forms

---

## 2.3 Entrada de Áudio no Browser

### Conceito

O usuário pode responder perguntas do wizard por áudio em vez de texto. O áudio é capturado no browser, enviado ao backend, transcrito via Whisper (OpenAI) e processado como texto.

### Fluxo

1. Usuário clica no botão de microfone (solicita permissão do browser)
2. Gravação começa com indicador visual (animação de onda sonora)
3. Usuário fala e para a gravação
4. Preview do áudio (botão play para ouvir antes de enviar)
5. Upload do arquivo para o backend
6. Backend transcreve via Whisper e retorna o texto
7. Texto transcrito aparece na tela

### Modelos Whisper Disponíveis

| Modelo | Custo/minuto | Indicação |
|--------|-------------|-----------|
| `whisper-1` (V2) | $0.006 | Balanceado — **recomendado para MVP** |
| `gpt-4o-transcribe` | $0.006 | Maior acurácia |
| `gpt-4o-mini-transcribe` | $0.003 | Mais barato, boa qualidade |

**Acurácia em Português**: Word Error Rate de **8-15%**. Formatos aceitos: mp3, mp4, wav, webm (máximo 25MB).

### Considerações de UX

- **Indicador visual**: Animação de onda sonora durante gravação
- **Preview**: Botão de play para ouvir antes de enviar
- **Refazer**: Botão de regravar se ficou ruim
- **Feedback**: Texto transcrito aparece na tela após processamento
- **Timeout**: Limite de 2-3 minutos por gravação
- **Compatibilidade mobile**: Safari 18.4+ suporta WebM/Opus. Versões mais antigas requerem fallback para MP4. Sempre fazer feature detection dinâmica

### Abordagem

**MVP**: Gravar → upload → transcrever (batch). Simples e funcional.
**Futuro**: Transcrição em tempo real via WebSocket (OpenAI Realtime API) para feedback instantâneo.

**Fontes:**
- OpenAI — Speech-to-Text Guide / Pricing
- MDN — MediaRecorder API

---

## 2.4 Design do Fluxo de Onboarding Completo

### Visão Geral dos Steps

O onboarding é dividido em 10 steps, com tempo estimado total de **15-30 minutos**:

| Step | Nome | Tempo Est. | Tipo |
|------|------|-----------|------|
| 0 | Registro | 1 min | Formulário simples |
| 1 | CNPJ + Site | 30 seg | Input + auto-enrich |
| 2 | Validação de Dados | 2 min | Review + correção |
| 3 | Tipo de Agente | 30 seg | Seleção |
| 4 | Sobre o Negócio | 5-8 min | Wizard híbrido |
| 5 | Configuração do Agente | 3-5 min | Wizard híbrido |
| 6 | Simulação (AHA Moment) | 2 min | Read-only |
| 7 | Ajustes Finos | 2-5 min | Editor |
| 8 | Pagamento | 2 min | Checkout |
| 9 | Lançamento de Campanha | 3-5 min | Upload + config |

### Detalhamento de Cada Step

**Step 0: Registro**
- Campos: Email, Senha, Nome completo, Aceitar termos
- Opção: Sign-in com Google (SSO) para reduzir fricção
- Após registro: Redirect direto para Step 1 (sem email de confirmação bloqueante)

**Step 1: CNPJ + Site**
- Input grande central com campo CNPJ formatado e campo de site opcional
- Ao submeter: feedback progressivo mostrando cada fonte sendo consultada em tempo real (checkbox com ✓ conforme completa)
- Tempo de enriquecimento: ~10-30 segundos (fontes em paralelo)

**Step 2: Validação dos Dados Enriquecidos**
- Card com dados pré-preenchidos e campos editáveis (Razão Social, Nome Fantasia, CNAE, Porte, Cidade, Setor)
- Indicadores de reputação: nota Reclame Aqui, Google Maps, concorrentes identificados
- Botões: "Corrigir dados" e "Confirmar"

**Step 3: Seleção do Tipo de Agente**
- Duas cards grandes com seleção exclusiva:
  - **Adimplente**: Lembretes de pagamento para quem está em dia. Evita atrasos
  - **Inadimplente**: Cobrança e negociação para quem está em atraso. Recupera dívidas
- Nota: "Depois você pode criar outros agentes dentro da plataforma"

**Step 4: Wizard Híbrido — Sobre o Negócio**
- Perguntas pré-definidas (baseadas no roteiro atual do Francisco):
  1. "Como funciona o modelo de negócio da sua empresa?" (textarea ou áudio)
  2. "Descreva o fluxo de cobrança atual — do atraso até o pagamento" (textarea ou áudio)
  3. "Quando vocês consideram que uma conta virou atrasada?" (select: D+1, D+5, D+15...)
  4. "Quem faz a cobrança hoje?" (multiselect: financeiro, CS, vendas, jurídico, terceiro, ninguém)
  5. "Quais canais vocês usam para cobrar?" (multiselect: WhatsApp, email, SMS, ligação, carta)
  6. "Vocês segmentam a cobrança por perfil, valor ou tempo de atraso?" (sim/não + detalhe)
- Chat IA gera follow-ups baseados nas respostas (exemplos: se respondeu "construtora", pergunta sobre tipo de dívida)

**Step 5: Wizard Híbrido — Configuração do Agente**
- Perguntas pré-definidas:
  1. Tom de voz (select: Formal, Amigável, Empático, Assertivo)
  2. Desconto máximo à vista (slider: 0-50%)
  3. Desconto máximo para parcelamento (slider: 0-50%)
  4. Número máximo de parcelas (select: 2x a 24x)
  5. Valor mínimo por parcela (input: R$)
  6. O que o agente NUNCA deve fazer (textarea: guardrails)
  7. Situações de escalação para humano (multiselect)
  8. Horários permitidos para contato (time pickers)

**Step 6: Simulação — AHA Moment**
- Chat read-only mostrando conversa simulada entre o agente recém-gerado e um devedor fictício
- 2-3 cenários diferentes (devedor cooperativo, hesitante, resistente)
- Métricas exibidas: taxa de acordo simulada, desconto médio oferecido, tempo médio de conversa
- Botões: "Ajustar agente" e "Aprovar"

**Step 7: Ajustes Finos**
- Campos editáveis: tom de voz, limites de desconto, regras de escalação, mensagem inicial
- Preview em tempo real: como a mensagem ficaria com as alterações
- Botão "Re-simular" para ver novo cenário com ajustes

**Step 8: Pagamento**
- Seleção de plano + checkout (Stripe Elements)
- Trial/créditos grátis para primeiras conversas
- Breakdown claro de custos

**Step 9: Lançamento de Campanha**
- Drag-and-drop de CSV/XLSX
- Mapeamento de colunas (nome, telefone, valor, vencimento)
- Validação e preview dos dados
- Configuração: horários de envio, frequência de follow-up
- Botão "Lançar campanha"

**Fontes:**
- Insaim Design — SaaS Onboarding Best Practices for 2025
- ProductFruits — B2B SaaS Onboarding
- Hopscotch — PLG Strategies

---

## 2.5 Abordagem de Frontend: Lovable + Backend API

### Por que Lovable

O frontend do onboarding será construído no **Lovable** (lovable.dev), uma ferramenta que gera aplicações React completas a partir de prompts em linguagem natural. A stack gerada pelo Lovable é **idêntica à stack atual da CollectAI**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui.

### Como a Integração Funciona

**Princípio fundamental: O Lovable é APENAS o frontend. Toda a lógica de negócio vive no FastAPI.**

A melhor forma de conectar Lovable ao backend é via **OpenAPI Specification**:

1. FastAPI gera automaticamente uma spec OpenAPI (JSON) a partir dos modelos Pydantic e rotas
2. Essa spec é exportada e fornecida ao Lovable via sua seção "Knowledge"
3. Lovable lê a spec e gera um client API tipado que corresponde ao backend
4. Todas as chamadas do frontend passam por esse client tipado

**Padrão recomendado: REST (não GraphQL)**. Lovable funciona melhor com endpoints REST padrão. GraphQL adiciona complexidade que a IA frequentemente não maneja bem.

### O que o Lovable Faz Bem (Frontend)

| Capacidade | Adequação para CollectAI |
|-----------|--------------------------|
| Wizard multi-step | Excelente — geração de formulários é ponto forte |
| Exibição de dados enriquecidos | Ótimo — data cards a partir de respostas da API |
| Indicadores de progresso / loading | Excelente |
| Design responsivo (mobile) | Excelente — Tailwind + shadcn/ui |
| Checkout (Stripe Elements) | Suportado |
| Chat viewer (simulação) | Bom — interfaces de chat são bem suportadas |

### O que o Backend Deve Fazer (FastAPI)

| Capacidade | Motivo |
|-----------|--------|
| Pipeline de enriquecimento CNPJ | Agregação multi-fonte, processamento LLM, 10-30s |
| Geração de config do agente | Context engineering complexo, structured output |
| Simulação agent-to-agent | Múltiplas chamadas LLM, gerenciamento de cenários, 30-60s |
| Transcrição de áudio (Whisper) | Processamento de arquivo, segurança de API key |
| Rate limiting e gestão de créditos | Deve ser server-authoritative |
| Webhooks Stripe | Server-side only, verificação de assinatura |
| Orquestração de campanha | Integração RabbitMQ, workflow complexo |

### Comunicação em Tempo Real

Para operações longas (enriquecimento, geração, simulação), usar **Server-Sent Events (SSE)**: o backend envia updates progressivos e o frontend exibe checkboxes com ✓ conforme cada etapa completa. SSE funciona bem com Lovable — é apenas a API nativa `EventSource` do browser.

### Autenticação

**Opção recomendada**: JWT emitido pelo FastAPI.
1. Usuário faz login via frontend Lovable
2. Frontend envia credenciais para o backend
3. FastAPI valida e retorna JWT + refresh token
4. Frontend armazena o token e inclui em todas as chamadas

**Opção alternativa**: Supabase Auth (Lovable tem integração nativa), com verificação do JWT do Supabase no FastAPI. Mais rápido de implementar auth UI, porém adiciona complexidade de dual auth.

### CORS

Configurar no FastAPI para permitir origens:
- URL de preview do Lovable (ex: `https://<project-id>.lovable.app`)
- Domínio de produção
- `localhost:5173` para desenvolvimento local

### Limitações do Lovable

- Não executa código server-side
- Não processa jobs em background
- Pode "alucinar" endpoints que não existem na API
- Requer re-importação da spec OpenAPI quando endpoints mudam
- Componentes complexos (audio recorder, SSE handler) podem precisar de refinamento manual no IDE
- Esperar gastar ~20-30% do tempo de desenvolvimento limpando e refinando código gerado pelo Lovable

### Recomendação de Arquitetura

**Ignorar Supabase como backend.** Usar Lovable puramente como gerador de código React. Toda a lógica de dados e negócio fica no FastAPI com Postgres/Redis/RabbitMQ. As Edge Functions do Supabase têm limites de 60s de execução e não rodam Python — inviável para enriquecimento, simulação e processamento ML.

### Workflow de Desenvolvimento

1. **Construir e testar o backend primeiro** (todos os endpoints)
2. **Exportar a spec OpenAPI** como artefato do backend
3. **Usar Lovable para prototipar UI** rapidamente com prompts
4. **Exportar para GitHub** via sync bidirecional do Lovable
5. **Refinar no IDE** (VS Code/Cursor) para edge cases
6. **Deploy**: Backend no infra existente, Frontend no Vercel ou Netlify

**Fontes:**
- Lovable Frontend Framework (Sidetool)
- How To Build a Frontend with Lovable.dev (Strapi)
- OpenAPI or Bust: How I Made Lovable Play Nice with a Real Backend (HackerNoon)
- Connecting Custom Backends to Lovable Frontends (RapidDev)
- From Lovable To Production: A Developer's Guide (Seismic)

---

# PARTE 3: Conhecendo a Empresa — O Que Realmente Importa para Gerar um Bom Agente

## 3.1 Análise Crítica: Quais Dados Criam um Agente Melhor?

### A Pergunta Central

O objetivo do onboarding é criar o **melhor agente de cobrança possível** para cada empresa. Isso exige responder: quais dados realmente impactam a qualidade do agente?

Para responder, analisamos cada fonte de dados possível pelo seu **impacto direto na qualidade do agente de cobrança**:

| Fonte de Dados | O que Fornece | Impacto na Qualidade do Agente | Veredicto |
|----------------|---------------|-------------------------------|-----------|
| **Wizard/Entrevista (SOP)** | Políticas de desconto, tom preferido, métodos de pagamento, regras de escalação, objeções comuns, fluxo de cobrança, limites de negociação | **CRÍTICO** — define 80%+ do comportamento do agente | ESSENCIAL |
| **Site da empresa (scraping + LLM)** | O que a empresa faz, público-alvo, produtos/serviços, tom de marca, diferenciais | **ALTO** — contextualiza o agente sobre o negócio do cliente | VALIOSO |
| **Reclame Aqui** | Nota, reclamações comuns, taxa de resolução | **MÉDIO** — ajuda a calibrar tom (empresa com nota baixa → agente mais empático) | OPCIONAL |
| **CNPJ (Receita Federal)** | Razão Social, Nome Fantasia, CNAE, endereço, porte, capital social, sócios | **BAIXO** — apenas preenche campos cadastrais; nenhum desses dados muda o comportamento do agente | DISPENSÁVEL como pipeline pago |
| **Google Maps** | Nota, reviews, localização | **BAIXO** — pouco relevante para qualidade de cobrança | DISPENSÁVEL |
| **LinkedIn** | Tamanho, setor | **BAIXO** — redundante com CNPJ e site | DISPENSÁVEL |
| **Notícias** | Contexto atual | **MUITO BAIXO** — raramente relevante para PMEs que são nosso ICP | DISPENSÁVEL |

### A Conclusão

**O wizard/entrevista é responsável por 80%+ da qualidade do agente.** É onde o cliente define suas políticas reais, tom, regras de negociação e SOP de cobrança — exatamente o que o agente precisa para operar.

O site da empresa adiciona contexto valioso (o que vendem, para quem, como se comunicam), mas é complementar ao wizard.

Dados de CNPJ (Razão Social, CNAE, endereço, capital social) **não mudam o comportamento do agente de cobrança**. Saber que a empresa tem CNAE "4751-2/01 - Comércio varejista de equipamentos de informática" não ajuda o agente a negociar melhor com um devedor. O que ajuda é saber que "a empresa vende computadores, aceita PIX e boleto, dá no máximo 15% de desconto à vista, e o tom deve ser profissional mas acolhedor".

---

## 3.2 Abordagem Recomendada: 3 Camadas de Conhecimento

### Camada 1: ESSENCIAL — Wizard/Entrevista (SOP do Cliente)

**Responsável por 80%+ da qualidade do agente.**

Esta é a fonte primária e insubstituível. As perguntas do wizard capturam:

- **Produto/Serviço**: O que a empresa vende e como cobra (recorrência, parcelamento, à vista)
- **Perfil do devedor**: Quem são os clientes inadimplentes (PF, PJ, faixa de valor típica)
- **Políticas de desconto**: Tabela de descontos permitidos (por faixa de atraso, por valor, à vista vs. parcelado)
- **Métodos de pagamento**: PIX, boleto, cartão, link de pagamento — e quais o agente pode gerar
- **Tom de voz**: Formal, informal, empático, direto — com exemplos
- **Regras de escalação**: Quando passar para humano (valor acima de X, menção de processo, N tentativas sem acordo)
- **Objeções comuns**: "Não reconheço essa dívida", "Estou desempregado", "Já paguei" — e como responder
- **Horários de contato**: Preferências da empresa além dos limites legais
- **Follow-up**: Frequência, mensagens de lembrete, quando desistir
- **Restrições específicas**: Coisas que o agente NUNCA deve dizer ou oferecer

**Formato**: Formulários estruturados (wizard) + chat com IA gerando follow-ups inteligentes + opção de áudio.

**Por que funciona**: Captura exatamente o "manual de operação" da cobrança da empresa — o SOP que hoje é extraído manualmente nas calls com o Francisco.

### Camada 2: VALIOSO — Site da Empresa (Scraping Automático + LLM)

**Adiciona contexto que enriquece o agente sem esforço do cliente.**

Quando o cliente informa o site (ou ele é extraído do CNPJ via BrasilAPI), o sistema automaticamente:

1. Renderiza o site com Playwright (headless browser)
2. Extrai o conteúdo textual principal
3. Envia para LLM com prompt de extração estruturada

**O que o LLM extrai:**
- O que a empresa faz (descrição em 2-3 frases)
- Produtos/serviços principais
- Público-alvo aparente (B2B, B2C, ambos)
- Tom de comunicação da marca (formal, casual, técnico)
- Diferenciais que a empresa destaca
- Canais de contato listados

**Uso no onboarding:**
- Pré-preenche campos do wizard (segmento, tipo de produto, tom sugerido)
- Permite que a IA do chat faça perguntas mais contextuais ("Vi que vocês vendem software por assinatura — a inadimplência é sobre mensalidades atrasadas?")
- Contextualiza o Agent Generator sobre o negócio

**Ferramenta**: `llm-scraper` (github.com/mishushakov/llm-scraper) — converte qualquer webpage em dados estruturados via LLM.

**Custo**: ~$0.01-0.03 por site (tokens GPT-4.1-mini). Essencialmente grátis em escala.

### Camada 3: OPCIONAL — Dados Complementares (Custo Zero)

Fontes gratuitas que adicionam contexto marginal, sem bloquear o fluxo:

**CNPJ via BrasilAPI (grátis, sem auth):**
- Apenas para preencher automaticamente: nome da empresa, nome fantasia, CNAE (para segmentação), porte
- **Não usar APIs pagas** (CNPJa, ReceitaWS premium) — o custo não se justifica pelo valor agregado
- Se BrasilAPI falhar, o cliente pode preencher manualmente (2 campos)

**Reclame Aqui (scraping básico, grátis):**
- Nota geral e volume de reclamações
- Uso: se a empresa tem nota muito baixa (< 5), sugere tom mais empático e guardrails mais conservadores
- Fase 2+, não essencial para MVP

---

## 3.3 Pipeline Simplificado

### Fluxo do Onboarding (revisado)

1. Cliente informa **CNPJ** e **site** (ou só o site)
2. Em paralelo (5-10 segundos):
   - BrasilAPI consulta CNPJ → nome, segmento, porte (gratuito)
   - Playwright + LLM scrape do site → contexto do negócio (~$0.02)
3. Dados pré-preenchem o wizard
4. **Wizard/Entrevista** (a parte mais importante):
   - Cliente responde perguntas estruturadas sobre políticas, tom, regras
   - IA gera follow-ups inteligentes baseados no contexto do site
   - Cliente pode responder por texto ou áudio (Whisper transcreve)
5. Agent Generator usa TUDO (wizard + contexto do site) para criar o agente

### Custo Total do Enrichment por Cliente

| Componente | Custo | Nota |
|-----------|-------|------|
| BrasilAPI (CNPJ) | $0.00 | Gratuito |
| Site scraping + LLM | ~$0.02 | GPT-4.1-mini tokens |
| **Total** | **~$0.02** | vs. $0.10-0.30 da abordagem anterior |

**Economia**: Eliminamos 80-93% do custo de enrichment ao remover APIs pagas de CNPJ e fontes de baixo valor.

### Impacto na Experiência

- **Onboarding mais rápido**: Sem esperar 6 fontes em paralelo, apenas 2 (BrasilAPI + site) → 5-10s vs. 30-60s
- **Menos pontos de falha**: 2 fontes em vez de 6 → pipeline mais robusto
- **Foco no que importa**: Cliente gasta mais tempo no wizard (que gera valor real) e menos tempo esperando enrichment
- **Mesma qualidade de agente**: O wizard sempre foi a fonte primária — agora isso está explícito

**Fontes:**
- BrasilAPI (brasilapi.com.br)
- llm-scraper (github.com/mishushakov/llm-scraper)

---

# PARTE 4: Framework de Agentes e Arquitetura do Onboarding

## 4.1 Panorama dos Frameworks de Agentes IA (2025-2026)

### Evolução da Arquitetura

A arquitetura de sistemas de IA evoluiu de chains sequenciais (2023) para agentes com ferramentas (2024) para sistemas multi-agente coordenados com grafos de estado (2025+).

### Padrões Arquiteturais Relevantes

| Padrão | Descrição | Quando Usar |
|--------|-----------|-------------|
| **Hierarchical (Supervisor)** | Agentes em árvore com supervisor no topo | Quando há clara hierarquia de responsabilidades |
| **Sequential Pipeline** | Agentes em série, cada um processa e passa adiante | Quando output de um é input do próximo |
| **Orchestrator-Workers** | Orquestrador decide dinamicamente quais tarefas delegar | Quando tarefas são dinâmicas e variáveis |
| **Evaluator-Optimizer** | Um LLM gera, outro avalia, loop de refinamento | Quando há critérios claros de qualidade |

**Para o onboarding da CollectAI**, o padrão mais adequado é **Sequential Pipeline**: Enrichment → Interview → Generation → Simulation, com cada etapa passando seus resultados para a próxima.

---

## 4.2 Comparação Profunda de Frameworks

### Os Candidatos

Analisei em profundidade 8 frameworks para decidir qual usar no sistema de onboarding:

### LangGraph (LangChain)

**O que é**: Framework baseado em grafos dirigidos (DAG) onde nós representam agentes/funções e arestas ditam o fluxo de dados. Um `StateGraph` centralizado mantém o contexto.

**Modelo-agnóstico?** Sim — suporta GPT-4, Claude, Gemini, Llama, DeepSeek e outros via interface unificada LangChain. Sem prompts ocultos — transparência total.

**Pontos fortes**:
- **Melhor gestão de estado** do mercado: estado é cidadão de primeira classe, com serialização, persistência e checkpointing
- **Execução durável** com recuperação automática de crashes
- **Human-in-the-loop nativo** com mecanismos de interrupt
- **Comprovado em produção**: LinkedIn, Uber, Replit, Elastic, Klarna (85M usuários)
- Ecossistema forte: 2.000+ contributors, 99K+ stars no LangChain

**Pontos fracos**:
- **Curva de aprendizado alta**: Mais complexo de configurar que alternativas
- **Debugging**: Grafos grandes podem ser difíceis de rastrear
- **Dependência do ecossistema LangChain**
- **LangSmith (observabilidade)** é pago ($39/seat/mês + $2.50-5.00/1K traces)

**Empresas usando em produção**: ~600-800 empresas. Uber (migrações de código), Elastic (detecção de ameaças em tempo real), Replit (geração de código), Klarna (assistente IA servindo 85M usuários), AppFolio (copilot economizando 10+ hrs/semana).

### OpenAI Agents SDK

**O que é**: SDK leve e oficial da OpenAI (evolução do Swarm experimental, lançado março/2025) com 4 primitivas: Agents, Handoffs, Guardrails, Tracing.

**Modelo-agnóstico?** Sim, mas com ressalvas — suporta 100+ LLMs via interface `ModelProvider` customizada, porém **melhor performance é com modelos OpenAI**. Ferramentas built-in (Code Interpreter, File Search) são exclusivas OpenAI.

**Pontos fortes**:
- **Extremamente leve**: Poucas abstrações, aprendizado rápido
- **Guardrails nativos**: Input/output validation rodando em paralelo
- **Handoffs elegantes**: Delegação natural entre agentes especializados
- **Tracing built-in**: Coleta abrangente de eventos, extensível
- Mantido ativamente pelo time da OpenAI

**Pontos fracos**:
- **Sem persistência de estado**: Estado existe só em memória, sem checkpointing
- **Sem human-in-the-loop nativo**: Implementação manual necessária
- **Menos maduro que LangGraph** para workflows longos e complexos
- **Sem modelagem de workflow em grafo**: Apenas padrões lineares/handoff

### Claude Agent SDK (Anthropic)

**O que é**: O mesmo infra que roda o Claude Code, agora disponível como SDK para construir agentes customizados. Disponível em Python e TypeScript.

**Modelo-agnóstico?** **NÃO** — restrito exclusivamente a modelos Claude (Sonnet, Opus, Haiku). Acesso via API Anthropic, AWS Bedrock ou Google Vertex AI, mas todos são Claude.

**Arquitetura**: Loop master single-threaded — um `while` loop que continua enquanto o modelo produz tool calls. Quando produz texto sem tools, o loop termina. Design deliberadamente simples.

**Pontos fortes**:
- Mesma infraestrutura que roda o Claude Code (comprovado)
- Subagentes para tarefas paralelas com contexto isolado
- Integração MCP (Model Context Protocol) para tools externas
- Tracing nativo com 3 variáveis de ambiente

**Pontos fracos**:
- **Lock-in total** em modelos Claude — impede usar GPT-4o-mini para tarefas baratas
- Feature requests para suporte a modelos de terceiros continuam sem implementação

### Como Cursor e Claude Code Constroem Seus Agentes

**Cursor**: NÃO usa LangGraph nem nenhum framework externo. Construiu um **framework proprietário** chamado Composer (arquitetura Mixture-of-Experts com Reinforcement Learning). Roda até 8 agentes simultaneamente usando isolamento com Git worktree. Suporta MCP para extensibilidade.

**Claude Code**: Também NÃO usa LangGraph. Usa **loop master single-threaded** (a mesma arquitetura do Agent SDK). ~12 tools deliberadamente restritas. Subagentes para preservar contexto e controlar custos. Sem vector databases nem embeddings — confia na compreensão de código do Claude.

**Insight da Anthropic**: "As implementações mais bem-sucedidas NÃO usavam frameworks complexos ou bibliotecas especializadas. Em vez disso, construíam com padrões simples e componíveis."

### Agency Swarm (Framework Atual da CollectAI)

**Estado atual**: v1.7.0 (janeiro/2026), migrou da Assistants API para estender o OpenAI Agents SDK. Suporte a multi-modelo via LiteLLM.

**Comunidade**: ~3.9K stars, ~1K forks. Lab companion repository **arquivado** em novembro/2025.

**Pontos fortes**: Metáfora organizacional intuitiva (agências com CEO, gerentes, trabalhadores), MIT licensed.

**Pontos fracos preocupantes**:
- **Risco de maintainer único**: Primariamente desenvolvido por VRSEN
- **Comunidade pequena**: 3.9K stars vs. 99K (LangChain), 25K (CrewAI)
- **Problemas de concorrência**: Issues reportados com interações de múltiplos usuários simultâneos
- **Rewrite recente**: Quando OpenAI deprecou Assistants API, Agency Swarm precisou de rewrite major — risco de repetição
- **Sem observabilidade enterprise**: Sem plataforma de tracing, sem certificações

### CrewAI

**O que é**: Framework role-based onde agentes comportam-se como "empregados" com responsabilidades específicas. Configuração via YAML.

**Modelo-agnóstico?** Sim. **Adoção**: $18M em funding, 100K+ devs certificados, 60% do Fortune 500, 60M+ execuções/mês. **HIPAA e SOC2 compliant**.

**Ponto forte diferencial**: Enterprise-ready com compliance, o que importa para serviços financeiros.

### Outros

- **Microsoft Agent Framework**: Preview público (out/2025). Melhor dentro do ecossistema Azure/Microsoft
- **Google ADK**: Otimizado para Gemini + Vertex AI
- **AWS Strands**: Melhor dentro do ecossistema AWS

---

## 4.3 Tabela Comparativa

| Critério | LangGraph | OpenAI Agents SDK | Claude Agent SDK | Agency Swarm | CrewAI |
|----------|-----------|-------------------|-----------------|--------------|--------|
| **Modelo-agnóstico** | Sim (todos) | Sim (melhor c/ OpenAI) | **Não (Claude only)** | Sim (via LiteLLM) | Sim |
| **Gestão de Estado** | Excelente (checkpointing) | Nenhum (só memória) | Session-based | Estende Agents SDK | Por role |
| **Human-in-the-Loop** | Nativo | Manual | Modelo de permissões | Limitado | Task limits |
| **Produção** | 600-800 empresas | Bom | Powers Claude Code | Moderado | 60% F500 |
| **Observabilidade** | LangSmith (pago) | Built-in (grátis) | Nativo (3 env vars) | Limitado | CrewAI Studio |
| **Curva de Aprendizado** | Alta | Baixa | Média | Baixa-Média | Baixa-Média |
| **Comunidade** | 99K+ stars | OpenAI backing | Anthropic backing | 3.9K stars | 25K+ stars |
| **Custo do Framework** | Free + LangSmith $39+/seat | Free | Free (pay Claude API) | Free | Free a $120K/ano |

---

## 4.4 Recomendação para a CollectAI

### Requisitos Críticos para o Onboarding de Cobrança

1. **Persistência de estado**: Workflows multi-step que podem durar dias
2. **Compliance regulatório**: Cobrança é altamente regulada — audit trail obrigatório
3. **Human-in-the-loop**: Gates de aprovação e compliance
4. **Flexibilidade de modelo**: Evitar vendor lock-in, otimizar custo/performance por tarefa
5. **Confiabilidade em produção**: Workflows financeiros são mission-critical
6. **Observabilidade**: Requisito de auditoria em serviços financeiros

### Recomendação Primária: LangGraph

**Por quê:**
- **Melhor gestão de estado** para workflows multi-step de onboarding (enrich → wizard → generate → simulate)
- **Human-in-the-loop nativo** para gates de compliance e aprovação
- **Modelo-agnóstico**: Usar Claude para raciocínio complexo, GPT-4o-mini para routing simples — otimizando custos
- **Execução durável** com recuperação de crashes — essencial para workflows financeiros
- **Comprovado em escala** (Klarna serve 85M usuários)
- **Observabilidade robusta** via LangSmith para audit trails

### Recomendação Secundária: CrewAI

Se a curva de aprendizado do LangGraph for um bloqueio, CrewAI é a segunda opção. Design role-based mapeia bem para o onboarding, é enterprise-ready (HIPAA/SOC2), e tem community grande.

### Por que NÃO os outros

- **OpenAI Agents SDK**: Sem persistência de estado é dealbreaker para workflows multi-step
- **Claude Agent SDK**: Lock-in em Claude inviabiliza otimização de custos
- **Agency Swarm**: Risco de maintainer único + comunidade pequena + rewrite recente — não confiável para sistema mission-critical

### Migração do Agency Swarm

1. **Fase 1**: Proof-of-concept com LangGraph para um workflow do onboarding
2. **Fase 2**: Rodar LangGraph (onboarding) e Agency Swarm (cobrança) em paralelo
3. **Fase 3**: Migração completa usando design model-agnostic do LangGraph

**Fontes:**
- LangGraph Official (langchain.com/langgraph) / LangSmith Pricing
- OpenAI Agents SDK (openai.github.io/openai-agents-python)
- Claude Agent SDK (platform.claude.com/docs/en/agent-sdk)
- Anthropic — Building Effective Agents
- Agency Swarm GitHub (github.com/VRSEN/agency-swarm)
- CrewAI (crewai.com)
- Cursor 2.0 Architecture (ByteByteGo)
- Claude Code Agent Architecture (ZenML)
- DataCamp — CrewAI vs LangGraph vs AutoGen

---

## 4.5 Agentes do Onboarding

### Agentes Necessários

O sistema de onboarding requer agentes específicos para o processo de setup, separados dos agentes de cobrança que rodam 24/7:

**1. Enrichment Agent**
- **Responsabilidade**: Orquestrar o pipeline de enriquecimento (CNPJ → N fontes → agregação)
- **Tools**: CNPJ API, Site Scraper, Reclame Aqui, Google Maps, News Search
- **Output**: CompanyProfile (JSON estruturado)

**2. Interview Agent**
- **Responsabilidade**: Conduzir o wizard híbrido, gerar follow-ups inteligentes
- **Context**: Recebe CompanyProfile do Enrichment Agent + respostas anteriores
- **Tools**: Whisper API (transcrição), Question Generator
- **Guardrails**: Manter foco em dados relevantes para cobrança, não divagar
- **Output**: BusinessContext (todas as respostas do wizard estruturadas)

**3. Agent Generator**
- **Responsabilidade**: Gerar a configuração completa do agente de cobrança
- **Input**: CompanyProfile + BusinessContext + AgentType
- **Output**: AgentConfig (JSON com prompt, tools, guardrails, policies)
- **Método**: Context engineering com structured output

**4. Simulation Orchestrator**
- **Responsabilidade**: Gerar conversa simulada entre o agente gerado e um devedor fictício
- **Sub-agentes**: Collection Agent (recém-gerado) + Debtor Simulator Agent
- **Output**: SimulationResult (conversa + métricas)

**5. Debtor Simulator Agent**
- **Responsabilidade**: Simular um devedor realista do segmento
- **Context**: CompanyProfile (setor, tipo de dívida, benchmarks)
- **Comportamentos**: Variação entre cooperativo, hesitante, resistente, confuso
- **Guardrails**: Manter realismo, não ser nem fácil demais nem impossível

### Separação de Contextos

- **Onboarding agents**: Rodam durante o setup, são efêmeros
- **Collection agents**: Rodam 24/7, são persistentes
- **Não compartilham threads**: Cada contexto tem sua própria memória

---

# PARTE 5: Sistema de Auto-Geração de Agentes

## 5.1 Context Engineering para Geração

### De Prompt Engineering para Context Engineering

Em 2025, o campo evoluiu de "prompt engineering" (craftar instruções isoladas) para "context engineering" (curar contextos dinâmicos e iterativos). Context engineering cobre **todos os tokens** que entram na context window, não só o prompt.

### As 6 Camadas de Contexto (Framework Anthropic)

1. **System Rules** — Define role, limites e comportamento. Muda raramente
2. **Memory** — Armazenamento persistente: dados da empresa, políticas, histórico
3. **Retrieved Documents** — Conhecimento externo via RAG: dados ERP, lista de devedores
4. **Tool Schemas** — Ações disponíveis: escalar, gerar link de pagamento, consultar saldo
5. **Recent Conversation** — Diálogo anterior com o devedor
6. **Current Task** — A mensagem que acabou de chegar

Os dados coletados no onboarding alimentam as 3 primeiras camadas do agente gerado.

## 5.2 Pipeline de Auto-Geração

### Como Funciona

1. **Input**: Todos os dados coletados no onboarding (CompanyProfile + BusinessContext + AgentType + user preferences)

2. **Processing**: O Agent Generator (LLM com structured output) recebe todo o contexto e gera a configuração completa do agente

3. **Output**: AgentConfig em JSON contendo:
   - System prompt detalhado e específico para o segmento
   - Lista de tools disponíveis (escalar, gerar link, verificar pagamento)
   - Guardrails categorizados (input rails, output rails, policy rails, tone rails)
   - Políticas de negociação (descontos, parcelas, horários)
   - Estratégias de negociação por cenário
   - Templates de mensagens (contato inicial, follow-up, confirmação)

4. **Validação**:
   - Schema validation (Pydantic)
   - Sanity checks: descontos dentro dos limites, horários válidos
   - Human review flag se algo parecer inconsistente
   - Versionamento: cada geração cria uma versão, cliente pode reverter

### Templates Base

Para acelerar a geração, manter templates base por tipo de agente:
- **Template Adimplente**: Foco em lembrete preventivo, tom suave, sem negociação de desconto
- **Template Inadimplente**: Foco em negociação, ofertas de desconto/parcelamento, escalação

O Agent Generator usa o template como ponto de partida e personaliza com os dados do onboarding.

## 5.3 Guardrails como Camada Separada

### Problema Atual

Hoje os guardrails da CollectAI estão **in-prompt** — incluídos como instruções no system prompt. Isso é frágil (LLMs podem contornar), não escalável e não auditável.

### Solução: Guardrails como Middleware

Migrar para uma arquitetura onde guardrails são camada entre o usuário e o agente:

**Mensagem do Devedor → INPUT RAILS → AGENTE (LLM) → OUTPUT RAILS → Resposta ao Devedor**

### Tipos de Guardrails

1. **Input Rails** (antes do agente processar): Validação de contexto, detecção de jailbreak, máscara de PII, filtro de conteúdo
2. **Output Rails** (depois do agente gerar resposta): Compliance CDC, Compliance LGPD, limites de política, verificação de tom, verificação de horário
3. **Policy Rails** (regras de negócio): Limites de desconto, limites de parcelamento, regras de escalação, frequência de contato
4. **Tone Rails** (consistência de marca): Tom configurado pelo cliente, nível de formalidade

### Frameworks Disponíveis

- **NVIDIA NeMo Guardrails**: Open-source, 5 tipos de rails, linguagem Colang
- **Guardrails AI**: Framework Python com validators combinados
- **Built-in do Agents SDK**: Decorators `@input_guardrail` e `@output_guardrail`

**Recomendação**: Para MVP, usar guardrails built-in do framework escolhido. Para produção, migrar para NeMo Guardrails. Manter guardrails in-prompt como camada adicional de backup.

**Fontes:**
- Anthropic — Effective Context Engineering for AI Agents
- NVIDIA NeMo Guardrails
- Guardrails AI (guardrailsai.com)

---

# PARTE 6: Simulação e AHA Moment

## 6.1 Importância do AHA Moment

### Definição

O AHA Moment da CollectAI é: **ver SEU agente, configurado com SUAS regras, negociando com um devedor do SEU segmento, usando o tom que VOCÊ escolheu**.

Não é ver um dashboard vazio ou ler documentação. É uma conversa realista, personalizada, acontecendo diante dos olhos do cliente — "uau, ele realmente negocia como eu faria — mas mais rápido e sem cansar".

### Benchmarks

- Usuários com valor core em **5-15 minutos**: **3x mais propensos a reter**
- AHA em **menos de 5 minutos**: **40% mais retenção em 30 dias**
- **Cada minuto extra**: **-3% conversão**
- Taxa de ativação top performers: **70-80%**

## 6.2 Arquitetura da Simulação Agent-to-Agent

### Conceito

Dois agentes conversam entre si:
1. **Collection Agent** (recém-gerado) — age como se estivesse cobrando
2. **Debtor Simulator Agent** — simula um devedor realista do segmento

A conversa é **pré-gerada no backend** antes do cliente ver. O cliente assiste read-only.

### Geração de Múltiplos Cenários

| Cenário | Personalidade | Típico |
|---------|--------------|--------|
| **1** | Cooperativo | Devedor que quer pagar mas precisa de condições |
| **2** | Hesitante | Devedor que precisa ser convencido |
| **3** | Resistente | Devedor que contesta e pede muito desconto |

### Métricas Exibidas ao Cliente

- **Taxa de acordo simulada**: ~65% (baseada nos 3 cenários)
- **Desconto médio oferecido**: 15%
- **Tempo médio de conversa**: 8 minutos
- **Escalações**: quantos cenários precisaram de humano

### Pesquisa Acadêmica Relevante

- **MADeN** (arXiv:2502.18228, Fev/2025): Framework Multi-Agent Debt Negotiation com 13 métricas. LLMs tendem a **conceder demais** — solução com DPO e rejection sampling
- **EmoDebt** (arXiv:2503.21080, Mar/2025): Framework de inteligência emocional para negociação agent-to-agent com matriz 7x7 de transição emocional

## 6.3 Avaliação e Iteração

1. Cliente vê a simulação (Step 6)
2. Cliente solicita ajustes (Step 7): "O tom está muito formal", "O desconto está baixo demais"
3. Agent Generator atualiza a configuração
4. Nova simulação é gerada (limite de 2-3 iterações grátis)
5. Cliente aprova e segue para pagamento

**Fontes:**
- Userpilot — AHA Moment Guide
- Sierra AI — Simulations: Secret Behind Great Agents
- arXiv 2502.18228, arXiv 2503.21080

---

# PARTE 7: Arquitetura do Backend

## 7.1 Visão Geral

### Stack

- **Frontend**: Construído no Lovable (React + Tailwind + shadcn/ui), conectado via API REST
- **Backend**: Python + FastAPI + Uvicorn
- **Framework de Agentes**: LangGraph (recomendado) ou alternativa
- **Mensageria**: RabbitMQ (para processamento assíncrono)
- **Cache**: Redis
- **Database**: PostgreSQL
- **Storage**: S3/MinIO (áudios, arquivos CSV)
- **APIs Externas**: OpenAI, CNPJ APIs, WhatsApp BSP, Stripe

### Princípio de Arquitetura

**API-first**: O backend é completamente independente do frontend. Toda comunicação via REST + SSE. Isso permite:
- Trocar o frontend (Lovable → outro) sem tocar no backend
- Testar o backend independentemente via Swagger/OpenAPI
- Múltiplos clientes consumindo a mesma API (web, mobile futuro, integrações)

## 7.2 APIs do Onboarding

### Grupos de Endpoints

**Registro e Sessão**
- Criar conta + sessão de onboarding
- Obter status da sessão
- Autenticação (login, refresh token)

**Enriquecimento**
- Disparar enriquecimento (CNPJ + site)
- SSE de progresso do enriquecimento
- Resultado do enriquecimento
- Atualizar dados da empresa (correções do cliente)

**Wizard**
- Salvar resposta de um step
- Gerar follow-up da IA
- Obter progresso do wizard

**Áudio**
- Upload de áudio → transcrição via Whisper → texto

**Geração de Agente**
- Gerar configuração do agente
- Retornar configuração gerada
- Aplicar ajustes

**Simulação**
- Gerar simulação agent-to-agent
- Retornar conversa simulada + métricas

**Campanha**
- Upload lista de devedores (CSV/XLSX)
- Validar lista
- Lançar campanha

**Pagamento**
- Criar payment intent (Stripe)
- Webhook de confirmação

### Processamento Assíncrono

Operações pesadas rodam em background via Celery workers ou consumers RabbitMQ:
- **Enriquecimento**: ~10-30s
- **Geração de agente**: ~5-15s
- **Simulação**: ~30-60s (múltiplos cenários)
- **Transcrição de áudio**: ~2-5s (rápido o suficiente para ser síncrono)

Comunicação com frontend: **Server-Sent Events (SSE)** para updates em tempo real, com fallback para polling.

### Rate Limiting

- Enriquecimento: 1 por sessão (re-enrich limitado a 3x)
- Follow-ups IA: Max 20 por sessão
- Simulações: Max 3 por sessão (grátis)
- Transcrições: Max 50 por sessão

## 7.3 Modelo de Dados

### Entidades Principais

- **Users**: Email, senha, nome, role, referência à empresa
- **Companies**: CNPJ, razão social, nome fantasia, segmento, porte, dados de enriquecimento (JSON)
- **Onboarding Sessions**: Referência à empresa e usuário, step atual, status (in_progress/completed/abandoned), respostas do wizard (JSON)
- **Generated Agents**: Referência à empresa e sessão, tipo (adimplente/inadimplente), configuração completa (JSON), versão, status (draft/active/paused)
- **Simulations**: Referência ao agente, cenários com conversas (JSON), métricas
- **Subscriptions**: Plano, referência Stripe, créditos restantes/usados, status
- **Campaigns**: Referência ao agente, status, tipo, total de contatos, acordos, configuração

### Abordagem

Usar PostgreSQL com JSONB para dados flexíveis (enrichment data, wizard responses, agent config). Migrações com Alembic.

## 7.4 Integração com WhatsApp Business API

### Consideração Crítica de Compliance

**Meta proíbe explicitamente cobrança de dívidas** na política do WhatsApp Business:

> "You may not use the WhatsApp Business Services for debt collection."

**Realidade brasileira:**
- IDEC (2013) reconheceu a legalidade de cobrança via WhatsApp sob lei brasileira
- Muitas empresas brasileiras usam WhatsApp para cobrança na prática
- **Risco principal**: Bloqueio da conta pela Meta (não responsabilidade legal)

**Estratégia recomendada:**
- Enquadrar mensagens como **"lembretes de pagamento"** e **"atendimento ao cliente"** (categorias utility/service)
- Usar linguagem de facilitação de pagamento, não demanda de dívida
- Consultar advogado especializado

### BSPs Recomendados

| BSP | Modelo | Pricing | Melhor Para |
|-----|--------|---------|-------------|
| **360dialog** | API Gateway | $50/mês fixo por número | Transparência de custo |
| **Twilio** | API Gateway | $0.005/msg + taxas Meta | Controle de desenvolvedor |

### Pricing de Mensagens (Brasil, pós-julho/2025)

| Categoria | Custo por Template | Notas |
|-----------|-------------------|-------|
| **Marketing** | ~$0.0625 | Mais caro — evitar |
| **Utility** | Menor que marketing | **GRÁTIS** dentro de 24h de janela de atendimento |
| **Service** | **GRÁTIS** | Respostas a mensagens do cliente |

**Fontes:**
- WhatsApp Business Policy
- 360dialog.com / Twilio
- Gallabox — WhatsApp Pricing Changes July 2025

---

# PARTE 8: Monetização e Modelo de Créditos

## 8.1 Panorama de Monetização em AI SaaS

### Tendências 2025-2026

- **Credit-based pricing** em alta: 79 empresas do PricingSaaS 500 Index (crescimento de 126%)
- **Usage-based**: 59% das empresas de software esperam crescimento
- **Outcome-based**: 45% das empresas SaaS experimentando pricing vinculado a resultado
- **Modelos híbridos dominam**: Maior mediana de crescimento (21%)

### Exemplos de Mercado

| Empresa | Modelo | Detalhe |
|---------|--------|---------|
| **Intercom Fin AI** | Outcome-based | $0.99 por conversa resolvida — **40% mais adoção** |
| **Salesforce** | Híbrido | $2/conversa para agents prebuilt + créditos |
| **Microsoft Copilot** | Híbrido | $30/user base + créditos para picos |

## 8.2 Modelo Recomendado: Híbrido (Base + Conversas)

### Estrutura

| Plano | Base Mensal | Conversas Incluídas | Agentes | Conv. Extra |
|-------|-----------|-------------------|---------|-------------|
| **Starter** | R$ 497 | 200 | 1 | R$ 1,50 |
| **Growth** | R$ 1.497 | 1.000 | 3 | R$ 1,20 |
| **Enterprise** | Custom | Custom | Ilimitado | Negociado |

**Por que este modelo:**
1. Base mensal garante receita previsível (MRR)
2. Conversas incluídas reduzem medo do desconhecido
3. Conversas extras capturam upside de alto uso
4. Simples de comunicar: "R$ 497/mês com 200 conversas. Extras a R$ 1,50 cada"

### Free Trial

- **Primeiras 50 conversas grátis** (sem cadastrar cartão)
- Objetivo: cliente experimenta o AHA Moment sem compromisso financeiro
- Benchmark: freemium → paid conversion de **20-30%** em PLG

---

## 8.3 Unit Economics Validados — Custo Real por Conversa de Cobrança

### Premissas (dados reais da operação)

| Parâmetro | Valor | Fonte |
|-----------|-------|-------|
| Modelo LLM | GPT-4.1-mini | Operação atual |
| Tokens por conversa engajada | ~22.000 tokens | Métricas reais |
| Taxa de engajamento | ~50% | Métricas reais (devedor responde) |
| Custo WhatsApp | Marketing messages | Meta nunca aceita utility para cobrança |
| Custo de compute/infra | ~$0.005/conversa | Métricas reais (atual) |

### Preços das APIs (fevereiro 2026)

**WhatsApp Business API — Brasil (per-message pricing, desde julho/2025):**

| Categoria | Custo por Mensagem | Nota |
|-----------|-------------------|------|
| **Marketing** | **$0.0625** | Usado para cobrança (Meta não aceita utility) |
| Utility | $0.0068 | Não aplicável para cobrança |
| Service (24h window) | Grátis | Mensagens dentro da janela de 24h após resposta do devedor |

> **Nota importante**: Desde julho/2025, a Meta mudou de cobrança por conversa (janela de 24h) para **cobrança por mensagem individual**. Cada template message outbound é cobrada separadamente.

**GPT-4.1-mini (OpenAI):**

| Tipo | Custo por 1M tokens |
|------|---------------------|
| Input | $0.40 |
| Input (cached) | $0.10 |
| Output | $1.60 |

### Custo por Conversa ENGAJADA (50% do total)

Conversa onde o devedor responde e há interação real.

| Componente | Cálculo | Custo |
|-----------|---------|-------|
| **WhatsApp marketing** | 1 msg template outbound ($0.0625). Devedor responde → abre janela 24h → msgs seguintes grátis. Se conversa ultrapassa 24h, +1 msg. Média: 1.2 msgs | **$0.075** |
| **GPT-4.1-mini** (22K tokens) | Split ~70% input / 30% output. Input: 15.4K × $0.40/1M = $0.00616. Output: 6.6K × $1.60/1M = $0.01056 | **$0.017** |
| **Prompt caching** | ~30% do input é system prompt cacheado: 4.6K × $0.10/1M = $0.00046 (em vez de $0.00184). Economia: $0.00138 | **-$0.001** |
| **Guardrails** (validação I/O) | Modelo leve para input/output rails | **$0.002** |
| **Compute/infra** | Servidor, processamento, filas | **$0.005** |
| **TOTAL conversa engajada** | | **~$0.098** |

### Custo por Conversa NÃO-ENGAJADA (50% do total)

Devedor não responde. O agente envia follow-ups ao longo de dias.

| Componente | Cálculo | Custo |
|-----------|---------|-------|
| **WhatsApp marketing** | 2-3 msgs template ao longo de dias (cada uma cobrada). Média: 2 msgs | **$0.125** |
| **GPT-4.1-mini** | Mínimo: seleção de template + routing (~500 tokens) | **$0.001** |
| **Compute/infra** | Menor (sem processamento de conversa) | **$0.002** |
| **TOTAL conversa não-engajada** | | **~$0.128** |

### Custo Médio Ponderado (Blended)

| Tipo | % do Total | Custo Unitário | Contribuição |
|------|-----------|---------------|-------------|
| Engajada | 50% | $0.098 | $0.049 |
| Não-engajada | 50% | $0.128 | $0.064 |
| **TOTAL BLENDED** | **100%** | | **~$0.113/conversa** |

> **Observação**: O custo da conversa não-engajada é **maior** que o da engajada, porque o WhatsApp cobra por cada mensagem de follow-up ($0.0625 cada), enquanto na conversa engajada as mensagens dentro da janela de 24h são grátis. Isso significa que **reduzir o número de follow-ups para não-engajados ou melhorar a taxa de engajamento tem impacto direto no custo**.

### Análise de Margem por Plano

| Plano | Preço/conv extra | Custo/conv | Margem por conv extra | Margem nas incluídas* |
|-------|-----------------|-----------|----------------------|----------------------|
| **Starter** | R$ 1,50 (~$0.26) | $0.113 | **57%** | **77%** (custo total R$ 115, preço R$ 497) |
| **Growth** | R$ 1,20 (~$0.21) | $0.113 | **46%** | **92%** (custo total R$ 115, preço R$ 1.497) |

*Margem nas conversas incluídas = (preço do plano - custo total das conversas incluídas) / preço do plano. A base mensal diluída inclui infra fixa e margem de contribuição.

### ROI Calculator para o Cliente

**Cenário: Empresa com R$ 500K em dívidas, 30% de inadimplência (R$ 150K)**

| Métrica | Sem CollectAI | Com CollectAI |
|---------|--------------|--------------|
| Taxa de recuperação | 25% (R$ 37.5K) | 40% (R$ 60K) |
| Custo operacional | R$ 5K/mês | R$ 1.5K/mês (Growth) |
| Recuperação líquida | R$ 32.5K | R$ 58.5K |
| **ROI** | — | **+80% recuperação, -70% custo** |

---

## 8.4 Custo do Onboarding por Cliente

### Breakdown por Etapa

O custo de onboardar cada novo cliente no sistema self-service:

| Etapa | O que Acontece | Custo Estimado | Nota |
|-------|---------------|---------------|------|
| **Enrichment** (site scraping + LLM) | Playwright renderiza site + GPT-4.1-mini extrai dados estruturados | $0.02-0.03 | BrasilAPI grátis |
| **Wizard/Interview — LLM follow-ups** | 5-10 interações com a IA gerando perguntas contextuais | $0.05-0.15 | Depende de quantos follow-ups |
| **Transcrição de áudio (Whisper)** | 3-10 minutos de áudio transcritos | $0.01-0.03 | GPT-4o-mini Transcribe a $0.003/min |
| **Geração do agente** | Prompt longo + structured output JSON (prompt, tools, guardrails, policies) | $0.03-0.10 | Output pesado (~5-10K tokens) |
| **Simulação agent-to-agent** (3 cenários) | 2 agentes conversando (collection + debtor simulator), 3 cenários | $0.10-0.30 | Etapa mais cara: múltiplos turns de 2 agentes |
| **Compute/infra** | Processamento server-side, filas, storage | $0.01-0.03 | Marginal |
| **TOTAL por onboarding** | | **$0.22-0.64** | **Típico: ~$0.40** |

### Custo em Escala

| Escala | Custo Variável (LLM + APIs) | Infra Fixa (mensal) | Custo Total Estimado |
|--------|----------------------------|--------------------|--------------------|
| **100 clientes** | ~$40 | ~$56/mês | **~$96** |
| **1.000 clientes** | ~$400 | ~$80-100/mês (upgrade em picos) | **~$500** |
| **10.000 clientes** | ~$4.000 | ~$150-200/mês (auto-scaling) | **~$4.200** |

### Custo de Onboarding vs. LTV do Cliente

| Métrica | Valor |
|---------|-------|
| Custo de onboarding por cliente | ~$0.40 (~R$ 2,30) |
| Receita mensal Starter | R$ 497 |
| **Payback do onboarding** | **< 1 hora** |
| LTV estimado (12 meses, Starter) | R$ 5.964 |
| **Custo de onboarding como % do LTV** | **0.04%** |

> **Conclusão**: O custo de onboarding é **irrelevante** em comparação com o valor gerado. Mesmo a simulação agent-to-agent (etapa mais cara) custa centavos. Isso confirma que vale investir em uma experiência de onboarding rica (com simulação, áudio, follow-ups de IA) porque o custo marginal é desprezível.

---

## 8.5 Projeção de Redução de Custos ao Longo do Tempo

### Tendência Histórica de Preços de LLMs

Os preços de modelos LLM caem consistentemente:
- GPT-4 (março/2023) → GPT-4o (maio/2024): **redução de ~75%**
- GPT-4o → GPT-4o-mini (julho/2024): **redução de ~90%**
- GPT-4o-mini → GPT-4.1-mini (abril/2025): **aumento de 167%** (mas com capacidades muito superiores)
- GPT-4.1-mini → GPT-4.1-nano (abril/2025): **redução de 75%** (trade-off de qualidade)

A tendência geral é de **modelos cada vez mais capazes a preços cada vez menores**. Estimativa conservadora: custo por token cai ~30-50% ao ano para modelos de mesma capacidade.

### Projeção de Custo por Conversa de Cobrança

| Horizonte | Custo/conversa | Variação | Drivers de Redução |
|-----------|---------------|---------|-------------------|
| **Hoje** | **$0.113** | Baseline | — |
| **6 meses** | **~$0.08** | -29% | Prompt caching agressivo (system prompt + histórico parcial), GPT-4.1-nano para routing/template selection, right-sizing da infra AWS |
| **12 meses** | **~$0.06** | -47% | AWS Reserved Instances (-30% no compute), novo modelo OpenAI mais barato, batching de guardrails, otimização de prompts (menos tokens) |
| **18 meses** | **~$0.04** | -65% | Próxima geração de modelo (tendência histórica -50%/ano), infra totalmente otimizada, cache de respostas frequentes |

### Alavancas Específicas de Redução

**1. Prompt Caching (impacto: -10-15% no custo LLM)**
- System prompt (~3-5K tokens) é idêntico em todas as chamadas → cacheável
- GPT-4.1-mini cached input: $0.10/1M vs. $0.40/1M (75% mais barato)
- Implementação: já disponível na API, basta estruturar o prompt corretamente

**2. Modelo Híbrido por Complexidade (impacto: -20-30% no custo LLM)**
- GPT-4.1-nano ($0.10/1M input, $0.40/1M output) para tarefas simples: routing, seleção de template, classificação de intenção
- GPT-4.1-mini para tarefas complexas: negociação, geração de resposta personalizada, cálculo de desconto
- Estimativa: 40% das chamadas podem usar nano → economia de ~60% nessas chamadas

**3. WhatsApp — Redução de Follow-ups (impacto: -15-20% no custo total)**
- Cada follow-up para não-engajado custa $0.0625
- Otimizar timing e conteúdo dos follow-ups para maximizar resposta na 1ª mensagem
- Meta: reduzir de 2 msgs médias para 1.5 msgs para não-engajados → economia de $0.03/conversa

**4. Right-sizing AWS (impacto: variável na infra fixa)**

| Setup | Custo Mensal | Nota |
|-------|-------------|------|
| **Atual: Directus em EC2 superdimensionado** | **~$60-120/mês** | Máquina maior que necessário para o tráfego atual |
| Otimizado: EC2 único t4g.medium (Docker) | ~$25-35/mês | FastAPI + Postgres + Redis + RabbitMQ em containers. Ideal para <100 clientes |
| Otimizado: Serviços separados AWS | ~$56/mês | EC2 t4g.small ($12) + RDS db.t4g.micro ($12) + ElastiCache ($9.50) + Amazon MQ ($22). Managed services, mais resiliente |
| Futuro: ECS Fargate + RDS | ~$40-45/mês | Auto-scaling, zero gerenciamento de EC2, paga pelo uso. Ideal para 100+ clientes com tráfego variável |

**Recomendação de migração:**
1. **Agora → 100 clientes**: EC2 único t4g.medium com Docker Compose (~$25/mês). Simples, barato, suficiente
2. **100-500 clientes**: Migrar PostgreSQL para RDS (backups automáticos, failover) + EC2 para app (~$35-40/mês)
3. **500+ clientes**: ECS Fargate + RDS + ElastiCache. Auto-scaling, sem gerenciamento de servidores (~$60-100/mês)

**5. AWS Savings Plans e Reserved Instances (impacto: -20-52% na infra)**
- Reserved Instances 1 ano: ~20-30% de desconto
- Savings Plans 3 anos: até 52% de desconto
- Aplicar quando volume de clientes justificar compromisso

### Cenário Consolidado: Custo Mensal por Escala de Operação

**Premissas**: Plano Starter (200 conversas/cliente), mix 50/50 engajada/não-engajada

| Cenário | Nº Clientes | Conversas/mês | Custo Variável/mês | Infra Fixa/mês | Custo Total/mês | Receita MRR | **Margem** |
|---------|------------|--------------|--------------------|--------------|-----------------|-----------| --------|
| **Seed** | 10 | 2.000 | $226 (~R$ 1.300) | ~$30 | ~R$ 1.470 | R$ 4.970 | **70%** |
| **Tração** | 50 | 10.000 | $1.130 (~R$ 6.500) | ~$45 | ~R$ 6.760 | R$ 24.850 | **73%** |
| **Escala** | 200 | 40.000 | $4.520 (~R$ 25.900) | ~$80 | ~R$ 26.360 | R$ 99.400 | **73%** |
| **Growth** | 1.000 | 200.000 | $22.600 (~R$ 129.600) | ~$150 | ~R$ 130.460 | R$ 497.000 | **74%** |

> **Nota**: A margem melhora ligeiramente com escala porque a infra fixa se dilui. Com as otimizações projetadas (prompt caching, modelo híbrido, AWS optimized), a margem pode chegar a **80-85%** em 12-18 meses.

**Fontes:**
- OpenAI API Pricing (platform.openai.com/docs/pricing)
- Meta WhatsApp Business Platform Pricing (business.whatsapp.com/products/platform-pricing)
- FlowCall — WhatsApp Business API Pricing 2026
- GetGabs — Meta Rate Card
- AWS — EC2, RDS, ElastiCache, Amazon MQ, Fargate pricing (us-east-1)
- GrowthUnhinged — 2025 State of SaaS Pricing
- Metronome — Rise of AI Credits
- Bessemer — AI Pricing Playbook
- Chargebee — Pricing AI Agents Playbook

---

# PARTE 9: Lançamento de Campanha e Pós-Onboarding

## 9.1 Upload e Processamento da Lista de Devedores

**Formatos aceitos**: CSV (delimitado por vírgula ou ponto-e-vírgula), XLSX (Excel). Futuro: integração direta com ERPs (Omie, Bling, Conta Azul).

**Campos**: Nome (obrigatório), Telefone (obrigatório), Valor devido (obrigatório), Data vencimento (obrigatório), Email/CPF/CNPJ/Segmento/Histórico (opcionais).

**Pipeline**: Upload → Parse → Mapeamento de colunas → Validação → Preview → Report de erros → Confirmação.

## 9.2 Configuração de Campanha

- Horários de envio (default: 08:00-20:00)
- Dias de envio (default: seg-sex, opção sábado)
- Frequência de follow-up (default: a cada 3 dias)
- Limite diário de mensagens
- Segmentação automática sugerida (por faixa de valor, tempo de atraso, perfil)

---

# PARTE 10: Segurança, Compliance e Governança

## 10.1 LGPD e Proteção de Dados

### Base Legal Recomendada para Cobrança

1. **Proteção ao crédito** (Art. 7, X) — mais diretamente aplicável
2. **Legítimo interesse** (Art. 7, IX) — se devedor recebeu serviço/produto e não pagou
3. **Execução de contrato** (Art. 7, V) — processamento necessário para execução do contrato

**NÃO usar** consentimento como base primária — devedor poderia revogar e impedir contato.

**Nota**: A LGPD é **silenciosa quanto a dados financeiros** — NÃO são "dados pessoais sensíveis".

### Direitos do Titular (Art. 18)

O sistema deve permitir: acesso, correção, anonimização/exclusão, portabilidade, informação sobre compartilhamento.

## 10.2 Regulação de Cobrança (CDC)

**Art. 42**: Consumidor inadimplente NÃO será exposto a ridículo ou submetido a constrangimento.

**Horários permitidos**: Dias úteis 08:00-20:00, Sábados 08:00-14:00, Domingos/feriados PROIBIDO.

**Proibido**: Exposição pública da dívida, ligações excessivas, contato com terceiros, cobrança fora de horário, ameaças.

→ Tudo isso deve ser **automatizado nos guardrails** do agente.

## 10.3 AI Governance

### Transparência

**LGPD Art. 20**: Devedor pode solicitar revisão de decisões feitas pela IA. Controller deve fornecer informações sobre critérios.

**PL 2338/2023 (AI Bill Brasil)**: Aprovado pelo Senado (dez/2024), em revisão pela Câmara. Chatbots devem divulgar que são IA.

**Recomendação**: O agente DEVE divulgar que é IA. Mensagem sugerida: "Este é um atendimento automatizado da [empresa]. Se preferir falar com um atendente humano, digite HUMANO a qualquer momento."

### Auditoria e Human-in-the-Loop

- Log completo de todas as conversas
- Decisões do agente registradas (qual desconto, por quê)
- Guardrails triggered registrados
- Escalação obrigatória para: valores acima do threshold, solicitação de humano, menção de processo judicial, N tentativas sem acordo

**Fontes:**
- LGPD (lgpd-brazil.info), CDC (planalto.gov.br)
- PL 2338/2023
- ICLG — Data Protection Brazil 2025

---

# PARTE 11: Roadmap de Implementação

## 11.1 Fases de Desenvolvimento

### Fase 1: Backend MVP (6-8 semanas)

**Foco: Backend completo como API-first**

| Componente | Escopo |
|-----------|--------|
| **Auth** | JWT, registro, login |
| **Enriquecimento** | CNPJ básico (ReceitaWS/BrasilAPI), SSE de progresso |
| **Wizard API** | Endpoints para salvar respostas dos steps |
| **Geração de Agente** | Agent Generator com templates base + customização |
| **Pagamento** | Stripe Checkout (planos fixos) |
| **Campanha** | Upload CSV + lançamento básico |
| **OpenAPI Spec** | Spec completa exportada para consumo do Lovable |

**Não inclui**: Chat IA, áudio, enriquecimento avançado, simulação.

### Fase 2: Frontend + AHA Moment (4-6 semanas)

**Foco: Frontend no Lovable + simulação**

| Componente | Escopo |
|-----------|--------|
| **Frontend Lovable** | Wizard multi-step consumindo API do backend |
| **Simulação** | Agent-to-agent com 2-3 cenários |
| **Enriquecimento+** | + Site scraping + Reclame Aqui |
| **Validação de dados** | Step de review com dados enriquecidos |
| **Ajustes** | Editor básico de tom/políticas com re-simulação |

### Fase 3: IA Híbrida (6-8 semanas)

| Componente | Escopo |
|-----------|--------|
| **Chat IA** | Interview Agent com follow-ups inteligentes |
| **Áudio** | MediaRecorder + Whisper (batch) |
| **Geração avançada** | Context engineering completo |
| **Guardrails** | Migração para camada separada |

### Fase 4: Polish (4 semanas)

| Componente | Escopo |
|-----------|--------|
| **Enriquecimento** | + Google Maps + notícias + concorrentes + benchmarks |
| **Analytics** | Dashboard de onboarding (funil, abandono, tempo) |
| **Mobile** | Otimização mobile-first |
| **Billing** | Usage-based billing com Stripe Metered |

## 11.2 Equipe Necessária

| Role | Perfil | Dedicação |
|------|--------|-----------|
| **Backend Dev** | Python senior, experiência com LLMs, FastAPI, async | Full-time |
| **Frontend** | Lovable + refinamento no IDE para edge cases | Part-time (fundador) |
| **UX Designer** | Experiência em B2B SaaS onboarding | Part-time ou freelancer |
| **Fundadores** | Product direction, QA, teste de agentes | Part-time (como hoje) |

## 11.3 Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Qualidade do agente gerado automaticamente | Alto | Templates robustos + review humano + simulação como QA |
| WhatsApp bloquear conta por cobrança | Alto | Enquadrar como utility/service, linguagem de facilitação, advogado |
| Abandono no onboarding | Alto | Progressive disclosure, save & resume, <15 min, AHA Moment cedo |
| O2OBOTS e Neofin lançarem self-service antes | Alto | **Velocidade de execução é tudo** — lançar MVP fast |
| Custo de tokens em escala | Médio | Cache, modelos leves para tarefas simples (gpt-4o-mini) |
| Latência do enriquecimento | Médio | Async, feedback progressivo, cache agressivo |
| LGPD/compliance violação | Alto | Guardrails automatizados, auditoria, logs |

---

# APÊNDICES

## Apêndice A: Glossário

| Termo | Definição |
|-------|----------|
| **Multi-agent** | Sistema com múltiplos agentes de IA coordenados |
| **Handoff** | Transferência de controle de um agente para outro |
| **Guardrails** | Regras/validações que limitam o comportamento do agente |
| **Context engineering** | Curadoria de todos os dados que entram na context window do LLM |
| **PLG** | Product-Led Growth — crescimento liderado pelo produto |
| **AHA Moment** | Instante em que o usuário percebe o valor do produto |
| **Structured output** | Output do LLM em formato JSON com schema definido |
| **SSE** | Server-Sent Events — streaming unidirecional do servidor |
| **Aging** | Tempo de atraso de uma dívida |
| **Wizard** | Interface de formulário com múltiplos steps sequenciais |
| **BSP** | Business Solution Provider (WhatsApp) |
| **MCP** | Model Context Protocol — padrão aberto para integração de ferramentas em sistemas IA |

## Apêndice B: Referências e Bibliografia

### Mercado e Dados
- Serasa Experian — Mapa da Inadimplência
- CNDL/SPC Brasil — Indicadores de Inadimplência
- Febraban — Pesquisa de Economia Bancária
- Market.us — AI for Debt Collection Market
- 6W Research — Brazil Debt Collection Software Market

### Competidores
- Neofin.com.br / Finsiders Brasil
- Monest.com.br / Finsiders — MIA
- EaseCob.com / EaseAndTrust.ai
- O2OBOTS.com
- Fintalk.ai, YKP.com.br, Moveo.ai
- Assertiva.com.br, Acerto.com.br
- C&R Software, HighRadius, Sedric AI, Vodex AI
- TrueAccord.com, Symend.com

### UX e Design
- Insaim Design — SaaS Onboarding Best Practices 2025
- NN/g — Cognitive Load, Progressive Disclosure
- Userpilot — AHA Moment Guide / Time-to-Value Benchmark
- Appcues — AHA Moment Guide
- JavaPro — AI-Powered Form Wizards

### Frameworks de Agentes
- LangGraph (langchain.com/langgraph)
- OpenAI Agents SDK (openai.github.io/openai-agents-python)
- Claude Agent SDK (platform.claude.com/docs)
- Anthropic — Building Effective Agents
- Agency Swarm (github.com/VRSEN/agency-swarm)
- CrewAI (crewai.com)
- Cursor 2.0 Architecture (ByteByteGo)
- Claude Code Architecture (ZenML)

### Lovable e Integração Frontend
- Lovable Frontend Framework (Sidetool)
- How I Made Lovable Play Nice with a Real Backend (HackerNoon)
- Connecting Custom Backends to Lovable (RapidDev)
- From Lovable To Production (Seismic)

### Tecnologia
- OpenAI — Speech-to-Text / Structured Outputs
- MDN — MediaRecorder API
- NVIDIA NeMo Guardrails

### APIs de Enriquecimento
- CNPJa, CNPJ.ws, ReceitaWS, BrasilAPI, OpenCNPJ
- Outscraper, SerpAPI
- Reclame Aqui API

### Legal e Compliance
- LGPD (lgpd-brazil.info)
- CDC — Lei 8.078/1990
- PL 2338/2023 — AI Bill Brasil
- ICLG — Data Protection Brazil 2025

### Monetização
- GrowthUnhinged — 2025 State of SaaS Pricing
- Bessemer — AI Pricing Playbook
- Chargebee — Pricing AI Agents Playbook

### WhatsApp
- WhatsApp Business Policy
- 360dialog.com
- Gallabox — Pricing Changes July 2025

### Pesquisa Acadêmica
- arXiv 2502.18228 — Debt Collection Negotiations with LLMs (MADeN)
- arXiv 2503.21080 — EmoDebt
