# Vila INTEIA — MANIFEST

Consolidado das 285 ondas implementadas (5 → 289, com lacunas). Referência operacional para analistas e parceiros.
Última atualização: 2026-05-05.

> Para navegação rápida ver [`INDEX.md`](INDEX.md). Para mapa visual ver [`MAP.md`](MAP.md).

## Ondas — bloco 1 (5–39, v1.0.0)

| # | Nome | PR | Entregas principais |
|---|---|---|---|
| 5 | Proveniência + Backtest | #1 | `engine/proveniencia/`, `engine/backtest/`, dataset seed eleição SP 2024 |
| 6 | GraphRAG nativo | #1 | `engine/memoria/grafo.py`, SQL grafo_conhecimento |
| 7 | Multi-plataforma social | #1 | `engine/plataformas/` (Twitter/Reddit/LinkedIn/TikTok) |
| 8 | MCP Server + calibração | #1 | `engine/mcp_server/`, grid search backtest |
| 9 | Scale Ray + vLLM (skeleton) | #1 | `engine/distribuido/` (Ray actors, tiers, vLLM client) |
| 10 | Fundamentos formais | #1 | `game_theory/`, `opinion_dynamics/`, `simulacao_avancada/`, `psicohistoria/` |
| 10.2 | Integração real Onda 10 | #1 | `engine/cognitivo/{crenca, integracoes_onda10}.py` + hook simulacao |
| 11 | Rastreamento tempo real | #2 | `engine/psicohistoria/detector_estado_vila.py` |
| 12 | UI live psico + fix hook | #3 | `frontend/psico_live.html`, fix n_conversas |
| 13 | Calibração online | #4 | `engine/psicohistoria/calibracao_online.py` (MLE/Laplace/EWMA) |
| 14 | Persistência Supabase | #4 | `engine/psicohistoria/persistencia.py`, SQL trajetoria_psico |
| 15 | HMM não-supervisionado | #4 | `engine/psicohistoria/hmm_estados.py` (K-Means + smoothing) |
| 16 | Decision helper Helena | #4 | `engine/psicohistoria/decision_helper.py` + hook helena.py |
| 17 | UI Avançada | #5 | `frontend/psico_avancado.html` |
| 18 | Auto-calibrador periódico | #5 | `engine/psicohistoria/auto_calibrador.py` |
| 19 | MCP tools +3 | #5 | vila.recomendacao + calibrar_online + hmm_descobrir |
| 20 | Replay + export | #6 | `engine/psicohistoria/replay.py` |
| 21 | Artigo PDF v2 | #6 | `docs/artigo/vila_inteia_artigo_v2_ondas_11_a_20.pdf` |
| 22 | Orquestrador plataformas | #7 | `engine/plataformas/orquestrador.py` + spillover |
| 23 | GraphRAG real em recuperar | #7 | Hook em `cognitivo/recuperar.py` + indexação em simulacao |
| 24 | 4 datasets históricos | #7 | Apple VPro, Americanas, Impeachment, TikTok (50 eventos total) |
| 25 | Tuner thresholds | #8 | `engine/psicohistoria/tuner_classificador.py` (grid 4⁴) |
| 26 | SSE stream eventos | #8 | `GET /stream` real-time |
| 27 | Backtest UI comparativo | #8 | `frontend/backtest.html` |
| 28 | Causalidade Pearl | #9 | `engine/causalidade/` (intervir, counterfactual, ATE, sweep) |
| 29 | Comparativo A/B | #9 | `engine/comparativo/` (runner + metricas) |
| 30 | CLI vila-cli | #9 | `scripts/vila_cli.py` 8 subcomandos |
| 31 | Event-sourcing JSONL | #10 | `engine/event_log.py` append-only |
| 32 | Cockpit unificado | #10 | `frontend/cockpit.html` single-pane |
| 33 | Artigo PDF v3 | #10 | `docs/artigo/vila_inteia_artigo_v3_ondas_22_a_33.pdf` |
| 34 | Event-log hook no loop | #11 | Hook simulacao emite eventos step/mule/calibracao |
| 35 | Meta-análise cross-runs | #11 | `engine/meta_analise.py` |
| 36 | Sim real validada | #11 | 56 steps, perplexity gain 91% via auto-calibração |
| 37 | Health endpoint | #12 | `GET /api/v1/vila/health` agregado |
| 38 | Export grafo + visualizer | #12 | `frontend/grafo.html` force-directed |
| 39 | MANIFEST consolidado | #12 | Este arquivo |

## Módulos engine (19)

- `game_theory/` (7 submódulos: equilibrio, mecanismos, jogos_repetidos, evolutivo, coordenacao, bem_comum, hmm)
- `opinion_dynamics/` (6 submódulos)
- `simulacao_avancada/` (7 submódulos)
- `psicohistoria/` (9 submódulos)
- `proveniencia/` (3 submódulos)
- `backtest/` (4 submódulos)
- `memoria/grafo.py` (GraphRAG)
- `plataformas/` (5 submódulos)
- `mcp_server/` (server + tools)
- `distribuido/` (Ray + vLLM esqueleto)
- `causalidade/` (Pearl do-calculus)
- `comparativo/` (A/B runner)
- `cognitivo/{crenca, integracoes_onda10}.py`
- `event_log.py`
- `meta_analise.py`

## Endpoints API (45+)

### `/api/v1/gametheory/*`
nash · stackelberg · torneio · replicator · hawk-dove · leilao-vickrey · degroot · deffuant · cascata · shapley · banzhaf · schelling/tipping-point · redes/small-world · redes/barabasi-albert · redes/comunidades · bem-comum/ostrom · bem-comum/public-goods · crencas/*

### `/api/v1/psicohistoria/*`
grafo · prever · estacionaria · plano-seldon · detectar-mule · divergencia · criticidade · agentes-anomalos · trajetoria-atual · divergencia-atual · mules-detectados · calibrar · hmm/descobrir · recomendacao · persistencia/stats · persistencia/flush · tuner/grid-search · stream (SSE) · backtest-comparativo

### `/api/v1/materia/*` · `/api/v1/backtest/*`
proveniencia · datasets · rodar/{dataset}

### `/api/v1/vila/*` · `/api/v1/grafo/*`
health (agregado) · grafo/export · grafo/stats

## Frontend UI (12 páginas)

- `index.html` (Vila núcleo — mapa, conversas)
- `cidade.html` (campus 3D Three.js)
- `jogo.html` (Assembleia Constituinte)
- `rede.html` (rede social)
- `dashboard.html` (KPIs agregados)
- `psicohistoria.html` (teoria)
- `psico_live.html` (trajetória ao vivo)
- `psico_avancado.html` (calibração + HMM + Helena)
- `gametheory.html` (Nash, stag hunt, Axelrod)
- `opinioes.html` (Deffuant, DeGroot, Bikhchandani)
- `coalizoes.html` (Shapley, Banzhaf, core)
- `backtest.html` (comparativo 5 datasets)
- `cockpit.html` (single-pane-of-glass)
- `grafo.html` (knowledge graph force-directed)

## MCP Tools (7)

- `vila.prever_trajetoria` — Markov forecast
- `vila.extrair_grafo` — GraphRAG
- `vila.backtest_dataset` — backtest preditivo
- `vila.calibrar` — grid search dataset
- `vila.recomendacao_estrategica` — Plano Seldon (Onda 16)
- `vila.calibrar_online` — recalibra matriz viva (Onda 13)
- `vila.hmm_descobrir` — K-Means estados latentes (Onda 15)

## Datasets backtest (5, 50 eventos)

- `seed_eleicao_municipal_sp_2024` (eleição)
- `lancamento_apple_vpro_2024` (lançamento tech)
- `americanas_crise_2023` (escândalo corporate)
- `impeachment_dilma_2016` (crise política)
- `tiktok_viral_2024` (viralização)

## Testes (322+, 100% passing)

13 suítes em CI GitHub Actions:
- test_game_theory (28) · test_opinion_dynamics (11) · test_simulacao_avancada (25)
- test_psicohistoria (22) · test_crenca (12) · test_proveniencia (18)
- test_grafo_conhecimento (11) · test_plataformas (7) · test_ondas_5_a_9 (15)
- test_detector_estado_vila (13) · test_ondas_13_a_16 (23) · test_ondas_17_19 (14)
- test_replay (17) · test_ondas_22_24 (26) · test_ondas_25_27 (18)
- test_ondas_28_30 (19) · test_event_log (13) · test_meta_analise (15)

## Artigos acadêmicos

- `docs/artigo/vila_inteia_artigo.pdf` v1 (Ondas 5-10, 9 pgs, 99 KB)
- `docs/artigo/vila_inteia_artigo_v2_ondas_11_a_20.pdf` (7 pgs, 67 KB)
- `docs/artigo/vila_inteia_artigo_v3_ondas_22_a_33.pdf` (50 KB)

## CLI

```bash
python scripts/vila_cli.py --url http://localhost:8100 trajetoria
python scripts/vila_cli.py --url ... recomendacao
python scripts/vila_cli.py --url ... calibrar --metodo laplace --alpha 0.1
python scripts/vila_cli.py --url ... backtest --dataset tiktok_viral_2024
python scripts/vila_cli.py --url ... export-run --arquivo /tmp/run.json
python scripts/vila_cli.py --url ... mules
python scripts/vila_cli.py --url ... stats
python scripts/vila_cli.py --url ... comparativo
```

## Execução rápida

```bash
# Testes
PYTHONPATH=. python tests/test_ondas_13_a_16.py

# Simulação live (151 agentes heurístico)
OMNIROUTE_API_KEY="" CLAUDE_API_KEY="" SUPABASE_VILA_URL="" \
PYTHONPATH=. python main.py live --port 8100 --intervalo 1 \
  --topico "tema desejado"

# Backtest via CLI
python scripts/vila_cli.py --url http://localhost:8100 backtest \
  --dataset tiktok_viral_2024

# MCP server stdio
python -m engine.mcp_server.server
```

## Validação empírica

Sim real (56 steps, 151 agentes, heurístico puro):
- Trajetória: 85.7% expansao / 14.3% equilibrio
- Perplexity vs baseline: 15.577
- Perplexity após Laplace α=0.1: 1.377
- **Ganho 91.2%** em log-likelihood médio
- Confirma necessidade Onda 13 (calibração online)

## CI Status

11 PRs mergeados ao main, todos com CI verde (GitHub Actions executando 13 suítes + syntax check + node --check).

---

## Ondas — bloco 2 (40–100, escala + validação)

Marcos: docker-compose, Prometheus, E2E Playwright, auth, OmniRoute, Groq, /super-intelligence, PDF export, K8s probes.

| # | Tema | Entrega-chave |
|---|---|---|
| 40 | Docker | `docker-compose.yml` (vila + mcp + healthcheck) |
| 41 | Benchmark perf | `tests/benchmark.py` (12 benches) |
| 42 | README | Quickstart 3 passos |
| 43 | Prometheus | `api/rotas_metrics.py` `/metrics` |
| 44–45 | CHANGELOG + E2E | v1.0.0 release notes; Playwright suite |
| 46–48 | Auth + rate-limit | X-API-Key + per-IP throttle + backup CLI + webhook |
| 49–51 | CI + artigo | Wire auth+notifier; CI matrix; artigo v4 |
| 52–54 | Nature + OpenAPI | Artigo Nature-style; `dump_openapi.py`; synth datasets |
| 55–57 | Log + tuner | JSON logs; validador calibração; genetic tuner |
| 58–62 | LLM tier | Tier gate, cache, OmniRoute, budget |
| 63–67 | Groq | Provider Groq (Llama 3.3 70B); cockpit tab LLM |
| 68–72 | Step cap + real | Cap LLM/step; validação Vila + LLM real |
| 75–80 | Endpoints LLM | `/conversas/llm-only`, `/forecast-narrativo`, `/counterfactual-narrativo`, `/recomendacao-intervencao` |
| 81–85 | God's Eye | `/super-intelligence`, `/predictive-power`, `/influencia-personas`, `/comunidades-personas`, SPA |
| 86–90 | Persona UX | `/persona-chat`, SSE stream, mapa toggle, `/panel-chat`, `/snapshot` |
| 91–95 | Backtest | Multi-model bench, `/backtest_real`, Platt, relatório, per-persona skill |
| 97–101 | Calibração | Runtime Platt; widget; `/backtest` REST; bootstrap CI; isotonic; reliability |
| 102 | BSS | Decomposição BSS; datasets crypto/twitter |
| 103–105 | Auth + mobile + PDF | X-API-Key + per-IP; mobile God's Eye; export PDF |
| 106–108 | Persistência | Supabase + JSONL backtest; `render.yaml`; `/livez` `/readyz` |
| 109–110 | Artigo + worker | Atualização Nature; `backtest_worker.py` daemon |
| 111–115 | UX backtest | Modal + history; reliability SVG; tour; CV holdout; persona-skill table |
| 116–120 | Integration | E2E 14-mod; webhook Discord/Slack; bench vs OASIS/MiroFish |

## Ondas — bloco 3 (101–200, ensemble + autoresearch)

Marcos: ensemble Bayesiano, self-consistency, conformal prediction, Karpathy autoresearch loop, multi-model.

| # | Tema | Entrega-chave |
|---|---|---|
| 121–125 | Few-shot + ensemble | Examples; weighted by skill; CoT; multi-step debate; bayesian blend |
| 126–130 | Robustez | Ensemble accuracy; dataset-conditional persona; self-consistency; adversarial |
| 131–133 | Verificação | LLM-as-judge; integrate adv+judge; full-stack validation |
| 134–140 | Calibração avançada | Rejection-aware CoT; outcome_framing; dispersion-aware; prob anchoring; persona skill per cat |
| 141–146 | Auto-select | Painel per-dataset; mock heuristic; prob clip; full_hedge; expõe params |
| 147–153 | Calibração runtime | Bayesian blend; isotonic runtime; CLI `fit_isotonic.py`; auto Platt vs iso; recency-weighted |
| 156–158 | Per-persona | Calibração; isotonic 20 samples; temperature diversity |
| 159–162 | AutoResearch | Karpathy loop; dataset peso override; resume from trace; conformal intervals |
| 164–168 | Multi-model | Median ensemble; prompt variant; wire ensemble; paper update; SA |
| 170–175 | Karpathy | Compare backtests CLI; full Karpathy; timing default; trace; meta-autoresearch |
| 179–191 | Trace + rotation | Múltiplos traces; circuit breaker; 6ev baseline; model rotation |
| 197 | Mirofish-style | Pipeline corpus → grafo → simulação |

## Ondas — bloco 4 (198–289, forecasting honesto + hybrid)

Marcos: a11y total, claude_motor saneado sem lookup de gabarito por padrão, factor models, post-cutoff classifier, conformal+EB+Lindy, mega-bench routed, Vila+LLM hybrid, Diebold-Mariano formal p<0.01.

| # | Tema | Entrega-chave |
|---|---|---|
| 198–219 | A11y boost | Aria-labels duais, semantic landmarks, noscript fallbacks (combined cruzou 0.90 em onda 210) |
| 220–222 | Painel offline | `claude_motor` convertido para estimador ground-truth-blind; teste LODO antigo virou guarda anti-leakage |
| 223–227 | Aria final | psico_live, cidade, super_intel, dashboard, backtest, vila-claude-motor skill |
| 228–229 | Validação SOTA | Bench vs 4 baselines; rigor SOTA 2026 |
| 232–242 | Real benchmark | 197 events large-scale; factor models (MOMENTUM bate baseline); cache atomic |
| 243–248 | Factor models | Multi-window; 4 advanced; 4 exóticos (Bollinger/Ichimoku/Stochastic/MACD); autoresearch 11 strategies |
| 249–253 | Post-cutoff | Classifier 30%→75%; stacking ensemble (brier 0.229); hold-out Q2 2026 (90% acc); +70 events; conformal+40 |
| 254–258 | Priors | EB priors per cat; Platt+Isotonic; Lindy duration; PIT histogram; act on PIT |
| 259–262 | Online | Hedge online; confidence stretch; Hosmer-Lemeshow; wire EB priors |
| 263–267 | Datasets + selective | Macro/corp/regulatory/geopolitics; reject option; AdaHedge; forecast-bench CLI; combined pipeline + holdout v2 |
| 268–269 | Cleanup | /simplify cleanup (5 findings); apply skipped findings |
| 270–278 | Theorems + datasets | 9+7+8+8+7+8 theorems via parallel agents; resolve future-work via 5 agents |
| 279–280 | LLM real | Manifold integration; LLM forecaster via Claude Code OAuth |
| 281–289 | Hybrid + DM | Vila+LLM hybrid log-pool; LLM-coordinator; BTC cohort EB; ETH cross-asset; DM test p<0.01; mega-bench `--routed` domain_router |

## Saneamento v1.1 (2026-05-05)

24 PRs órfãos das v1.0/v1.1 fechados sem merge (linhas de experimento descontinuadas, ondas 115–191 e 281–282). Triagem completa: [`TRIAGEM_PRS_2026-05-05.md`](TRIAGEM_PRS_2026-05-05.md).
