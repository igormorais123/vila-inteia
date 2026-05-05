# Vila INTEIA — Índice Mestre

> Ponto de entrada único. Use este arquivo para encontrar qualquer coisa no projeto sem precisar abrir 20 abas.
> Última atualização: 2026-05-05 (onda 289).

## Para começar (30 segundos)

| Quero... | Vá para |
|---|---|
| Subir o projeto local | [`README.md`](README.md) — Quickstart 3 passos |
| Entender a arquitetura | [`MAP.md`](MAP.md) + [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Ver o que existe (lista exaustiva) | [`MANIFEST.md`](MANIFEST.md) |
| Ler o histórico de versões | [`CHANGELOG.md`](CHANGELOG.md) |
| Contribuir código | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Operar em produção | [`docs/DEPLOY.md`](docs/DEPLOY.md) |

## Documentos por papel

### Desenvolvedor novo
1. [`README.md`](README.md) — quickstart
2. [`MAP.md`](MAP.md) — mapa visual da árvore
3. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — visão de alto nível
4. [`docs/FLUXO_DADOS.md`](docs/FLUXO_DADOS.md) — fluxo de dados completo (1.5k linhas)
5. [`docs/REFERENCIA_TECNICA.md`](docs/REFERENCIA_TECNICA.md) — referência técnica detalhada
6. [`CONTRIBUTING.md`](CONTRIBUTING.md) — workflow git, testes, code review

### Quer entender o produto
1. [`CONSTITUICAO_VILA.md`](CONSTITUICAO_VILA.md) — doutrina + 7 mandamentos + 151 lendários
2. [`FRAMEWORK_INTERACOES.md`](FRAMEWORK_INTERACOES.md) — modelo de interações
3. [`HARNESS_VILA.md`](HARNESS_VILA.md) — harness completo (técnico + vivencial + funcional)
4. [`HARNESS_VILA_VIVENCIAL.md`](HARNESS_VILA_VIVENCIAL.md) — jornada do usuário
5. [`HARNESS_VILA_FUNCIONAL.md`](HARNESS_VILA_FUNCIONAL.md) — operações + KPIs

### Operação / deploy
1. [`docs/DEPLOY.md`](docs/DEPLOY.md) — Render + K8s + systemd
2. [`docs/USAR_LLM.md`](docs/USAR_LLM.md) — configurar Groq/Gemini/Claude
3. [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md) — APIs externas
4. [`render.yaml`](render.yaml) + [`docker-compose.yml`](docker-compose.yml) + [`Dockerfile`](Dockerfile)

### Pesquisador / leitura científica
1. [`docs/artigo/vila_inteia_artigo.html`](docs/artigo/vila_inteia_artigo.html) — v1 (Ondas 5-10)
2. [`docs/artigo/vila_inteia_artigo_v2_ondas_11_a_20.html`](docs/artigo/vila_inteia_artigo_v2_ondas_11_a_20.html)
3. [`docs/artigo/vila_inteia_artigo_v3_ondas_22_a_33.html`](docs/artigo/vila_inteia_artigo_v3_ondas_22_a_33.html)
4. [`docs/artigo/vila_inteia_artigo_v4_ondas_34_a_51.html`](docs/artigo/vila_inteia_artigo_v4_ondas_34_a_51.html)
5. [`docs/artigo/vila_inteia_nature.html`](docs/artigo/vila_inteia_nature.html) — Nature-style revisado
6. [`docs/HONEST_FORECASTING_ARTICLE.md`](docs/HONEST_FORECASTING_ARTICLE.md) — forecasting honesto
7. [`docs/onda284_hybrid_geopolitica_historico.md`](docs/onda284_hybrid_geopolitica_historico.md) — LLM bate Vila
8. [`docs/onda286_replicacao_n30.md`](docs/onda286_replicacao_n30.md) — replicação confirmatória

### Agente IA trabalhando aqui
1. [`MAP.md`](MAP.md) — leia primeiro para orientação
2. [`MANIFEST.md`](MANIFEST.md) — tabela canônica de ondas
3. [`docs/REFERENCIA_TECNICA.md`](docs/REFERENCIA_TECNICA.md) — APIs, schemas, tipos
4. [`CONTRIBUTING.md`](CONTRIBUTING.md) — padrões obrigatórios

## Mapa rápido por código

### Backend (`api/`, `engine/`)
| Quero... | Pasta | Arquivo principal |
|---|---|---|
| Adicionar endpoint novo | `api/` | `api/rotas_*.py` (13 arquivos) |
| Lógica de simulação central | `engine/simulacao_avancada/` | `simulador.py` |
| Game theory (Nash, VCG, etc.) | `engine/game_theory/` | 7 submódulos |
| Dinâmica de opinião (DeGroot, etc.) | `engine/opinion_dynamics/` | 6 submódulos |
| Psico-história (Markov, Plano de Seldon) | `engine/psicohistoria/` | 9 módulos |
| Backtest / Forecasting | `engine/backtest/` | `runner.py`, `metricas.py` |
| Calibração (Platt, Isotonic, EB) | `engine/backtest/calibracao.py` | + `engine/psicohistoria/calibracao_online.py` |
| Causalidade Pearl | `engine/causalidade/pearl.py` | do-calculus, ATE |
| GraphRAG / memória | `engine/memoria/grafo.py` | nativo |
| MCP server (Claude tools) | `engine/mcp_server/` | 15+ tools |
| Pipeline cognitivo | `engine/cognitivo/` | conversar, crença, executar |
| Plataformas sociais sintéticas | `engine/plataformas/` | orquestrador.py |
| Agentes vivos (Helena, Efesto) | `engine/agentes_vivos/` | helena.py, efesto.py |
| Harness (observabilidade, orçamento) | `engine/harness/` | observabilidade.py |

### Frontend (`frontend/`)
| Quero... | Página |
|---|---|
| Painel central de monitoramento | [`cockpit.html`](frontend/cockpit.html) |
| God's Eye (meta-análise) | [`super_intelligence.html`](frontend/super_intelligence.html) |
| Mapa 3D do campus | [`cidade.html`](frontend/cidade.html) |
| Estado psico-histórico live | [`psico_live.html`](frontend/psico_live.html) |
| Backtest comparativo | [`backtest.html`](frontend/backtest.html) |
| Grafo de conhecimento | [`grafo.html`](frontend/grafo.html) |
| Game theory solver UI | [`gametheory.html`](frontend/gametheory.html) |
| Pipeline Mirofish | [`mirofish_plus.html`](frontend/mirofish_plus.html) |
| Feed social sintético | [`rede.html`](frontend/rede.html) |
| Stats LLM (cache/budget) | [`llm_stats.html`](frontend/llm_stats.html) |

### Scripts (`scripts/`)
| Quero... | Script |
|---|---|
| CLI principal Vila | [`scripts/vila_cli.py`](scripts/vila_cli.py) |
| Mega-bench forecasting | `scripts/run_n100_pipeline.py` + `forecast-mega-bench` |
| Benchmark multi-modelo LLM | [`scripts/benchmark_models.py`](scripts/benchmark_models.py) |
| Backtest worker (daemon) | [`scripts/backtest_worker.py`](scripts/backtest_worker.py) |
| Gerar relatório backtest | [`scripts/gerar_relatorio_backtest.py`](scripts/gerar_relatorio_backtest.py) |
| AutoResearch loop | [`scripts/autoresearch_vila.py`](scripts/autoresearch_vila.py) |
| Diebold-Mariano test | [`scripts/onda287_dm_test_llm_vs_vila.py`](scripts/onda287_dm_test_llm_vs_vila.py) |
| Backup Supabase | [`scripts/vila_backup.py`](scripts/vila_backup.py) |

### Testes (`tests/`)
167 arquivos. Para rodar tudo: `pytest tests/`. Categorias principais:
- **Forecasting/Backtest** (20): `test_backtest_*`, `test_calibracao_*`, `test_conformal*`
- **Game Theory** (15): `test_nash*`, `test_stackelberg`, `test_replicator`
- **Estatística** (35): `test_brier_*`, `test_diebold_mariano`, `test_hosmer_lemeshow`, `test_pit_*`
- **LLM** (12): `test_llm_judge`, `test_claude_motor`, `test_helena_*`
- **E2E** (10): `test_e2e_playwright`, `test_e2e_pipeline`
- **Benchmark perf**: [`tests/benchmark.py`](tests/benchmark.py)

## Bancos de dados

- **Supabase** (`conecta-2026`) — produção, persistência principal
- **Schema**: [`sql/`](sql/) (definições) + [`migrations/`](migrations/) (4 migrações versionadas)
- **JSONL local** — event-sourcing append-only em `data/events/`
- **Datasets backtest** — [`data/backtest/`](data/backtest/) (versionado, 46+ datasets, 600 eventos)

## Endpoints API (45+)

Lista completa em [`docs/openapi.json`](docs/openapi.json). Resumo por arquivo de rota:

| Arquivo | Prefixo | O que expõe |
|---|---|---|
| `rotas_vila.py` | `/api/v1/vila/*` | Iniciar/step/estado/mapa simulação |
| `rotas_psicohistoria.py` | `/api/v1/psicohistoria/*` | Grafo Markov, prever, Plano Seldon, calibrar |
| `rotas_gametheory.py` | `/api/v1/gametheory/*` | Nash, Stackelberg, replicator, torneio |
| `rotas_proveniencia.py` | `/api/v1/materia|backtest/*` | Hash, datasets, rodar backtest |
| `rotas_colmeia.py` | `/api/v1/colmeia/*` | Ranking, estado, NPC genoma |
| `rotas_grafo.py` | `/api/v1/grafo/*` | Export, stats centrality |
| `rotas_harness.py` | `/api/v1/harness/*` | Saúde, traces |
| `rotas_health.py` | `/livez`, `/readyz` | K8s probes |
| `rotas_llm.py` | `/api/v1/llm/*` | Cache stats, budget |
| `rotas_metrics.py` | `/metrics` | Prometheus exposition |
| `rotas_mirofish.py` | `/api/v1/mirofish/*` | Pipeline corpus → grafo → sim |
| `rotas_rede_social.py` | `/api/v1/rede/*` | Feed, post, trending, tema |
| `rotas_vivos.py` | `/api/v1/agentes-vivos/*` | Status Helena/Efesto, heartbeat |

## Operação

| Comando | O que faz |
|---|---|
| `docker-compose up` | Sobe Vila + MCP + healthcheck |
| `python main.py` | API local em `:8100` |
| `python scripts/vila_cli.py --help` | CLI |
| `pytest tests/` | Roda os 167 testes |
| `pytest tests/benchmark.py` | Roda benches de performance |
| `python scripts/run_n100_pipeline.py` | Mega-bench forecasting |
| `bash scripts/uptime_check.sh` | Health check (systemd-friendly) |

## Triagem e saneamento

- [`TRIAGEM_PRS_2026-05-05.md`](TRIAGEM_PRS_2026-05-05.md) — triagem dos PRs órfãos da v1.0 (24 fechados em 5/5/2026)

## Convenções

- **Idioma**: português brasileiro (código com termos técnicos em inglês onde padrão).
- **Versionamento**: SemVer. Tag estável: `v1.0.0` (20/04/2026).
- **Numeração de ondas**: contínua desde a 5. Cada onda = 1 PR (ou bloco de PRs em ondas grandes).
- **Commit style**: `feat(ondaN): título curto (#PR)` ou `fix|chore|docs(...)`.
- **CI**: GitHub Actions verde obrigatório para merge em main.
