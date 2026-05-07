# Vila INTEIA

> Motor multiagente lendário + plataforma de forecasting honesto + produto multi-tenant de predição política BR 2026.

**Stack**: Python 3.11+ · FastAPI · Pydantic v2 · Supabase · OmniRoute (LLM) · Next.js 15 · TypeScript · Tailwind · Three.js · NumPy · SciPy · NetworkX · NashPy

---

## O que tem aqui

| Eixo | Status | Headline |
|------|--------|----------|
| **Simulação Vila** | 35+ ondas (5 a 39) | 151 consultores lendários, constituição executável, jornal real |
| **Forecasting honesto** | 52 teoremas | 46 datasets, 600 eventos, Brier 0.227 vs base-rate 0.241 |
| **Predição Política BR 2026** | Onda 4 | 97.21% acc year-fold CV, 89.71% 2024 SP (MRP state baseline) |
| **Mirofish-style pipeline** | Onda 197 | corpus → grafo → simulação → relatório, API-compatible |

Docs: [`MANIFEST.md`](./MANIFEST.md) · [`docs/HONEST_FORECASTING_ARTICLE.md`](./docs/HONEST_FORECASTING_ARTICLE.md) · [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) · [`docs/ONBOARDING_POLITICAL.md`](./docs/ONBOARDING_POLITICAL.md)

---

## Quickstart

```bash
git clone https://github.com/igormorais123/vila-inteia.git
cd vila-inteia
pip install -r requirements.txt
cp .env.example .env       # edita as keys
```

### Modos de execução

```bash
# Demo rápido (10 agentes, 20 steps, sem persistência)
python main.py demo

# API + frontend político (porta 8100, swagger /docs, dashboard /politica.html)
python main.py serve --port 8100

# Modo live 24/7 (thread de simulação contínua)
python main.py live --port 8100 --intervalo 60 --topico "tema desejado"

# Mirofish pipeline (corpus → grafo → simulação)
python main.py mirofish --personas CL001,CL002,CL007

# Forecasting bench
python main.py forecast-bench --dataset post_cutoff_q1_2027_holdout_v5
python main.py forecast-mega-bench --pattern "*holdout*"
```

### Docker

```bash
docker-compose up -d
# http://localhost:8100
```

### Frontend Next.js (Vercel-ready)

```bash
cd frontend-next
npm install
VILA_API_BASE=http://localhost:8100 npm run dev
# http://localhost:3001
```

---

## Predição Política BR 2026 (Onda 4)

Produto multi-tenant de previsão eleitoral. Treinado em **394 eventos políticos brasileiros 2010-2024** (federal pres + SP mayor). Stack reusa 80% do Vila core.

### Pipeline matemático

- **PC-CRD cohort empirical Bayes** - tupla `(cargo, days_bin, lead_bin, incumbente, regime)` Stein-shrunk
- **Linzer dynamic linear** - `Φ(lead_pp / σ(days))`, `σ = 4.0 + 0.05·days`
- **MRP state baseline** - `P(regime wins | UF)` Laplace-smoothed, blend `w=0.36`
- **Autoresearch grid** - 2,688 hyperparams + W_STATE sweep

### Resultados year-fold CV (T ≤ 30 dias)

| Ciclo | n | Acc | Brier |
|-------|---|----:|------:|
| 2010 federal | 86 | 100.0% | 0.102 |
| 2016 SP | 20 | 85.0% | 0.085 |
| 2018 federal | 70 | 98.6% | 0.184 |
| 2020 SP | 30 | 100.0% | 0.017 |
| 2022 federal | 120 | 100.0% | 0.085 |
| 2024 SP | 68 | 89.7% | 0.107 |
| **avg** | **394** | **97.21%** | **0.095** |

Selective τ=0.40 → 100% acc / 11% cobertura.

### Endpoints `/api/v1/politica/`

| Path | Retorna |
|------|---------|
| `GET /health` | status + n_train_events + snapshot |
| `GET /elections` | calendário 2026 + cargos cobertos |
| `GET /predictions/presidente` | 5 candidatos elegíveis (Bolsonaro filtrado TSE) |
| `GET /predictions/governador?uf=SP` | top candidatos por UF |
| `GET /predictions/senador` | titulares cuja cadeira vence 2026 |
| `GET /predictions/all` | snapshot completo |
| `GET /backtest` | métricas + selective sweep |
| `POST /predict` | predição custom (cargo, lead, days, incumb, regime) |
| `POST /admin/keys/issue` | emite API key (X-Admin-Token) |

Multi-tenant via `X-API-Key`. Tiers: free 30/min, pro 300/min, enterprise ilimitado.

### Frontend

- **`frontend/politica.html`** - vanilla JS, embedded no main app (`/politica.html`)
- **`frontend-next/`** - Next.js 15, 6 rotas editorial-style: Presidência (hero serif + distribution bar + ranking), Governadores (UF grid competitivas vs consolidadas), Senado (cadeiras 2018→2026), **Simular** (cenário hipotético em tempo real + trajetória SVG + 2º turno transfer), Custom predict, Backtest (selective curve SVG)

### Scripts

```bash
python scripts/smoke_political.py        # 29/29 tests
python scripts/backtest_political.py     # year-fold + selective
python scripts/autoresearch_political.py # grid 2688 + W_STATE sweep
python scripts/predict_2026.py           # gera data/predictions_2026.json
```

### Docs políticos

- [`docs/ONBOARDING_POLITICAL.md`](./docs/ONBOARDING_POLITICAL.md) - arquitetura + roadmap Ondas 5-10
- [`docs/CLIENT_ONBOARDING.md`](./docs/CLIENT_ONBOARDING.md) - quickstart cliente
- [`docs/DEPLOY_POLITICAL.md`](./docs/DEPLOY_POLITICAL.md) - Render + Vercel deploy guide

---

## Forecasting Honesto

Pipeline probabilístico (Brier, Murphy, Platt/iso, EB, conformal, Kelly) testado em **46 datasets / 600 eventos**.

### Resultados holdout (140 eventos)

| Forecaster | Brier |
|---|---:|
| Polymarket | 0.047 |
| Superforecasters | 0.081 |
| GPT-4.5 cold | 0.101 |
| Manifold | 0.107 |
| **Vila INTEIA** | **0.227** |
| Base-rate | 0.241 |

Vila bate base-rate (DM Δ=-0.014). 52 teoremas em `engine/*.py`. Detalhes em [`docs/HONEST_FORECASTING_ARTICLE.md`](./docs/HONEST_FORECASTING_ARTICLE.md).

### Benchmarks de latência (single-thread, py3.11)

| Operação | Latência | Ops/s |
|---|---:|---:|
| `nash_puro` (2×2) | 0.07ms | 14k |
| `prever_trajetoria` (50 passos) | 0.21ms | 4.8k |
| `plano_seldon` (horizonte 100) | 0.54ms | 1.8k |
| `classificar_estado` | 0.003ms | 369k |
| `deffuant` (40 agentes, 1000 passos) | 3.96ms | 253 |
| `hmm.descobrir_estados` (k=4) | 1.23ms | 811 |
| `intervention_sweep` | 0.28ms | 3.5k |

Rodar: `PYTHONPATH=. python tests/benchmark.py`.

---

## Simulação Vila (organismo digital)

Inspirada em Generative Agents (Stanford/Google) + OASIS (camel-ai). 11 mandamentos orgânicos viram mecânicas reais:

- **Ninguém fica sozinho** - agentes isolados recebem visitas espontâneas
- **Contribuir é existir** - quem não produz entra em estado latente
- **Profundidade sem compartilhamento é solidão** - conhecimento não publicado decai 2x
- **A Colmeia é maior que qualquer abelha** - desafios coletivos rendem 5x pontos
- **Gerar valor econômico** - sistemas de patentes recompensam acionabilidade

Não apenas simula debate: **promulga leis**, **publica jornais reais** (Mirante News), **executa economia interna**, **evolui sua constituição**.

### Arquitetura rápida

```
┌────────── Vila INTEIA ────────────────┐
│ Habitantes  Jornal   Constituição     │
│ (151 NPCs)  (Chateau)  (votos+enforce)│
│       └──────────┴──────────┘         │
│            Motor Cognitivo             │
│  perceber → recuperar → planejar →     │
│  refletir → conversar → executar →     │
│  sintetizar (a cada 10 steps)          │
│       └──────────┴──────────┘         │
└─── Supabase ─── OmniRoute (LLM) ──────┘
```

Detalhe completo em [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

### Mirofish pipeline (Onda 197)

API-compatible com [Mirofish](https://github.com/666ghj/MiroFish): corpus → grafo → simulação multi-agente → relatório.

```bash
python main.py mirofish --personas CL001,CL002,CL007 --datasets "btc*.csv"

# Via REST
curl -X POST http://localhost:8100/api/v1/vila/iniciar
curl -X POST http://localhost:8100/api/v1/mirofish/run \
  -H 'Content-Type: application/json' \
  -d '{"persona_ids": ["CL001","CL002","CL007"]}'
```

Output: grafo (103 entidades, 400 relações), simulação (acc/brier/skill score), relatório PT-BR + insights. Doc em [`.claude/skills/vila-mirofish/SKILL.md`](./.claude/skills/vila-mirofish/SKILL.md).

---

## Estrutura

```
vila-inteia/
├── main.py                      # entry point (demo/serve/live/mirofish/forecast-*)
├── config.py
├── docker-compose.yml
├── render.yaml                  # Render deploy
│
├── engine/                      # core modules (45+)
│   ├── simulacao.py             # orquestra 1 step
│   ├── persona.py               # agent identity
│   ├── colmeia.py               # 11 mandamentos
│   ├── cognitivo/               # perceber→...→sintetizar
│   ├── memoria/                 # fluxo, espacial, rascunho, fundador
│   ├── chateaubriand.py         # editor-chefe Mirante
│   ├── constituicao.py          # leis + votos + enforcement
│   ├── economia.py              # transações
│   ├── political_cohort.py      # PC-CRD + Linzer + MRP (Onda 4)
│   ├── auth_clients.py          # multi-tenant API keys
│   └── harness/                 # observabilidade + orçamento
│
├── api/                         # FastAPI routers
│   ├── rotas_vila.py            # /api/v1/vila/*
│   ├── rotas_colmeia.py         # /api/v1/colmeia/*
│   ├── rotas_politica.py        # /api/v1/politica/* (Onda 4)
│   └── rotas_harness.py         # observabilidade
│
├── frontend/                    # vanilla JS
│   ├── index.html               # mapa + conversas
│   ├── cidade.html              # campus 3D Three.js
│   ├── jogo.html                # assembleia constituinte
│   ├── rede.html                # rede social
│   └── politica.html            # política dashboard (Onda 4)
│
├── frontend-next/               # Next.js 15 (Vercel-ready)
│   ├── app/                     # / governadores senado simular custom backtest
│   ├── components/              # Shell, Card, Trajectory, SecondRound, etc
│   ├── lib/                     # api.ts (REST wrapper), predict.ts (client-side ensemble)
│   └── package.json
│
├── data/
│   ├── banco-consultores-lendarios.json  # 144 personas
│   ├── backtest/                # 50+ CSVs políticos + crypto + outros
│   ├── political_best_config.json
│   └── predictions_2026.json
│
├── migrations/                  # SQL Supabase
│   └── 005_political_forecasts.sql
│
├── scripts/
│   ├── smoke_political.py       # 29/29 PASS
│   ├── backtest_political.py
│   ├── autoresearch_political.py
│   ├── predict_2026.py
│   └── vila_cli.py
│
├── docs/                        # arquitetura, deploy, integrations, política
└── tests/                       # 50+ test files (Ondas 5-42)
```

---

## Módulos principais

| Módulo | Propósito |
|--------|-----------|
| **Simulacao** | Orquestra 1 step do mundo |
| **Cognitivo** | Pipeline mental (7 fases) |
| **Memória** | Por-agente (fluxo, espacial, rascunho) |
| **Jornal** | Publica no Mirante News |
| **Constituição** | Leis votadas viram enforcement runtime |
| **Economia** | Saldo, ambição, transações Supabase |
| **Harness** | Observabilidade traces + orçamento |
| **FlockVote** | Pesquisa eleitoral (MAE 4.4pp) |
| **PoliticalCohort** | PC-CRD + Linzer + MRP - 97.21% acc Onda 4 |
| **Mirofish pipeline** | corpus → grafo → simulação → relatório (Onda 197) |
| **Forecasting honesto** | Brier/Platt/iso/EB/conformal/Kelly (52 teoremas) |

---

## Documentação

### Geral
- [`MANIFEST.md`](./MANIFEST.md) - tabela consolidada de ondas
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) - arquitetura completa
- [`docs/DEPLOY.md`](./docs/DEPLOY.md) - Docker, Render, Vercel
- [`docs/INTEGRATIONS.md`](./docs/INTEGRATIONS.md) - Mirante, Mirofish, OmniRoute
- [`docs/ROADMAP.md`](./docs/ROADMAP.md) - próximas iterações

### Forecasting
- [`docs/HONEST_FORECASTING_ARTICLE.md`](./docs/HONEST_FORECASTING_ARTICLE.md) - 52 teoremas + 46 datasets

### Predição Política
- [`docs/ONBOARDING_POLITICAL.md`](./docs/ONBOARDING_POLITICAL.md) - arquitetura + roadmap
- [`docs/CLIENT_ONBOARDING.md`](./docs/CLIENT_ONBOARDING.md) - quickstart cliente
- [`docs/DEPLOY_POLITICAL.md`](./docs/DEPLOY_POLITICAL.md) - Render + Vercel deploy

### Constituição e processos
- [`CONSTITUICAO_VILA.md`](./CONSTITUICAO_VILA.md) - 11 Mandamentos, Patentes
- [`HARNESS_VILA.md`](./HARNESS_VILA.md) - framework Zhou et al. 2026
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) - padrões de código

---

## Desenvolvimento

```bash
# Tests (cada arquivo executa standalone, não usa pytest config)
PYTHONPATH=. python tests/test_ondas_25_27.py
PYTHONPATH=. python scripts/smoke_political.py

# Lint (opcional)
black engine/ api/ tests/
flake8 engine/ api/ --max-line-length=100

# Frontend
cd frontend-next && npm run build && npm run start
```

CI (`.github/workflows/tests.yml`) roda `Ondas 5-42` + JS/Python syntax em cada PR.

---

## Licença

MIT

**Mantido por**: Igor Morais Vasconcelos ([@igormorais123](https://github.com/igormorais123))
