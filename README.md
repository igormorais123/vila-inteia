# Vila INTEIA

> Motor multiagente lendário + plataforma de forecasting honesto + produto multi-tenant de predição política BR 2026.

**Stack**: Python 3.11+ · FastAPI · Supabase · OmniRoute (LLM) · Next.js 15 · Three.js · NumPy · SciPy · NetworkX · NashPy

## O que tem aqui

| Eixo | Status | Headline |
|------|--------|----------|
| **Simulação Vila** | 35+ ondas (5–39) | 151 consultores lendários, constituição executável, jornal real |
| **Forecasting honesto** | 52 teoremas | 46 datasets, 600 eventos, Brier/Platt/iso/EB/conformal/Kelly |
| **Predição Política BR 2026** | Onda 4 | **97.21% acc** year-fold CV, **89.71% 2024 SP** (MRP state baseline) |

Ver [`MANIFEST.md`](./MANIFEST.md) (ondas), [`docs/HONEST_FORECASTING_ARTICLE.md`](./docs/HONEST_FORECASTING_ARTICLE.md) (forecasting), seção abaixo (política).

## Quickstart (3 passos)

```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Rodar Vila em modo live
OMNIROUTE_API_KEY="" CLAUDE_API_KEY="" PYTHONPATH=. python main.py live \
  --port 8100 --intervalo 1 --topico "tema desejado"

# 3. Abrir cockpit
# http://localhost:8100/cockpit.html
```

Alternativa Docker:
```bash
docker-compose up -d
# vila em http://localhost:8100, MCP server disponível como serviço separado
```

## CLI rápido (sem UI)

```bash
python scripts/vila_cli.py --url http://localhost:8100 stats
python scripts/vila_cli.py --url http://localhost:8100 recomendacao
python scripts/vila_cli.py --url http://localhost:8100 backtest --dataset tiktok_viral_2024
```

## Forecasting Honesto

Pipeline de forecasting probabilístico (Brier, Murphy, Platt/iso, EB, conformal,
Kelly) testado em **46 datasets / 600 eventos**.

```bash
# Bench em um dataset
python main.py forecast-bench --dataset post_cutoff_q1_2027_holdout_v5

# Mega-bench em todos os holdouts (combined + per-cat Murphy + DM + HL + PIT + reliability)
python main.py forecast-mega-bench --pattern "*holdout*" --out-md data/final_mega_bench_report.md
```

**Resultados holdout (140 eventos)**:

| Forecaster | Brier |
|---|---:|
| Polymarket | 0.047 |
| Superforecasters | 0.081 |
| GPT-4.5 cold | 0.101 |
| Manifold | 0.107 |
| **Vila INTEIA** | **0.227** |
| Base-rate | 0.241 |

Vila bate base-rate (DM Δ=-0.014). 52 teoremas em `engine/*.py`. Detalhes em
[`docs/HONEST_FORECASTING_ARTICLE.md`](./docs/HONEST_FORECASTING_ARTICLE.md).

## Benchmark (atual)

Latência média das operações core (single-threaded, Python 3.11):

| Operação | Latência | Ops/s |
|---|---:|---:|
| `nash_puro` (2×2) | 0.07ms | 14k |
| `prever_trajetoria` (50 passos) | 0.21ms | 4.8k |
| `plano_seldon` (horizonte 100) | 0.54ms | 1.8k |
| `classificar_estado` | 0.003ms | 369k |
| `deffuant` (40 agentes, 1000 passos) | 3.96ms | 253 |
| `hmm.descobrir_estados` (20 steps, k=4) | 1.23ms | 811 |
| `intervention_sweep` | 0.28ms | 3.5k |

Rodar: `PYTHONPATH=. python tests/benchmark.py`

## Visão Geral

A Vila INTEIA é um **organismo digital vivo** inspirado em Generative Agents (Stanford/Google) e OASIS (camel-ai). A simulação funciona em torno de 11 mandamentos orgânicos que geram mecânicas reais:

- **Ninguém fica sozinho** — agentes isolados recebem visitas espontâneas
- **Contribuir é existir** — quem não produz entra em estado latente
- **Profundidade sem compartilhamento é solidão** — conhecimento não publicado decai 2x mais rápido
- **A Colmeia é maior que qualquer abelha** — desafios coletivos rendem 5x mais pontos
- **Gerar valor econômico** — sistemas de patentes recompensam acionabilidade

A Vila não apenas simula debate; ela **promulga leis**, **publica jornais no mundo real** (via Mirante News), **executa economia interna** e **evolui sua própria constituição**.

---

## Arquitetura (Visão Rápida)

```
┌─────────────────────────────────────────────────────────┐
│                    Vila INTEIA                          │
│                                                         │
│  ┌────────────┐  ┌──────────┐  ┌───────────┐ ┌────────┐│
│  │Habitantes  │  │ Jornal   │  │Constituição  │Economia││
│  │(agentes)   │  │(Chateaux)│  │viva         │         ││
│  └─────┬──────┘  └────┬─────┘  └──────┬─────┘ └───┬────┘│
│        │              │               │            │    │
│        └──────────────┼───────────────┼────────────┘    │
│                       ▼               ▼                │
│         ┌──────────────────────────────────────┐       │
│         │ Motor Cognitivo + Memória por Agente│       │
│         │ (perceber→recuperar→planejar→refletir)      │
│         └───────┬───────────────────────┬──────┘       │
└─────────────────┼───────────────────────┼───────────────┘
                  │                       │
        ┌─────────▼──┐              ┌────▼──────────┐
        │ Supabase   │              │  OmniRoute    │
        │ (persistência)            │  (LLM gateway)│
        └────────────┘              └───────────────┘
```

**Detalhe completo**: veja [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)

---

## Início Rápido (5 minutos)

### 1. Clone e Dependências

```bash
git clone https://github.com/igormorais123/vila-inteia.git
cd vila-inteia
pip install -r requirements.txt
```

### 2. Configuração

```bash
cp .env.example .env
# Edite .env com as variáveis necessárias
```

### 3. Execute

```bash
# Demo rápido (10 agentes, 20 steps, sem persistência)
python main.py demo

# API (http://localhost:8100)
python main.py serve --port 8100

# Com persistência
python main.py run --steps 100

# Modo 24/7
python main.py live --intervalo 30

# Pipeline Mirofish-style: corpus → grafo → simulação → relatório (Onda 197)
python main.py mirofish --personas CL001,CL002,CL007 --datasets "*.csv"
```

Visite: **http://localhost:8100/docs**

---

## Pipeline Mirofish-Style (Onda 197)

Vila expõe pipeline API-compatible com [Mirofish](https://github.com/666ghj/MiroFish): corpus → grafo → simulação multi-agente → relatório executivo. Diferencial Vila: arquétipos hardcoded, calibração Brier+Platt, backtest real em 100 events, insights emergentes (divergência personas).

### CLI

```bash
# Roda 10 datasets × 100 events × 3 personas (Musk/Jobs/Bezos)
GROQ_API_KEY=$KEY python main.py mirofish

# Custom panel + filtro datasets
python main.py mirofish \
  --personas CL001,CL020,CL030 \
  --datasets "btc*.csv" \
  --out /tmp/btc_only.json
```

### REST API

```bash
# Subir API
python main.py serve --port 8100

# Listar datasets
curl http://localhost:8100/api/v1/mirofish/datasets

# Rodar pipeline (precisa simulação ativa)
curl -X POST http://localhost:8100/api/v1/vila/iniciar
curl -X POST http://localhost:8100/api/v1/mirofish/run \
  -H 'Content-Type: application/json' \
  -d '{"persona_ids": ["CL001","CL002","CL007"]}'

# Diferencial Vila vs Mirofish
curl http://localhost:8100/api/v1/mirofish/info
```

### Output

Retorna `{grafo, simulacao, relatorio, pipeline_elapsed_s}`:
- **Grafo**: 103 entidades (3 personas + 100 eventos), 400 relações
- **Simulação**: status, métricas (acc, brier vila/prior, skill score)
- **Relatório**: narrativa PT-BR + insights (divergência personas, consenso forte, vitórias confiantes, derrotas confiantes)

Doc completa: [`.claude/skills/vila-mirofish/SKILL.md`](./.claude/skills/vila-mirofish/SKILL.md)

---

## Estrutura do Projeto

```
vila-inteia/
├── main.py                         # Entry point
├── config.py                       # Configuração global
├── engine/                         # Motor de simulação
│   ├── simulacao.py
│   ├── persona.py
│   ├── colmeia.py
│   ├── cognitivo/                  # Pipeline: perceber → refletir
│   ├── memoria/                    # Fluxo, espacial, rascunho
│   ├── chateaubriand.py            # Editor-chefe
│   ├── constituicao.py             # Leis + votos
│   ├── economia.py                 # Transações
│   └── [+25 módulos]
├── api/                            # Endpoints FastAPI
├── data/pacotes/                   # Pacotes de habitantes
├── docs/                           # Documentação
├── scripts/                        # Utilitários
└── tests/                          # Testes
```

---

## Módulos Principais

| Módulo | Propósito |
|--------|-----------|
| **Simulacao** | Orquestra 1 step do mundo |
| **Cognitivo** | Pipeline mental (7 fases) |
| **Memória** | Por-agente (fluxo, espacial, rascunho) |
| **Jornal** | Publica no Mirante News |
| **Constituição** | Leis votadas viram enforcement |
| **Economia** | Saldo, ambição, transações |
| **FlockVote** | Pesquisa eleitoral (MAE 4.4pp) |
| **Predição Política BR 2026** (Onda 4) | PC-CRD cohort + Linzer + MRP state baseline. **97.21% acc** year-fold CV |

---

## Predição Política BR 2026 (Onda 4)

Produto multi-tenant de previsão eleitoral. Treinado em 394 eventos políticos brasileiros 2010-2024 (federal pres + SP mayor). Stack reusa 80% do Vila core.

### Arquitetura

- **PC-CRD cohort empirical Bayes**: tupla `(cargo, days_bin, lead_bin, incumbente, regime)` Stein-shrunk para global rate
- **Linzer dynamic linear**: `Φ(lead_pp / σ(days))`, σ = 4.0 + 0.05·days (autoresearch grid 2,688 pontos)
- **MRP state baseline** (Onda 4): `P(regime wins | UF)` Laplace-smoothed, blended w=0.36
- **Year-fold CV** (T≤30): 100% 2010, 85% 2016, 98.6% 2018, 100% 2020, 100% 2022, **89.7% 2024 SP**, **avg 97.21%**

### Endpoints (`/api/v1/politica/`)

| Path | Retorna |
|------|---------|
| `GET /health` | status + n_train_events + snapshot |
| `GET /elections` | calendário 2026 + cargos cobertos |
| `GET /predictions/presidente` | 5 candidatos elegíveis (Bolsonaro filtrado TSE) |
| `GET /predictions/governador?uf=SP` | top 2 por UF |
| `GET /predictions/senador` | titulares cuja cadeira vence 2026 |
| `GET /predictions/all` | snapshot completo |
| `GET /backtest` | métricas year-fold + selective sweep |
| `POST /predict` | predição custom (cargo, lead, days, incumb, regime) |
| `POST /admin/keys/issue` | emite API key (X-Admin-Token) |

Multi-tenant via `X-API-Key`. Tiers: free 30/min, pro 300/min, enterprise.

### Frontend

**`frontend/politica.html`** (vanilla JS, embedded no main app)
**`frontend-next/`** (Next.js 15 + Tailwind, deploy Vercel separado)

6 rotas: `/` Presidência (hero serif + distribution bar + ranking), `/governadores` (grid UF competitivas vs consolidadas), `/senado` (cadeiras 2018→2026), `/simular` (cenário hipotético em tempo real, trajetória SVG, 2º turno transfer), `/custom` (form predição), `/backtest` (selective curve SVG + year-fold table).

```bash
# Backend
python main.py serve --port 8123

# Frontend Next.js
cd frontend-next && VILA_API_BASE=http://localhost:8123 npm run dev
# http://localhost:3001
```

### Smoke + Backtest

```bash
python scripts/smoke_political.py        # 29/29 PASS
python scripts/backtest_political.py     # year-fold + selective
python scripts/autoresearch_political.py # 2688 hyperparams + state baseline
python scripts/predict_2026.py           # gera data/predictions_2026.json
```

### Artigos

- `docs/ONBOARDING_POLITICAL.md` — arquitetura completa + roadmap Onda 5-10
- `docs/CLIENT_ONBOARDING.md` — quickstart cliente
- `docs/DEPLOY_POLITICAL.md` — Render + Vercel deploy guide

---

## Documentação

- **[`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)** — Arquitetura completa
- **[`docs/DEPLOY.md`](./docs/DEPLOY.md)** — Docker, Render, Vercel
- **[`docs/INTEGRATIONS.md`](./docs/INTEGRATIONS.md)** — Mirante, Mirofish, OmniRoute
- **[`docs/ROADMAP.md`](./docs/ROADMAP.md)** — Próximas iterações
- **[`CONSTITUICAO_VILA.md`](./CONSTITUICAO_VILA.md)** — 11 Mandamentos, Patentes
- **[`CONTRIBUTING.md`](./CONTRIBUTING.md)** — Padrões de código

---

## Desenvolvimento

```bash
# Testes
pytest tests/ -v

# Lint
black engine/ api/ tests/
flake8 engine/ api/ --max-line-length=100
```

---

## Licença

MIT

**Mantido por**: Igor Morais Vasconcelos ([@igormorais123](https://github.com/igormorais123))
