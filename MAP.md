# Vila INTEIA — Mapa Estrutural

> Mapa visual de tudo o que existe no repositório. Para detalhes, ver [`INDEX.md`](INDEX.md) e [`MANIFEST.md`](MANIFEST.md).
> Última atualização: 2026-05-05 (onda 289).

## Árvore raiz

```
vila-inteia/
├── api/                       # 13 arquivos rotas_*.py — endpoints FastAPI
├── engine/                    # 16 submódulos — núcleo de simulação e forecasting
├── frontend/                  # 18 páginas HTML interativas
├── scripts/                   # 31 utilitários CLI + daemons + deploy
├── tests/                     # 167 arquivos de teste
├── docs/                      # 24 .md + 5 artigos HTML + openapi.json
├── data/                      # estado persistente + datasets backtest
├── migrations/                # 4 migrações SQL Supabase
├── sql/                       # esquema base não migracional
├── main.py                    # entrypoint FastAPI
├── config.py                  # configuração central
├── docker-compose.yml         # orquestração local
├── Dockerfile                 # imagem Vila
├── render.yaml                # deploy Render
├── requirements.txt           # deps Python 3.11
├── VERSION                    # 1.0.0
├── INDEX.md                   # índice mestre (este projeto)
├── MAP.md                     # este arquivo
├── MANIFEST.md                # tabela canônica das ondas
├── CHANGELOG.md               # histórico de versões
├── README.md                  # quickstart
├── CONTRIBUTING.md            # guia contribuição
├── CONSTITUICAO_VILA.md       # doutrina + 7 mandamentos
├── FRAMEWORK_INTERACOES.md    # modelo de interações
├── HARNESS_VILA.md            # harness completo
├── HARNESS_VILA_FUNCIONAL.md  # operações + KPIs
└── HARNESS_VILA_VIVENCIAL.md  # jornada do usuário
```

## engine/ — núcleo (16 submódulos)

```
engine/
├── game_theory/               # Nash (puro/misto), Stackelberg, VCG, replicator, ESS, Schelling, Ostrom
│   ├── equilibrio.py          # 7 submódulos
│   ├── mecanismos.py
│   ├── jogos_repetidos.py
│   ├── evolutivo.py
│   ├── coordenacao.py
│   ├── bem_comum.py
│   └── hmm.py
│
├── opinion_dynamics/          # DeGroot, bounded confidence, cascatas, bayesiano (6 submódulos)
│
├── simulacao_avancada/        # Campus 3D, coalizões, redes, info imperfeita (7 submódulos)
│
├── psicohistoria/             # Asimov-style — grafo Markov + Plano Seldon (9 módulos)
│   ├── detector_estado_vila.py
│   ├── calibracao_online.py   # MLE/Laplace/EWMA
│   ├── persistencia.py        # Supabase
│   ├── hmm_estados.py         # K-Means + smoothing
│   ├── decision_helper.py     # Helena hook
│   ├── auto_calibrador.py
│   ├── replay.py
│   ├── tuner_classificador.py
│   └── ...
│
├── backtest/                  # Forecasting + validação histórica (46+ datasets, 600 eventos)
│   ├── runner.py              # orquestrador
│   ├── metricas.py            # Brier, Murphy, skill, BSS
│   ├── calibracao.py          # Platt, Isotonic, Empirical Bayes
│   └── dataset.py
│
├── memoria/                   # GraphRAG nativo + indexação fluxo
│   ├── grafo.py
│   ├── espacial.py
│   ├── fluxo.py
│   └── fundador.py
│
├── causalidade/               # Pearl do-calculus
│   └── pearl.py               # intervir, counterfactual, ATE, sweep
│
├── comparativo/               # A/B + Diebold-Mariano + McNemar
│
├── distribuido/               # Ray actors + vLLM (skeleton para scale)
│
├── mcp_server/                # Claude MCP (15+ tools expostas)
│
├── cognitivo/                 # Pipeline cognitivo: conversar → crença → executar
│
├── plataformas/               # Twitter/Reddit/LinkedIn/TikTok sintéticos + spillover
│
├── skills_oficinas/           # Centros: laboratório, torre estratégia, tribunal
│
├── proveniencia/              # Hash blockchain-style + integridade
│
├── harness/                   # Observabilidade, orçamento, skill registry
│
└── agentes_vivos/             # Helena (estratégia) + Efesto (CTO) — heartbeat 24/7
```

## api/ — endpoints (13 arquivos)

```
api/
├── rotas_vila.py              # /api/v1/vila/*           — sim core
├── rotas_psicohistoria.py     # /api/v1/psicohistoria/*  — Markov + Plano Seldon
├── rotas_gametheory.py        # /api/v1/gametheory/*     — Nash, Stackelberg
├── rotas_proveniencia.py      # /api/v1/materia,backtest/* — hash + datasets
├── rotas_colmeia.py           # /api/v1/colmeia/*        — ranking, NPCs
├── rotas_grafo.py             # /api/v1/grafo/*          — export, stats
├── rotas_harness.py           # /api/v1/harness/*        — traces, saúde
├── rotas_health.py            # /livez, /readyz           — K8s probes
├── rotas_llm.py               # /api/v1/llm/*            — cache, budget
├── rotas_metrics.py           # /metrics                  — Prometheus
├── rotas_mirofish.py          # /api/v1/mirofish/*       — pipeline corpus
├── rotas_rede_social.py       # /api/v1/rede/*           — feed, trending
└── rotas_vivos.py             # /api/v1/agentes-vivos/*  — Helena/Efesto
```

## frontend/ — UI (18 páginas)

```
frontend/
├── index.html                 # landing + links
├── cockpit.html               # painel central (Onda 32)
├── super_intelligence.html    # God's Eye meta-análise (Onda 81)
├── psico_live.html            # estado psico live (Onda 12)
├── psico_avancado.html        # análise avançada (Onda 17)
├── psicohistoria.html         # psico-história plena
├── backtest.html              # comparativo + reliability (Onda 27)
├── grafo.html                 # force-directed (Onda 38)
├── cidade.html                # mapa 3D campus
├── jogo.html                  # interface de jogo
├── rede.html                  # feed social sintético
├── coalizoes.html             # coalizões dinâmicas
├── gametheory.html            # solver UI matriz payoffs
├── mirofish_plus.html         # pipeline Mirofish
├── opinioes.html              # grafo opiniões
├── dashboard.html             # KPIs JSON
├── llm_stats.html             # cache + budget LLM (Onda 65)
└── banco-consultores-lendarios.json  # 151 consultores
```

## Fluxo de dados (alto nível)

```
                ┌─────────────────────────────────────────┐
                │  USUÁRIO / AGENTE EXTERNO               │
                │  (UI, MCP client, CLI, webhook)          │
                └────────────────┬────────────────────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  │      api/ (FastAPI)         │
                  │  rotas_*.py — 45+ endpoints │
                  └──────────────┬──────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐       ┌───────────────┐       ┌────────────────┐
│ engine/       │       │ engine/       │       │ engine/        │
│ simulacao_    │       │ psicohistoria │       │ backtest +     │
│ avancada/     │◄─────►│ + cognitivo/  │◄─────►│ forecasting/   │
│ (Vila core)   │       │ (estados)     │       │ (calibração)   │
└──────┬────────┘       └──────┬────────┘       └───────┬────────┘
       │                       │                        │
       │     ┌─────────────────┴────────┐               │
       │     │ engine/game_theory/      │               │
       │     │ + opinion_dynamics/      │               │
       │     │ + causalidade/           │               │
       │     │ (matemática formal)      │               │
       │     └──────────────────────────┘               │
       │                                                │
       └────────────────────┬───────────────────────────┘
                            │
                ┌───────────┴────────────┐
                │ engine/memoria/        │
                │ (GraphRAG + fluxo)     │
                └───────────┬────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Supabase   │     │ data/events │     │ data/backtest/  │
│ (conecta-   │     │ (JSONL log) │     │ (datasets reais)│
│  2026)      │     │             │     │                 │
└─────────────┘     └─────────────┘     └─────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ engine/agentes_vivos/  (Helena + Efesto, heartbeat 24/7) │
│ engine/harness/        (observabilidade + orçamento)     │
│ engine/mcp_server/     (Claude tools, 15+)               │
│ engine/plataformas/    (redes sociais sintéticas)        │
└──────────────────────────────────────────────────────────┘
```

Detalhes em [`docs/FLUXO_DADOS.md`](docs/FLUXO_DADOS.md) (1.5k linhas).

## docs/ — documentação (24 .md)

```
docs/
├── ARCHITECTURE.md            # alto nível
├── FLUXO_DADOS.md             # fluxo completo (65 KB)
├── REFERENCIA_TECNICA.md      # ref técnica (1262 linhas)
├── ROADMAP.md                 # plano futuro
├── DEPLOY.md                  # produção
├── USAR_LLM.md                # Groq/Gemini/Claude
├── INTEGRATIONS.md            # APIs externas
├── EVOLUCAO_GENOMAS.md        # NPCs evolutivos
├── API_COLMEIA.md             # API doutrina
├── API_COLMEIA_QUICKSTART.md
├── AUTORESEARCH_PROGRAM.md
├── HONEST_FORECASTING_ARTICLE.md
├── PLANO_IMPLEMENTACAO.md
├── PLANO_ONDA10_GAME_THEORY.md
├── PLANO_REFORMA_VILA.md
├── PLANO_SUPERA_MIROFISH.md
├── ONDA133_VALIDATION.md
├── onda284_hybrid_geopolitica_historico.md
├── onda286_replicacao_n30.md
├── openapi.json               # OpenAPI 3.0 (184 KB)
└── artigo/
    ├── vila_inteia_artigo.html              # v1
    ├── vila_inteia_artigo_v2_ondas_11_a_20.html
    ├── vila_inteia_artigo_v3_ondas_22_a_33.html
    ├── vila_inteia_artigo_v4_ondas_34_a_51.html
    ├── vila_inteia_nature.html              # Nature-style
    └── build.sh
```

## Linha do tempo de ondas (5 → 289)

Resumo. Detalhamento em [`MANIFEST.md`](MANIFEST.md) e [`CHANGELOG.md`](CHANGELOG.md).

```
┌─────────────────────────────────────────────────────────────────────┐
│  Ondas 5–39  (v1.0.0 — Fundação)                                    │
│  Proveniência, GraphRAG, MCP, fundamentos formais (game theory,     │
│  opinion dynamics), psico-história, calibração online, UI cockpit,  │
│  causalidade Pearl, A/B comparativo, CLI, event-sourcing, MANIFEST. │
│  Marcos: artigo v1, v2, v3 publicados. 38 ondas em 13 PRs.          │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Ondas 40–100  (v1.1 — Escala + Validação)                          │
│  Docker, Prometheus, E2E Playwright, auth + rate-limit, OmniRoute,  │
│  Groq, budget LLM, /super-intelligence, /persona-chat, /panel-chat, │
│  PDF export, history persistence, /livez /readyz, backtest worker,  │
│  reliability diagram, cross-validation, webhook alerts.             │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Ondas 101–200  (v1.2 — Ensemble + AutoResearch)                    │
│  Bootstrap CI, isotonic, BSS, datasets BR, ensemble weighted,       │
│  bayesian blend, self-consistency, adversarial+judge, conformal     │
│  prediction, multi-model ensemble, Karpathy autoresearch loop,      │
│  meta-autoresearch, Mirofish-style pipeline, model rotation.        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Ondas 201–289  (v1.3 — Forecasting Honesto + Hybrid)               │
│  A11y boost, claude_motor sem lookup padrão, factor models          │
│  (MOMENTUM, Bollinger, Ichimoku), post-cutoff classifier 75%,       │
│  stacking ensemble, hold-out Q2 2026 (90% acc), conformal,          │
│  Empirical Bayes, Lindy, PIT, Hosmer-Lemeshow, Hedge/AdaHedge,      │
│  selective forecasting, mega-bench routed, Manifold integration,    │
│  LLM forecaster (Claude OAuth), Vila+LLM hybrid, Diebold-Mariano    │
│  formal p<0.01, BTC cohort, ETH cross-asset, autoroute por domínio. │
└─────────────────────────────────────────────────────────────────────┘
```

## Estatísticas (5/5/2026)

| Métrica | Valor |
|---|---|
| Versão estável | 1.0.0 (20/04/2026) |
| Última onda | 289 (5/5/2026, PR #221) |
| Total de ondas | 285 (com lacunas em 40-50, 73-74, 244, 246) |
| Submódulos engine/ | 16 |
| Endpoints API | 45+ (13 arquivos rotas_*.py) |
| Páginas frontend | 18 |
| Scripts CLI | 31 |
| Arquivos de teste | 167 |
| Datasets backtest | 46+ (600 eventos forecasting, 197 backtest) |
| Documentos .md | 24 (em docs/) + 9 top-level |
| Artigos científicos | 5 HTML (v1–v4 + Nature) |
| Consultores Lendários | 151 (genomas + skill matrix) |
| PRs órfãos fechados (5/5) | 24 (saneamento v1.1) |

## Convenções de leitura deste mapa

- `▼` = fluxo de dependência ou tempo
- `◄─►` = comunicação bidirecional entre módulos
- Caminhos relativos à raiz `vila-inteia/`
- Nomes em monoespaçado = arquivos/pastas reais; em itálico = conceitos
