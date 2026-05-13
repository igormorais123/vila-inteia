# Auditoria completa — Vila INTEIA

Data da auditoria: 2026-05-13
Diretorio auditado: `C:\Agentes\vila-inteia`
Repositorio remoto: `https://github.com/igormorais123/vila-inteia.git`
Branch: `main`
Commit auditado: `0d9fd96 docs(onda7): linter-improved bench_all_models.py + BENCHMARKS.md (#230)`

## 1. Resumo executivo

A Vila INTEIA hoje e um repositorio grande, funcional e multi-produto. Ele nao e apenas uma simulacao narrativa: contem API FastAPI, frontends, datasets, motores de previsao, game theory, psico-historia, observabilidade, scripts de benchmark e um produto novo de predicao politica BR 2026.

O que esta mais pronto para uso real:

1. **API local FastAPI + frontend estatico**: sobe com `python main.py serve --port 8100`.
2. **Predicao Politica BR 2026**: endpoints em `/api/v1/politica/*`, smoke test 29/29 passando.
3. **Game theory e dinamica social matematica**: testes especificos 28/28 passando apos instalar dependencias declaradas.
4. **Backtests e datasets locais**: 63 CSVs em `data/backtest`, endpoint de listagem respondeu.
5. **Dashboard Next.js cliente**: lint, build de producao e `npm audit` passam apos atualizar Next/PostCSS e criar lockfile para commit.
6. **Vila multiagente**: inicializa e responde via API, com agentes, locais, estado e rede social.
7. **Harness/observabilidade**: endpoints de saude, traces, orcamento, skills e fundador existem e respondem.

O que exige cautela antes de expor publicamente:

1. Em modo dev, autenticacao global fica desligada se `VILA_API_TOKEN` ou `VILA_API_KEYS` estiverem vazios.
2. Alguns endpoints sensiveis agora exigem API key quando `VILA_API_KEYS` esta configurado, mas producao ainda deve falhar startup se tokens essenciais estiverem vazios.
3. A suite completa ainda mistura testes script-style e pytest-style; varios testes especificos passam, mas a organizacao geral precisa limpeza.
4. Publicacao Mirante com `auto_push` continua sendo recurso administrativo e deve ficar restrita a ambiente interno.
5. LLMs, Supabase e provedores externos dependem de chaves/servicos configurados; sem isso, parte do sistema opera em modo local/heuristico.

## 1.1 Correcoes aplicadas em 2026-05-13

| Area | Correcao aplicada | Validacao |
|---|---|---|
| Workspace/oficinas | Validacao de `desafio_id` e `nome_arquivo`, `resolve()` e containment check dentro de `data/entregas` | `python -m pytest tests/test_workspace_security.py -q` -> 14 passed |
| Endpoints sensiveis | Python sandbox, workspace e publicacao Mirante passaram a usar `auth_e_rate` | TestClient: sem key -> 401; path traversal com key -> 400 |
| Frontend Next.js | `next` atualizado para `^15.5.18`, lockfile criado, ESLint instalado, PostCSS fixado via override | `npm run lint`, `npm run build`, `npm audit --json` -> ok/0 vulnerabilidades |
| Scripts operacionais | `backtest_political.py`, `predict_2026.py` e `bench_all_models.py` ganharam `argparse` e `--help` sem escrita de arquivos | `python scripts\<script>.py --help` -> help e exit 0 |
| Testes legados | `test_calibration.py` deixou de usar caminho Linux absoluto; `test_mirofish_style.py` ajustado para encoding e quantidade real de eventos | `python tests/test_calibration.py`; `PYTHONUTF8=1 python tests/test_mirofish_style.py` -> ok |

## 2. Inventario real do repositorio

Contagem observada:

| Area | Quantidade |
|---|---:|
| Arquivos versionados/listaveis por `rg --files` | 726 |
| Arquivos Python totais | 484 |
| Rotas/API Python em `api/` | 15 arquivos |
| Modulos Python em `engine/` | 254 arquivos |
| Scripts Python em `scripts/` | 37 arquivos |
| Testes em `tests/` | 174 arquivos |
| Datasets CSV | 63 |
| Documentos Markdown | 57 |
| JSONs versionados | 26 |
| Paginas HTML estaticas | 23 |
| Paginas/componentes TSX | 18 |

Estrutura principal:

| Caminho | Funcao real |
|---|---|
| `main.py` | Entrypoint CLI/API/live/demo/benchmarks |
| `api/` | 204 endpoints FastAPI detectados por decorator |
| `engine/` | Nucleo: simulacao, forecasting, game theory, LLM, memoria, harness |
| `frontend/` | UI estatica servida pelo FastAPI |
| `frontend-next/` | Dashboard Next.js para produto politico |
| `scripts/` | Backtests, benchmarks, deploy, predict, probes, CLI |
| `data/` | Snapshots, datasets, benchmarks e banco de consultores |
| `docs/` | Documentacao tecnica, onboarding, deploy, benchmarks |
| `migrations/` e `sql/` | SQL Supabase/Postgres |
| `tests/` | Testes script-style e pytest-style |

## 3. Como rodar

### 3.1 Preparar Python

```powershell
cd C:\Agentes\vila-inteia
python -m pip install -r requirements.txt
```

Observacao: o projeto documenta Python 3.11+, mas a auditoria foi feita em Python 3.14. Algumas libs avisam compatibilidade parcial com Pydantic v1 em Python 3.14.

### 3.2 Subir API + frontend estatico

```powershell
cd C:\Agentes\vila-inteia
python main.py serve --port 8100
```

Depois abrir:

| URL | Uso |
|---|---|
| `http://localhost:8100/` | frontend estatico raiz |
| `http://localhost:8100/politica.html` | dashboard politico estatico |
| `http://localhost:8100/cockpit.html` | cockpit Vila |
| `http://localhost:8100/docs` | Swagger/FastAPI |
| `http://localhost:8100/api/v1/vila/health` | health agregado |
| `http://localhost:8100/api/v1/politica/health` | health politico |

### 3.3 Subir modo live

```powershell
python main.py live --port 8100 --intervalo 30 --topico "IA no Brasil"
```

Esse modo sobe servidor e roda steps periodicos. Use com poucos agentes se quiser economizar:

```powershell
$env:VILA_MAX_AGENTES="20"
python main.py live --port 8100 --intervalo 30
```

### 3.4 Rodar simulacao CLI sem servidor

```powershell
python main.py run --steps 20 --agentes 10 --topico "futuro da educação"
```

### 3.5 Rodar frontend Next.js

```powershell
cd C:\Agentes\vila-inteia\frontend-next
npm install
$env:VILA_API_BASE="http://localhost:8100"
npm run dev
```

Abrir `http://localhost:3001`.

Build de producao:

```powershell
npm run build
```

Na auditoria atualizada, `npm run lint`, `npm run build` e `npm audit --json` passaram. O projeto agora tem `frontend-next/package-lock.json` pronto para commit e um wrapper local de lint para evitar conflito com configuracao ESLint fora da pasta do frontend.

## 4. Capacidades reais e como usar

### 4.1 Predicao Politica BR 2026

Status: **funcional e mais pronto para produto**.

Arquivos principais:

| Arquivo | Papel |
|---|---|
| `api/rotas_politica.py` | Endpoints REST politicos |
| `engine/political_cohort.py` | Cohort empirical-Bayes + Linzer-style + MRP state baseline |
| `engine/auth_clients.py` | API keys multi-tenant em `data/clients.json` |
| `scripts/smoke_political.py` | Smoke test 29 checks |
| `scripts/backtest_political.py` | Backtest politico local |
| `scripts/predict_2026.py` | Gera snapshot `data/predictions_2026.json` |
| `frontend/politica.html` | Dashboard estatico |
| `frontend-next/` | Dashboard cliente Next.js |

Snapshot versionado auditado:

| Campo | Valor |
|---|---|
| `predicted_at` | `2026-05-08` |
| `horizon_days` | `149` |
| candidatos presidencia | 5 |
| senadores no snapshot | 4 |
| UFs de governador no snapshot | 9 |

Endpoints:

| Endpoint | O que faz |
|---|---|
| `GET /api/v1/politica/health` | status, treino carregado, snapshot |
| `GET /api/v1/politica/elections` | calendario e cargos suportados |
| `GET /api/v1/politica/predictions/presidente` | ranking presidencial |
| `GET /api/v1/politica/predictions/governador?uf=SP` | candidatos por UF |
| `GET /api/v1/politica/predictions/governador` | todas as UFs |
| `GET /api/v1/politica/predictions/senador` | lista de senado |
| `GET /api/v1/politica/predictions/all` | snapshot completo |
| `GET /api/v1/politica/backtest` | metricas historicas |
| `POST /api/v1/politica/predict` | previsao custom |
| `GET /api/v1/politica/me` | identidade/tier da chave |
| `POST /api/v1/politica/admin/keys/issue` | emite chave cliente |
| `POST /api/v1/politica/admin/keys/revoke` | revoga chave |

Uso:

```powershell
curl http://localhost:8100/api/v1/politica/health
curl http://localhost:8100/api/v1/politica/predictions/presidente
curl "http://localhost:8100/api/v1/politica/predictions/governador?uf=SP"
```

Predicao custom:

```powershell
curl -X POST http://localhost:8100/api/v1/politica/predict `
  -H "Content-Type: application/json" `
  -d '{"cargo":"governador","poll_lead_pp":8,"days_to_election":45,"incumbente":1,"regime":"right"}'
```

Emitir chave cliente:

```powershell
$env:VILA_ADMIN_TOKEN="gere_um_token_forte"
curl -X POST http://localhost:8100/api/v1/politica/admin/keys/issue `
  -H "X-Admin-Token: gere_um_token_forte" `
  -H "Content-Type: application/json" `
  -d '{"name":"cliente-teste","tier":"pro","contact":"email@cliente.com"}'
```

Observacao operacional: hoje as chaves politicas ficam em `data/clients.json`. Para producao, a propria doc recomenda trocar por Supabase `vila_clients`.

### 4.2 Vila multiagente

Status: **funcional localmente**.

O que faz:

| Recurso | Uso real |
|---|---|
| Inicializar agentes lendarios | `POST /api/v1/vila/iniciar` |
| Rodar steps | `POST /api/v1/vila/step` |
| Ver estado | `GET /api/v1/vila/estado` |
| Ver mapa | `GET /api/v1/vila/mapa` |
| Listar agentes | `GET /api/v1/vila/agentes` |
| Ver agente | `GET /api/v1/vila/agente/{agente_id}` |
| Injetar topico | `POST /api/v1/vila/topico` |
| Sintetizar topico | `POST /api/v1/vila/sintetizar/{topico}` |
| Relatorio | `GET /api/v1/vila/relatorio` ou `/relatorio/markdown` |

Uso minimo:

```powershell
curl -X POST http://localhost:8100/api/v1/vila/iniciar `
  -H "Content-Type: application/json" `
  -d '{"nome":"demo","max_agentes":10}'

curl -X POST http://localhost:8100/api/v1/vila/step `
  -H "Content-Type: application/json" `
  -d '{"n_steps":1}'

curl http://localhost:8100/api/v1/vila/estado
```

Nota realista: muitas conversas podem funcionar em modo heuristico/offline, mas as partes LLM dependem de `OMNIROUTE_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY` ou `CLAUDE_API_KEY`.

### 4.3 Forecasting, backtest e calibracao

Status: **funcional em varias rotas; alguns testes antigos precisam limpeza**.

Recursos:

| Recurso | Como usar |
|---|---|
| Listar datasets | `GET /api/v1/backtest/datasets` |
| Rodar backtest simples | `GET /api/v1/backtest/rodar/{dataset}` |
| Rodar backtest Vila | `POST /api/v1/vila/backtest/rodar` |
| Rodar acc | `POST /api/v1/vila/backtest/rodar-acc` |
| Historico | `GET /api/v1/vila/backtest/historico` |
| Ultimo resultado | `GET /api/v1/vila/backtest/ultimo` |
| Reliability | `GET /api/v1/vila/backtest/reliability` |
| Bootstrap CI | `GET /api/v1/vila/backtest/bootstrap-ci` |
| Brier decomposition | `GET /api/v1/vila/backtest/brier-decomp` |
| CV holdout | `GET /api/v1/vila/backtest/cv-holdout` |
| Bayesian blend | `GET /api/v1/vila/backtest/bayesian-blend` |
| Baselines | `GET /api/v1/vila/backtest/baselines` |
| Platt vs isotonic | `GET /api/v1/vila/backtest/platt-vs-isotonic` |
| Aplicar calibracao | `POST /api/v1/vila/calibracao/aplicar` |
| Auto-fit | `POST /api/v1/vila/calibracao/auto-fit` |

Exemplo:

```powershell
curl http://localhost:8100/api/v1/backtest/datasets
curl http://localhost:8100/api/v1/backtest/rodar/tiktok_viral_2024
```

Scripts relevantes:

```powershell
python scripts/rodar_backtest_real.py
python scripts/gerar_relatorio_backtest.py
python scripts/run_n100_pipeline.py
python scripts/fit_isotonic.py
python scripts/political_stats_rigor.py
```

Verificacao atual: `tests/test_calibration.py` foi ajustado para usar caminho relativo ao repositorio e passa no Windows.

### 4.4 Game theory e dinamica de opiniao

Status: **funcional**.

Endpoints:

| Endpoint | O que faz |
|---|---|
| `POST /api/v1/gametheory/nash` | equilibrio de Nash |
| `POST /api/v1/gametheory/stackelberg` | Stackelberg |
| `POST /api/v1/gametheory/torneio` | torneio de estrategias |
| `POST /api/v1/gametheory/replicator` | dinamica replicator |
| `GET /api/v1/gametheory/hawk-dove` | ESS Hawk-Dove |
| `POST /api/v1/gametheory/leilao-vickrey` | leilao Vickrey |
| `POST /api/v1/gametheory/degroot` | consenso DeGroot |
| `POST /api/v1/gametheory/deffuant` | bounded confidence |
| `POST /api/v1/gametheory/cascata` | cascata informacional |
| `POST /api/v1/gametheory/shapley` | Shapley value |
| `POST /api/v1/gametheory/banzhaf` | poder Banzhaf |
| `GET /api/v1/gametheory/schelling/tipping-point` | tipping point |
| `GET /api/v1/gametheory/redes/small-world` | rede small-world |
| `GET /api/v1/gametheory/redes/barabasi-albert` | rede scale-free |
| `POST /api/v1/gametheory/redes/comunidades` | comunidades |
| `GET /api/v1/gametheory/bem-comum/ostrom` | principios Ostrom |
| `POST /api/v1/gametheory/bem-comum/public-goods` | bens publicos |

Uso:

```powershell
curl http://localhost:8100/api/v1/gametheory/hawk-dove
```

Verificacao: `python tests/test_game_theory.py` retornou 28 ok, 0 fail apos instalar `nashpy`.

### 4.5 Psico-historia

Status: **responde localmente**.

O que faz:

| Endpoint | Uso |
|---|---|
| `POST /api/v1/psicohistoria/grafo` | extrair/usar grafo psico-historico |
| `POST /api/v1/psicohistoria/prever` | prever trajetoria |
| `GET /api/v1/psicohistoria/estacionaria` | distribuicao estacionaria |
| `POST /api/v1/psicohistoria/plano-seldon` | plano/recomendacao |
| `POST /api/v1/psicohistoria/detectar-mule` | detectar Mule |
| `POST /api/v1/psicohistoria/divergencia` | divergencia |
| `GET /api/v1/psicohistoria/criticidade/{estado}` | criticidade por estado |
| `POST /api/v1/psicohistoria/calibrar` | calibracao online |
| `GET /api/v1/psicohistoria/hmm/descobrir` | estados latentes HMM/KMeans |
| `GET /api/v1/psicohistoria/recomendacao` | recomendacao Helena |
| `GET /api/v1/psicohistoria/stream` | stream SSE |

Uso:

```powershell
curl http://localhost:8100/api/v1/psicohistoria/estacionaria
curl http://localhost:8100/api/v1/psicohistoria/recomendacao
```

### 4.6 Colmeia, NPCs e genomas

Status: **funcional para consulta**.

Endpoints principais:

| Endpoint | Uso |
|---|---|
| `GET /api/v1/colmeia/ranking` | ranking dos agentes |
| `GET /api/v1/colmeia/estado` | estado da Colmeia |
| `GET /api/v1/colmeia/npc/{nome}` | detalhe de NPC |
| `GET /api/v1/colmeia/top-patentes` | patentes |
| `GET /api/v1/colmeia/mandamentos` | mandamentos |
| `GET /api/v1/colmeia/npc/{nome}/memorias` | memorias |
| `GET /api/v1/colmeia/npc/{nome}/genoma` | genoma |
| `GET /api/v1/colmeia/comparar-genomas` | comparacao |

Uso:

```powershell
curl http://localhost:8100/api/v1/colmeia/ranking
```

### 4.7 Rede social sintetica

Status: **API existe e responde; geracao rica pode depender de LLM**.

Endpoints:

| Endpoint | Uso |
|---|---|
| `GET /api/v1/rede/feed` | feed |
| `GET /api/v1/rede/trending` | topicos |
| `GET /api/v1/rede/stats` | estatisticas |
| `POST /api/v1/rede/tema` | injetar tema |
| `POST /api/v1/rede/evento` | publicar evento |
| `POST /api/v1/rede/gerar-posts` | gerar posts |
| `POST /api/v1/rede/debate` | debate |
| `POST /api/v1/rede/provocar` | provocar debate |
| `POST /api/v1/rede/helena-sintese` | sintese Helena |

Uso:

```powershell
curl http://localhost:8100/api/v1/rede/stats
```

### 4.8 Mirofish-style pipeline

Status: **endpoint responde; teste especifico ajustado e passando**.

O que faz:

1. Usa datasets em `data/backtest`.
2. Constroi grafo.
3. Roda simulacao com personas.
4. Gera relatorio.

Endpoints:

| Endpoint | Uso |
|---|---|
| `GET /api/v1/mirofish/info` | explica pipeline |
| `GET /api/v1/mirofish/datasets` | lista datasets |
| `POST /api/v1/mirofish/run` | executa pipeline |

Uso:

```powershell
curl http://localhost:8100/api/v1/mirofish/datasets
```

Para rodar pipeline, primeiro inicialize a Vila:

```powershell
curl -X POST http://localhost:8100/api/v1/vila/iniciar `
  -H "Content-Type: application/json" `
  -d '{"nome":"mirofish","max_agentes":10}'

curl -X POST http://localhost:8100/api/v1/mirofish/run `
  -H "Content-Type: application/json" `
  -d '{"dataset_glob":"*.csv","persona_ids":["CL001","CL002","CL007"],"base_dir":"data/backtest"}'
```

Seguranca: `base_dir` tem allowlist para `data/backtest`, bom controle contra path traversal.

### 4.9 Harness: observabilidade, orcamento, skills e fundador

Status: **endpoints existem e respondem; arquitetura documentada em `HARNESS_VILA.md`**.

Endpoints:

| Endpoint | Uso |
|---|---|
| `GET /api/v1/harness/saude` | saude do harness |
| `GET /api/v1/harness/traces` | traces |
| `GET /api/v1/harness/traces/{trace_id}` | trace especifico |
| `GET /api/v1/harness/traces/agente/{agente_id}` | traces por agente |
| `GET /api/v1/harness/metricas` | metricas |
| `GET /api/v1/harness/orcamento` | configuracao de orcamento |
| `GET /api/v1/harness/orcamento/consumo` | consumo |
| `POST /api/v1/harness/flush` | flush administrativo |
| `GET /api/v1/harness/skills` | skills registradas |
| `GET /api/v1/harness/capabilities` | capability cards |
| `GET /api/v1/harness/fundador` | ficha do fundador |
| `GET /api/v1/harness/fundador/injecao` | injecao prompt |
| `POST /api/v1/harness/simular-decisao` | simula decisao |

Uso:

```powershell
curl http://localhost:8100/api/v1/harness/saude
curl http://localhost:8100/api/v1/harness/skills
```

Nota: `harness-vila` recomenda nao mexer em `engine/cognitivo`, `engine/memoria`, `engine/oficinas.py`, `engine/chateaubriand.py`, `engine/constituicao.py` ou `engine/ia_client.py` sem enquadrar a mudanca em uma Onda/Gap do `HARNESS_VILA.md`.

### 4.10 Agentes vivos: Helena e Efesto

Status: **API existe; efeitos externos dependem de configuracao**.

Endpoints:

| Endpoint | Uso |
|---|---|
| `GET /api/v1/vivos/status` | status Helena/Efesto |
| `POST /api/v1/vivos/heartbeat/{agente}` | executa heartbeat |
| `GET /api/v1/vivos/{agente}/ultimos` | ultimos registros |
| `POST /api/v1/vivos/publicar-coluna-hoje` | publica coluna |
| `GET /api/v1/vivos/coluna/previa` | previa |
| `GET /api/v1/vivos/coluna/historico` | historico |
| `GET /api/v1/vivos/coluna/hoje` | coluna HTML |
| `GET /api/v1/vivos/coluna/{data}` | coluna por data |
| `GET /api/v1/vivos/coluna/{data}/mdx` | MDX |

Uso:

```powershell
curl http://localhost:8100/api/v1/vivos/status
curl -X POST http://localhost:8100/api/v1/vivos/heartbeat/helena
```

### 4.11 Desafios, oficinas, workspace e Python sandbox

Status: **funcional localmente; nao expor sem autenticacao**.

Recursos:

| Recurso | Endpoint |
|---|---|
| Catalogo de desafios | `GET /api/v1/vila/desafios` |
| Iniciar desafio | `POST /api/v1/vila/desafio/iniciar` |
| Estado do desafio | `GET /api/v1/vila/desafio` |
| Contribuir | `POST /api/v1/vila/desafio/contribuir` |
| Votar | `POST /api/v1/vila/desafio/votar` |
| Usar Python sandbox | `POST /api/v1/vila/ferramentas/python` |
| Ver recursos por local | `GET /api/v1/vila/ferramentas/recursos/{local_id}` |
| Oficinas | `GET /api/v1/vila/oficinas` |
| Workspace | `GET /api/v1/vila/workspace` |
| Compilar workspace | `GET /api/v1/vila/workspace/{desafio_id}/compilar` |
| Ler arquivo | `GET /api/v1/vila/workspace/{desafio_id}/arquivo/{nome_arquivo}` |

O sandbox bloqueou nos testes:

| Caso | Resultado |
|---|---|
| `x = 2 + 2; print(x)` | executou |
| `open("x.txt", "w")` | bloqueado |
| `import os` | bloqueado |
| loop infinito | timeout |

Exemplo:

```powershell
curl -X POST http://localhost:8100/api/v1/vila/desafio/iniciar `
  -H "Content-Type: application/json" `
  -d '{"tema":"produto de previsão política","descricao":"gerar plano comercial","steps_por_fase":10}'
```

Controle atual: `engine/oficinas.py` agora valida segmentos de caminho, resolve os paths e garante que leitura/escrita/listagem permanecam dentro de `data/entregas`. Os endpoints de workspace e Python sandbox tambem exigem API key quando `VILA_API_KEYS` esta configurado.

### 4.12 Publicacao no Mirante

Status: **codigo existe; depende de `MIRANTE_API_URL`, `MIRANTE_API_TOKEN` ou `MIRANTE_CONTENT_DIR`**.

Endpoints:

| Endpoint | Uso |
|---|---|
| `POST /api/v1/vila/mirante/publicar` | publica artigo direto |
| `POST /api/v1/vila/mirante/publicar-do-workspace` | cria artigo a partir do workspace |

Variaveis:

```powershell
$env:MIRANTE_API_URL="https://mirantenews.com.br"
$env:MIRANTE_API_TOKEN="token_compartilhado"
```

Modo dev:

```powershell
$env:MIRANTE_CONTENT_DIR="C:\Agentes\frontend\content\mirante"
```

Risco residual: `auto_push=true` executa `git add/commit/push` no repo do Mirante. O endpoint agora exige API key quando `VILA_API_KEYS` esta configurado, mas em producao este fluxo deve ficar admin-only e preferencialmente restrito a job interno.

### 4.13 LLMs e provedores externos

Status: **codigo existe; funcionamento depende de chaves ou servicos locais**.

Variaveis relevantes:

| Variavel | Uso |
|---|---|
| `OMNIROUTE_URL` | gateway local/remoto, default `http://localhost:20128` |
| `OMNIROUTE_API_KEY` | chave OmniRoute |
| `GROQ_API_KEY` | Groq |
| `GEMINI_API_KEY` | Gemini |
| `CLAUDE_API_KEY` | Anthropic fallback |
| `IA_ALLOW_API_FALLBACK` | permite fallback pago |
| `OSA_URL` | Optimal System Agent |

Como usar:

```powershell
$env:OMNIROUTE_URL="http://localhost:20128"
$env:OMNIROUTE_API_KEY="..."
python main.py serve --port 8100
```

Sem chaves, varias rotas respondem com heuristica, cache vazio ou erro controlado; conversas ricas e pesquisa web real ficam limitadas.

### 4.14 Supabase e persistencia

Status: **opcional; `.env` local contem `SUPABASE_VILA_URL` e `SUPABASE_VILA_KEY`**.

Variaveis:

```powershell
$env:SUPABASE_VILA_URL="https://..."
$env:SUPABASE_VILA_KEY="..."
```

Migrações:

```powershell
psql $env:SUPABASE_VILA_URL -f migrations/005_political_forecasts.sql
```

Tabelas previstas no produto politico:

| Tabela | Uso |
|---|---|
| `vila_election_calendar` | calendario |
| `vila_candidates` | candidatos |
| `vila_polls` | pesquisas |
| `vila_forecasts` | previsoes |
| `vila_election_results` | resultados oficiais |
| `vila_clients` | clientes/API keys |
| `vila_client_usage` | telemetria |
| `vila_cohort_fits` | fits reproduziveis |

### 4.15 MCP server

Status: **codigo existe**.

Uso:

```powershell
python -m engine.mcp_server.server
```

O servidor implementa JSON-RPC stdio minimo: `initialize`, `tools/list`, `tools/call`, `ping`.

### 4.16 CLI principal

Comandos de `main.py`:

| Comando | Uso |
|---|---|
| `run` | simulacao CLI |
| `serve` | API + frontend |
| `live` | servidor + simulacao continua |
| `demo` | demo rapido |
| `mirofish` | pipeline corpus -> grafo -> sim -> relatorio |
| `benchmark` | Vila vs baselines |
| `factor-bench` | factor models |
| `factor-autoresearch` | grid de pesos |
| `forecast-bench` | classifier post-cutoff |
| `forecast-mega-bench` | relatorio combinado |
| `forecast-vs-external` | Vila vs prob externa |

Uso:

```powershell
python main.py --help
python main.py run --steps 10 --agentes 10
python main.py serve --port 8100
```

CLI separada:

```powershell
python scripts/vila_cli.py --url http://localhost:8100 stats
python scripts/vila_cli.py --url http://localhost:8100 trajetoria
python scripts/vila_cli.py --url http://localhost:8100 recomendacao
python scripts/vila_cli.py --url http://localhost:8100 backtest --dataset tiktok_viral_2024
```

## 5. Frontends

### 5.1 Frontend estatico

Servido automaticamente por FastAPI:

| Pagina | Uso |
|---|---|
| `/index.html` | entrada geral |
| `/politica.html` | produto politico |
| `/cockpit.html` | cockpit |
| `/dashboard.html` | KPIs |
| `/jogo.html` | jogo/assembleia |
| `/rede.html` | rede social |
| `/cidade.html` | campus |
| `/backtest.html` | backtests |
| `/gametheory.html` | game theory |
| `/psicohistoria.html` | psico-historia |
| `/psico_live.html` | estado live |
| `/psico_avancado.html` | calibracao/HMM |
| `/super_intelligence.html` | God's Eye |
| `/mirofish_plus.html` | pipeline Mirofish |
| `/llm_stats.html` | LLM/cache |

### 5.2 Frontend Next.js

Paginas:

| Rota | Uso |
|---|---|
| `/` | presidencia |
| `/governadores` | UFs |
| `/senado` | senadores |
| `/simular` | cenario hipotetico |
| `/custom` | predict custom |
| `/backtest` | curva seletiva/backtest |

Status auditado:

| Check | Resultado |
|---|---|
| `npm install` | instalou e gerou `package-lock.json` |
| `npm run lint` | passou sem warnings |
| `npm run build` | compilou com Next.js 15.5.18 |
| ESLint | instalado via `eslint` + `eslint-config-next` |
| `npm audit --json` | 0 vulnerabilidades |
| Lockfile | `frontend-next/package-lock.json` criado e pronto para commit |

Observacao: o script `npm run lint` usa `frontend-next/scripts/lint.cjs` para forcar a configuracao local do Next e evitar que um `eslint.config.js` em pasta superior interfira no frontend.

## 6. Verificacoes executadas nesta auditoria

| Verificacao | Resultado |
|---|---|
| `git pull --ff-only origin main` | atualizado para `0d9fd96` |
| `python -m pip install -r requirements.txt` | dependencias declaradas instaladas; instalou `nashpy` |
| `python scripts/smoke_political.py` | 29 passed, 0 failed |
| `python tests/test_btc_cohort.py` | 12 ok, 0 fail |
| `python tests/test_auth_middleware.py` | 8 ok, 0 fail |
| `python tests/test_game_theory.py` | 28 ok, 0 fail |
| `python tests/test_persona_chat.py` | 19 ok, 0 fail |
| `python tests/test_proveniencia.py` | 18 ok, 0 fail |
| `python tests/test_eventos_v1.py` | exit 0 |
| `python -m pytest tests/test_workspace_security.py -q` | 14 passed |
| `python tests/test_calibration.py` | 7 ok, 0 fail |
| `PYTHONUTF8=1 python tests/test_mirofish_style.py` | 24 ok, 0 fail |
| `python -m compileall api engine scripts -q` | exit 0 |
| API em memoria com routers principais | todos os routers importaram |
| Endpoints amostra | health, politica, gametheory, colmeia, rede, psico, datasets, metrics responderam |
| Sandbox Python direto | bloqueou `open`, `import os` e timeout |
| Endpoints sensiveis sem API key | workspace, Python sandbox e Mirante retornaram 401 quando `VILA_API_KEYS` foi definido |
| Workspace com path traversal | retornou 400 e nao criou diretorio fora do escopo |
| `npm run lint` em `frontend-next` | passou |
| `npm run build` em `frontend-next` | compilou |
| `npm audit --json` | 0 vulnerabilidades |

Falhas/gaps observados:

| Check | Resultado |
|---|---|
| `pytest tests/test_btc_cohort.py` | erro interno porque o arquivo chama `sys.exit`; como script passa |
| Suite completa via `pytest` | ainda precisa separacao entre testes script-style e pytest-style antes de virar criterio unico de CI |

## 7. Auditoria de seguranca

### 7.1 Ameacas principais

Ativos sensiveis:

1. API keys de clientes politicos.
2. Tokens Supabase, Mirante, OmniRoute/Groq/Gemini/Claude.
3. Datasets e previsoes que podem afetar clientes.
4. Endpoints que executam simulacao, publicacao, workspace e Python sandbox.
5. Reputacao do produto se previsoes forem vendidas sem disclaimers.

Fronteiras de confianca:

1. Usuario externo -> FastAPI.
2. Frontend Next/HTML -> API.
3. API -> Supabase/Mirante/LLMs/OSA.
4. API -> filesystem local (`data/`, workspace, snapshots).
5. Agentes internos -> ferramentas de codigo/pesquisa/publicacao.

### 7.2 Achados de seguranca

#### S1 — Auth desligada por padrao em dev

Evidencia:

| Arquivo | Comportamento |
|---|---|
| `engine/auth.py` | se `VILA_API_TOKEN` vazio, auth global fica off |
| `engine/auth_middleware.py` | se `VILA_API_KEYS` vazio, endpoints custosos ficam sem auth |
| `api/rotas_politica.py` | chamadas anonimas aceitas em parte do produto politico |

Impacto: se o servico for exposto publicamente sem env vars, usuarios anonimos conseguem acionar endpoints custosos e potencialmente perigosos.

Mitigacao:

```powershell
$env:VILA_API_TOKEN="token_forte"
$env:VILA_API_KEYS="cliente1,cliente2"
$env:VILA_ADMIN_TOKEN="admin_forte"
```

Recomendacao: em producao, falhar startup se tokens essenciais estiverem vazios.

#### S2 — Next.js vulneravel por versao — resolvido

Evidencia original: `npm audit` em `frontend-next` apontou `next@15.5.15` vulneravel. Fix sem major: `15.5.18`.

Impacto: inclui DoS, SSRF/middleware bypass e XSS conforme advisories npm/GHSA.

Correcao aplicada:

```powershell
cd frontend-next
npm install
npm run lint
npm run build
npm audit --json
```

Resultado: `next` ficou em `^15.5.18`, `postcss` foi fixado via override, `package-lock.json` foi criado e `npm audit --json` voltou 0 vulnerabilidades.

#### S3 — Workspace com path handling fraco — resolvido

Evidencia original: `engine/oficinas.py` usava `os.path.join(self.base_dir, desafio_id, nome_arquivo)` em escrita/leitura sem `resolve()` + containment check.

Impacto: se um atacante controlar `desafio_id` ou `nome_arquivo` em fluxo exposto, pode haver path traversal dentro/fora do workspace.

Correcao aplicada: `Workspace` agora valida segmentos, rejeita `..`, separadores, caminhos absolutos e nomes vazios, resolve caminhos e garante que o resultado permanece dentro do diretorio base. Teste dedicado: `python -m pytest tests/test_workspace_security.py -q` -> 14 passed.

#### S4 — Publicacao Mirante com `auto_push` — mitigado

Evidencia: `engine/publicar_mirante.py` executa `git add`, `git commit`, `git push` quando `auto_push=True`.

Impacto: se endpoint ficar publico, um usuario pode tentar acionar commit/push no repo configurado.

Mitigacao aplicada: endpoints de publicacao Mirante agora usam `auth_e_rate`, portanto exigem API key quando `VILA_API_KEYS` esta configurado.

Risco residual: em producao, este recurso ainda deve exigir token administrativo, `auto_push` deve ficar desabilitado por padrao e o push deve rodar preferencialmente como job interno.

#### S5 — Scripts com efeitos colaterais inesperados — resolvido

Evidencia original: `scripts/backtest_political.py --help`, `scripts/predict_2026.py --help` e `scripts/bench_all_models.py --help` executavam e escreviam arquivos em vez de mostrar help.

Impacto: risco operacional de sobrescrever snapshots/benchmarks por engano.

Correcao aplicada: os tres scripts agora usam `argparse`; `--help` mostra ajuda e termina com exit 0 sem escrita. Tambem foram adicionadas opcoes explicitas de saida, como `--out`.

## 8. Dependencias e lacunas de ambiente

Declaradas em `requirements.txt`:

| Pacote | Uso |
|---|---|
| FastAPI/Uvicorn/Pydantic | API |
| OpenAI/Anthropic/httpx | LLM e integracoes |
| numpy/scipy/networkx/nashpy | modelos, grafos, game theory |

Usadas mas nao claramente cobertas em `requirements.txt`:

| Pacote | Onde aparece | Observacao |
|---|---|---|
| `scikit-learn` | isotonic, BART proxy | necessario para alguns scripts |
| `pymc`, `pymc_bart` | `bench_bart.py` | opcional; cai para proxy se ausente |
| `pandas/lxml/bs4` | docs/scripts de coleta historica | documentado em onboarding, nao declarado |
| Node/npm | `frontend-next` | separado do Python |

Recomendacao: criar `requirements-dev.txt` e/ou `requirements-research.txt` para benchmarks e scripts cientificos.

## 9. O que e produto, o que e laboratorio

### Produto mais pronto

1. Predicao Politica BR 2026.
2. API FastAPI local.
3. Frontend politico estatico.
4. Dashboard Next.js com lint/build/audit passando.
5. Backtests politicos e benchmarks documentados.

### Laboratorio funcional

1. Simulacao Vila multiagente.
2. Psico-historia.
3. Game theory.
4. Mirofish-style pipeline.
5. Rede social sintetica.
6. Harness.
7. Agentes vivos.

### Experimental / precisa hardening

1. Workspace com escrita/leitura de arquivos, agora com path containment mas ainda sensivel por natureza.
2. Python sandbox exposto via API, agora com auth/rate quando `VILA_API_KEYS` existe.
3. Publicacao Mirante com git push, mitigada por auth/rate mas ainda administrativa.
4. Provedores LLM e web search em cascata.
5. Scripts de autoresearch/benchmarks pesados.

## 10. Como vender/explicar o projeto hoje

A descricao honesta:

> Vila INTEIA e uma plataforma multiagente e de forecasting que combina simulacao de agentes lendarios, backtests estatisticos, game theory, psico-historia e um produto cliente de predicao politica BR 2026. O modulo politico e o mais pronto comercialmente; o restante e um laboratorio operacional de inteligencia coletiva, simulacao e pesquisa.

Nao dizer:

1. Que todas as 200+ rotas estao prontas para cliente final.
2. Que todos os testes passam via `pytest`.
3. Que a seguranca esta pronta para internet sem configurar tokens.
4. Que LLM funciona sem chaves/servicos externos.
5. Que os 97.21% sao garantia futura; sao validacao historica nos dados/versionamento atual.

## 11. Plano recomendado de saneamento

### Semana 1 — deixar rodavel e seguro

| Item | Status |
|---|---|
| Atualizar `next` para `15.5.18+` | feito |
| Criar `frontend-next/package-lock.json` para commit | feito |
| Adicionar ESLint/ajustar lint do build | feito |
| Corrigir path traversal no workspace | feito |
| Bloquear endpoints perigosos com auth/rate | feito para workspace, Python sandbox e Mirante quando `VILA_API_KEYS` existe |
| Padronizar scripts com `argparse` e `--help` | feito para `backtest_political.py`, `predict_2026.py` e `bench_all_models.py` |
| Falhar startup em producao sem tokens | pendente |
| Exigir token admin especifico para `auto_push` | pendente |

### Semana 2 — testes e docs

1. Separar testes script-style de pytest-style.
2. Corrigir caminhos absolutos Linux.
3. Criar `requirements-dev.txt`.
4. Criar matriz de endpoints: publico, cliente, admin, interno.
5. Atualizar `MAP.md` e `MANIFEST.md` para refletir `frontend-next` e produto politico.

### Semana 3 — produto politico

1. Persistir clientes no Supabase.
2. Telemetria de uso por API key.
3. Rate-limit real por cliente anonimo tambem.
4. Job diario para `predict_2026.py`.
5. Deploy Next separado com env `VILA_API_BASE`.

### Semana 4 — pacote comercial

1. `docs/CLIENT_ONBOARDING.md` enxuto e atualizado.
2. Demo gravada com 3 fluxos: snapshot, predict custom, backtest.
3. Disclaimers juridicos e estatisticos.
4. Pagina de status e SLA.
5. Chaves de cliente provisionadas via admin seguro.

## 12. Checklist de uso rapido por objetivo

| Objetivo | Comando/URL |
|---|---|
| Subir API | `python main.py serve --port 8100` |
| Abrir dashboard politico | `http://localhost:8100/politica.html` |
| Abrir Swagger | `http://localhost:8100/docs` |
| Rodar smoke politico | `python scripts/smoke_political.py` |
| Ver predicao presidente | `GET /api/v1/politica/predictions/presidente` |
| Fazer predict custom | `POST /api/v1/politica/predict` |
| Rodar Vila pequena | `python main.py run --steps 10 --agentes 10` |
| Iniciar sim via API | `POST /api/v1/vila/iniciar` |
| Rodar step | `POST /api/v1/vila/step` |
| Ver agentes | `GET /api/v1/vila/agentes` |
| Game theory | `GET /api/v1/gametheory/hawk-dove` |
| Psico-historia | `GET /api/v1/psicohistoria/estacionaria` |
| Datasets | `GET /api/v1/backtest/datasets` |
| Mirofish datasets | `GET /api/v1/mirofish/datasets` |
| Harness saude | `GET /api/v1/harness/saude` |
| Metrics Prometheus | `GET /metrics` |
| Next dev | `cd frontend-next; npm run dev` |
| Next build | `cd frontend-next; npm run build` |

## 13. Conclusao

O projeto e real e executavel, mas nao e um produto unico simples. Ele e uma plataforma com um produto mais maduro no topo: **Predicao Politica BR 2026**. A API principal sobe, os routers importam, endpoints representativos respondem, o smoke politico passa, game theory passa, sandbox tem bloqueios basicos e o frontend Next agora passa lint, build e audit.

Ja foram corrigidos os pontos mais diretos de saneamento: update/lockfile do Next, ESLint, vulnerabilidades npm, path safety do workspace, protecao basica dos endpoints mais perigosos e scripts que escreviam arquivos ao receber `--help`. O proximo passo tecnico e fechar as decisoes de producao: startup deve falhar sem tokens, `auto_push` deve exigir admin real, a suite de testes precisa ser separada entre script-style e pytest-style, e o modulo politico deve ganhar persistencia/telemetria de clientes no Supabase.
