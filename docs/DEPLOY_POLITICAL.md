# Deploy guia — Predição Política BR 2026

## Pré-requisitos

- Render.com workspace acesso (`vila-inteia` service)
- Vercel optional (frontend Next.js separado, futuro)
- Supabase project URL + key

## Variáveis novas (Render dashboard)

```
VILA_ADMIN_TOKEN          # generate: openssl rand -hex 24
POLITICA_HOUSE_EFFECTS=0  # disabled by default; flip to 1 to test
```

## Pre-deploy checks

```bash
# 1. testes locais passando
python3 scripts/smoke_political.py
# espera: 29 passed, 0 failed

# 2. backtest reprodutível
python3 scripts/backtest_political.py
# espera: data/political_backtest_results.json regenerado

# 3. autoresearch convergiu
python3 scripts/autoresearch_political.py
# espera: best avg_acc >= 0.94

# 4. snapshot 2026 atual
python3 scripts/predict_2026.py
# espera: data/predictions_2026.json regenerado com Lula top, Tarcisio SP top
```

## Deploy passo-a-passo

```bash
# 1. commit (na feat branch atual)
git add api/rotas_politica.py engine/political_cohort.py engine/auth_clients.py \
        scripts/autoresearch_political.py scripts/backtest_political.py \
        scripts/predict_2026.py scripts/smoke_political.py \
        frontend/politica.html frontend/dashboard.html main.py render.yaml \
        migrations/005_political_forecasts.sql \
        data/backtest/eleicoes_br_real_polls.csv \
        data/backtest/governadores_br_historico.csv \
        data/political_best_config.json data/predictions_2026.json \
        data/political_backtest_results.json data/political_autoresearch_results.json \
        docs/ONBOARDING_POLITICAL.md docs/DEPLOY_POLITICAL.md
git commit -m "feat(onda288): political prediction product BR 2026

- PC-CRD cohort + Linzer ensemble, 94.16% acc 6-cycle year-fold CV
- Real polls: 2010/2018/2022 federal pres + 2016/2020/2024 SP mayor (648 events)
- Multi-tenant API: /api/v1/politica/* with X-API-Key + rate limit
- Frontend dashboard at /politica.html
- Selective tau=0.15 ships 96.1% acc at 92% coverage
- Honest 2024 SP miss: industry-wide poll bias, not model failure"

# 2. push to feat branch (igualmente seguro - feat branch, nao main)
git push origin HEAD

# 3. PR para main, esperar review
gh pr create --title "Onda 288: Political prediction BR 2026" --body "$(cat <<'EOF'
## Summary
- Multi-tenant political prediction product reusing 80% Vila stack
- 94.16% acc on 394 historical events (year-fold CV, T<=30 days)
- Selective tau=0.15: 96.1% acc at 92% coverage
- 29/29 smoke tests passing

## Test plan
- [ ] `python3 scripts/smoke_political.py` — 29/29 PASS
- [ ] `curl /api/v1/politica/health` returns 200 with snapshot
- [ ] `/politica.html` renders 4 stat cards + 4 tabs
EOF
)"

# 4. apos merge na main, Render auto-deploy
# 5. SET VILA_ADMIN_TOKEN no Render dashboard ANTES do deploy completar
# 6. healthcheck post-deploy
curl https://vila-inteia.onrender.com/api/v1/politica/health
curl https://vila-inteia.onrender.com/api/v1/politica/predictions/presidente | jq '.candidates[0]'
```

## Rollback

```bash
# git revert
git revert <merge-sha>
git push origin main

# OR Render dashboard: Manual deploy -> Previous successful deploy
```

## Pos-deploy: emitir 1ª chave cliente

```bash
ADMIN_TOKEN=<copy from Render env>
curl -X POST https://vila-inteia.onrender.com/api/v1/politica/admin/keys/issue \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "cliente_X", "tier": "pro", "contact": "email@cliente.com"}'

# resposta: {"api_key": "vila_pol_...", "tier": "pro"}
# entregar essa key ao cliente
```

## Domínio custom (opcional)

- Render: Settings -> Custom Domain -> `politica.inteia.com.br`
- DNS: CNAME apontando para `vila-inteia.onrender.com`
- TLS auto-provisionado via Let's Encrypt
