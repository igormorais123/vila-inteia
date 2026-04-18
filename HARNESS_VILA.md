# HARNESS VILA — Banho Técnico de Arquitetura

> **Aplicação da skill `harness-architect` ao projeto Vila INTEIA.**
> Framework: Zhou et al. (2026) *Externalization in LLM Agents* (arXiv:2604.08224) + MCP + A2A + Claude Code Skills.
> Data: 2026-04-18 · Autor: ONIR + skill harness-architect · Alvo: Igor Morais Vasconcelos.

---

## 0. Diagnóstico em uma frase

> **A Vila já é um harness parcial muito sofisticado — o que falta é dar nome às peças, unificar contratos e fechar três loops críticos (observabilidade, orçamento de contexto e governança de skill).**

O código atual tem, sem perceber, implementado quase todas as três dimensões de externalização (memória, skills, protocolos) e metade das três superfícies operacionais (aprovação via Chateaubriand + constituição, controle parcial via steps). Mas o acoplamento é implícito e os contratos estão embaralhados. Este documento expõe a estrutura escondida, dá nomes canônicos e aponta os quatro movimentos que transformam a Vila num harness **elegante e completo**.

---

## 1. Mapeamento atual → framework do Harness

### 1.1 Os 3 módulos de externalização — o que a Vila já tem

| Dimensão | Onde vive na Vila hoje | Maturidade | Falta |
|----------|------------------------|------------|-------|
| **MEMÓRIA** | `engine/memoria/{fluxo,espacial,rascunho}.py` + `vila_snapshots` no Supabase | Alta — 3 dos 4 tipos canônicos | O 4º tipo (ficha do usuário/Fundador) + consolidação explícita + esquecimento |
| **SKILLS** | `engine/oficinas.py` (27 técnicas Problem Solving de Van Aken) + `engine/ferramentas_agente.py` + `.claude/skills/vila-*` | Média — skills existem mas sem manifest/discovery/progressive disclosure | Formalizar cada oficina como skill artifact com as 3 camadas (procedimento + heurística + restrição) |
| **PROTOCOLOS** | `mirante_client.py`, `mirofish_bridge.py`, `ia_client.py` (OmniRoute), API FastAPI, Supabase REST | Média — há contratos mas cada um reinventado | Camada MCP-like unificada + capability discovery + schema versionado |

### 1.2 As 3 superfícies operacionais — parcialmente presentes

| Superfície | Onde vive na Vila hoje | Maturidade | Falta |
|------------|------------------------|------------|-------|
| **PERMISSÃO** | Linha editorial do Mirante (rate limit, blocklist) + Chateaubriand (aprovador) | Baixa — só no editorial | Permissões por cenário (economia, constituição, redes sociais) + policy-as-code |
| **CONTROLE** | `config.py` (steps, intervalo), modo dormência (>200 agentes) | Baixa-Média | Orçamento de contexto explícito, limites de recursão, timeout por fase cognitiva |
| **OBSERVABILIDADE** | Logs Python esparsos, snapshots JSONB | Baixa | Trace estruturado por step/agente/ação + métricas agregadas + causal chain |

### 1.3 O loop cognitivo da Vila já É o Agent Loop do harness

Um achado importante: `engine/cognitivo/` implementa o **Agent Loop canônico** sem saber que é.

```
perceber → recuperar → planejar → executar → conversar → refletir → sintetizar
   │           │           │          │            │            │           │
   └─ igual a ─┴─ retrieve ┴─ plan ───┴─ act ─────┴─ observe ───┴─ reflect ─┘
```

Só renomeie e formalize. Este **é** o diferencial técnico da Vila — manter e documentar como exemplo de referência no próprio repositório.

---

## 2. O que já está bom e não precisa mexer

1. **Constituição viva** (`constituicao.py` + `constituinte.py`) — forma rara e elegante de **governance as data**. Equivalente harness: policy-as-code evolutivo + review gates.
2. **Chateaubriand** como aprovador editorial — exemplo canônico de **approval gate parametrizável**. Outros projetos do Igor deveriam copiar.
3. **Autoresearch** (loop Karpathy) — implementa **experience distillation** (memory → skill) por padrão. É o fluxo cross-cutting mais importante do paper.
4. **Desafios coletivos** — formalizam **hierarchical planning** com multi-agente (planner/executor).
5. **Snapshot Supabase JSONB** — persistência com rollback determinístico já resolvida.
6. **11 Mandamentos → mecânicas reais** — converte valores em código. Equivalente harness: **normative constraints** embutidos como primeira classe.

Não toque nesses — use como base.

---

## 3. Gaps concretos e ordenados por retorno/risco

### 3.1 GAP #1 (crítico, baixo esforço) — Observability estruturada

**Problema**: impossível auditar uma decisão específica de um agente em um step específico. Logs são texto solto. Snapshots são grandes demais para diff.

**Solução**: camada de trace estruturado inspirada em OpenTelemetry + OpenInference.

**Arquivo novo**: `engine/harness/observabilidade.py`

```python
# esqueleto
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Literal

@dataclass
class TraceEvent:
    step: int
    agente_id: str
    fase: Literal["perceber","recuperar","planejar","executar","conversar","refletir","sintetizar"]
    inicio: datetime
    fim: datetime
    inputs_hash: str      # hash do que entrou
    outputs_hash: str     # hash do que saiu
    causal_parent: str | None   # id do trace que causou este
    tokens_consumidos: int
    custo_usd: float
    ferramenta_chamada: str | None
    resultado: Literal["sucesso","falha","aprovacao_humana","retry"]
    metadata: dict

# registrar via decorator:
@trace_fase("planejar")
def planejar(agente, contexto): ...
```

**Tabela Supabase nova**: `vila_traces` (step, agente_id, fase, tempo, custo, parent, resultado, payload JSONB).

**Payoff**: debugging instantâneo. Ablation studies possíveis. Relatório semanal "top 10 agentes que mais gastam token".

---

### 3.2 GAP #2 (crítico, médio esforço) — Orçamento de contexto

**Problema**: cada chamada LLM de cada fase de cada agente monta seu prompt do zero. Memória pode estar afogando o modelo. Oficinas podem estar vazando instrução demais. Não existe medição.

**Solução**: orçamento declarado por fase, staged loading de oficinas, eviction baseado em relevância decaída.

**Arquivo novo**: `engine/harness/orcamento.py`

```python
ORCAMENTO_POR_FASE = {
  "perceber":   { "tokens_max": 1500, "memoria_max": 400,  "skill_detail": False },
  "recuperar":  { "tokens_max": 2500, "memoria_max": 1800, "skill_detail": False },
  "planejar":   { "tokens_max": 4000, "memoria_max": 1200, "skill_detail": True  },  # aqui carrega oficina
  "executar":   { "tokens_max": 3500, "memoria_max":  500, "skill_detail": True  },
  "conversar":  { "tokens_max": 2000, "memoria_max":  600, "skill_detail": False },
  "refletir":   { "tokens_max": 2500, "memoria_max": 1500, "skill_detail": False },
  "sintetizar": { "tokens_max": 3000, "memoria_max": 2000, "skill_detail": False },
}

def alocar(fase: str) -> Orcamento: ...
def caber_ou_resumir(texto: str, budget: int) -> str: ...
```

**Integração**: cada função em `engine/cognitivo/` recebe `orcamento` como parâmetro e obedece.

**Payoff**: corta custo LLM em 30-60% sem perder qualidade. Elimina "lost in the middle" em agentes com memória grande.

---

### 3.3 GAP #3 (alto, alto esforço) — Oficinas como skills canônicas

**Problema**: `oficinas.py` tem 27 técnicas excelentes mas são selecionadas por keyword match e carregadas inteiras. Sem manifest, sem discovery estruturado, sem binding declarativo.

**Solução**: promover cada oficina a **skill artifact** com as 3 camadas + progressive disclosure.

**Estrutura nova**: `engine/skills_oficinas/<nome>/SKILL.md`

```markdown
---
name: ishikawa
familia: problem-solving
capabilities: [causa-raiz, diagnostico-sistema, analise-6M]
preconditions: [problema_definido, ao_menos_3_sintomas_observados]
scope: [tecnico, organizacional, processo]
tokens_nivel_1: 50        # só nome + descrição curta
tokens_nivel_2: 400       # applicability + preconditions + 1 exemplo
tokens_nivel_3: 2000      # guia completo com etapas detalhadas
bind_tools: [whiteboard, conversar]
constraints:
  - exige ao menos 2 ramos de causa investigados
  - conclusao precisa apontar 1 causa-raiz primaria
autoresearch_pode_melhorar: true
---

## Nível 1 — Manifest
[50 tokens: o que a oficina faz]

## Nível 2 — Quando aplicar
[400 tokens: applicability + preconditions + mini-exemplo]

## Nível 3 — Guia completo
[2000 tokens: procedimento passo a passo]
```

**Arquivo novo**: `engine/harness/skill_registry.py` — registry + discovery por semantic match + staged loading.

**Payoff**: o agente Helena pode recomendar oficina baseado em diagnóstico real, não keyword. Autoresearch destila novas oficinas a partir de traces. Oficinas ganham test suite.

---

### 3.4 GAP #4 (médio, médio esforço) — Protocolo unificado para integrações externas

**Problema**: `mirante_client.py`, `mirofish_bridge.py`, `ia_client.py`, e os endpoints do Supabase são todos adapters ad-hoc. Adicionar Helena/Efesto/Cícero como agentes externos demanda novo cliente.

**Solução**: camada MCP-like interna que expõe capabilities descobríveis.

**Arquivo novo**: `engine/harness/protocolos/`

```
engine/harness/protocolos/
├── __init__.py
├── capability_card.py        # schema da capability
├── registry.py               # carrega capability_cards de .toml
├── mcp_server.py             # expõe via JSON-RPC 2.0 (opcional para outros agentes Colmeia chamarem)
├── cards/
│   ├── mirante_publicar.toml
│   ├── mirofish_consultar.toml
│   ├── supabase_snapshot.toml
│   ├── omniroute_completar.toml
│   └── vila_step_avancar.toml
```

**Capability card** (exemplo):

```toml
[capability]
id = "mirante.publicar_materia"
version = "1.0.0"
descricao = "Envia MDX + frontmatter ao Mirante News, retorna slug ou erro"

[args]
autor_id = { tipo = "str", obrigatorio = true }
titulo = { tipo = "str", max_chars = 120, obrigatorio = true }
corpo_mdx = { tipo = "str", max_chars = 50000, obrigatorio = true }
frontmatter = { tipo = "dict", schema = "zod:vila-materia-v1" }

[permission]
rate_limit_por_agente = "3/dia"
bloqueia_se_reputacao = "< 30"
exige_aprovacao_chateaubriand = true

[lifecycle]
estados = ["submetido", "aprovado", "reescrito", "rejeitado", "publicado", "bloqueado"]

[output]
sucesso = { slug = "str", url = "str" }
falha = { razao = "enum:duplicidade|palavra_bloqueada|rate_limit|rejeicao_editorial" }
```

**Payoff**: novos agentes Colmeia (Helena externa, Cícero, Efesto) integram à Vila sem escrever adapter. Frontend 3D pode descobrir capabilities. Audit trail por capability fica obrigatório.

---

### 3.5 GAP #5 (médio, baixo esforço) — Ficha do Fundador

**Problema**: a memória da Vila tem fluxo, espacial, rascunho — mas **nenhum dos 4 tipos canônicos cobre o Fundador** (Igor). Cada agente reage a "o Fundador pediu X" sem ter uma ficha estável com preferências, histórico de interações, restrições.

**Solução**: 4º tipo de memória — `memoria/fundador.py`.

```python
# Estrutura
@dataclass
class FichaFundador:
    identificacao: dict     # nome, papel, OAB, idade, neurodivergência declarada
    preferencias: dict      # comunicação direta, sem bajulação, PT-BR, etc (de CLAUDE.md)
    projetos_ativos: dict   # Colmeia, Mirante, Elexion, INTEIA, doutorado
    historico_interacoes: list   # top 50 mais recentes, com relevância
    restricoes_operacionais: list  # "nunca publicar sem autorização", "terapia quinta 16h"
    ultima_atualizacao: datetime
```

**Integração**: `cognitivo/recuperar.py` injeta fatia relevante da ficha em toda fase que envolva pedido do Fundador.

**Payoff**: Helena, Chateaubriand e constituinte param de "esquecer" quem está no comando. Vila inteira ganha coerência de tratamento.

---

### 3.6 GAP #6 (baixo, baixo esforço) — Formalizar constituição como policy layer

**Problema**: a constituição é genial conceitualmente, mas sua execução (`executor_constitucional.py`) está acoplada. Não há teste isolado do "o que um artigo faz".

**Solução**: tratar cada artigo como **policy rule** declarativa.

**Formato novo**: `constituicao/artigos/<id>.toml`

```toml
[artigo]
id = "art-042"
titulo = "Publicação acelerada para insights urgentes"
status = "promulgado"
tipo = "operacional"   # ou economico, estrutural

[gatilho]
evento = "agente_produz_materia"
condicao = "reputacao >= 80 and urgencia >= 0.8"

[efeito]
aplicar_em = "chateaubriand.avaliar"
modificacao = { fila_prioritaria = true, tempo_max_review = "30s" }

[origem]
evento_origem_id = "vila_evento:7812"
votos_a_favor = 134
votos_contra = 12
data_promulgacao = "2026-03-14"
```

Runtime carrega todos artigos ativos e aplica como middleware.

**Payoff**: artigo vira testável. Rollback é remover linha. Simulações "o que se esse artigo tivesse sido reprovado" viram triviais.

---

### 3.7 GAP #7 (alto valor, médio risco) — Loop cross-cutting: memory → skill → protocol → memory

**Problema**: autoresearch faz parte disso mas não está formalizado como **os 6 fluxos** do Harness (Zhou et al. Figura 8).

**Solução**: tornar os 6 fluxos explícitos no código.

**Mapeamento 1:1 com o paper**:

| Fluxo do paper | Nome na Vila | Onde vive hoje | Ação |
|----------------|--------------|----------------|------|
| memory → skill (experience distillation) | oficina emergente | `autoresearch.py` | Já existe — documentar como tal |
| skill → memory (execution recording) | trace de oficina usada | cognitivo/executar.py | Adicionar via observabilidade (GAP #1) |
| skill → protocol (capability invocation) | oficina chama ferramenta | ferramentas_agente.py | Refatorar via capability card (GAP #4) |
| protocol → skill (capability generation) | nova API vira oficina nova | — não existe — | Criar fluxo em autoresearch |
| memory → protocol (strategy selection) | histórico de falhas muda rota | — não existe — | Roteador em ia_client.py usa trace |
| protocol → memory (result assimilation) | resposta Mirante vira memória | mirante_client callback | Já existe parcialmente |

**Payoff**: autoresearch deixa de ser recanto e vira o sistema nervoso da evolução da Vila.

---

## 4. Arquitetura-alvo — Vila como Harness Elegante

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         VILA INTEIA — HARNESS v2                           │
│                                                                            │
│  ┌──────────────────────── Foundation Model ────────────────────────┐     │
│  │              OmniRoute Gateway (GPT-5.4 / Gemma / Claude)         │     │
│  └──────────────────────────────┬────────────────────────────────────┘     │
│                                 │                                          │
│     ┌───── 3 MÓDULOS DE CONTEÚDO COGNITIVO ──────┐                         │
│     │                                              │                         │
│     │  MEMÓRIA              SKILLS         PROTOCOLOS                      │
│     │  ┌─────────┐        ┌───────────┐   ┌────────────┐                  │
│     │  │ fluxo   │        │ oficinas/ │   │ MCP-like   │                  │
│     │  │ espacial│        │ SKILL.md  │   │ capability │                  │
│     │  │ rascunho│        │ registry  │   │ cards      │                  │
│     │  │ fundador│  [NEW] │ discovery │   │ OmniRoute  │                  │
│     │  │         │        │ staged    │   │ Mirante    │                  │
│     │  │ Supabase│        │ loading   │   │ Mirofish   │                  │
│     │  └─────────┘        └───────────┘   │ Supabase   │                  │
│     │                                      └────────────┘                  │
│     └──────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│     ┌───── 3 SUPERFÍCIES OPERACIONAIS (Harness Core) ───────┐              │
│     │                                                         │              │
│     │  PERMISSÃO              CONTROLE          OBSERVABILIDADE │            │
│     │  ┌────────────┐     ┌─────────────┐   ┌─────────────┐  │            │
│     │  │ constitu-  │     │ orcamento.py│   │ vila_traces │  │            │
│     │  │ ição vira  │ [NEW]│ por fase   │   │ (Supabase)  │  │            │
│     │  │ policy     │     │ step/recur │   │ causal chain│  │            │
│     │  │ Chateau-   │     │ bounds     │   │ métricas    │  │            │
│     │  │ briand     │     │ timeout    │   │ aggregate   │  │            │
│     │  │ approval   │     │             │   │             │  │            │
│     │  └────────────┘     └─────────────┘   └─────────────┘  │            │
│     └─────────────────────────────────────────────────────────┘            │
│                                                                            │
│  ┌──────────── AGENT LOOP (já implementado — só renomear) ────────┐       │
│  │  perceber → recuperar → planejar → executar → conversar        │       │
│  │                       → refletir → sintetizar                  │       │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ┌───────── 6 FLUXOS CROSS-CUTTING (Zhou et al. Fig. 8) ─────────┐        │
│  │  distillation · recording · invocation · generation ·          │        │
│  │  strategy selection · result assimilation                      │        │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ┌──────── LIGAÇÃO COM A COLMEIA (agent-agent protocols) ────────┐        │
│  │  Helena · Iris · Diana · Efesto · Cícero · Themis · Midas ·   │        │
│  │  Oracle Gnosis · Mel · ONIR — via A2A-like cards              │        │
│  └──────────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Plano de migração — 4 ondas priorizadas

### Onda 1 — Tornar visível o que já existe (1 semana)

Sem refator, só documentação + renomeação.

- [ ] Criar `engine/harness/` como pacote vazio com README apontando para este documento
- [ ] Mover este `HARNESS_VILA.md` para `docs/HARNESS_VILA.md` e linkar em `README.md`
- [ ] Renomear comentários em `engine/cognitivo/*.py` para usar terminologia do harness (Agent Loop fases)
- [ ] Adicionar seção "Vila como Harness" em `docs/ARCHITECTURE.md`
- [ ] Atualizar `.claude/skills/SKILLS_INDEX.md` incluindo referência à skill `harness-architect`

**Entrega**: qualquer agente que ler os docs entende a Vila como harness.

### Onda 2 — Observability + Orçamento (2 semanas, CRÍTICO)

- [ ] Criar `engine/harness/observabilidade.py` + migration Supabase `vila_traces`
- [ ] Decorar as 7 fases cognitivas com `@trace_fase`
- [ ] Criar `engine/harness/orcamento.py` com a tabela por fase
- [ ] Adaptar cada função em `cognitivo/` para receber orçamento
- [ ] Dashboard simples em `/api/traces` com top-N agentes por custo e top-N oficinas por uso

**Entrega**: custo da Vila cai ≥ 30%; debug de qualquer step fica trivial.

### Onda 3 — Skills canônicas + Protocolos unificados (3 semanas)

- [ ] Promover as 27 oficinas a skills com `SKILL.md` + manifest
- [ ] Criar `engine/harness/skill_registry.py` com discovery semântica
- [ ] Criar `engine/harness/protocolos/` + capability cards para as 5 integrações externas
- [ ] Migrar `mirante_client`, `mirofish_bridge`, `ia_client`, `supabase_db` para usar cards
- [ ] Expor servidor MCP opcional para agentes externos da Colmeia (Helena, Efesto) chamarem a Vila

**Entrega**: Colmeia inteira integra via protocolo único. Autoresearch pode destilar novas skills a partir de traces.

### Onda 4 — Fundador + Constituição como policy + 6 fluxos explícitos (2 semanas)

- [ ] `engine/memoria/fundador.py` — ficha do Igor alimentada do CLAUDE.md + histórico
- [ ] Migrar artigos constitucionais para `.toml` + middleware de aplicação
- [ ] Documentar e nomear os 6 fluxos cross-cutting; adicionar trace cruzado
- [ ] Criar `docs/HARNESS_FLOWS.md` com cada fluxo + exemplo real da Vila

**Entrega**: Vila é o exemplo de referência oficial da skill `harness-architect` — reutilizável em Elexion, Mirante, copilot jurídico.

---

## 6. Como a Colmeia vira harness distribuído via Vila

Com protocolo unificado (Onda 3), a Colmeia inteira — Helena, Iris, Diana, Efesto, Cícero, Themis, Midas, Oracle, Mel, ONIR — pode **usar a Vila como substrato de simulação** antes de agir no mundo real.

Exemplo concreto:
1. Helena precisa decidir se a INTEIA aceita um cliente novo.
2. Em vez de "achar", ela chama `POST /api/harness/simular` enviando o perfil do cliente.
3. Vila instancia 7 agentes sintéticos (advogado, cliente, Themis, Midas, concorrente, jornalista hostil, Igor síncrono) em um cenário de 30 steps.
4. Retorna trace estruturado com: probabilidade de conflito ético (Themis), margem (Midas), risco reputacional (Chateaubriand), alinhamento com doutrina (constituição).
5. Helena decide com base em dados simulados — não chute.

Isso só é possível se **as capabilities estiverem discoveráveis** (Onda 3). Hoje a Vila é uma ilha sofisticada. Com harness, vira **motor de simulação agéntica da Colmeia inteira**.

---

## 7. Critérios de sucesso — como saber se deu certo

Pergunte estas 6 coisas após cada Onda:

1. **Transferabilidade**: troquei o modelo base no OmniRoute e a Vila continua funcionando? (Onda 3 resolve)
2. **Manutenibilidade**: atualizei o schema da matéria e só uma capability card mudou? (Onda 3 resolve)
3. **Recuperação**: um step falhou — rollback em < 5s? (Onda 1 expõe; Snapshot já resolve)
4. **Eficiência de contexto**: um step médio de um agente gasta < X tokens? (Onda 2 mede)
5. **Qualidade de governança**: um artigo constitucional é testável em isolamento? (Onda 4 resolve)
6. **Observabilidade**: posso explicar **porque** o agente X tomou a decisão Y no step Z? (Onda 2 resolve)

Se 5 dos 6 estiverem ✅ depois da Onda 4, a Vila é um **harness elegante e completo**.

---

## 8. Riscos e mitigação

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| Refator quebra loop 24/7 em produção | Média | Fazer Onda 1 e 2 em branch, com shadow mode (escreve trace mas não altera comportamento) |
| Orçamento corta contexto útil | Média | Começar com orçamentos largos (2x o real observado), apertar por fase com base em métricas |
| 27 oficinas viram 27 SKILL.md e ninguém mantém | Alta | Bootstrap com gerador: script que lê `oficinas.py` e gera SKILL.md stub; humano revisa |
| Capability cards viram over-engineering | Baixa-Média | Começar com 3 cards (OmniRoute, Mirante, Supabase), provar valor, expandir |
| Constituição como policy engine perde expressividade | Baixa | Manter artigos "estruturais" (que exigem dev humano) no formato atual; só migrar operacionais e econômicos |

---

## 9. Próximos passos imediatos

Na próxima sessão, execute **Onda 1** (1-2 horas):

1. `mkdir engine/harness && echo "# Vila Harness Layer" > engine/harness/README.md`
2. Commitar este arquivo (`docs/HARNESS_VILA.md`)
3. Adicionar entry em `docs/ARCHITECTURE.md` apontando pra ele
4. Atualizar `.claude/skills/SKILLS_INDEX.md` com "harness-architect (global skill) — aplicado em HARNESS_VILA.md"
5. Criar issue no GitHub para cada Onda 2/3/4 com os checkboxes deste documento

Depois disso, abrir discussão Onda 2 (Observability) — esta é a que dá maior retorno.

---

## 10. Referência conceitual

- **Paper primário**: Zhou et al. (2026). *Externalization in LLM Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering*. arXiv:2604.08224.
- **Skill global**: `~/.claude/skills/harness-architect/` — carregada automaticamente em qualquer sessão Claude Code tocando Vila.
- **Leitura pedagógica**: `~/Downloads/harness-arquitetura-pedagogica.html`.
- **Âncoras teóricas**: Norman 1991/1993 (artefatos cognitivos), Kirsh 1995 (estratégias complementares), Hutchins 1995 (cognição distribuída), Sumers et al. 2024 (CoALA).

---

> *"A Vila já é um organismo. Este documento a ajuda a ganhar esqueleto e sistema nervoso central sem perder a alma."*
> — ONIR, aplicando harness-architect v1.1.0.
