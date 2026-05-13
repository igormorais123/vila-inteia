#!/usr/bin/env bash
set -euo pipefail

# Wrapper para o Hermes da VPS operar a Vila INTEIA.
# Copiar para /root/.hermes/bin/hermes-vila e aplicar chmod +x.
#
# Variaveis opcionais:
#   VILA_INTEIA_URL=http://127.0.0.1:8090
#   VILA_API_TOKEN=<nao imprimir>
#   VILA_API_KEY=<nao imprimir>
#   VILA_REPO=/opt/vila-inteia

base="${VILA_INTEIA_URL:-http://127.0.0.1:8090}"
repo="${VILA_REPO:-/opt/vila-inteia}"
cmd="${1:-health}"
shift || true

headers=()
if [[ -n "${VILA_API_TOKEN:-}" ]]; then
  headers+=(-H "X-API-Token: ${VILA_API_TOKEN}")
fi
if [[ -n "${VILA_API_KEY:-}" ]]; then
  headers+=(-H "X-API-Key: ${VILA_API_KEY}")
fi

curl_get() {
  curl -fsS "${headers[@]}" "$base$1"
}

curl_post_json() {
  local path="$1"
  local payload="$2"
  curl -fsS "${headers[@]}" -H 'Content-Type: application/json' -d "$payload" "$base$path"
}

need_repo() {
  if [[ ! -d "$repo" ]]; then
    echo "Repositorio nao encontrado: $repo" >&2
    echo "Defina VILA_REPO=/caminho/da/vila-inteia" >&2
    exit 2
  fi
}

case "$cmd" in
  health)
    curl_get "/api/v1/vila/health"
    ;;
  docs)
    echo "$base/docs"
    ;;
  metrics)
    curl_get "/metrics"
    ;;
  politica-health)
    curl_get "/api/v1/politica/health"
    ;;
  politica-presidente)
    curl_get "/api/v1/politica/predictions/presidente"
    ;;
  politica-governador)
    uf="${1:-}"
    if [[ -z "$uf" ]]; then
      echo "Uso: hermes-vila politica-governador <UF>" >&2
      exit 2
    fi
    curl_get "/api/v1/politica/predictions/governador?uf=$uf"
    ;;
  politica-governadores)
    curl_get "/api/v1/politica/predictions/governador"
    ;;
  politica-senador)
    curl_get "/api/v1/politica/predictions/senador"
    ;;
  politica-all)
    curl_get "/api/v1/politica/predictions/all"
    ;;
  politica-backtest)
    curl_get "/api/v1/politica/backtest"
    ;;
  politica-me)
    curl_get "/api/v1/politica/me"
    ;;
  backtest-datasets)
    curl_get "/api/v1/backtest/datasets"
    ;;
  gametheory-hawk-dove)
    curl_get "/api/v1/gametheory/hawk-dove"
    ;;
  psicohistoria-estacionaria)
    curl_get "/api/v1/psicohistoria/estacionaria"
    ;;
  colmeia-ranking)
    curl_get "/api/v1/colmeia/ranking"
    ;;
  rede-stats)
    curl_get "/api/v1/rede/stats"
    ;;
  mirofish-datasets)
    curl_get "/api/v1/mirofish/datasets"
    ;;
  harness-saude)
    curl_get "/api/v1/harness/saude"
    ;;
  harness-skills)
    curl_get "/api/v1/harness/skills"
    ;;
  harness-metricas)
    curl_get "/api/v1/harness/metricas"
    ;;
  vila-iniciar)
    max_agentes="${1:-10}"
    curl_post_json "/api/v1/vila/iniciar" "{\"nome\":\"hermes-vps\",\"max_agentes\":$max_agentes}"
    ;;
  vila-step)
    n_steps="${1:-1}"
    curl_post_json "/api/v1/vila/step" "{\"n_steps\":$n_steps}"
    ;;
  vila-estado)
    curl_get "/api/v1/vila/estado"
    ;;
  vila-agentes)
    curl_get "/api/v1/vila/agentes"
    ;;
  repo-status)
    need_repo
    git -C "$repo" status --short
    ;;
  repo-commit)
    need_repo
    git -C "$repo" log -1 --oneline
    ;;
  smoke-politica)
    need_repo
    (cd "$repo" && python scripts/smoke_political.py)
    ;;
  compilecheck)
    need_repo
    (cd "$repo" && python -m compileall api engine scripts -q)
    ;;
  *)
    cat >&2 <<'USAGE'
Comandos:
  health, docs, metrics
  politica-health, politica-presidente, politica-governador <UF>,
  politica-governadores, politica-senador, politica-all, politica-backtest, politica-me
  backtest-datasets, gametheory-hawk-dove, psicohistoria-estacionaria,
  colmeia-ranking, rede-stats, mirofish-datasets
  harness-saude, harness-skills, harness-metricas
  vila-iniciar [max_agentes], vila-step [n], vila-estado, vila-agentes
  repo-status, repo-commit, smoke-politica, compilecheck
USAGE
    exit 2
    ;;
esac
