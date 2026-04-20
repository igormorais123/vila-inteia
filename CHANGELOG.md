# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/).
Projeto segue [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-04-20

### Milestone
Primeiro release estável. 38+ ondas implementadas, 353+ testes passing, 13 PRs
mergeados em sequência ao main. Ver `MANIFEST.md` para tabela consolidada.

### Added — infraestrutura
- `docker-compose.yml` (Onda 40) — vila + mcp-server + healthcheck + volumes
- `tests/benchmark.py` (Onda 41) — 12 benches cobrindo game theory/psico/grafo
- `README.md` Quickstart 3 passos (Onda 42)
- `api/rotas_metrics.py` (Onda 43) — `/metrics` Prometheus exposition
- `MANIFEST.md` (Onda 39) — referência operacional consolidada
- `api/rotas_health.py` (Onda 37) — `/api/v1/vila/health` agregado 8 subsistemas
- `api/rotas_grafo.py` + `frontend/grafo.html` (Onda 38) — export + visualizer

### Added — análise
- `engine/event_log.py` (Onda 31) — event-sourcing JSONL append-only
- `engine/meta_analise.py` (Onda 35) — cross-runs stats (KL, variância, convergência)
- `engine/causalidade/` (Onda 28) — Pearl do-calculus (intervir, counterfactual, ATE)
- `engine/comparativo/` (Onda 29) — A/B runner com conclusões automáticas
- `scripts/vila_cli.py` (Onda 30) — 8 subcomandos HTTP CLI

### Added — psico-história
- `engine/psicohistoria/detector_estado_vila.py` (Onda 11) — rastreamento tempo real
- `engine/psicohistoria/calibracao_online.py` (Onda 13) — MLE/Laplace/EWMA
- `engine/psicohistoria/persistencia.py` (Onda 14) — Supabase batched
- `engine/psicohistoria/hmm_estados.py` (Onda 15) — K-Means + smoothing
- `engine/psicohistoria/decision_helper.py` (Onda 16) — Plano Seldon → urgência
- `engine/psicohistoria/auto_calibrador.py` (Onda 18) — recalibração periódica
- `engine/psicohistoria/replay.py` (Onda 20) — export/import JSON
- `engine/psicohistoria/tuner_classificador.py` (Onda 25) — grid search thresholds

### Added — UI
- `frontend/psico_live.html` (Onda 12), `psico_avancado.html` (Onda 17)
- `frontend/backtest.html` (Onda 27), `cockpit.html` (Onda 32)
- `frontend/grafo.html` (Onda 38) — force-directed sem D3

### Added — fundamentos (Onda 10)
- `engine/game_theory/` — Nash, Stackelberg, VCG, replicator, Axelrod, Ostrom
- `engine/opinion_dynamics/` — DeGroot, Deffuant, Bikhchandani, Bayes, Latané
- `engine/simulacao_avancada/` — A*, Shapley, Schelling, Hotelling, Watts-Strogatz
- `engine/psicohistoria/` — grafo Markov + Plano Seldon + Mule detector

### Added — integrações
- `engine/plataformas/` (Onda 7 + 22) — Twitter/Reddit/LinkedIn/TikTok + orquestrador
- `engine/memoria/grafo.py` (Onda 6 + 23) — GraphRAG nativo hook recuperar
- `engine/mcp_server/` (Onda 8 + 19) — 7 MCP tools
- `engine/distribuido/` (Onda 9) — Ray actors + vLLM (esqueleto)

### Added — backtest
- 5 datasets históricos: eleição SP 2024, Apple Vision Pro, Americanas crise,
  impeachment Dilma, TikTok viral (50 eventos totais, Onda 5 + 24)

### Added — artigos
- `docs/artigo/vila_inteia_artigo.pdf` v1 (Ondas 5-10, 9 pgs)
- `docs/artigo/vila_inteia_artigo_v2_ondas_11_a_20.pdf` (7 pgs)
- `docs/artigo/vila_inteia_artigo_v3_ondas_22_a_33.pdf`

### Validação empírica
Sim real 56 steps, 151 agentes (heurístico puro):
- Distribuição observada: 85.7% expansao / 14.3% equilibrio
- Perplexity baseline: 15.577
- Perplexity Laplace α=0.1: 1.377
- **Ganho 91.2%** log-likelihood médio (Onda 36)

### CI
13 PRs mergeados ao main, todos com GitHub Actions verde.

## [0.x.y] — histórico pré-v1.0.0

Ondas prévias (harness, vivos, migrations) documentadas em commits pré-onda-5.
