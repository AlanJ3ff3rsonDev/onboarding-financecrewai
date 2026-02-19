# Pesquisa e Arquitetura: Sistema de Onboarding Self-Service

## CollectAI / Finance Crew AI

**Data:** 18 de Fevereiro de 2026
**Versão:** 1.0
**Classificação:** Documento Interno — Estratégico

---

# Sumário Executivo

## O Problema

O crescimento da CollectAI está limitado pela capacidade de onboarding manual. Hoje, cada novo cliente passa por uma call individual com o fundador, onde são coletados dados sobre a empresa, fluxo de cobrança, políticas e preferências. Com isso, o agente de cobrança é criado manualmente — prompt, tools, guardrails, políticas de desconto e tom de voz.

Esse processo limita a aquisição a **5-10 calls por semana**, criando um gargalo direto no crescimento. O time fundador trabalha 1-2 horas por dia (todos têm empregos paralelos), o que torna o modelo atual insustentável para escalar além de poucos clientes por mês.

## A Solução Proposta

Criar um **onboarding self-service** onde o cliente:

1. **Se cadastra** e informa CNPJ/site da empresa
2. **Tem seus dados enriquecidos automaticamente** (Receita Federal, site, Reclame Aqui, Google Maps, redes sociais, concorrentes, benchmarks do setor)
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

## Decisões Arquiteturais Chave

1. **Padrão de UX**: Wizard híbrido + chat conversacional
2. **Enriquecimento**: Pipeline multi-fonte com agregação por LLM
3. **Geração de agentes**: Context engineering com structured output (JSON)
4. **Guardrails**: Camada separada (não mais in-prompt)
5. **Simulação**: Agent-to-agent com debtor simulator calibrado por segmento
6. **Monetização**: Modelo híbrido (base mensal + créditos por uso)
7. **Framework de agentes**: Avaliação OpenAI Agents SDK vs. Agency Swarm atual

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

**Contexto macro:**
- Selic em **15,25%** (maior desde julho/2006)
- Desemprego paradoxalmente baixo: **5,6%** (menor desde 2012)
- Renda média real cresceu 5,7% para R$ 3.560
- Inflação projetada: ~4,06% para 2026

**Fontes:**
- Serasa Mapa da Inadimplência (serasa.com.br)
- Central do Varejo — Brasil encerra 2025 com 50% de inadimplência
- CNDL/SPC Brasil — Recorde de inadimplentes
- Revista Nordeste — 81,2 milhões de pessoas inadimplentes
- InfoMoney — Inadimplência cartão rotativo recorde 2025
- Agência Brasil — Juros cartão rotativo 451,5%
- Febraban — Pesquisa economia bancária dez/2025
- ANBC — Perspectivas 2026

---

## 1.2 Mercado de Cobrança Digital e IA

### Tamanho do Mercado Global

O mercado de cobrança com IA está em crescimento acelerado:

| Segmento | Valor 2024 | Projeção | CAGR |
|----------|-----------|----------|------|
| **IA para Cobrança** | USD 3,34 bi | USD 15,9 bi (2034) | 16,90% |
| **Software de Cobrança** | USD 3,30 bi | USD 7,74 bi (2033) | 9,95% |
| **Serviços de Cobrança** | USD 47,7 bi | USD 69,1 bi (2035) | 3,70% |

### Impacto Comprovado da IA na Cobrança

Dados de mercado que validam a proposta da CollectAI:

- **McKinsey**: IA melhora taxas de recuperação em **até 25%**; segmentação por IA pode elevar a recuperação em **15-25%** enquanto reduz custos em **até 70%**
- **Kaplan Group**: Scoring preditivo com IA melhorou recuperação em média **25%**
- **Juniper Research**: Instituições financeiras com IA agentic viram **31% de melhoria** nas taxas de recuperação
- **HighRadius**: 20% de redução em past-due, 30% de aumento de produtividade
- **Vodex AI**: 3x de melhoria na taxa de recuperação, 7x de melhoria na taxa de conexão
- **Dado geral**: IA pode quadruplicar a produtividade dos cobradores (2-4x) e reduzir custos operacionais em **30-50%**
- **Adoção**: 61% das empresas adotaram analytics preditivo e 55% comunicação automatizada com consumidores

### Players Globais

**C&R Software (+ Zelas AI)**
- Líder de mercado há 40+ anos; produto principal: Debt Manager
- Lançou **Zelas** (jan/2026): assistente agentic com IA que coordena agentes especializados
- Features: drafting de scripts em tempo real, sumarização de contas, surfacing de políticas
- Designed para ambientes altamente regulados
- Pricing: enterprise (não divulgado)

**Sedric AI**
- Foco: **monitoramento de compliance** para cobrança
- Audita automaticamente **100% das interações** com consumidores
- Detecta violações regulatórias em tempo real
- Multi-canal: transcreve e traduz chamadas em **40+ idiomas**

**HighRadius**
- Plataforma agentic de O2C (Order-to-Cash) com **15+ agentes de IA**
- Resultados: **20% redução em past-due**, **30% aumento de produtividade**, **redução de DSO em até 12 dias**
- 1.000+ clientes globais (P&G, Ferrero, J&J, Danone)
- **Líder do Gartner Magic Quadrant** por 3 anos consecutivos
- Pricing: subscription-based, pay-as-you-go SaaS

**Kolleno**
- Plataforma de AR management com workflows automatizados por IA
- Features: lembretes/follow-ups/escalações automatizadas, AI Copilot para tom/canal/mensagem otimizados
- 100+ template tags para emails
- Pricing: enterprise custom

**Vodex AI**
- Foco: **agentes de voz com IA** para cobrança
- Resultados em case studies: connect rates **7x maiores**, recovery rates **3x maiores**
- Compliance com FDCPA, TCPA, CFPB

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
- Agentes de IA no WhatsApp descritos como "duas vezes mais eficazes" que chatbots tradicionais

**3. Scoring Preditivo**
- Modelos de ML analisam: histórico de pagamento, perfil de crédito, padrões de transação, sinais demográficos, tendências macro
- Geram: scores de propensão a pagar, modelos de preferência de canal, estratégias de cura otimizadas

**Fontes:**
- Market.us — AI for Debt Collection Market
- Mordor Intelligence — Debt Collection Software Market
- C&R Software — AI Native / Zelas Launch
- Sedric AI — Debt Collection
- HighRadius — Automated Debt Collection / Agentic AI Blog
- Vodex AI — Debt Collection / Case Studies
- Kolleno.com
- Bridgeforce — Transforming Recovery Rates
- WapiKit — WhatsApp Business Statistics 2025
- Moveo.AI — WhatsApp Debt Collection
- Webio — WhatsApp for Debt Collection

---

## 1.3 Análise Competitiva Detalhada

### Competidores Brasileiros

**Neofin** — O competidor mais direto
- Fundada em janeiro/2023
- **Captou R$ 35 milhões** em rodada seed (janeiro/2025), liderada por Quona e Upload
- Produto: sistema inteligente de cobrança automatizada com "régua de cobrança" por IA
- Features: regras multi-canal automatizadas (email, WhatsApp, SMS), segmentação por perfil de pagamento, dashboards, Serasa integration, integrações ERP (Omie, Protheus, Nomus)
- Roadmap: portal de renegociação 100% automático, CRM avançado de cobrança, conversas via WhatsApp com IA
- **Diferencial vs. CollectAI**: Neofin foca em automação de régua; CollectAI foca em agentes autônomos que negociam com linguagem natural

**Monest (MIA)**
- Baseada em Curitiba, PR
- **Pioneira no Brasil** no uso de ChatGPT-4 para recuperação de crédito
- Produto: **MIA** — assistente virtual que conduz negociações via diálogo natural
- Resultados: redução de custos em **até 35%**, produtividade do time **+40%**, taxa de recuperação **+5%**
- Oferece formato **white-label** para bancos e fintechs
- Clientes: Adiante Recebíveis, Arco Educação, Grupo Marista

**EaseCob.ai**
- Cobrança e negociação por IA via WhatsApp e voz
- Modelos proprietários treinados em carteiras de clientes
- Multi-canal: WhatsApp, voz, SMS, email, redes sociais
- Estima probabilidade de pagamento após contato

**Neurotech**
- Fundada em 2002, Recife — **adquirida pela B3 por R$ 1,142 bilhão**
- 100+ clientes, 1.000+ soluções implementadas
- Produto de cobrança: **Bruce Cobrança** — usa speech analytics e análise de dados não-estruturados
- Soluções possibilitam aumento de **15-20%** na oferta de crédito sem elevar risco
- Modelo enterprise — sem self-service

**Assertiva**
- Uma das **maiores datatechs do Brasil** com **6.000+ clientes**
- Acesso a **200 milhões de CPFs** e **60+ milhões de CNPJs**
- Produto: **Assertiva Recupere** — automação de cobrança com boleto, IA, VoIP, workflows
- Pricing: a partir de **R$ 250/mês**
- Foco em PMEs com automação básica — não tem agentes com IA conversacional

**Acordo Certo (Acerto)**
- **Maior plataforma online** de pagamento e renegociação de dívidas do Brasil
- **3,7+ milhões** de brasileiros cadastrados
- **$10M+** em dívidas pagas por mês
- Usa **H2O Driverless AI** para scoring (propensão a aderir, propensão a pagar)
- **Consumer-facing**: marketplace entre credores e devedores — não é concorrente direto (B2C)

### Tabela Comparativa

| Aspecto | CollectAI | Neofin | Monest | EaseCob | Assertiva |
|---------|-----------|--------|--------|---------|-----------|
| **Modelo** | Agentes autônomos | Régua automatizada | Assistente IA | IA multi-canal | Workflow + VoIP |
| **IA Conversacional** | Sim (negociação) | Roadmap | Sim (GPT-4) | Sim (proprietário) | Não |
| **Self-Service Onboard** | Em desenvolvimento | Não | Não | Não | Parcial |
| **WhatsApp** | Sim | Sim | Não especificado | Sim | SMS/email |
| **Multi-agente** | Sim (4 agentes) | Não | Agente único | Não especificado | Não |
| **Target** | PME-Mid | PME-Mid | Mid-Enterprise | Mid-Enterprise | PME |
| **Pricing** | TBD | Não divulgado | Não divulgado | Não divulgado | R$ 250+/mês |
| **Funding** | Bootstrapped | R$ 35M seed | Não divulgado | Não divulgado | Estabelecida |

### Gap Analysis

**O que nenhum competidor oferece:**
1. **Onboarding self-service** com geração automática de agente
2. **Simulação agent-to-agent** como AHA Moment
3. **Enriquecimento avançado automático** (CNPJ + site + Reclame Aqui + concorrentes)
4. **Wizard híbrido** com chat + áudio
5. **Arquitetura multi-agente** completa acessível via self-service

> **Posicionamento único**: A CollectAI é a única plataforma que combina self-service onboarding + agentes autônomos multi-agente + WhatsApp-first + geração automática de agentes. Isso a posiciona como o "Claude Code da cobrança" — uma plataforma onde qualquer empresa cria seus agentes de cobrança sem precisar de uma call.

**Fontes:**
- Neofin.com.br — Release janeiro/2025
- Finsiders Brasil — Neofin R$ 35M
- Monest.com.br
- Finsiders — Monest MIA
- EaseCob.com / EaseAndTrust.ai
- Neurotech.com.br
- Assertiva / Assertiva Recupere
- Acerto.com.br
- H2O.ai — Acordo Certo Case Study

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
| **Descoberta** | Pesquisa "cobrança automatizada" no Google ou vê no LinkedIn | Não sabe que existe IA para cobrança | SEO + LinkedIn content |
| **Avaliação** | Visita o site, lê sobre a solução | "Será que funciona pra minha empresa?" | Case studies, ROI calculator |
| **Cadastro** | Cria conta, informa CNPJ | "Vai ser complicado de configurar?" | Registro simples, 30 segundos |
| **Enriquecimento** | Sistema busca dados automaticamente | "Vou ter que preencher 50 campos?" | Auto-fill com dados do CNPJ |
| **Entrevista** | Responde perguntas no wizard | "Não sei termos técnicos" | Linguagem simples, áudio, IA adapta |
| **Geração** | Sistema gera o agente | "Será que o agente entende meu negócio?" | Simulação mostra agente em ação |
| **AHA Moment** | Vê simulação agent-to-agent | "Uau, ele realmente negocia como eu faria!" | Conversa realista personalizada |
| **Ajuste** | Revisa e ajusta tom/regras | "E se ele fizer algo errado?" | Controle total das regras + guardrails |
| **Pagamento** | Escolhe plano e cadastra cartão | "Quanto vai custar?" | Pricing transparente + trial grátis |
| **Ativação** | Upload de lista e lança campanha | "E agora, como começo?" | Wizard guiado de campanha |
| **Retenção** | Acompanha resultados no dashboard | "Está funcionando?" | KPIs em tempo real + relatórios |

### Benchmarks de Time-to-Value

Dados de mercado para calibrar o onboarding:

- **Média SaaS**: 1 dia, 12 horas, 23 minutos até primeiro valor percebido
- **Ferramentas de desenvolvimento**: meta de menos de 30 minutos
- **Meta CollectAI**: **15-30 minutos** do cadastro até o AHA Moment (simulação)

Dados críticos:
- Usuários que experienciam valor core **em 5-15 minutos** são **3x mais propensos a reter** que os que esperam 30+ minutos
- Produtos que entregam AHA Moment **em 5 minutos** mostram **40% mais retenção em 30 dias**
- **Cada minuto extra** de time-to-value **reduz conversão em 3%**

Taxa de ativação benchmark:
- Média: 37,5% (mediana ~30%)
- Boa: 40-60%
- Top performers: 70-80%

**Fontes:**
- Userpilot — Time-to-Value Benchmark Report 2024
- Userpilot — AHA Moment Guide
- ProductLed — PLG Metrics
- High Alpha — 2025 SaaS Benchmarks
- Flowjam — SaaS Onboarding Best Practices 2025

---

# PARTE 2: UX/UI e Design do Onboarding

## 2.1 Fundamentos de UX para Onboarding Self-Service B2B

### Por que Onboarding é Crítico

Dado de mercado: **66% dos clientes B2B param de comprar** após uma experiência de onboarding ruim. O onboarding é o momento mais crítico da jornada do cliente — é onde a percepção de valor se forma (ou morre).

### Princípios de Design

**1. Progressive Disclosure (Revelação Progressiva)**
Mostrar informações apenas quando o usuário precisa delas, não todas de uma vez. Em vez de um formulário com 50 campos, dividir em steps com 3-5 campos cada. Cada step revela o próximo apenas após o anterior ser completado.

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

Os padrões mais eficazes identificados na pesquisa:

| Padrão | Quando Usar | Exemplo |
|--------|------------|---------|
| **Wizard Flow** | Apps data-heavy que precisam coleta estruturada | Configuração de agente (CollectAI) |
| **Product Tour** | Familiarizar com interface existente | Primeiro acesso ao dashboard |
| **Checklist** | Múltiplas tarefas independentes | Setup pós-onboarding |
| **Tooltip** | Orientação contextual in-place | Campos complexos do wizard |
| **Empty State** | Motivar primeira ação | Dashboard vazio → "Crie seu primeiro agente" |

**Referências de mercado:**

- **Slack**: SSO com um clique → convite de equipe → tutorial interativo de canais. AHA moment: quando equipe envia **2.000 mensagens**
- **HubSpot**: Self-serve extensivo com comunidade + artigos + vídeos. Progress bars em todo o onboarding. PLG com resource center para aprendizado independente
- **Intercom**: Segmentação por role no signup — cada persona (vendas, suporte, marketing) vê uma experiência diferente. Mensagens in-app e tooltips adaptados
- **Calendly**: Sign in com Google (1 step para conectar calendário) → auto-teste. AHA moment: usuário agenda reunião consigo mesmo

### Para Usuários Não-Técnicos

A persona da CollectAI (analista financeiro) não é técnica. Princípios essenciais:

- **Não remover complexidade, mas gerenciar quando e como o usuário a experiencia**
- Orientação contextual > documentação extensa
- Focar em ajudar o usuário a ter sucesso cedo, não em explicar tudo
- Gamificação leve: progress bars, indicadores visuais de conquista
- Quebrar workflows complexos em passos sequenciais simples
- Experiências orientadas a resultado reduzem ansiedade e constroem confiança

**Fontes:**
- Insaim Design — SaaS Onboarding Best Practices for 2025
- Onething Design — B2B SaaS UX Design 2026
- UserGuiding — B2B SaaS Onboarding
- NN/g — New Users Need Support with Gen-AI Tools
- ProductFruits — B2B SaaS Onboarding
- Super Users Studio — 6 Top UX Trends Transforming B2B SaaS 2025

---

## 2.2 O Padrão Híbrido: Wizard + Chat Conversacional

### O Conceito

O padrão híbrido combina dois modelos de interação:

1. **Wizard estruturado**: Steps pré-definidos com campos específicos — garante que todos os dados necessários sejam coletados
2. **Chat conversacional com IA**: Agente observa as respostas e gera perguntas de follow-up inteligentes — captura nuances e detalhes que um formulário fixo não pegaria

Este é um padrão emergente em 2025, documentado como "AI-Powered Form Wizards" pela JavaPro: assistentes dinâmicos que guiam o usuário step-by-step, validam input em tempo real, e usam RAG para oferecer ajuda contextual sobre como preencher campos.

### Como Funciona na CollectAI

```
┌──────────────────────────────────────────┐
│            WIZARD STEP 4                  │
│     "Políticas de Cobrança"              │
│                                          │
│  ┌────────────────────────────────┐      │
│  │ Desconto máximo à vista: [25%] │      │
│  │ Parcelas máximas: [6x]         │      │
│  │ Valor mínimo parcela: [R$ 200] │      │
│  └────────────────────────────────┘      │
│                                          │
│  ┌────────────────────────────────┐      │
│  │ 🤖 Chat IA                     │      │
│  │ "Você mencionou que o desconto │      │
│  │ máximo é 25%. Esse desconto    │      │
│  │ vale para todos os tipos de    │      │
│  │ dívida ou varia por faixa de   │      │
│  │ valor/tempo de atraso?"        │      │
│  │                                │      │
│  │ [Digitar resposta...]    [🎤]  │      │
│  └────────────────────────────────┘      │
│                                          │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░ 70%             │
│  [← Voltar]              [Próximo →]    │
└──────────────────────────────────────────┘
```

### Fluxo Detalhado

1. **Wizard step aparece** com campos pré-definidos (alguns já pré-preenchidos pelo enriquecimento)
2. **Cliente preenche os campos** (texto) ou **grava áudio** (botão de microfone)
3. **IA observa as respostas** e analisa se há lacunas ou oportunidades de aprofundamento
4. **IA gera follow-ups contextuais** no chat embeddado: "Você mencionou X. Pode me contar mais sobre Y?"
5. **Cliente responde** os follow-ups (texto ou áudio)
6. **Dados estruturados são salvos** em tempo real no backend
7. **Progress bar atualiza** mostrando avanço
8. **Próximo step** é liberado quando os dados mínimos foram coletados

### Referências Técnicas

- **boost.ai Get Started Wizard**: Onboarding co-pilot com interface de diálogo que guia enterprises na configuração de novas instâncias de agentes, gerando fundação funcional (intents, ações generativas, knowledge sources, guardrails) em minutos
- **OpenAI ChatKit** (outubro/2025): Framework drop-in de chat UI com streaming, attachments, e workflows de agentes
- **Sendbird Conversational Forms**: Formulários conversacionais integrados a chat
- **assistant-ui**: Framework de chat embeddado para React

**Fontes:**
- JavaPro — AI-Powered Form Wizards: Chat, Click, Done
- boost.ai — Introducing Get Started Wizard
- Sendbird — AI Conversational Forms
- assistant-ui (assistant-ui.com)
- Lazarev Agency — Chatbot UI Examples

---

## 2.3 Entrada de Áudio no Browser

### Arquitetura Técnica

O fluxo de captura de áudio no browser segue esta arquitetura:

```
[Botão 🎤] → getUserMedia → MediaRecorder → Chunks → Blob → Upload → Whisper API → Texto
```

### Fluxo Detalhado

**1. Permissão e captura:**
```javascript
// Solicitar permissão do microfone
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

// Detectar formato suportado (cross-browser)
function getSupportedMimeType() {
    const types = [
        'audio/webm;codecs=opus',  // Chrome, Firefox, Safari 18.4+
        'audio/webm',
        'audio/mp4',               // Safari (fallback)
        'audio/wav'
    ];
    return types.find(type => MediaRecorder.isTypeSupported(type));
}

// Criar recorder
const mimeType = getSupportedMimeType();
const recorder = new MediaRecorder(stream, { mimeType });
```

**2. Gravação:**
```javascript
const chunks = [];
recorder.ondataavailable = (e) => chunks.push(e.data);
recorder.onstop = () => {
    const blob = new Blob(chunks, { type: mimeType });
    uploadToBackend(blob);
};
recorder.start();
```

**3. Upload e Transcrição (Backend — Python):**
```python
from openai import OpenAI
client = OpenAI()

audio_file = open("recording.webm", "rb")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    language="pt"  # Português
)
# transcript.text contém o texto transcrito
```

### Modelos Whisper Disponíveis (2025)

| Modelo | Custo/minuto | Indicação |
|--------|-------------|-----------|
| `whisper-1` (V2) | $0.006 | Balanceado — **recomendado para MVP** |
| `gpt-4o-transcribe` | $0.006 | Maior acurácia |
| `gpt-4o-mini-transcribe` | $0.003 | Mais barato, boa qualidade |

**Acurácia em Português**: Word Error Rate de **8-15%** (idioma de recurso médio). Detecção automática de idioma incluída sem custo extra.

**Formatos aceitos**: mp3, mp4, mpeg, mpga, m4a, wav, webm (máximo 25MB)

### Considerações de UX

- **Indicador visual**: Animação de onda sonora durante gravação
- **Preview**: Botão de play para ouvir antes de enviar
- **Refazer**: Botão de regravar se ficou ruim
- **Feedback**: Texto transcrito aparece na tela após processamento
- **Timeout**: Limite de 2-3 minutos por gravação (evitar áudios longos)

### Compatibilidade Mobile (iOS Safari)

**Estado atual (2025):**
- Safari 18.4+ suporta `audio/webm;codecs=opus` via MediaRecorder
- Versões mais antigas requerem fallback para MP4/AAC
- **Sempre usar** `MediaRecorder.isTypeSupported()` para feature detection
- Nunca hardcodar formato — detectar dinamicamente

**Padrão de implementação cross-browser:**
```javascript
function getRecorderConfig() {
    const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/wav'
    ];
    const mimeType = mimeTypes.find(t => MediaRecorder.isTypeSupported(t));
    const extensionMap = {
        'audio/webm;codecs=opus': '.webm',
        'audio/webm': '.webm',
        'audio/mp4': '.mp4',
        'audio/wav': '.wav'
    };
    return { mimeType, extension: extensionMap[mimeType] };
}
```

### Alternativa: RecordRTC

Biblioteca WebRTC para gravação cross-browser. Oferece fallback mechanisms quando MediaRecorder não está disponível (usa WebAudio API). Recomendada como fallback para browsers mais antigos.

### Abordagem Avançada: Streaming em Tempo Real

Para versões futuras, é possível fazer transcrição em tempo real via WebSocket:
- **OpenAI Realtime API**: `wss://api.openai.com/v1/realtime` com modelos `gpt-4o-transcribe`
- Latência: primeiras transcrições parciais em ~150-300ms (conexão cabeada)
- VAD (Voice Activity Detection) automático
- Ideal para: feedback em tempo real durante respostas longas

**Recomendação**: Começar com batch (gravar → upload → transcrever). Migrar para streaming na versão 2+ se houver demanda.

**Fontes:**
- MDN — MediaRecorder API
- MDN — MediaStream Recording API
- OpenAI — Speech-to-Text Guide
- OpenAI — Pricing
- RecordRTC.org
- Build with Matija — iPhone Safari MediaRecorder
- WebKit Blog — MediaRecorder API
- Baseten — Real-Time Transcription Tutorial
- OpenAI — Realtime API

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

### Step 0: Registro

**Layout**: Página clean, campos mínimos
- Email
- Senha
- Nome completo
- Aceitar termos de uso

**Opção**: Sign-in com Google (SSO) para reduzir fricção.
**Após registro**: Redirect direto para Step 1 (sem email de confirmação bloqueante — confirmar depois).

### Step 1: CNPJ + Site

**Layout**: Input grande central

```
┌────────────────────────────────────────┐
│  "Vamos conhecer sua empresa"          │
│                                        │
│  CNPJ: [__.___.___/____-__]           │
│                                        │
│  Site (opcional): [www.exemplo.com.br] │
│                                        │
│  [Buscar dados da empresa →]           │
│                                        │
│  Loading: "Buscando dados na Receita   │
│  Federal... ✓                          │
│  Analisando site da empresa... ⏳      │
│  Consultando reputação... ⏳           │
│  Buscando dados do setor... ⏳"        │
└────────────────────────────────────────┘
```

**Feedback progressivo**: Mostrar cada fonte sendo consultada em tempo real (checkbox com ✓ conforme completa).
**Tempo de enriquecimento**: ~10-30 segundos (fontes em paralelo).

### Step 2: Validação dos Dados Enriquecidos

**Layout**: Card com dados pré-preenchidos, campos editáveis

```
┌────────────────────────────────────────┐
│  "Confirme os dados da sua empresa"    │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │ Razão Social: [Empresa XYZ Ltda] │  │
│  │ Nome Fantasia: [XYZ Cobranças]   │  │
│  │ CNAE: [6822-6/00 - Gestão...]    │  │
│  │ Porte: [Média Empresa]           │  │
│  │ Cidade: [São Paulo - SP]         │  │
│  │ Funcionários (est.): [~50]       │  │
│  │ Setor: [Construção Civil]        │  │
│  └──────────────────────────────────┘  │
│                                        │
│  📊 Reputação: Reclame Aqui 7.8/10    │
│  ⭐ Google Maps: 4.2/5 (127 reviews)  │
│  🔍 Concorrentes identificados: 5      │
│                                        │
│  [Corrigir dados]     [Confirmar →]    │
└────────────────────────────────────────┘
```

### Step 3: Seleção do Tipo de Agente

**Layout**: Duas cards grandes, seleção exclusiva

```
┌────────────────────────────────────────┐
│  "Que tipo de agente você quer criar?" │
│                                        │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ 📋 ADIMPLENTE │  │ ⚠️ INADIMPL. │   │
│  │              │  │              │   │
│  │ Lembretes de │  │ Cobrança e   │   │
│  │ pagamento p/ │  │ negociação   │   │
│  │ quem está em │  │ p/ quem está │   │
│  │ dia. Evita   │  │ em atraso.   │   │
│  │ atrasos.     │  │ Recupera     │   │
│  │              │  │ dívidas.     │   │
│  │ [Selecionar] │  │ [Selecionar] │   │
│  └──────────────┘  └──────────────┘   │
│                                        │
│  💡 "Depois você pode criar outros     │
│  agentes dentro da plataforma"         │
└────────────────────────────────────────┘
```

### Step 4: Wizard Híbrido — Sobre o Negócio

**Layout**: Formulário + chat IA embeddado
**Perguntas pré-definidas** (baseadas no roteiro atual do Francisco):

1. "Como funciona o modelo de negócio da sua empresa? Como o dinheiro entra?" (textarea ou áudio)
2. "Descreva o fluxo de cobrança atual — do atraso até o pagamento" (textarea ou áudio)
3. "Quando vocês consideram que uma conta virou atrasada? (D+1, D+5, D+15...)" (select)
4. "Quem faz a cobrança hoje?" (multiselect: financeiro, CS, vendas, jurídico, terceiro, ninguém)
5. "Quais canais vocês usam para cobrar?" (multiselect: WhatsApp, email, SMS, ligação, carta)
6. "Vocês segmentam a cobrança por perfil, valor ou tempo de atraso?" (sim/não + detalhe)

**Chat IA** gera follow-ups baseados nas respostas. Exemplos:
- Se respondeu "construtora": "Entendi que vocês são do setor de construção. As dívidas são relacionadas a financiamento de imóveis, prestação de serviços, ou compra de materiais?"
- Se respondeu "D+30": "Vocês fazem algum contato preventivo antes dos 30 dias? Lembrete de vencimento, por exemplo?"

### Step 5: Wizard Híbrido — Configuração do Agente

**Perguntas pré-definidas:**

1. "Qual tom de voz o agente deve usar?" (select: Formal, Amigável, Empático, Assertivo)
2. "Qual o desconto máximo que pode ser oferecido à vista?" (slider: 0-50%)
3. "Qual o desconto máximo para parcelamento?" (slider: 0-50%)
4. "Número máximo de parcelas?" (select: 2x a 24x)
5. "Valor mínimo por parcela?" (input: R$)
6. "O que o agente NUNCA deve fazer?" (textarea: guardrails)
7. "Em quais situações deve escalar para um humano?" (multiselect: valor acima de X, cliente insatisfeito, solicitação jurídica, outro)
8. "Horários permitidos para contato?" (time pickers)

**Chat IA** complementa:
- "Vocês oferecem condições diferentes para clientes antigos vs. novos?"
- "Existe alguma frase ou expressão que representa a identidade da empresa que o agente deveria usar?"

### Step 6: Simulação — AHA Moment

**Layout**: Chat read-only mostrando conversa simulada

```
┌────────────────────────────────────────┐
│  "Veja como seu agente agiria"         │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │ Agente XYZ Cobranças         🤖 │  │
│  │ ──────────────────────────────── │  │
│  │                                  │  │
│  │ 🤖 Olá João! Aqui é da XYZ     │  │
│  │ Cobranças. Identificamos que     │  │
│  │ existe uma pendência no valor    │  │
│  │ de R$ 3.500,00 ref. à parcela   │  │
│  │ de janeiro. Gostaríamos de       │  │
│  │ conversar sobre as opções de     │  │
│  │ pagamento. Pode falar agora?     │  │
│  │                                  │  │
│  │ 👤 Oi, tô passando por uma     │  │
│  │ dificuldade financeira agora.    │  │
│  │ Não tenho como pagar tudo.       │  │
│  │                                  │  │
│  │ 🤖 Entendo perfeitamente, João. │  │
│  │ Sabemos que imprevistos          │  │
│  │ acontecem. Temos algumas opções  │  │
│  │ que podem te ajudar:             │  │
│  │                                  │  │
│  │ 1️⃣ À vista com 20% de desconto: │  │
│  │    R$ 2.800,00                   │  │
│  │ 2️⃣ Em 3x de R$ 1.225,00        │  │
│  │ 3️⃣ Em 6x de R$ 641,67          │  │
│  │                                  │  │
│  │ Qual opção funciona melhor pra   │  │
│  │ você?                            │  │
│  │ ...                              │  │
│  └──────────────────────────────────┘  │
│                                        │
│  📊 Resultado da simulação:            │
│  • Taxa de acordo simulada: ~65%       │
│  • Desconto médio oferecido: 15%       │
│  • Tempo médio de conversa: 8 min      │
│                                        │
│  [← Ajustar agente]  [Aprovar →]      │
└────────────────────────────────────────┘
```

**Detalhes técnicos da simulação**: A conversa é gerada no backend (agent-to-agent) antes do cliente ver. O agente de cobrança recém-gerado conversa com um Debtor Simulator Agent calibrado para o segmento. 2-3 cenários diferentes são gerados (devedor cooperativo, hesitante, resistente).

### Step 7: Ajustes Finos

**Layout**: Editor com preview lado a lado
- Campos editáveis: tom de voz, limites de desconto, regras de escalação, mensagem inicial
- Preview em tempo real: como a mensagem ficaria com as alterações
- Botão "Re-simular" para ver novo cenário com ajustes

### Step 8: Pagamento

**Layout**: Seleção de plano + checkout Stripe
- Plano selecionado com breakdown de custos
- Input de cartão (Stripe Elements)
- Trial/créditos grátis para primeiras conversas
- Botão "Começar a cobrar"

### Step 9: Lançamento de Campanha

**Layout**: Upload de lista + configuração
- Drag-and-drop de CSV/XLSX
- Mapeamento de colunas (nome, telefone, valor, vencimento)
- Validação e preview dos dados
- Configuração: horários de envio, frequência de follow-up
- Botão "Lançar campanha"

---

## 2.5 Componentes de Frontend (React + Tailwind + shadcn/ui)

### Stack Recomendada

O frontend atual já usa React + TypeScript + Vite + Tailwind CSS + shadcn/ui. Manter a stack e adicionar:

| Componente | Biblioteca | Propósito |
|-----------|-----------|----------|
| **Stepper/Wizard** | Custom com shadcn | Steps do onboarding |
| **Chat Window** | assistant-ui ou custom | Chat IA embeddado |
| **Audio Recorder** | Custom (MediaRecorder API) | Captura de áudio |
| **File Uploader** | react-dropzone | Upload CSV/XLSX |
| **Policy Editor** | Custom com shadcn sliders | Config de políticas |
| **Simulation Viewer** | Custom chat UI read-only | Visualizar simulação |
| **State Management** | Zustand | Estado do wizard |
| **Data Fetching** | React Query (TanStack) | API calls + cache |
| **Forms** | React Hook Form + Zod | Validação |
| **Animações** | Framer Motion | Transições entre steps |
| **SSE/Streaming** | EventSource API | Updates em tempo real |

### Estrutura de Componentes

```
src/
├── pages/
│   └── Onboarding/
│       ├── index.tsx              (Router dos steps)
│       ├── steps/
│       │   ├── Registration.tsx    (Step 0)
│       │   ├── CompanyInput.tsx    (Step 1)
│       │   ├── DataValidation.tsx  (Step 2)
│       │   ├── AgentType.tsx       (Step 3)
│       │   ├── BusinessInfo.tsx    (Step 4)
│       │   ├── AgentConfig.tsx     (Step 5)
│       │   ├── Simulation.tsx      (Step 6)
│       │   ├── Adjustments.tsx     (Step 7)
│       │   ├── Payment.tsx         (Step 8)
│       │   └── CampaignLaunch.tsx  (Step 9)
│       └── components/
│           ├── WizardStepper.tsx
│           ├── ChatPanel.tsx
│           ├── AudioRecorder.tsx
│           ├── EnrichmentProgress.tsx
│           ├── SimulationViewer.tsx
│           └── PolicySliders.tsx
├── stores/
│   └── onboardingStore.ts    (Zustand - estado do wizard)
├── hooks/
│   ├── useAudioRecorder.ts
│   ├── useEnrichment.ts
│   └── useSimulation.ts
└── api/
    └── onboarding.ts         (React Query hooks)
```

### State Management (Zustand)

```typescript
interface OnboardingState {
  currentStep: number;
  companyData: CompanyData | null;
  enrichmentData: EnrichmentData | null;
  agentType: 'adimplente' | 'inadimplente' | null;
  wizardResponses: Record<string, any>;
  generatedAgent: AgentConfig | null;
  simulation: SimulationResult | null;
  setStep: (step: number) => void;
  setCompanyData: (data: CompanyData) => void;
  // ...
}
```

### Responsividade

- **Mobile-first**: A persona pode acessar do celular
- **Breakpoints**: sm (640px), md (768px), lg (1024px)
- **Chat panel**: Em mobile, ocupa tela cheia como bottom sheet
- **Audio recorder**: Botão FAB fixo no mobile

**Fontes:**
- shadcn/ui (ui.shadcn.com)
- assistant-ui (assistant-ui.com)
- Zustand (zustand-demo.pmnd.rs)
- React Hook Form (react-hook-form.com)
- Framer Motion (framer.com/motion)

---

# PARTE 3: Pipeline de Enriquecimento de Empresa

## 3.1 Arquitetura do Pipeline de Enriquecimento

### Visão Geral

Quando o cliente informa o CNPJ (e opcionalmente o site), o sistema dispara um pipeline de enriquecimento que consulta múltiplas fontes em paralelo, agrega os dados brutos via LLM, e pré-preenche o wizard.

```
                    ┌─────────────┐
                    │  CNPJ Input │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Orquestrador│
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │  Receita   │   │   Site    │   │ Reclame   │
    │  Federal   │   │  Scraping │   │   Aqui    │
    └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │  Google   │   │  LinkedIn │   │  Notícias │
    │   Maps    │   │  Company  │   │  Recentes │
    └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼──────┐
                    │  LLM Aggr.  │
                    │  (GPT-4o)   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Dados       │
                    │ Estruturados│
                    └─────────────┘
```

### Princípios de Design do Pipeline

1. **Paralelismo**: Todas as fontes são consultadas em paralelo (não sequencialmente)
2. **Resiliência**: Se uma fonte falha, as outras continuam (graceful degradation)
3. **Cache**: Dados da Receita Federal cacheados por 30 dias; reviews por 7 dias
4. **Feedback progressivo**: Frontend mostra cada fonte completando em tempo real
5. **Fallback chains**: Se ReceitaWS falha → BrasilAPI → OpenCNPJ (cache)

---

## 3.2 Detalhamento por Fonte de Dados

### Fonte 1: Receita Federal (CNPJ)

**APIs disponíveis:**

| Provedor | Free Tier | Rate Limit (Free) | Dados Especiais |
|----------|-----------|-------------------|-----------------|
| **ReceitaWS** | Sim | 3 req/min | Simples, amplamente usado |
| **CNPJ.ws** | Sim | 3 req/min | Multi-fonte (RF, Sintegra, Suframa) |
| **CNPJa** | Parcial (cache grátis) | Créditos | Mais completo: sócios, Simples, geolocalização, PDF |
| **BrasilAPI** | Sim (grátis) | Comunidade | Open-source, sem auth |
| **OpenCNPJ** | Sim (grátis) | 100 req/min | DB completo para download (550 GB) |

**Dados retornados (todos os provedores):**
- Razão Social, Nome Fantasia
- Situação Cadastral (ativa, suspensa, etc.)
- Data de Abertura
- Natureza Jurídica
- Endereço completo (rua, número, cidade, estado, CEP)
- CNAE principal e secundários
- Telefone e email
- Quadro Societário (sócios — nomes, CPF, qualificação)
- Capital Social
- Porte da empresa

**CNPJa adicionalmente oferece:**
- Status Simples Nacional e MEI
- Inscrições Estaduais (CCC/SINTEGRA)
- Registro SUFRAMA
- Emissão de PDF
- Geolocalização precisa + mapa aéreo / street view

**Recomendação**: Usar **CNPJa** como fonte primária (mais completa) com **BrasilAPI** como fallback gratuito.

### Fonte 2: Site da Empresa (Scraping + LLM)

**Arquitetura:**
1. **Playwright** renderiza o site (suporta JavaScript-heavy)
2. **LLM** processa o HTML/texto e extrai dados estruturados

**Ferramenta recomendada**: `llm-scraper` (github.com/mishushakov/llm-scraper) — converte qualquer webpage em dados estruturados usando LLMs, suporta streaming.

**Prompt de extração:**
```
Analise o site desta empresa e extraia:
1. O que a empresa faz (produtos/serviços)
2. Público-alvo
3. Tom de comunicação (formal/informal/técnico)
4. Diferenciais mencionados
5. Canais de contato disponíveis
6. Indícios de volume de clientes
7. Tipo de cobrança provável (assinatura, parcelamento, projeto)
```

**Output**: JSON estruturado com os campos acima.
**Custo estimado**: ~$0.01-0.05 por site (tokens GPT-4o).

### Fonte 3: Reclame Aqui

**Opções de acesso:**
- **RA API (oficial)**: REST/JSON, paga (contato comercial), permite ler E responder reclamações
- **Web scraping**: Scrapers Python disponíveis no GitHub, limitado a página 50

**Dados coletados:**
- Nota geral da empresa (0-10)
- Taxa de resposta (%)
- Taxa de solução (%)
- Nota do consumidor
- Volume de reclamações
- Principais categorias de reclamação

**Uso no onboarding**: A nota do Reclame Aqui indica o nível de cuidado necessário com CX. Empresas com nota baixa precisam de agentes com tom mais empático e guardrails mais rígidos.

### Fonte 4: Google Maps Reviews

**APIs:**
- **Outscraper**: **500 reviews grátis/mês**, $3/1.000 após. Reviews ilimitados por local.
- **SerpAPI**: $75/mês para 5.000 buscas. Retorna info do reviewer, texto, respostas.

**Dados coletados:**
- Nota média (1-5)
- Volume de reviews
- Sentimento predominante
- Reclamações comuns (extraídas via LLM)

**Recomendação**: **Outscraper** para o MVP (free tier generoso).

### Fonte 5: LinkedIn Company

**Acesso:**
- API oficial limitada (requer OAuth 2.0, aprovação)
- Scraping legal para dados públicos (hiQ Labs vs. LinkedIn, 2022)
- Ferramentas: ScrapIn, Bright Data, Skrapp.io

**Dados coletados:**
- Número de funcionários (estimado)
- Setor/indústria
- Descrição da empresa
- Localização

**Risco**: Scraping direto sem proxies = restrição de conta em minutos.
**Recomendação para MVP**: Usar dados do CNPJ (porte, CNAE) como proxy. LinkedIn enriquecimento na versão 2+.

### Fonte 6: Notícias Recentes

**Método**: Google News scraping ou Google Search API
**Dados coletados**: Manchetes recentes sobre a empresa — crescimento, demissões, crises, prêmios
**Uso**: Contextualizar a situação atual da empresa para calibrar o agente

### Fonte 7: Análise de Concorrentes

**Método**: Buscar empresas com mesmo CNAE na mesma região via CNPJ APIs
**Dados coletados**: Quantos concorrentes existem, porte, notas no Reclame Aqui/Google
**Uso**: Benchmarks do setor para calibrar expectativas de recuperação

---

## 3.3 Aggregation Layer com LLM

### Conceito

Todos os dados brutos das 7 fontes são enviados para o GPT-4o com um prompt de agregação que gera um perfil estruturado da empresa.

### Prompt de Agregação

```
Você é um analista especializado em crédito e cobrança no Brasil. Com base nos dados
brutos coletados de múltiplas fontes sobre esta empresa, gere um perfil estruturado.

## Dados Brutos
{dados_receita_federal}
{dados_site}
{dados_reclame_aqui}
{dados_google_maps}
{dados_noticias}
{dados_concorrentes}

## Output Esperado (JSON)
{
  "company_profile": {
    "name": "Nome fantasia",
    "legal_name": "Razão social",
    "segment": "Segmento (construção, varejo, SaaS, etc.)",
    "size": "Porte (micro, pequena, média, grande)",
    "estimated_revenue": "Faturamento estimado",
    "estimated_employees": "Funcionários estimados",
    "location": "Cidade/Estado",
    "years_active": "Anos de operação"
  },
  "collection_context": {
    "likely_debt_types": ["Tipo 1", "Tipo 2"],
    "likely_payment_methods": ["Boleto", "Cartão", "PIX"],
    "estimated_default_rate": "Taxa estimada de inadimplência do setor",
    "recommended_tone": "Formal/Amigável/Empático/Assertivo",
    "recommended_channels": ["WhatsApp", "Email"],
    "sector_benchmarks": {
      "avg_recovery_rate": "X%",
      "avg_time_to_recover": "X dias"
    }
  },
  "reputation": {
    "reclame_aqui_score": 7.8,
    "google_rating": 4.2,
    "cx_sensitivity": "alta/média/baixa",
    "main_complaints": ["Tipo 1", "Tipo 2"]
  },
  "risks": ["Risco 1", "Risco 2"],
  "recommendations": ["Recomendação 1", "Recomendação 2"]
}
```

### Uso dos Dados Agregados

1. **Pré-preenchimento do wizard**: Campos como segmento, porte, tom recomendado já vêm preenchidos
2. **Perguntas contextuais**: A IA no chat sabe o segmento e faz perguntas relevantes
3. **Calibração do agente**: O Agent Generator usa esses dados como contexto para gerar o prompt
4. **Calibração do simulador**: O Debtor Simulator usa os benchmarks do setor para simular devedores realistas

**Custo estimado por enriquecimento completo**: ~$0.10-0.30 (APIs + tokens LLM)

**Fontes:**
- CNPJa API (cnpja.com/en/api)
- CNPJ.ws (cnpj.ws)
- ReceitaWS (receitaws.com.br)
- BrasilAPI (github.com/BrasilAPI)
- OpenCNPJ (opencnpj.org)
- Outscraper (outscraper.com)
- SerpAPI (serpapi.com)
- Reclame Aqui API (produtos.reclameaqui.com.br)
- llm-scraper (github.com/mishushakov/llm-scraper)
- Firecrawl — Complete Guide to Data Enrichment
- n8n — CNPJ Enrichment Workflow

---

# PARTE 4: Arquitetura Multi-Agente

## 4.1 Fundamentos de Sistemas Multi-Agente

### Evolução da Arquitetura de IA

A arquitetura de sistemas de IA evoluiu significativamente:

```
2023: Chains (LangChain)     → Sequência fixa de chamadas
2024: Agents (ReAct, Tool)   → Agente único com ferramentas
2025: Multi-Agent Systems    → Múltiplos agentes coordenados
2025+: Stateful Graphs       → Grafos de estado com checkpoint
```

### Padrões Arquiteturais

**1. Hierarchical (Supervisor)**
- Agentes organizados em árvore com supervisor no topo
- Supervisor delega tarefas e coordena resultados
- **Quando usar**: Quando há clara hierarquia de responsabilidades
- **CollectAI atual**: Já usa este padrão (Supervisor → Negociação → Agreement → Payment Link)

**2. Mixture of Experts (Paralelo)**
- Múltiplos agentes processam a mesma tarefa em paralelo
- Agregador sintetiza os melhores resultados
- **Quando usar**: Quando diferentes perspectivas melhoram o resultado
- **CollectAI**: Poderia usar para gerar múltiplas estratégias de negociação

**3. Sequential Pipeline**
- Agentes em série, cada um processa e passa adiante
- Modelo "assembly line"
- **Quando usar**: Quando o output de um é input do próximo
- **CollectAI onboarding**: Enrichment → Interview → Generation → Simulation

**4. Event-Driven**
- Agentes reagem a eventos (mensagens, webhooks)
- Desacoplados via message broker
- **Quando usar**: Sistemas distribuídos com alta concorrência
- **CollectAI runtime**: Mensagens do WhatsApp → RabbitMQ → Agent response

### Best Practices para Orquestração

1. **Tratar cada handoff como API versionada** — JSON Schema validation com `schemaVersion` e `trace_id`, auto-repair, escalação humana após N falhas
2. **Separar responsabilidades por role** — agentes especializados (Retrieval, Research, Drafting, Reviewing), permissões de tools vinculadas a roles
3. **Agentes como funções** — output com instruções de controle ("route to X_agent"), orquestrador decide routing
4. **Instrumentar com OpenTelemetry** — armazenar runs no Langfuse, enforce least privilege e content safety, rate-limit tools
5. **Separar memória** — curto prazo (conversa) vs. longo prazo (histórico), preservar proveniência

---

## 4.2 OpenAI Agents SDK vs Agency Swarm vs Alternativas

### OpenAI Agents SDK (Produção-Ready)

O novo SDK da OpenAI (evolução do Swarm experimental) é a opção mais madura para produção:

**Features principais:**
- **Agents**: LLMs com instructions, tools e handoffs configuráveis
- **Handoffs**: Transferência de controle entre agentes com `tool_description_override` e callback `on_handoff`
- **Guardrails**: Input e output validados via agentes dedicados com `tripwire_triggered`
- **Tracing**: Built-in tracing no OpenAI Dashboard + custom processors
- **MCP (Model Context Protocol)**: Integração com servidores MCP
- **Sessions**: State management entre chamadas

**Padrão de código:**
```python
from agents import Agent, Runner, handoff, InputGuardrail

# Agente de cobrança
collection_agent = Agent(
    name="Collection Agent",
    instructions="Você é um agente de cobrança...",
    handoffs=[escalation_agent, payment_agent]
)

# Guardrail de compliance
@input_guardrail
async def compliance_check(ctx, agent, input):
    result = await Runner.run(compliance_agent, input)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_non_compliant
    )

# Executar
result = await Runner.run(collection_agent, input="Não posso pagar")
```

### Agency Swarm (Framework Atual da CollectAI)

**Prós:**
- Já implementado e funcionando
- Custom tools folder por agente
- Instructions em markdown separado
- Suporte a OpenAI Assistant API com threads persistentes

**Contras:**
- Falta de state/memory management nativo entre interações
- Experimental, não robusto para produção em escala
- Handoff manual pode causar deadlocks
- Documentação e suporte limitados

### Comparação de Frameworks

| Aspecto | OpenAI Agents SDK | Agency Swarm | CrewAI | LangGraph |
|---------|-------------------|--------------|--------|-----------|
| **Maturidade** | Alta (OpenAI oficial) | Média | Alta | Alta |
| **Handoffs** | Nativo, type-safe | Manual | Role-based | Graph edges |
| **Guardrails** | Nativo (input/output) | In-prompt | Não nativo | Custom nodes |
| **State** | Sessions | Threads | Role memory | State graphs + checkpoints |
| **Tracing** | Built-in | Nenhum | Logs | LangSmith |
| **Lock-in** | OpenAI | OpenAI | Model-agnostic | Model-agnostic |
| **Curva** | Baixa | Baixa | Média | Alta |
| **Produção** | Sim | Parcial | Sim | Sim |

### Recomendação

**Curto prazo (MVP)**: Manter Agency Swarm para os agentes de cobrança existentes. Implementar o sistema de onboarding com **OpenAI Agents SDK** (novo código, sem migração).

**Médio prazo**: Avaliar migração completa para OpenAI Agents SDK ou LangGraph, dependendo de:
- Necessidade de model-agnostic (LangGraph)
- Preferência por ecossistema OpenAI (Agents SDK)
- Complexidade dos workflows (LangGraph para grafos complexos)

---

## 4.3 Arquitetura dos Agentes de Cobrança (Atual + Expandida)

### Sistema Atual

```
┌─────────────────────────────────────────┐
│              SUPERVISOR AGENT            │
│     QA, Compliance, Escalação           │
│                                         │
│  ┌───────────┐  ┌───────────┐          │
│  │Negotiation│──│ Agreement │          │
│  │  Agent    │  │ Analysis  │          │
│  └───────────┘  └─────┬─────┘          │
│                       │                 │
│                 ┌─────▼─────┐          │
│                 │ Payment   │          │
│                 │ Link Gen  │          │
│                 └───────────┘          │
└─────────────────────────────────────────┘
```

### Expansão Recomendada

**Novos agentes para o sistema de cobrança:**

1. **Identification Agent** (novo) — Detecta atrasos automaticamente a partir de dados do ERP/lista
2. **Triage Agent** (novo) — Classifica devedores por prioridade (valor, aging, perfil) e define estratégia
3. **Reminder Agent** (novo, para adimplentes) — Envia lembretes de vencimento com tom suave
4. **Customer Service Agent** (futuro) — Tira dúvidas, direciona para o agente correto
5. **Boleto Generation Agent** (futuro, integração ASA) — Gera boletos automaticamente

---

## 4.4 Arquitetura dos Agentes do Onboarding

### Novos Agentes Necessários

O sistema de onboarding requer agentes diferentes dos de cobrança:

```
┌─────────────────────────────────────────────────┐
│              ONBOARDING ORCHESTRATOR              │
│                                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │ Enrichment │  │ Interview  │  │   Agent    │ │
│  │   Agent    │  │   Agent    │  │ Generator  │ │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘ │
│        │               │               │         │
│        │          ┌────▼─────┐          │         │
│        └─────────►│Aggregator│◄─────────┘         │
│                   └────┬─────┘                    │
│                        │                          │
│               ┌────────▼─────────┐                │
│               │   Simulation     │                │
│               │   Orchestrator   │                │
│               └───┬──────────┬───┘                │
│                   │          │                     │
│           ┌───────▼───┐ ┌───▼──────┐             │
│           │ Collection│ │  Debtor  │             │
│           │   Agent   │ │Simulator │             │
│           │ (gerado)  │ │  Agent   │             │
│           └───────────┘ └──────────┘             │
└───────────────────────────────────────────────────┘
```

**1. Enrichment Agent**
- **Responsabilidade**: Orquestrar o pipeline de enriquecimento (Parte 3)
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
- **Método**: Context engineering com structured output (Parte 5)

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

É fundamental separar os agentes de onboarding dos agentes de cobrança (runtime):
- **Onboarding agents**: Rodam durante o setup, são efêmeros
- **Collection agents**: Rodam 24/7, são persistentes
- **Não compartilham threads**: Cada contexto tem sua própria memória

**Fontes:**
- OpenAI Agents SDK (openai.github.io/openai-agents-python)
- Agency Swarm GitHub (github.com/VRSEN/agency-swarm)
- DataCamp — CrewAI vs LangGraph vs AutoGen
- Latenode — LangGraph vs AutoGen vs CrewAI 2025
- Galileo — Framework Comparison
- Skywork AI — Best Practices for Handoffs
- Microsoft Azure — AI Agent Design Patterns
- Confluent — Event-Driven Multi-Agent Systems
- Swarms — Multi-Agent Architectures
- SparkCo — Deep Dive OpenAI Swarm Patterns

---

# PARTE 5: Sistema de Auto-Geração de Agentes

## 5.1 Context Engineering para Geração de Agentes

### De Prompt Engineering para Context Engineering

Em 2025, o campo evoluiu de "prompt engineering" (craftar instruções isoladas) para "context engineering" (curar contextos dinâmicos e iterativos). Context engineering cobre **todos os tokens** que entram na context window, não só o prompt.

### As 6 Camadas de Contexto (Framework Anthropic, Set/2025)

1. **System Rules** — O system prompt que define role, limites e comportamento. Muda raramente. Define tom e restrições fundamentais.

2. **Memory** — Armazenamento persistente de longo prazo. Preferências duráveis, fatos estáveis, resumos de projetos. Na CollectAI: dados da empresa, políticas, histórico de campanhas anteriores.

3. **Retrieved Documents** — Conhecimento externo atualizado via RAG. Documentos, databases, APIs. Na CollectAI: dados do ERP, lista de devedores, histórico de pagamentos.

4. **Tool Schemas** — Ações disponíveis: function calls, API endpoints. Na CollectAI: escalar para humano, gerar link de pagamento, consultar saldo.

5. **Recent Conversation** — Memória de curto prazo. Diálogo anterior, decisões tomadas. Na CollectAI: histórico da conversa com o devedor.

6. **Current Task** — A requisição imediata. Input de curta duração. Na CollectAI: a mensagem do devedor que acabou de chegar.

### Aplicação ao Onboarding

Os dados coletados no onboarding alimentam as 3 primeiras camadas:

| Camada | Fonte no Onboarding | Exemplo |
|--------|---------------------|---------|
| **System Rules** | Agent Generator | "Você é o agente de cobrança da XYZ Construções. Seu tom é empático e profissional..." |
| **Memory** | CompanyProfile + BusinessContext | Segmento, tipo de dívida, políticas, benchmarks |
| **Tool Schemas** | Seleção de tools no onboarding | Escalar, gerar link, consultar saldo |

---

## 5.2 Pipeline de Auto-Geração

### Input

Todos os dados coletados no onboarding:

```json
{
  "company_profile": { /* dados do Enrichment Agent */ },
  "business_context": { /* respostas do Interview Agent */ },
  "agent_type": "inadimplente",
  "user_preferences": {
    "tone": "empático",
    "max_discount_cash": 0.25,
    "max_discount_installments": 0.20,
    "max_installments": 6,
    "min_installment_value": 200,
    "escalation_rules": ["valor > 50000", "cliente insatisfeito"],
    "forbidden_behaviors": ["ameaçar", "expor dívida a terceiros"],
    "working_hours": "08:00-20:00 seg-sex"
  }
}
```

### Processing

O Agent Generator (GPT-4o com structured output) recebe todo o contexto e gera a configuração completa:

**Mega-prompt de geração:**
```
Você é um especialista em criação de agentes de IA para cobrança de dívidas.
Com base nos dados da empresa e nas preferências do usuário, gere a configuração
completa de um agente de cobrança.

## Dados da Empresa
{company_profile}

## Contexto do Negócio
{business_context}

## Tipo de Agente
{agent_type}

## Preferências do Usuário
{user_preferences}

## Regras de Geração
1. O system prompt deve ser detalhado e específico para o segmento da empresa
2. O tom deve ser consistente com a preferência do usuário
3. As políticas devem respeitar os limites definidos pelo usuário
4. Os guardrails devem incluir compliance com CDC e LGPD
5. As estratégias de negociação devem ser calibradas para o setor
6. Incluir exemplos de mensagens para os cenários mais comuns

Retorne no formato JSON especificado abaixo.
```

### Output (JSON Schema)

```json
{
  "agent_config": {
    "name": "Agente XYZ Construções",
    "version": "1.0",
    "type": "inadimplente",

    "system_prompt": "Você é o agente de cobrança da XYZ Construções...[prompt completo]",

    "tools": [
      {
        "name": "escalate_to_human",
        "description": "Escala a conversa para atendimento humano",
        "trigger_conditions": ["valor > R$50.000", "3+ tentativas falhas"]
      },
      {
        "name": "generate_payment_link",
        "description": "Gera link de pagamento seguro",
        "parameters": { "amount": "float", "installments": "int" }
      },
      {
        "name": "check_payment_status",
        "description": "Verifica status de pagamento",
        "parameters": { "payment_id": "string" }
      }
    ],

    "guardrails": {
      "input_rails": [
        "Rejeitar mensagens com conteúdo ofensivo ou ameaçador",
        "Filtrar tentativas de jailbreak ou desvio de tema"
      ],
      "output_rails": [
        "Nunca revelar informações da dívida a terceiros",
        "Nunca ameaçar ou constranger o devedor",
        "Respeitar horários: 08:00-20:00 seg-sex",
        "Não oferecer descontos acima dos limites configurados"
      ],
      "policy_rails": [
        "Desconto máximo à vista: 25%",
        "Desconto máximo parcelado: 20%",
        "Máximo 6 parcelas",
        "Parcela mínima: R$ 200"
      ],
      "tone_rails": [
        "Manter tom empático e profissional",
        "Não usar linguagem técnica ou jurídica",
        "Sempre oferecer alternativas antes de pressionar"
      ]
    },

    "policies": {
      "max_discount_cash_percent": 25,
      "max_discount_installments_percent": 20,
      "max_installments": 6,
      "min_installment_value": 200,
      "working_hours": { "start": "08:00", "end": "20:00" },
      "working_days": ["seg", "ter", "qua", "qui", "sex"],
      "escalation_threshold_value": 50000,
      "max_attempts_before_escalation": 3,
      "follow_up_interval_days": 3
    },

    "negotiation_strategies": [
      {
        "scenario": "Devedor diz que não pode pagar",
        "strategy": "Oferecer parcelamento, começando pelo número máximo de parcelas"
      },
      {
        "scenario": "Devedor contesta a dívida",
        "strategy": "Validar dados, apresentar detalhes, oferecer esclarecimento"
      },
      {
        "scenario": "Devedor pede desconto maior que o permitido",
        "strategy": "Explicar que o desconto atual é o máximo, oferecer parcelamento como alternativa"
      }
    ],

    "message_templates": {
      "initial_contact": "Olá {nome}! Aqui é da {empresa}...",
      "follow_up_1": "Oi {nome}, passando para lembrar...",
      "payment_confirmation": "Ótima notícia, {nome}! Recebemos..."
    }
  }
}
```

### Validação do Output

1. **Schema validation**: Pydantic valida estrutura JSON
2. **Sanity checks**: Descontos dentro dos limites, horários válidos, tools existentes
3. **Human review flag**: Se algo parecer inconsistente, flaggar para revisão
4. **Versionamento**: Cada geração cria uma versão (v1, v2...), cliente pode reverter

### Templates Base

Para acelerar a geração, manter templates base por tipo de agente:
- **Template Adimplente**: Foco em lembrete preventivo, tom suave, sem negociação de desconto
- **Template Inadimplente**: Foco em negociação, ofertas de desconto/parcelamento, escalação

O Agent Generator usa o template como ponto de partida e personaliza com os dados do onboarding.

---

## 5.3 Guardrails e Compliance

### Problema Atual

Hoje os guardrails da CollectAI estão **in-prompt** — incluídos como instruções no system prompt do agente. Isso é:
- **Frágil**: LLMs podem "esquecer" ou contornar instruções longas
- **Não escalável**: Cada agente precisa de guardrails repetidos
- **Não auditável**: Difícil rastrear qual regra foi violada

### Solução: Guardrails como Camada Separada

Migrar para uma arquitetura onde guardrails são **middleware** entre o usuário e o agente:

```
[Mensagem do Devedor]
        │
  ┌─────▼─────┐
  │  INPUT     │  ← Filtra conteúdo, detecta jailbreak, máscara PII
  │  RAILS     │
  └─────┬─────┘
        │
  ┌─────▼─────┐
  │  AGENTE    │  ← Processa a mensagem normalmente
  │  (LLM)     │
  └─────┬─────┘
        │
  ┌─────▼─────┐
  │  OUTPUT    │  ← Valida compliance, verifica limites, checa tom
  │  RAILS     │
  └─────┬─────┘
        │
  [Resposta ao Devedor]
```

### Tipos de Guardrails

**1. Input Rails (antes do agente processar)**
- Validação de contexto: mensagem é relevante para cobrança?
- Detecção de jailbreak: tentativa de desviar o agente?
- Máscara de PII: proteger dados sensíveis nos logs
- Filtro de conteúdo ofensivo

**2. Output Rails (depois do agente gerar resposta)**
- Compliance CDC: não ameaçar, não expor dívida
- Compliance LGPD: não revelar dados pessoais indevidamente
- Limites de política: desconto oferecido está dentro dos limites?
- Verificação de tom: mensagem mantém o tom configurado?
- Verificação de horário: mensagem está sendo enviada em horário permitido?

**3. Policy Rails (regras de negócio)**
- Limites de desconto (por faixa de valor, por aging)
- Limites de parcelamento
- Regras de escalação
- Frequência de contato (não bombardear o devedor)
- Regras de renegociação

**4. Tone Rails (consistência de marca)**
- Manter tom configurado pelo cliente
- Não usar linguagem técnica/jurídica se não configurado
- Manter personalidade consistente ao longo da conversa

### Frameworks Disponíveis

**NVIDIA NeMo Guardrails:**
- Open-source, Python
- 5 tipos de rails: input, output, dialog, retrieval, execution
- Linguagem própria (Colang) para definir regras
- Integração com LangGraph para workflows multi-agente
- Cache LFU para performance
- GPU acceleration

**Guardrails AI:**
- Framework Python com RAIL spec
- Validators combinados em chains
- Guardrails Index com 24 guardrails benchmarkados
- Integra com NeMo Guardrails

**OpenAI Agents SDK (Built-in):**
- `@input_guardrail` e `@output_guardrail` decorators
- Guardrails como agentes dedicados com `tripwire_triggered`
- Integrado ao tracing

### Recomendação

**Para o MVP**: Usar guardrails built-in do OpenAI Agents SDK (mais simples, já integrado).
**Para produção**: Migrar para NeMo Guardrails + Agents SDK (mais robusto, configurável por YAML, auditável).
**Manter guardrails in-prompt como backup**: Mesmo com middleware externo, manter instruções de compliance no system prompt como camada adicional de segurança.

**Fontes:**
- Anthropic — Effective Context Engineering for AI Agents
- PromptBuilder — Context Engineering Guide 2025
- Prompting Guide — Context Engineering
- OpenAI — Structured Outputs
- NVIDIA NeMo Guardrails (developer.nvidia.com)
- NeMo Guardrails Docs (docs.nvidia.com)
- Guardrails AI (guardrailsai.com)
- Invariant Labs — Guardrails as Middleware
- Datadog — LLM Guardrails Best Practices

---

# PARTE 6: Simulação e AHA Moment

## 6.1 Importância do AHA Moment em Product-Led Growth

### Definição

O AHA Moment é o instante em que o usuário **percebe pela primeira vez o valor do produto** e entende por que precisa dele. Diferente da ativação (evento comportamental), o AHA Moment é uma **realização cognitiva e emocional**.

### Para a CollectAI

O AHA Moment da CollectAI é: **ver SEU agente, configurado com SUAS regras, negociando com um devedor do SEU segmento, usando o tom que VOCÊ escolheu**.

Não é:
- Ver um dashboard vazio
- Ler uma documentação
- Preencher mais formulários

É:
- Uma conversa realista, personalizada, acontecendo diante dos seus olhos
- A sensação de "uau, ele realmente negocia como eu faria — mas mais rápido e sem cansar"

### Benchmarks

- Usuários que experienciam valor core em **5-15 minutos** são **3x mais propensos a reter**
- Produtos com AHA em **menos de 5 minutos** mostram **40% mais retenção em 30 dias**
- **Cada minuto extra** reduz conversão em **3%**
- Taxa de ativação top performers: **70-80%**

### Exemplos de AHA Moments Inspiradores

| Empresa | AHA Moment | Estratégia |
|---------|-----------|-----------|
| **Slack** | Equipe envia 2.000 mensagens | Convite de equipe antes de usar o produto |
| **Dropbox** | Primeiro arquivo sincroniza entre dispositivos | Simplicidade + loop viral (espaço grátis) |
| **Calendly** | Usuário agenda reunião consigo mesmo | Sign in com Google (1 step) + auto-teste |
| **Zoom** | Primeira videochamada conecta instantaneamente | Zero fricção (convidado não precisa de conta) |
| **CollectAI** | Ver agente negociando com devedor simulado | Simulação personalizada após onboarding |

---

## 6.2 Arquitetura da Simulação Agent-to-Agent

### Conceito

Dois agentes conversam entre si:
1. **Collection Agent** (recém-gerado pelo onboarding) — age como se estivesse cobrando
2. **Debtor Simulator Agent** — simula um devedor realista do segmento do cliente

A conversa é **pré-gerada no backend** antes do cliente ver. O cliente assiste a conversa read-only, como se estivesse vendo uma gravação.

### Debtor Simulator Agent

**Prompt base:**
```
Você é um devedor simulado para fins de demonstração de um agente de cobrança.

## Perfil do Devedor
- Segmento: {segment} (ex: cliente de construtora)
- Tipo de dívida: {debt_type} (ex: parcela de imóvel)
- Valor: {typical_debt_value} (ex: R$ 15.000)
- Dias em atraso: {typical_aging} (ex: 45 dias)
- Personalidade: {personality} (cooperativo / hesitante / resistente)

## Comportamento
- Responda naturalmente como um devedor real faria
- Se cooperativo: mostre boa vontade mas peça melhores condições
- Se hesitante: mostre dúvida, peça tempo, questione valores
- Se resistente: conteste a dívida, reclame, peça desconto alto
- NUNCA seja impossível de negociar — sempre deixe abertura
- Use linguagem coloquial brasileira natural
```

### Pesquisa Acadêmica Relevante

**"Debt Collection Negotiations with LLMs" (arXiv:2502.18228, Fev/2025)**
- Framework MADeN (Multi-Agent Debt Negotiation) com 13 métricas
- Agentes usam tuplas (Thoughts, Dialogue, Action)
- Descoberta: LLMs tendem a **conceder demais** comparados a humanos
- Solução: Post-training com DPO e rejection sampling
- Métrica proposta: **CCI** (Comprehensive Collection Index) = média harmônica de Collection Recovery Index e Debtor Health Index

**"EmoDebt" (arXiv:2503.21080, Mar/2025)**
- Framework de inteligência emocional para negociação agent-to-agent
- Matriz 7x7 de transição emocional (7 estados emocionais)
- Otimizador Bayesiano para aprender políticas ótimas de transição emocional
- Supera baselines não-adaptativas e emotion-agnostic

### Geração de Múltiplos Cenários

Para cada simulação, gerar **2-3 cenários** com perfis diferentes:

| Cenário | Personalidade | Típico |
|---------|--------------|--------|
| **1** | Cooperativo | Devedor que quer pagar mas precisa de condições |
| **2** | Hesitante | Devedor que precisa ser convencido |
| **3** | Resistente | Devedor que contesta e pede muito desconto |

### Métricas da Simulação

Exibir ao cliente após a simulação:
- **Taxa de acordo simulada**: ~65% (baseada nos 3 cenários)
- **Desconto médio oferecido**: 15%
- **Tempo médio de conversa**: 8 minutos
- **Escalações**: 0/3 cenários precisaram de humano

### Formato de Apresentação

- **Chat-style UI**: Bolhas de mensagem, read-only
- **Indicadores**: Emoji do agente (🤖) vs. devedor (👤)
- **Anotações**: Tooltips opcionais explicando a estratégia do agente
- **Transição animada**: Mensagens aparecem com delay (simula tempo real)
- **Navegação**: Botões para alternar entre cenários

---

## 6.3 Avaliação e Iteração

### Fluxo Pós-Simulação

```
Simulação → Cliente avalia → Ajustes → Re-simulação → Aprovação
```

1. **Cliente vê a simulação** (Step 6)
2. **Cliente solicita ajustes** (Step 7): "O tom está muito formal", "O desconto está baixo demais"
3. **Agent Generator** atualiza a configuração
4. **Nova simulação** é gerada (opcional — limite de 2-3 iterações grátis)
5. **Cliente aprova** e segue para pagamento

### Limites de Iteração

Para evitar uso excessivo de tokens:
- **Grátis**: 2-3 simulações completas (6-9 conversas no total)
- **Cada simulação extra**: consome créditos
- **Ajustes que não precisam de re-simulação**: mudanças de tom, mensagem inicial, horários

### Feedback Loop

Os dados das simulações alimentam melhoria do sistema:
- Quais tipos de ajustes são mais comuns? → Melhorar templates base
- Quais cenários o agente performa mal? → Melhorar prompts de geração
- Quais segmentos precisam de mais contexto? → Melhorar enriquecimento

**Fontes:**
- Userpilot — AHA Moment Guide / Examples
- Amplitude — AHA Moment
- Appcues — AHA Guide
- ProductLed Alliance — 9 AHA Moments
- Sierra AI — Simulations: Secret Behind Great Agents
- Sierra AI — tau-Bench Benchmarking
- Cognigy — Simulator for AI Agent Evaluation
- Maxim AI — Agent Simulation Evaluation
- Lyzr — Agent Simulation Engine
- arXiv 2502.18228 — Debt Collection Negotiations with LLMs
- arXiv 2503.21080 — EmoDebt

---

# PARTE 7: Arquitetura Técnica Completa

## 7.1 Visão Geral da Arquitetura

### Stack Atual
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: Python + FastAPI + Agency Swarm + OpenAI GPT-4
- **Mensageria**: RabbitMQ
- **Cache**: Redis

### Novos Componentes para o Onboarding

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  React + Tailwind + shadcn/ui                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│  │ Wizard  │ │  Chat   │ │ Audio   │ │ Simul.  │         │
│  │ Steps   │ │ Panel   │ │Recorder │ │ Viewer  │         │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘         │
│       └────────────┴──────────┴────────────┘               │
│                        │ REST API / SSE                     │
└────────────────────────┼────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────┐
│                    API GATEWAY                               │
│               FastAPI + Uvicorn                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ /onboarding/*  endpoints                              │   │
│  │ /agents/*      endpoints                              │   │
│  │ /campaigns/*   endpoints                              │   │
│  └──────────────────────┬───────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                    SERVICES LAYER                             │
│                                                              │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│  │Enrichment │  │Onboarding │  │  Agent    │               │
│  │ Service   │  │ Service   │  │Generation │               │
│  └─────┬─────┘  └─────┬─────┘  │ Service  │               │
│        │               │        └─────┬─────┘               │
│  ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐             │
│  │Simulation │  │  Whisper  │  │ Guardrail │             │
│  │ Service   │  │ Service   │  │ Service   │             │
│  └───────────┘  └───────────┘  └───────────┘             │
└──────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                   INFRASTRUCTURE                             │
│                                                              │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐           │
│  │RabbitMQ│  │ Redis  │  │Postgres│  │  S3/   │           │
│  │ Queue  │  │ Cache  │  │   DB   │  │ MinIO  │           │
│  └────────┘  └────────┘  └────────┘  └────────┘           │
│                                                              │
│  ┌────────────────────────────────────────────┐             │
│  │           External APIs                     │             │
│  │  OpenAI │ CNPJ APIs │ WhatsApp │ Stripe    │             │
│  └────────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────┘
```

---

## 7.2 Backend Architecture (Python + FastAPI)

### Endpoints do Onboarding

```python
# === REGISTRO E SESSÃO ===
POST   /api/v1/onboarding/register        # Cria conta + sessão de onboarding
GET    /api/v1/onboarding/session/{id}     # Status da sessão

# === ENRIQUECIMENTO ===
POST   /api/v1/onboarding/enrich           # Dispara enriquecimento (CNPJ + site)
GET    /api/v1/onboarding/enrich/{id}/status  # Polling ou SSE do progresso
GET    /api/v1/onboarding/enrich/{id}/result  # Resultado do enriquecimento

# === WIZARD ===
POST   /api/v1/onboarding/wizard/step      # Salva resposta de um step
POST   /api/v1/onboarding/wizard/followup  # Gera follow-up da IA
GET    /api/v1/onboarding/wizard/progress   # Progresso do wizard

# === ÁUDIO ===
POST   /api/v1/onboarding/audio/transcribe  # Upload áudio → Whisper → texto

# === GERAÇÃO DE AGENTE ===
POST   /api/v1/onboarding/agent/generate    # Gera config do agente
GET    /api/v1/onboarding/agent/{id}        # Retorna config gerada
PUT    /api/v1/onboarding/agent/{id}/adjust  # Aplica ajustes

# === SIMULAÇÃO ===
POST   /api/v1/onboarding/simulation/generate  # Gera simulação agent-to-agent
GET    /api/v1/onboarding/simulation/{id}       # Retorna conversa simulada

# === LANÇAMENTO ===
POST   /api/v1/onboarding/campaign/launch     # Lança primeira campanha
POST   /api/v1/onboarding/campaign/upload     # Upload lista devedores
POST   /api/v1/onboarding/campaign/validate   # Valida lista
```

### Processamento Assíncrono

Operações pesadas rodam em background:

- **Enriquecimento**: ~10-30s → Celery worker ou RabbitMQ consumer
- **Geração de agente**: ~5-15s → Celery worker
- **Simulação**: ~30-60s (múltiplos cenários) → Celery worker
- **Transcrição de áudio**: ~2-5s por gravação → direto na API (rápido o suficiente)

**Comunicação com frontend**: Server-Sent Events (SSE) para updates em tempo real, com fallback para polling.

### Rate Limiting

- **Enriquecimento**: 1 por sessão (re-enrich limitado a 3x)
- **Follow-ups IA**: Max 20 por sessão
- **Simulações**: Max 3 por sessão (grátis)
- **Transcrições**: Max 50 por sessão

---

## 7.3 Frontend Architecture (React + Tailwind)

### Estrutura de Rotas

```
/onboarding                    → Redirect para step atual
/onboarding/register           → Step 0
/onboarding/company            → Steps 1-2
/onboarding/agent-type         → Step 3
/onboarding/interview          → Steps 4-5
/onboarding/simulation         → Step 6
/onboarding/adjustments        → Step 7
/onboarding/payment            → Step 8
/onboarding/launch             → Step 9
```

### Persistência de Estado

- **Zustand store** para estado do wizard em memória
- **localStorage** como backup (caso browser feche)
- **Backend** como source of truth (salva a cada step completado)
- **Reconexão**: Se o usuário sai e volta, retoma do último step salvo no backend

### API Integration

```typescript
// React Query hooks para cada endpoint
const useEnrichment = (cnpj: string) =>
  useQuery(['enrichment', cnpj], () => api.enrich(cnpj));

const useSimulation = (agentId: string) =>
  useQuery(['simulation', agentId], () => api.getSimulation(agentId));

// SSE para updates em tempo real
const useEnrichmentSSE = (sessionId: string) => {
  useEffect(() => {
    const source = new EventSource(`/api/v1/onboarding/enrich/${sessionId}/status`);
    source.onmessage = (e) => updateProgress(JSON.parse(e.data));
    return () => source.close();
  }, [sessionId]);
};
```

---

## 7.4 Database Schema

### Tabelas Principais

```sql
-- Empresas cadastradas
CREATE TABLE companies (
    id UUID PRIMARY KEY,
    cnpj VARCHAR(18) UNIQUE NOT NULL,
    legal_name VARCHAR(255),
    trade_name VARCHAR(255),
    segment VARCHAR(100),
    size VARCHAR(50),
    enrichment_data JSONB,  -- Dados completos do enriquecimento
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessões de onboarding
CREATE TABLE onboarding_sessions (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    user_id UUID REFERENCES users(id),
    current_step INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'in_progress', -- in_progress, completed, abandoned
    wizard_responses JSONB DEFAULT '{}',       -- Respostas do wizard
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Agentes gerados
CREATE TABLE generated_agents (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    session_id UUID REFERENCES onboarding_sessions(id),
    agent_type VARCHAR(20) NOT NULL, -- adimplente, inadimplente
    config JSONB NOT NULL,            -- Config completa (prompt, tools, etc.)
    version INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'draft', -- draft, active, paused, archived
    created_at TIMESTAMP DEFAULT NOW()
);

-- Simulações
CREATE TABLE simulations (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES generated_agents(id),
    scenarios JSONB NOT NULL,  -- Array de cenários com conversas
    metrics JSONB,             -- Métricas agregadas
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usuários
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    company_id UUID REFERENCES companies(id),
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Assinaturas e créditos
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    plan VARCHAR(50) NOT NULL,           -- starter, growth, enterprise
    stripe_subscription_id VARCHAR(255),
    credits_remaining INTEGER DEFAULT 0,
    credits_used INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    started_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Campanhas
CREATE TABLE campaigns (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    agent_id UUID REFERENCES generated_agents(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    type VARCHAR(20),       -- recurring, delinquent, preventive
    total_contacts INTEGER DEFAULT 0,
    agreements INTEGER DEFAULT 0,
    config JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Migrações

Usar **Alembic** para migrações de schema (já padrão com FastAPI + SQLAlchemy).

---

## 7.5 Integração com WhatsApp Business API

### Consideração Crítica de Compliance

**Meta proíbe explicitamente cobrança de dívidas** na política do WhatsApp Business:

> "You may not use the WhatsApp Business Services for debt collection."

**Realidade brasileira:**
- IDEC (2013) reconheceu a legalidade de cobrança via WhatsApp sob lei brasileira
- Lei brasileira não proíbe cobrança via aplicativos de mensagem
- Muitas empresas brasileiras usam WhatsApp para cobrança na prática
- **Risco principal**: Bloqueio da conta pela Meta (não responsabilidade legal)

**Estratégia recomendada:**
- Enquadrar mensagens como **"lembretes de pagamento"** e **"atendimento ao cliente"** (categorias utility/service)
- Usar linguagem de **facilitação de pagamento e negociação**, não demanda de dívida
- Templates aprovados devem focar em: confirmação de pagamento, opções de parcelamento, link de pagamento
- Consultar advogado especializado para este uso específico

### BSPs Recomendados

| BSP | Modelo | Pricing | Melhor Para |
|-----|--------|---------|-------------|
| **360dialog** | API Gateway | $50/mês fixo por número | Transparência de custo, alto volume |
| **Twilio** | API Gateway | $0.005/msg + taxas Meta | Controle de desenvolvedor, customização |
| **Wati** | BSP Completo | $49/mês + markup | PMEs, dashboard, chatbot no-code |
| **Infobip** | Enterprise | Custom | Grandes empresas, omnichannel |

**Recomendação**: Começar com **360dialog** ou **Twilio** para controle de desenvolvedor e pricing transparente.

### Pricing de Mensagens (Brasil, pós-julho/2025)

| Categoria | Custo por Template | Notas |
|-----------|-------------------|-------|
| **Marketing** | ~$0.0625 | Mais caro — evitar |
| **Utility** | Menor que marketing | **GRÁTIS** dentro de 24h de janela de atendimento |
| **Authentication** | Taxas reduzidas | OTP/login |
| **Service** | **GRÁTIS** | Respostas a mensagens do cliente |

**Janelas gratuitas:**
- Templates utility dentro de 24h da última mensagem do cliente: GRÁTIS
- Respostas a clicks de anúncios WhatsApp: GRÁTIS por 72h
- Mensagens de serviço iniciadas pelo cliente: GRÁTIS

### WhatsApp Flows

Formulários interativos **dentro do WhatsApp** — múltiplas telas com dropdowns, botões e inputs de texto. Nativos na experiência do chat, sem sair do app.

**Uso potencial na CollectAI:**
- Apresentar opções de pagamento (à vista vs. parcelado)
- Coletar confirmação de dados do devedor
- Permitir escolha de data de pagamento

**Requisito**: Funciona APENAS com WhatsApp Business API.

**Fontes:**
- WhatsApp Business Policy (business.whatsapp.com/policy)
- Poli Digital — Regras para Cobrança WhatsApp
- PliQ — Novas Regras WhatsApp Business Brasil
- Webio — Compliance in WhatsApp Debt Collection
- 360dialog (360dialog.com/pricing)
- Gallabox — WhatsApp Pricing Changes July 2025
- Twilio — WhatsApp Pricing
- Sanoflow — WhatsApp Flows Complete Guide

---

# PARTE 8: Monetização e Modelo de Créditos

## 8.1 Panorama de Monetização em AI SaaS

### Tendências 2025-2026

**Crescimento de credit-based pricing:**
- **79 empresas** do PricingSaaS 500 Index oferecem pricing baseado em créditos (vs. 35 no final de 2024) — **crescimento de 126%**
- Inclui: Figma, HubSpot, Salesforce
- Créditos funcionam como "camada de abstração": cliente compra blocos de créditos, cada ação de IA consome créditos conforme "burn table"

**Usage-based em ascensão:**
- **59% das empresas de software** esperam crescimento de modelos usage-based em 2025
- Pricing por transação ganhando tração: cobrar por ação automatizada

**Outcome-based emergente:**
- **Gartner**: até 2025, **30%+ das soluções enterprise** incorporaram componentes outcome-based
- **45% das empresas SaaS** experimentando pricing vinculado a valor/resultado
- Split típico: **50-70% fee base + 30-50% vinculado a resultado**

**Modelos híbridos dominam:**
- Empresas com modelos híbridos (subscription + usage) reportam **maior mediana de crescimento: 21%**
- **41% das empresas SaaS enterprise** implementando pricing híbrido

### Exemplos de Mercado

| Empresa | Modelo | Detalhe |
|---------|--------|---------|
| **Intercom Fin AI** | Outcome-based | $0.99 por conversa resolvida pela IA — **40% mais adoção** em 6 meses |
| **Salesforce** | Híbrido | $2/conversa para agents prebuilt + créditos separados para agents custom |
| **Microsoft Copilot** | Híbrido | $30/user base + créditos para picos de uso |
| **Zendesk** | Outcome-based | Cobra apenas por resultados bem-sucedidos |
| **Sierra** | Outcome-based | Cobra por resolução bem-sucedida |

---

## 8.2 Modelo Recomendado para CollectAI

### Análise dos Modelos

| Modelo | Prós (CollectAI) | Contras (CollectAI) |
|--------|-------------------|---------------------|
| **Subscription fixa** | Previsível, simples | Não captura upside de alto uso |
| **Por mensagem** | Alinha custo com uso | Cliente não sabe quanto vai gastar |
| **Por crédito** | Flexível, familiar | "O que vale 1 crédito?" mata deals |
| **Por valor recuperado** | Máximo alinhamento | Complexo, exige rastrear pagamentos |
| **Híbrido** | Melhor de dois mundos | Levemente mais complexo de comunicar |

### Recomendação: Modelo Híbrido (Base + Conversas)

**Estrutura recomendada:**

```
┌─────────────────────────────────────────────┐
│                 PLANOS                       │
│                                             │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ │
│  │  STARTER  │ │  GROWTH   │ │ ENTERPRISE│ │
│  │           │ │           │ │           │ │
│  │ R$ 497/mês│ │R$ 1.497/mês│ │  Custom  │ │
│  │           │ │           │ │           │ │
│  │ 1 agente  │ │ 3 agentes │ │ Ilimitado │ │
│  │ 200 conv. │ │ 1.000 conv│ │ Custom    │ │
│  │ Dashboard │ │ Dashboard │ │ Dashboard │ │
│  │ WhatsApp  │ │ Multi-canal│ │ Multi-canal│ │
│  │ Email sup.│ │ Chat sup. │ │ Dedicado  │ │
│  │           │ │           │ │           │ │
│  │ Conv. extra│ │ Conv. extra│ │ Volume    │ │
│  │ R$ 1,50   │ │ R$ 1,20   │ │ negociado │ │
│  └───────────┘ └───────────┘ └───────────┘ │
└─────────────────────────────────────────────┘
```

**Por que este modelo:**

1. **Base mensal garante receita previsível** (MRR para o negócio)
2. **Conversas incluídas** reduzem medo do desconhecido (cliente sabe o mínimo que pode usar)
3. **Conversas extras** capturam upside de alto uso sem punir
4. **Alinhamento de incentivos**: mais conversas = mais cobrança = mais recuperação = mais valor para o cliente
5. **Simples de comunicar**: "R$ 497/mês com 200 conversas. Extras a R$ 1,50 cada."

### Alternativa Futura: Success Fee

Para clientes maiores, oferecer modelo híbrido com componente de success fee:
- Base menor + **5-10% do valor recuperado** pela IA
- Máximo alinhamento: CollectAI ganha mais quando o cliente ganha mais
- Requer integração de pagamento para rastrear valores recuperados (integração ASA)
- Implementar após escala (10+ clientes)

### Free Trial / Onboarding

- **Primeiras 50 conversas grátis** (sem cadastrar cartão)
- Objetivo: cliente experimenta o AHA Moment sem compromisso financeiro
- Após 50 conversas: paywall com upsell para Starter
- Benchmark: freemium → paid conversion de **20-30%** em PLG

---

## 8.3 Precificação de Créditos (Unit Economics)

### Custo Interno por Conversa

| Componente | Custo Estimado | Notas |
|-----------|---------------|-------|
| **Tokens GPT-4o** | ~$0.02-0.08 | ~2.000-5.000 tokens por conversa completa |
| **WhatsApp API** | ~$0.06 | ~1 template + mensagens de serviço |
| **Guardrails** | ~$0.01 | Input + output validation |
| **Infra** | ~$0.005 | Compute, storage, queue |
| **Total** | ~$0.10-0.16 | Por conversa completa |

### Pricing de Venda

Com markup de **8-10x** sobre custo (padrão AI SaaS):

| Plano | Conversas | Custo Interno | Preço Mensal | Margem |
|-------|-----------|---------------|-------------|--------|
| **Starter** | 200 | R$ 100-160 | R$ 497 | ~70% |
| **Growth** | 1.000 | R$ 500-800 | R$ 1.497 | ~55% |
| **Enterprise** | Custom | Negociado | Custom | ~50% |

**Conversas extras:**
- Starter: R$ 1,50/conversa (margem ~85%)
- Growth: R$ 1,20/conversa (margem ~80%)

### ROI Calculator para o Cliente

**Cenário: Empresa com R$ 500K em dívidas, 30% de inadimplência (R$ 150K)**

| Métrica | Sem CollectAI | Com CollectAI |
|---------|--------------|--------------|
| Taxa de recuperação | 25% (R$ 37.5K) | 40% (R$ 60K) |
| Custo operacional | R$ 5K/mês (1 pessoa) | R$ 1.5K/mês (plano Growth) |
| Recuperação líquida | R$ 32.5K | R$ 58.5K |
| **ROI** | — | **+80% recuperação, -70% custo** |

**Fontes:**
- GrowthUnhinged — 2025 State of SaaS Pricing
- Metronome — Rise of AI Credits
- Schematic HQ — Credit-Based Pricing
- PYMNTS — AI Moves SaaS Toward Usage-Based
- EY — Outcome-Based Pricing
- L.E.K. Consulting — Rise of Outcome-Based Pricing
- Chargebee — Pricing AI Agents Playbook
- Maxio — 2025 SaaS Pricing Report
- Lago — 6 Proven Pricing Models
- Bessemer — AI Pricing Playbook
- Stripe — Usage-Based Billing

---

# PARTE 9: Lançamento de Campanha e Pós-Onboarding

## 9.1 Upload e Processamento da Lista de Devedores

### Formatos Aceitos
- **CSV** (delimitado por vírgula ou ponto-e-vírgula)
- **XLSX** (Excel)
- **Integração direta com ERPs** (futuro: Omie, Bling, Conta Azul)

### Campos

| Campo | Obrigatório | Formato |
|-------|------------|---------|
| Nome | Sim | Texto |
| Telefone | Sim | +55DDDNUMERO |
| Valor devido | Sim | Numérico (R$) |
| Data vencimento | Sim | DD/MM/AAAA |
| Email | Não | email@dominio.com |
| CPF/CNPJ | Não | Formatado |
| Segmento | Não | Texto |
| Histórico | Não | Texto |

### Pipeline de Processamento

1. **Upload**: Drag-and-drop no browser
2. **Parse**: Detectar delimitador, encoding, formato de data
3. **Mapeamento de colunas**: UI para associar colunas do CSV aos campos do sistema
4. **Validação**: Formato de telefone, deduplicação, check de opt-in
5. **Enriquecimento** (opcional): Complementar dados faltantes
6. **Preview**: Mostrar primeiras 10 linhas para confirmação
7. **Report de erros**: Linhas com problemas destacadas em vermelho

---

## 9.2 Configuração de Campanha

### Parâmetros de Configuração

- **Horários de envio**: Início e fim (default: 08:00-20:00)
- **Dias de envio**: Seg-Sex (default), com opção de sábado
- **Frequência de follow-up**: A cada X dias (default: 3)
- **Limite diário**: Máximo de mensagens por dia
- **Mensagem inicial**: Editável (com preview)

### Segmentação Automática

O sistema sugere segmentação baseada nos dados:
- Por **faixa de valor**: até R$ 1K / R$ 1-5K / R$ 5-20K / acima de R$ 20K
- Por **tempo de atraso**: 1-30 dias / 31-90 dias / 91-180 dias / 180+ dias
- Por **perfil**: Primeira inadimplência / reincidente

### Métricas em Tempo Real

Dashboard de campanha mostrando:
- **Enviados**: Total de mensagens enviadas
- **Entregues**: Taxa de entrega (%)
- **Lidos**: Taxa de leitura (%)
- **Respondidos**: Taxa de resposta (%)
- **Em negociação**: Conversas ativas
- **Acordos**: Acordos fechados + valor total
- **Escalados**: Conversas escaladas para humano

---

# PARTE 10: Segurança, Compliance e Governança

## 10.1 LGPD e Proteção de Dados

### Dados Pessoais Tratados

| Dado | Categoria | Base Legal |
|------|-----------|-----------|
| Nome, CPF, telefone | Pessoal | Proteção ao crédito (Art. 7, X) |
| Valor da dívida | Financeiro (não sensível) | Legítimo interesse (Art. 7, IX) |
| Histórico de pagamento | Financeiro | Execução de contrato (Art. 7, V) |
| Gravações de conversa | Pessoal | Legítimo interesse + consentimento |
| Dados da empresa (CNPJ) | Não pessoal | Não se aplica (PJ) |

**Nota importante**: A LGPD é **silenciosa quanto a dados financeiros** — eles NÃO são classificados como "dados pessoais sensíveis". Dados financeiros não são sequer mencionados especificamente como dados pessoais, exceto no contexto da base legal de "proteção ao crédito".

### Base Legal Recomendada

Para cobrança, usar preferencialmente:
1. **Proteção ao crédito** (Art. 7, X) — base legal mais diretamente aplicável
2. **Legítimo interesse** (Art. 7, IX) — se o devedor recebeu serviço/produto e não pagou
3. **Execução de contrato** (Art. 7, V) — processamento necessário para execução do contrato

**Não usar** consentimento como base primária — o devedor poderia revogar o consentimento e efetivamente impedir o contato.

### Direitos do Titular (Art. 18)

O sistema deve permitir:
- **Acesso**: Devedor pode solicitar quais dados são tratados
- **Correção**: Corrigir dados incorretos
- **Anonimização/Exclusão**: Quando dados não forem mais necessários
- **Portabilidade**: Transferir dados a outro fornecedor
- **Informação sobre compartilhamento**: Com quem os dados são compartilhados
- **Revogação de consentimento**: Se consentimento for usado como base

### Retenção de Dados

| Tipo de Dado | Prazo | Justificativa |
|-------------|-------|---------------|
| Dados do devedor | Enquanto dívida ativa + 5 anos | Prescrição de dívida (CDC) |
| Conversas | 2 anos após resolução | Auditoria e compliance |
| Dados da empresa (cliente) | Enquanto conta ativa + 5 anos | Relação contratual |
| Logs de sistema | 1 ano | Segurança e debugging |

---

## 10.2 Regulação de Cobrança no Brasil

### CDC (Código de Defesa do Consumidor)

**Art. 42**: O consumidor inadimplente NÃO será:
- Exposto a ridículo
- Submetido a qualquer tipo de constrangimento ou ameaça

**Art. 71** (criminal): Proíbe:
- Ameaças, coação, constrangimento físico ou moral
- Declarações falsas ou enganosas
- Qualquer procedimento que exponha injustificadamente o consumidor ao ridículo
- Interferência com trabalho, descanso ou lazer

**Horários permitidos:**
- **Dias úteis**: 08:00 às 20:00
- **Sábados**: 08:00 às 14:00 (interpretação mais restritiva)
- **Domingos e feriados**: PROIBIDO

**Práticas proibidas:**
- Exposição pública da dívida
- Ligações excessivas
- Contato com terceiros para informar sobre a dívida
- Cobrança em horários inapropriados
- Ameaças de qualquer tipo
- Humilhação ou constrangimento

**Direito do consumidor**: Se cobrado indevidamente, direito à **restituição em dobro** do que foi pago em excesso (Art. 42, parágrafo único).

### Implementação no Agente

Todos estes limites devem ser **automatizados nos guardrails**:
- Output rail verifica horário antes de enviar mensagem
- Output rail verifica tom (não ameaçador, não constrangedor)
- Policy rail limita frequência de contato
- Policy rail impede contato com terceiros

---

## 10.3 AI Governance

### Transparência

**LGPD Art. 20** — Direito à revisão de decisões automatizadas:
- Devedor pode solicitar revisão de decisões feitas pela IA
- Controller deve fornecer informações claras sobre critérios e procedimentos
- **Diferença do GDPR**: LGPD NÃO exige que a revisão seja feita por humano

**PL 2338/2023 (AI Bill Brasil)**:
- Aprovado pelo Senado em dez/2024, em revisão pela Câmara
- **Chatbots devem divulgar** que são sistemas de IA
- Exige explicabilidade e auditabilidade
- Requer avaliações públicas de impacto

**Recomendação**: O agente **deve divulgar** que é IA. Mesmo que PL 2338 ainda não é lei, o Art. 20 da LGPD já exige transparência sobre decisões automatizadas que afetam perfil de crédito. Quando a AI Bill for promulgada, será obrigatório.

**Implementação sugerida**: Mensagem inicial do agente inclui "Este é um atendimento automatizado da [empresa]. Se preferir falar com um atendente humano, digite HUMANO a qualquer momento."

### Auditoria

- **Log completo** de todas as conversas (com timestamps)
- **Decisões do agente** registradas (qual desconto ofereceu, por quê)
- **Guardrails triggered** registrados (tentativa de violação bloqueada)
- **Escalações** com motivo
- **Retenção de logs**: 2 anos mínimo

### Human-in-the-Loop

Momentos que **obrigatoriamente** devem ter revisão humana:
- Valores acima do threshold definido pelo cliente
- Devedor solicita atendimento humano
- Devedor ameaça processo judicial
- Agente não consegue resolver após N tentativas
- Detecção de vulnerabilidade do devedor (indicadores de saúde mental, idoso, etc.)

### Bias Detection

- Monitorar se o agente trata devedores de forma equitativa
- Comparar taxas de acordo por perfil demográfico
- Alertar se houver discrepância significativa

**Fontes:**
- LGPD (lgpd-brazil.info)
- CDC (planalto.gov.br)
- IBA — Brazilian Legal Framework on Automated Decision-Making
- Securiti — Brazil AI Regulation
- Chambers — AI Brazil 2025
- IAPP — LGPD Court Decisions
- ICLG — Data Protection Brazil 2025
- Data Privacy Brasil — Legitimate Interest under LGPD

---

# PARTE 11: Roadmap de Implementação

## 11.1 Fases de Desenvolvimento

### Fase 1: MVP (6-8 semanas)

**Objetivo**: Onboarding funcional com geração básica de agente

| Componente | Escopo |
|-----------|--------|
| **Registro** | Email/senha, criação de conta |
| **Enriquecimento** | CNPJ básico (ReceitaWS/BrasilAPI) |
| **Wizard** | Steps estruturados SEM chat IA (formulário puro) |
| **Tipo de agente** | Seleção adimplente/inadimplente |
| **Geração** | Agent Generator com templates base + customização por dados |
| **Pagamento** | Stripe Checkout (planos fixos) |
| **Campanha** | Upload CSV + lançamento básico |

**Não inclui**: Chat IA, áudio, enriquecimento avançado, simulação, ajustes finos.

### Fase 2: AHA Moment (4-6 semanas)

**Objetivo**: Simulação agent-to-agent e enriquecimento expandido

| Componente | Escopo |
|-----------|--------|
| **Simulação** | Agent-to-agent com 2-3 cenários |
| **Enriquecimento** | + Site scraping + Reclame Aqui |
| **Validação de dados** | Step de review com dados enriquecidos |
| **Ajustes** | Editor básico de tom/políticas com re-simulação |

### Fase 3: IA Híbrida (6-8 semanas)

**Objetivo**: Chat IA no wizard + áudio + geração avançada

| Componente | Escopo |
|-----------|--------|
| **Chat IA** | Interview Agent com follow-ups inteligentes |
| **Áudio** | MediaRecorder + Whisper (batch) |
| **Geração avançada** | Context engineering completo, structured output |
| **Guardrails** | Migração para camada separada (NeMo ou Agents SDK) |

### Fase 4: Polish (4 semanas)

**Objetivo**: Enriquecimento completo + refinamento

| Componente | Escopo |
|-----------|--------|
| **Enriquecimento** | + Google Maps + notícias + concorrentes + benchmarks |
| **Simulação** | Múltiplos cenários com personas variadas |
| **Analytics** | Dashboard de onboarding (funil, abandono, tempo) |
| **Mobile** | Otimização mobile-first |
| **Billing** | Usage-based billing com Stripe Metered |

---

## 11.2 Equipe Necessária

| Role | Perfil | Dedicação |
|------|--------|-----------|
| **Frontend Dev** | React senior, experiência com chat UI e forms complexos | Full-time (ou 2 part-time) |
| **Backend Dev** | Python senior, experiência com LLMs, FastAPI, async | Full-time |
| **UX Designer** | Experiência em B2B SaaS onboarding | Part-time ou freelancer |
| **Fundadores** | Product direction, QA, teste de agentes | Part-time (como hoje) |

**Alternativa**: 1 full-stack senior que domina React + Python + LLMs pode fazer MVP sozinho nas fases 1-2.

---

## 11.3 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Qualidade do agente gerado automaticamente | Alta | Alto | Templates base robustos + review humano opcional + simulação como QA |
| Latência do enriquecimento (fontes lentas) | Média | Médio | Processamento async, feedback progressivo, cache agressivo |
| Custo de tokens GPT-4o em escala | Média | Médio | Cache de respostas comuns, modelos mais leves para tasks simples (gpt-4o-mini) |
| Compatibilidade de áudio no mobile (iOS) | Média | Baixo | RecordRTC como fallback, feature detection |
| WhatsApp bloquear conta por cobrança | Alta | Alto | Enquadrar como utility/service, linguagem de facilitação, advogado especializado |
| Abandono no onboarding | Alta | Alto | Progressive disclosure, save & resume, <15 min total, AHA Moment cedo |
| LGPD/compliance violação | Baixa | Alto | Guardrails automatizados, auditoria, logs, DPO |

---

# APÊNDICES

## Apêndice A: Glossário Técnico

| Termo | Definição |
|-------|----------|
| **Multi-agent** | Sistema com múltiplos agentes de IA coordenados |
| **Handoff** | Transferência de controle de um agente para outro |
| **Guardrails** | Regras/validações que limitam o comportamento do agente |
| **Context engineering** | Curadoria de todos os dados que entram na context window do LLM |
| **PLG** | Product-Led Growth — crescimento liderado pelo produto (vs. vendas) |
| **AHA Moment** | Instante em que o usuário percebe o valor do produto |
| **Structured output** | Output do LLM em formato JSON com schema definido |
| **RAG** | Retrieval-Augmented Generation — busca + geração |
| **SSE** | Server-Sent Events — streaming unidirecional do servidor |
| **DSO** | Days Sales Outstanding — dias para receber |
| **CNAE** | Classificação Nacional de Atividades Econômicas |
| **Aging** | Tempo de atraso de uma dívida |
| **PTP** | Promise to Pay — promessa de pagamento |
| **Burn table** | Tabela que define quantos créditos cada ação consome |
| **Wizard** | Interface de formulário com múltiplos steps sequenciais |
| **BSP** | Business Solution Provider (WhatsApp) |

## Apêndice B: Exemplos de Prompts

### B.1 Prompt de Agregação de Enriquecimento

```
Você é um analista especializado em crédito e cobrança no Brasil.
Analise os dados brutos de múltiplas fontes sobre esta empresa e gere
um perfil estruturado no formato JSON especificado.

Foque em:
1. Identificar o segmento exato e tipo provável de dívida
2. Estimar a taxa de inadimplência do setor
3. Recomendar tom de comunicação baseado na reputação
4. Identificar riscos específicos do segmento
5. Sugerir benchmarks realistas de recuperação

Dados brutos:
{raw_data}

Retorne em JSON conforme schema: {schema}
```

### B.2 Prompt de Geração de Agente (System Prompt Template)

```
Você é o agente de cobrança da {company_name}, uma empresa de {segment}
localizada em {city}/{state}.

## Sua Identidade
- Nome: Agente {company_trade_name}
- Tom: {tone} (formal/amigável/empático/assertivo)
- Canal: WhatsApp

## Sobre a Empresa
{company_description}

## Tipos de Dívida que Você Cobra
{debt_types}

## Políticas de Negociação
- Desconto máximo à vista: {max_discount_cash}%
- Desconto máximo parcelado: {max_discount_installments}%
- Parcelas máximas: {max_installments}x
- Valor mínimo por parcela: R$ {min_installment}
- Horários de contato: {working_hours}

## O que Você NUNCA Deve Fazer
{forbidden_behaviors}
- Ameaçar o devedor de qualquer forma
- Expor a dívida a terceiros
- Cobrar fora do horário permitido
- Oferecer descontos acima dos limites
- Usar linguagem jurídica ou técnica intimidadora

## Quando Escalar para Humano
{escalation_rules}
- Devedor solicita atendimento humano
- Devedor menciona processo judicial
- Após {max_attempts} tentativas sem acordo
- Valor acima de R$ {escalation_threshold}

## Fluxo de Conversa
1. Cumprimento e identificação
2. Informar sobre a pendência (sem expor detalhes antes de confirmar identidade)
3. Ouvir a situação do devedor
4. Apresentar opções de pagamento personalizadas
5. Negociar dentro dos limites
6. Gerar link de pagamento se houver acordo
7. Follow-up conforme configurado
```

### B.3 Prompt do Interview Agent (Follow-up Generator)

```
Você é o agente de entrevista do onboarding da CollectAI. Seu papel é
analisar as respostas do cliente durante o wizard e gerar perguntas de
follow-up para coletar informações mais detalhadas.

## Contexto da Empresa
{company_profile}

## Respostas Anteriores
{previous_responses}

## Resposta Atual
{current_response}

## Regras
1. Gere 1-2 perguntas de follow-up focadas em lacunas de informação
2. Use linguagem simples e acessível (persona: analista financeiro)
3. Foque em dados que impactam diretamente a configuração do agente
4. Não repita perguntas já respondidas
5. Se a resposta está completa e clara, retorne "nenhum follow-up necessário"

## Exemplos de Follow-ups Relevantes
- Se mencionou "construtora" → perguntar sobre tipo de dívida (imóvel, serviço, material)
- Se mencionou "parcelamento" → perguntar sobre limites e condições
- Se mencionou "WhatsApp" → perguntar quem é o remetente (empresa, pessoa)
```

### B.4 Prompt do Debtor Simulator

```
Você é um simulador de devedor para demonstração. Simule um devedor
realista do segmento {segment}.

## Perfil
- Nome: {fake_name}
- Dívida: R$ {debt_value} referente a {debt_description}
- Atraso: {days_overdue} dias
- Personalidade: {personality} (cooperativo/hesitante/resistente)

## Comportamento
- Cooperativo: quer resolver mas precisa de boas condições
- Hesitante: precisa ser convencido, pede tempo, questiona
- Resistente: contesta valores, reclama, pede descontos altos

## Regras
1. Responda naturalmente, como brasileiro falaria no WhatsApp
2. Use linguagem coloquial (abreviações, emojis leves OK)
3. Não seja impossível de negociar — sempre deixe abertura
4. Reaja realisticamente às propostas do agente
5. A conversa deve durar 6-12 turnos até resolução
```

## Apêndice C: Schema JSON do Agente Gerado

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["agent_config"],
  "properties": {
    "agent_config": {
      "type": "object",
      "required": ["name", "type", "system_prompt", "tools", "guardrails", "policies"],
      "properties": {
        "name": { "type": "string" },
        "version": { "type": "string", "pattern": "^\\d+\\.\\d+$" },
        "type": { "type": "string", "enum": ["adimplente", "inadimplente"] },
        "system_prompt": { "type": "string", "minLength": 100 },
        "tools": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "description": { "type": "string" },
              "trigger_conditions": { "type": "array", "items": { "type": "string" } },
              "parameters": { "type": "object" }
            }
          }
        },
        "guardrails": {
          "type": "object",
          "properties": {
            "input_rails": { "type": "array", "items": { "type": "string" } },
            "output_rails": { "type": "array", "items": { "type": "string" } },
            "policy_rails": { "type": "array", "items": { "type": "string" } },
            "tone_rails": { "type": "array", "items": { "type": "string" } }
          }
        },
        "policies": {
          "type": "object",
          "properties": {
            "max_discount_cash_percent": { "type": "number", "minimum": 0, "maximum": 100 },
            "max_discount_installments_percent": { "type": "number", "minimum": 0, "maximum": 100 },
            "max_installments": { "type": "integer", "minimum": 1 },
            "min_installment_value": { "type": "number", "minimum": 0 },
            "working_hours": { "type": "object" },
            "working_days": { "type": "array", "items": { "type": "string" } }
          }
        },
        "negotiation_strategies": { "type": "array" },
        "message_templates": { "type": "object" }
      }
    }
  }
}
```

## Apêndice D: Referências e Bibliografia Completa

### Mercado e Dados
- Serasa Experian — Mapa da Inadimplência (serasa.com.br)
- CNDL/SPC Brasil — Indicadores de Inadimplência (cndl.org.br)
- Banco Central do Brasil — Relatório de Estabilidade Financeira (bcb.gov.br)
- Febraban — Pesquisa de Economia Bancária (portal.febraban.org.br)
- Market.us — AI for Debt Collection Market Report
- Mordor Intelligence — Debt Collection Software Market

### Competidores
- C&R Software / Zelas AI (crsoftware.com)
- Sedric AI (sedric.ai)
- HighRadius (highradius.com)
- Kolleno (kolleno.com)
- Vodex AI (vodex.ai)
- Neofin (neofin.com.br)
- Monest (monest.com.br)
- EaseCob (easecob.com)
- Assertiva (assertiva.com.br)
- Acordo Certo / Acerto (acerto.com.br)

### UX e Design
- Insaim Design — SaaS Onboarding Best Practices 2025
- Onething Design — B2B SaaS UX Design 2026
- UserGuiding — B2B SaaS Onboarding
- NN/g — New Users Need Support with Gen-AI Tools
- Userpilot — AHA Moment Guide / Time-to-Value Benchmark
- JavaPro — AI-Powered Form Wizards
- assistant-ui (assistant-ui.com)

### Arquitetura de Agentes
- OpenAI Agents SDK (openai.github.io/openai-agents-python)
- Agency Swarm (github.com/VRSEN/agency-swarm)
- CrewAI, LangGraph, AutoGen — comparações DataCamp
- Anthropic — Effective Context Engineering for AI Agents
- NVIDIA NeMo Guardrails (developer.nvidia.com)
- Sierra AI — Simulations (sierra.ai/blog)
- arXiv 2502.18228 — Debt Collection Negotiations with LLMs
- arXiv 2503.21080 — EmoDebt

### Tecnologia
- OpenAI — Speech-to-Text / Structured Outputs / Realtime API
- MDN — MediaRecorder API
- RecordRTC (recordrtc.org)
- Stripe — Usage-Based Billing

### APIs de Enriquecimento
- CNPJa (cnpja.com)
- CNPJ.ws (cnpj.ws)
- ReceitaWS (receitaws.com.br)
- BrasilAPI (github.com/BrasilAPI)
- OpenCNPJ (opencnpj.org)
- Outscraper (outscraper.com)
- SerpAPI (serpapi.com)

### Legal e Compliance
- LGPD (lgpd-brazil.info)
- CDC — Lei 8.078/1990 (planalto.gov.br)
- PL 2338/2023 — AI Bill Brasil
- IAPP — LGPD Court Decisions
- Chambers — Data Protection Brazil 2025

### Monetização
- GrowthUnhinged — 2025 State of SaaS Pricing
- Metronome — Rise of AI Credits
- EY — Outcome-Based Pricing
- Bessemer — AI Pricing Playbook
- Chargebee — Pricing AI Agents Playbook

### WhatsApp
- WhatsApp Business Policy (business.whatsapp.com/policy)
- 360dialog (360dialog.com)
- Gallabox — Pricing Changes July 2025
- Sanoflow — WhatsApp Flows Guide
