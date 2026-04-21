#!/usr/bin/env bash
# Onda 108: uptime check cron-friendly.
#
# Uso:
#   bash scripts/uptime_check.sh [BASE_URL]
#   # cron: */5 * * * * bash /app/scripts/uptime_check.sh https://vila.app >> /var/log/vila-uptime.log
#
# Exit 0 = all OK. Exit 1 = degradation. Exit 2 = down.

set -u

BASE="${1:-http://localhost:8900}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Liveness (must be 200)
LIVE=$(curl -s --max-time 5 -o /dev/null -w "%{http_code}" "$BASE/api/v1/vila/livez")
if [ "$LIVE" != "200" ]; then
  echo "$TIMESTAMP DOWN livez=$LIVE"
  exit 2
fi

# Readiness (200 or 503)
READY=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/api/v1/vila/readyz")
READY_CODE=$(echo "$READY" | tail -1)
READY_BODY=$(echo "$READY" | head -n -1)

# Step freshness (not stale)
STEP=$(curl -s --max-time 10 "$BASE/api/v1/vila/estado" | python -c "import json,sys;d=json.load(sys.stdin);print(d.get('step',-1))" 2>/dev/null || echo "-1")

# LLM budget
BUDGET=$(curl -s --max-time 10 "$BASE/api/v1/llm/stats" 2>/dev/null | python -c "import json,sys;d=json.load(sys.stdin);print(d.get('budget',{}).get('n_chamadas',0))" 2>/dev/null || echo "0")

if [ "$READY_CODE" = "200" ]; then
  echo "$TIMESTAMP OK step=$STEP llm_chamadas=$BUDGET"
  exit 0
else
  echo "$TIMESTAMP DEGRADED ready=$READY_CODE step=$STEP body=${READY_BODY:0:200}"
  exit 1
fi
