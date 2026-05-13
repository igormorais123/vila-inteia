# Handoff Hermes VPS — Vila INTEIA

Fonte: `docs/AUDITORIA_COMPLETA_2026-05-13.md`
Data: 2026-05-13
Repositorio: `https://github.com/igormorais123/vila-inteia.git`
Branch: `main`
Commit auditado inicialmente: `0d9fd96 docs(onda7): linter-improved bench_all_models.py + BENCHMARKS.md (#230)`
Commit de saneamento aplicado: `fa5c9a2 fix: harden vila audit findings`

Este documento e o pacote curto que pode ser passado ao Hermes da VPS para ele acompanhar a Vila INTEIA como projeto ativo e usar a Vila como ponto operacional de consulta, monitoramento e execucao.

## 1. O que passar para o Hermes da VPS

Arquivos recomendados para memoria da VPS:

| Origem local | Destino sugerido na VPS | Funcao |
|---|---|---|
| `docs/AUDITORIA_COMPLETA_2026-05-13.md` | `/root/.hermes/memories/project-roots/vila-inteia/AUDITORIA_COMPLETA_2026-05-13.md` | Fonte completa da auditoria |
| `docs/HERMES_VPS_HANDOFF_2026-05-13.md` | `/root/.hermes/memories/project-roots/vila-inteia/HERMES_VPS_HANDOFF_2026-05-13.md` | Resumo operacional para o Hermes |
| `docs/hermes-vila-wrapper-vps.sh` | `/root/.hermes/bin/hermes-vila` | Wrapper para o Hermes usar a API |
| `README.md`, `MAP.md`, `MANIFEST.md`, `HARNESS_VILA.md` | `/root/.hermes/memories/project-roots/vila-inteia/readmes/` | Contexto canonico do projeto |
| `docs/DEPLOY.md`, `docs/DEPLOY_POLITICAL.md`, `docs/ONBOARDING_POLITICAL.md` | `/root/.hermes/memories/project-roots/vila-inteia/deploy/` | Runbook de deploy e produto politico |
| `migrations/005_political_forecasts.sql` | `/root/.hermes/memories/project-roots/vila-inteia/sql/` | Schema previsto do produto politico |

Nao passar para memoria nem backup sanitizado:

1. `.env`, `.env.*`, arquivos de auth, cookies, tokens, profiles de browser.
2. `data/clients.json` se tiver API keys reais de clientes.
3. Valores de `SUPABASE_*`, `MIRANTE_*`, `OMNIROUTE_*`, `GROQ_*`, `GEMINI_*`, `CLAUDE_*`, `VILA_API_*`.
4. Dumps ou logs que tragam headers, tokens, dados de cliente ou prompts privados.

Regra: a VPS deve registrar apenas nome da variavel e status operacional: presente, ausente, validada, invalida ou pendente.

## 2. Ponto atual do projeto

A Vila INTEIA esta executavel e grande. Ela nao e so uma simulacao narrativa: inclui API FastAPI, frontends, datasets, forecasting, game theory, psico-historia, observabilidade, scripts de benchmark e produto de predicao politica BR 2026.

Produto mais pronto:

1. Predicao Politica BR 2026.
2. API FastAPI local.
3. Frontend politico estatico.
4. Dashboard Next.js com lint, build e audit passando.
5. Backtests politicos e benchmarks documentados.

Laboratorio funcional:

1. Vila multiagente.
2. Psico-historia.
3. Game theory.
4. Mirofish-style pipeline.
5. Rede social sintetica.
6. Harness, traces, orcamento, skills e fundador.
7. Agentes vivos Helena/Efesto.

Ainda nao tratar como produto publico sem hardening:

1. Workspace e Python sandbox expostos por API.
2. Publicacao Mirante com `auto_push`.
3. Scripts de autoresearch/benchmarks pesados.
4. Rotas dependentes de LLM, Supabase e provedores externos.

## 3. Como o Hermes deve operar a Vila na VPS

Na VPS ja existe historico de wrapper em `/root/.hermes/bin/hermes-vila`, apontando para `http://127.0.0.1:8090`. Se a instancia continuar nessa porta, manter:

```bash
export VILA_INTEIA_URL="http://127.0.0.1:8090"
```

No ambiente local de desenvolvimento, a auditoria usa porta `8100`:

```bash
python main.py serve --port 8100
```

Na VPS, preferir porta `8090` se o servico atual ja estiver nesse padrao:

```bash
cd /opt/vila-inteia
python -m pip install -r requirements.txt
python main.py serve --port 8090
```

Rotas basicas de saude que o Hermes deve conhecer:

| Objetivo | Endpoint |
|---|---|
| Saude Vila agregada | `GET /api/v1/vila/health` |
| Saude politica | `GET /api/v1/politica/health` |
| Swagger | `GET /docs` |
| Metrics Prometheus | `GET /metrics` |
| Harness | `GET /api/v1/harness/saude` |
| Skills harness | `GET /api/v1/harness/skills` |

## 4. Comandos que valem entrar no wrapper `hermes-vila`

Adicionar ou manter comandos equivalentes no wrapper da VPS:

```bash
hermes-vila health
hermes-vila politica-health
hermes-vila politica-presidente
hermes-vila politica-governador SP
hermes-vila politica-senador
hermes-vila politica-all
hermes-vila backtest-datasets
hermes-vila harness-saude
hermes-vila harness-skills
hermes-vila metrics
hermes-vila vila-estado
hermes-vila vila-agentes
```

Mapeamento sugerido:

| Comando | Chamada |
|---|---|
| `politica-health` | `GET /api/v1/politica/health` |
| `politica-presidente` | `GET /api/v1/politica/predictions/presidente` |
| `politica-governador UF` | `GET /api/v1/politica/predictions/governador?uf=UF` |
| `politica-senador` | `GET /api/v1/politica/predictions/senador` |
| `politica-all` | `GET /api/v1/politica/predictions/all` |
| `backtest-datasets` | `GET /api/v1/backtest/datasets` |
| `harness-saude` | `GET /api/v1/harness/saude` |
| `harness-skills` | `GET /api/v1/harness/skills` |
| `metrics` | `GET /metrics` |
| `vila-estado` | `GET /api/v1/vila/estado` |
| `vila-agentes` | `GET /api/v1/vila/agentes` |

## 5. Variaveis que a VPS deve checar, sem revelar valor

Obrigatorias antes de expor publicamente:

| Variavel | Uso |
|---|---|
| `VILA_API_TOKEN` | Auth global quando configurada |
| `VILA_API_KEYS` | API keys para endpoints custosos/sensiveis |
| `VILA_ADMIN_TOKEN` | Rotas administrativas do produto politico |

LLM e pesquisa:

| Variavel | Uso |
|---|---|
| `OMNIROUTE_URL` | Gateway OmniRoute |
| `OMNIROUTE_API_KEY` | Chave OmniRoute |
| `GROQ_API_KEY` | Groq |
| `GEMINI_API_KEY` | Gemini |
| `CLAUDE_API_KEY` | Anthropic fallback |
| `IA_ALLOW_API_FALLBACK` | Permite fallback pago |
| `OSA_URL` | Optimal System Agent |

Persistencia e integracoes:

| Variavel | Uso |
|---|---|
| `SUPABASE_VILA_URL` | Supabase Vila |
| `SUPABASE_VILA_KEY` | Chave Supabase Vila |
| `MIRANTE_API_URL` | Publicacao Mirante |
| `MIRANTE_API_TOKEN` | Token Mirante |
| `MIRANTE_CONTENT_DIR` | Fallback dev Mirante |
| `VILA_API_BASE` | Base da API para frontend Next.js |

## 6. Monitoramento minimo

Checks frequentes, a cada 5 a 15 minutos:

1. `GET /api/v1/vila/health`
2. `GET /api/v1/politica/health`
3. `GET /api/v1/harness/saude`
4. `GET /metrics`

Checks diarios:

1. `python scripts/smoke_political.py` deve manter `29 passed, 0 failed`.
2. `GET /api/v1/politica/predictions/presidente` deve retornar candidatos.
3. `GET /api/v1/backtest/datasets` deve listar datasets.
4. `GET /api/v1/gametheory/hawk-dove` deve responder.

Checks semanais:

1. `python -m compileall api engine scripts -q`
2. `python -m pytest tests/test_workspace_security.py -q`
3. `python tests/test_game_theory.py`
4. `cd frontend-next && npm run lint && npm run build && npm audit --json`

## 7. Alertas que o Hermes deve levantar

Alertar Igor se:

1. A API cair ou `/api/v1/politica/health` falhar.
2. `VILA_API_TOKEN`, `VILA_API_KEYS` ou `VILA_ADMIN_TOKEN` estiverem ausentes em ambiente de producao.
3. O endpoint Mirante com `auto_push` estiver exposto fora de rede interna.
4. `python scripts/smoke_political.py` deixar de passar.
5. `npm audit --json` voltar vulnerabilidade no `frontend-next`.
6. O snapshot politico ficar velho em relacao ao ciclo de atualizacao definido.
7. O Hermes detectar arquivo de segredo sendo copiado para memoria, repo ou backup.

## 8. Proximas tarefas tecnicas para acompanhar

Prioridade 1:

1. Falhar startup em producao quando tokens essenciais estiverem vazios.
2. Exigir token admin especifico para `auto_push`.
3. Confirmar se a instancia VPS esta no commit `fa5c9a2` ou posterior.
4. Atualizar wrapper `hermes-vila` com comandos politicos e harness.

Prioridade 2:

1. Separar testes script-style de pytest-style.
2. Criar `requirements-dev.txt` e/ou `requirements-research.txt`.
3. Criar matriz de endpoints: publico, cliente, admin, interno.
4. Atualizar `MAP.md` e `MANIFEST.md` para refletir `frontend-next` e produto politico.

Prioridade 3:

1. Persistir clientes e usage no Supabase (`vila_clients`, `vila_client_usage`).
2. Criar job diario para `predict_2026.py`.
3. Deploy separado do Next.js com `VILA_API_BASE`.
4. Preparar `docs/CLIENT_ONBOARDING.md` enxuto.

## 9. Resumo curto para `MEMORY.md` da VPS

```markdown
## 2026-05-13 — Vila INTEIA auditada e pronta para acompanhamento pelo Hermes VPS

Fonte: `/root/.hermes/memories/project-roots/vila-inteia/AUDITORIA_COMPLETA_2026-05-13.md`.
Repo: `https://github.com/igormorais123/vila-inteia.git`, branch `main`, commit auditado inicialmente `0d9fd96`, com saneamento aplicado em `fa5c9a2`.

Estado: plataforma executavel com API FastAPI, frontends, datasets, forecasting, game theory, psico-historia, harness e produto principal de Predicao Politica BR 2026. Modulo politico e o mais pronto para produto; Vila multiagente, psico-historia, game theory, Mirofish, rede sintetica e agentes vivos sao laboratorio funcional.

Hermes VPS deve usar `hermes-vila` para health, politica, backtests, harness e metricas. Antes de exposicao publica, checar `VILA_API_TOKEN`, `VILA_API_KEYS` e `VILA_ADMIN_TOKEN` sem registrar valores. Nao copiar `.env`, `data/clients.json` com chaves reais, tokens Mirante/Supabase/LLM ou perfis de browser. Riscos principais: auth desligada se env vazio, `auto_push` Mirante, Python sandbox/workspace e suite de testes ainda misturando script-style com pytest-style.
```

## 10. Criterio de aceite para dizer que a VPS absorveu o projeto

1. Arquivos de memoria copiados para `/root/.hermes/memories/project-roots/vila-inteia/`.
2. `MEMORY.md` da VPS atualizado com o resumo curto.
3. `docs/hermes-vila-wrapper-vps.sh` instalado como `/root/.hermes/bin/hermes-vila`.
4. `hermes-vila health` responde.
5. `hermes-vila politica-health` responde.
6. `hermes-vila politica-presidente` responde ranking.
7. `hermes-vila harness-saude` responde.
8. Checks de segredo confirmam variaveis por status, sem imprimir valores.
9. Monitoramento diario configurado para smoke politico e health.
