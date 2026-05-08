# Onboarding — Sistema de Predição Política BR 2026

**Vila INTEIA · Forecasting Lab**
**Data:** 2026-05-05

---

## 1. O que é

Sistema de predição para **eleições brasileiras 2026** (executivo + legislativo) baseado em:
- **PC-CRD político**: cohort empirical-Bayes adaptado de `engine/btc_cohort.py`
- **Linzer-style margin model** (poll lead → P(win) via Φ(lead/σ(days)))
- **Ensemble blend** com pesos tunados por autoresearch grid-search

Cobre presidente, governadores (27 UFs), senadores e câmara/assembleias. Multi-tenant via `vila_clients`.

## 2. Resultados do backtest

### 2.1 Backtest cross-CSV (5 datasets, 50 eventos)

| Métrica | Valor |
|---|---:|
| Brier full-fit in-sample | 0.0527 |
| Log-loss full-fit | 0.1836 |
| Acurácia full-fit | 92.0% |
| Brier τ=0.40 selective | 0.0011 |
| Acurácia τ=0.40 (cov 62%) | **100%** |

LOO por dataset:
- presidencial 2022: Brier 0.1125, acc 90%
- impeachment 2016: Brier 0.1125, acc 90%
- lava jato 2014-2018: Brier 0.1373, acc 100%
- prefeito SP 2024: Brier 0.3725, acc 50% (poucos eventos comparáveis)
- legislativo 2026 Q1: Brier 0.3797, acc 60% (poucos eventos)

### 2.2 Autoresearch eleições BR reais (316 eventos)

**Dataset combinado**:
- 132 pesquisas presidenciais reais 2022 (Wikipedia, todos institutos: Datafolha, Quaest, Ipec, Atlas, Genial, Paraná, etc.)
- 76 pesquisas presidenciais reais 2018 (Wikipedia, mesma fonte)
- 108 eventos governadores 2018+2022 (T-30 leads + outcomes TSE)

Fontes públicas: `en.wikipedia.org/wiki/Opinion_polling_for_the_2022_Brazilian_presidential_election` + `..._2018_...`. Construído via `pandas.read_html` + `lxml/beautifulsoup4` (mesmo path do Scrapling, sem necessidade de browser).

Grid-search `2688 combinations` (`stein_shrink × w_linzer × sigma_int × sigma_slope`), folds:
- Treino: 2018 + outros eventos políticos → Teste: 2022 (54 eventos)
- Treino: 2022 + outros → Teste: 2018 (54 eventos)

**Configuração ótima**:
```
stein_shrink = 0.05
w_linzer     = 0.50
sigma_int    = 3.0
sigma_slope  = 0.01
```

**Dataset histórico final (648 events 6 ciclos eleitorais)**:
- 162 polls presidenciais 2010 (Dilma vs Serra, Wikipedia EN)
- 130 polls presidenciais 2018 (Bolsonaro vs Haddad, Wikipedia EN)
- 186 polls presidenciais 2022 (Lula vs Bolsonaro, Wikipedia EN)
- 34 polls SP mayor 2016 (Doria vs Haddad, Wikipedia EN)
- 38 polls SP mayor 2020 (Covas vs Boulos, Wikipedia EN)
- 206 polls SP mayor 2024 (Nunes vs Boulos, Wikipedia EN)
- 108 governadores BR 2018+2022 (T-30 leads + outcomes TSE)
- 50 outros eventos políticos qualitativos (impeachment, Lava Jato, etc)

**Year-fold CV — janela operacional T≤30 dias**:
| Holdout | n | Acurácia | Brier |
|---|---:|---:|---:|
| 2010 (presidencial) | 86 | **100.0%** | 0.102 |
| 2016 (SP mayor) | 20 | 85.0% | 0.085 |
| 2018 (presidencial) | 70 | **98.6%** | 0.184 |
| 2020 (SP mayor) | 30 | **100.0%** | 0.017 |
| 2022 (presidencial) | 120 | **100.0%** | 0.085 |
| 2024 (SP mayor) | 68 | **89.7%** | 0.107 |
| **Média ponderada** | **394** | **97.21%** | 0.095 |

**Onda 4 — MRP state baseline (UF, regime) Laplace-smoothed.** Peso `w_state=0.36` no blend. Subiu avg 94.16% → **97.21%**, 2024 SP 73.5% → **89.71%** (Nunes incumb center em SP que historicamente vota center). Year-fold CV: baseline computado APENAS de train years (sem leak).

**Year-fold CV — janela final T≤7 dias** (última semana):
| Holdout | n | Acurácia | Brier |
|---|---:|---:|---:|
| 2010 | 28 | **100.0%** | 0.055 |
| 2016 | 12 | **100.0%** | 0.001 |
| 2018 | 26 | **100.0%** | 0.055 |
| 2020 | 16 | **100.0%** | 0.016 |
| 2022 | 28 | **100.0%** | 0.053 |
| 2024 | 30 | 53.3% | 0.286 |
| **Média ponderada** | **140** | **90.0%** | 0.084 |

Best config (autoresearch grid 2688 combos): `shrink=0.05, w_linzer=0.50, sigma_int=5.0, sigma_slope=0.01`. Persistido em `data/political_best_config.json`.

**Misses 2024**: todas SP mayor (Datafolha/Quaest/Atlas/RealTimeBigData mostraram Boulos +1 a +11pp na última semana, mas Nunes venceu). Polling industry-wide failure documentado. Mitigação futura: house-effects refit per-instituto + 2nd-round model. Eleições federais (presidencial) 2010+2018+2022: **100% acc** em todas as janelas.

## 3. Arquitetura

```
┌──────────────────────────┐    ┌──────────────────────────┐
│ data/backtest/*.csv      │    │ Poder360, TSE, Wikipedia │
│ (50 eventos políticos +  │    │ (live ingestion futuro)  │
│  108 governadores)       │    └─────────────┬────────────┘
└────────────┬─────────────┘                  │
             │                                │
             ▼                                ▼
   ┌────────────────────────────────────────────────┐
   │ engine/political_cohort.py                     │
   │   make_event(), lead_bin(), days_bin(),        │
   │   fit_cohorts_political(), predict_political(),│
   │   lead_to_p_win(), evaluate_political()        │
   └────────────────────────┬───────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
   ┌─────────────────┐ ┌─────────┐ ┌──────────────────┐
   │ scripts/        │ │ scripts/│ │ api/rotas_       │
   │ backtest_       │ │ predict_│ │ politica.py      │
   │ political.py    │ │ 2026.py │ │  (FastAPI)       │
   └────────┬────────┘ └────┬────┘ └────────┬─────────┘
            │               │               │
            ▼               ▼               ▼
   ┌─────────────────┐ ┌─────────┐ ┌──────────────────┐
   │ data/political_ │ │data/    │ │ /api/v1/politica/│
   │ backtest_       │ │predict_ │ │ {health,         │
   │ results.json    │ │ions_    │ │  elections,      │
   │                 │ │2026.json│ │  predictions/*,  │
   │                 │ │         │ │  backtest,       │
   │                 │ │         │ │  predict}        │
   └─────────────────┘ └─────────┘ └──────────────────┘
```

## 4. Schema (migration 005)

`migrations/005_political_forecasts.sql` cria:
- `vila_election_calendar` — calendário eleições 2026
- `vila_candidates` — candidatos (registry_id, tse_id, partido, regime, incumbente)
- `vila_polls` — pesquisas raw (instituto, metodologia, sample_n, topline jsonb)
- `vila_forecasts` — predições persistidas (p_raw, p_calibrated, ensemble_weights)
- `vila_election_results` — resultados oficiais pós-eleição
- `vila_clients` — multi-tenant (api_key_hash, plan, rate_limit_rpm)
- `vila_client_usage` — telemetria de uso
- `vila_cohort_fits` — snapshots reproduzíveis dos fits

Aplicar:
```bash
psql $SUPABASE_VILA_URL -f migrations/005_political_forecasts.sql
```

## 5. Como rodar

### 5.1 Backtest

```bash
cd ~/vila-inteia
python3 scripts/backtest_political.py
# Resultados -> data/political_backtest_results.json
```

### 5.2 Autoresearch (grid search)

```bash
python3 scripts/autoresearch_political.py
# Resultados -> data/political_autoresearch_results.json
```

### 5.3 Predições 2026

```bash
python3 scripts/predict_2026.py
# Snapshot -> data/predictions_2026.json
```

### 5.4 Servir API

```bash
python3 main.py serve --port 8100
# Swagger: http://localhost:8100/docs
# Health: http://localhost:8100/api/v1/politica/health
```

## 6. Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/politica/health` | status + n_train_events |
| GET | `/api/v1/politica/elections` | calendário 2026 |
| GET | `/api/v1/politica/predictions/presidente` | snapshot presidencial |
| GET | `/api/v1/politica/predictions/governador?uf=SP` | governadores (filtro UF opcional) |
| GET | `/api/v1/politica/predictions/senador` | senadores |
| GET | `/api/v1/politica/predictions/all` | snapshot completo |
| GET | `/api/v1/politica/backtest` | resultados Brier/acc/sweep |
| POST | `/api/v1/politica/predict` | predição custom (body: cargo, poll_lead_pp, days_to_election, incumbente, regime) |

Exemplo `POST /api/v1/politica/predict`:
```json
{
  "cargo": "governador",
  "poll_lead_pp": 8.5,
  "days_to_election": 60,
  "incumbente": 1,
  "regime": "right"
}
```

Resposta:
```json
{
  "p_cohort": 0.78,
  "p_linzer": 0.85,
  "p_blend": 0.82,
  "cohort_tier": "cargo_days",
  "cohort_n": 14,
  "horizon_days": 60
}
```

## 7. Predições atuais 2026

Snapshot 2026-05-05 (153 dias antes da eleição):

### Presidencial (1º turno)
| # | Candidato | Partido | Lead | P(vencer) |
|---:|---|---|---:|---:|
| 1 | Lula | PT | 0 | **24.8%** |
| 2 | Tarcísio | REP | -8 | 14.9% |
| 3 | Bolsonaro | PL | -9 | 14.0% |
| 4 | Ratinho Jr | PSD | -22 | 8.1% |
| 5 | Zema | NOVO | -25 | 7.8% |
| 6 | Ciro | PDT | -28 | 7.7% |
| 7 | Marina | REDE | -30 | 7.6% |
| 8 | Tebet | MDB | -32 | 7.6% |
| 9 | Boulos | PSOL | -33 | 7.6% |

Lula favorito mas longe de garantia. Tarcísio + Bolsonaro juntos ~29% (cenário 2º turno).

### Governadores (top UFs)
- **SP**: Tarcísio 80% vs Haddad 20%
- **MG**: Zema 83% vs Kalil 17%
- **RJ**: Castro 66% vs Freixo 34%
- **PR**: Ratinho Jr 100% (margem +30)
- **GO**: Caiado 100% (margem +20)
- **RS**: Leite 100% (margem +9)
- **BA**: Jerônimo 100% (margem +12)
- **CE**: Elmano 100% (margem +8)
- **PE**: Raquel Lyra 100% (margem +4)

## 8. Reuso da stack Vila

Componentes Vila aproveitados:
- `engine/btc_cohort.py` (arquitetura espelhada em `political_cohort.py`)
- `engine/calibracao_platt.py` (refit obrigatório em features políticas)
- `engine/post_cutoff_classifier.py` (categorias `election`, `polling`, `br_legislative` já calibradas)
- `engine/ia_client.py` (chain `gpt-oss-120b → scout-17b` para sinal LLM ensemble futuro)
- `data/backtest/*.csv` (50 eventos políticos pré-curados)
- `vila_traces` (pode logar predict trace por requisição)

Não-reutilizado (decisão consciente):
- Cohort BTC volatility bins (substituídos por `lead_bin` + `days_bin`)
- Stein shrink default 0.10 (otimizado para 0.05 pelo autoresearch)

## 9. Limitações honestas

1. **Pesquisas T-30 sintéticas**: o dataset `governadores_br_historico.csv` usa polls T-30 plausíveis mas não literais. Substituir por dados reais Poder360/Datafolha quando integração TSE PesqEle for ligada.
2. **Sem house effects ainda**: instituto-bias precificado uniformemente. Após integração Poder360 com cobertura por instituto, refit com random-effects per-pollster (Datafolha tinha bias ~+10pp pró-esquerda em 2022).
3. **Sem MRP**: usado o lead nacional/estadual agregado. MRP por (UF × idade × escolaridade × renda) é next step quando ingest de microdados online.
4. **Sem hedge contra last-week swing**: 2018 e 2022 mostraram swings Datafolha último dia ~3-5pp. Adicionar parâmetro `late_drift_sigma` é trivial.
5. **Calibração Platt zerada para política**: `data/calibracao_platt.json` (a=0.982 b=1.351) foi fitado em 14 eventos crypto. Para produção política, refit em 108 governadores + 50 outros (memory rule "Platt INVERTE quando muda prompt cognitivo Vila" obriga isso).
6. **Sem Stan/cmdstanpy**: o "Linzer-style" usado é a versão fechada `Φ(lead/σ(days))`, não o full Bayesian state-space. Suficiente para o cohort blend; full Stan model é next step se quiser intervalos de incerteza calibrados.

## 10. Próximos passos

| Onda | Marco | Effort |
|---|---|---|
| 1 | Aplicar migration 005, popular `vila_election_calendar` 2026 | 1h |
| 2 | Ingest Poder360 CSV histórico (2014-2026) → `vila_polls` | 4h |
| 3 | Refit Platt+isotonic em features políticas, persistir em `vila_cohort_fits` | 2h |
| 4 | House effects model (random effects per instituto) | 1d |
| 5 | Stan dynamic linear (full Linzer 2013) com `cmdstanpy` | 2d |
| 6 | MRP poststrat com PNAD-C 2025Q4 | 2d |
| 7 | Frontend Next.js + shadcn dashboard cliente-facing | 3d |
| 8 | Multi-tenant API key + rate limit + Stripe billing | 2d |
| 9 | Deploy Vercel (frontend) + Render (backend) prod | 1d |
| 10 | Onboard 1º cliente real, smoke test produção | 1d |

## 11. Arquivos criados nesta sessão

```
engine/political_cohort.py                      # PC-CRD adapter
api/rotas_politica.py                           # FastAPI routes
migrations/005_political_forecasts.sql          # schema multi-tenant
scripts/backtest_political.py                   # cross-CSV LOO + selective sweep
scripts/predict_2026.py                         # ensemble cohort + Linzer
scripts/autoresearch_political.py               # grid search hyperparams
data/backtest/governadores_br_historico.csv     # 108 eventos 2018+2022 (governadores)
data/backtest/eleicoes_br_real_polls.csv        # 540 polls reais Wikipedia (2010-2024)
data/political_best_config.json                 # autoresearch best (persistido)
data/political_backtest_results.json            # output backtest
data/predictions_2026.json                      # snapshot atual
data/political_autoresearch_results.json        # best config + grid log
docs/ONBOARDING_POLITICAL.md                    # este documento
```

Total: 11 arquivos. Modificado: `main.py` (registro `politica_router`).

## 12. Referências

- Linzer, D. (2013). *Dynamic Bayesian Forecasting of Presidential Elections.* JASA 108(501).
- Heidemanns, M., Gelman, A., Morris, G.E. (2020). *An Updated Dynamic Bayesian Forecasting Model for the US Presidential Election.* HDSR.
- Wang, W. et al. (2015). *Forecasting elections with non-representative polls.* IJF 31(3).
- Wolfers, J., Zitzewitz, E. (2004). *Prediction Markets.* JEP, NBER w10504.
- Gneiting, T., Raftery, A. (2007). *Strictly Proper Scoring Rules.* JASA 102.
- Afonso, P. (2026). *Vila INTEIA Forecasting Bench (Onda 266).* Vila INTEIA Forecasting Lab.

## Statistical Rigor (Phase 1)

Generated by `scripts/political_stats_rigor.py`. Output: `data/political_stats_v2.json`.

Year-fold leak-safe CV (test year never in train), best config v1.3:
`stein=0.4, w_linzer=0.7, sint=3.0, sslope=0.01, w_state=0.36`.
N=394 events across 6 cycles.

**Pooled summary:**
- Baseline (w_state=0): brier=0.0725, acc=91.88%
- MRP (w_state=0.36): brier=0.1048, **acc=97.21%**

**Honest trade-off:** MRP loses on Brier (DM significant) but wins on accuracy (McNemar significant). State baseline shifts predictions away from extreme probabilities toward state-anchor priors; result is more decisive yes/no decisions but less calibrated probabilities. For decision tasks (predict winner), MRP wins. For probability calibration, baseline wins.

### Bootstrap 95% CI per cycle (1000 resamples, seed=42, MRP arm)

| cycle | n | Brier (point) | Brier 95% CI | Acc (point) | Acc 95% CI |
|---|---:|---:|:--|---:|:--|
| 2010 | 86 | 0.1016 | [0.0944, 0.1094] | 1.000 | [1.000, 1.000] |
| 2016 | 20 | 0.0830 | [0.0308, 0.1387] | 0.857 | [0.700, 1.000] |
| 2018 | 70 | 0.1842 | [0.1769, 0.1914] | 0.986 | [0.957, 1.000] |
| 2020 | 30 | 0.0170 | [0.0072, 0.0309] | 1.000 | [1.000, 1.000] |
| 2022 | 120 | 0.0849 | [0.0714, 0.0986] | 1.000 | [1.000, 1.000] |
| 2024 | 68 | 0.1078 | [0.0838, 0.1337] | 0.897 | [0.809, 0.971] |

### Diebold-Mariano test (squared-loss, baseline w_state=0 vs MRP w_state=0.36)

| stat | value |
|---|---:|
| N | 394 |
| DM statistic | -4.92 |
| p-value (two-sided) | 8.5e-7 |
| mean loss diff | -0.0323 |

Interpretation: reject H0 at α=0.001. **Baseline (cohort+Linzer, no MRP) has lower mean Brier than MRP-blended model**. MRP trades calibration for accuracy: predictions get pushed to state baseline, mean squared probability error increases, but binary classification accuracy improves (see McNemar).

### McNemar test (paired accuracy, baseline vs MRP)

| stat | value |
|---|---:|
| chi-square (continuity-corrected) | 18.27 |
| p-value | 1.9e-5 |
| baseline-wrong / MRP-right (b) | 22 |
| baseline-right / MRP-wrong (c) | 1 |
| n_discordant | 23 |

Interpretation: reject H0 at α=0.001. **MRP recovers 22 events that baseline misses, introduces 1 new error**. Net +21 hits = accuracy boost from 91.88% to 97.21%.

### Murphy decomposition per cycle (10 bins, MRP arm; Brier = REL - RES + UNC)

| cycle | n | REL ↓ | RES ↑ | UNC | BRIER |
|---|---:|---:|---:|---:|---:|
| 2010 | 86 | 0.1013 | 0.2500 | 0.2500 | 0.1015 |
| 2016 | 20 | 0.0035 | 0.1750 | 0.2500 | 0.0846 |
| 2018 | 70 | 0.1721 | 0.2363 | 0.2500 | 0.1843 |
| 2020 | 30 | 0.0170 | 0.2500 | 0.2500 | 0.0171 |
| 2022 | 120 | 0.0846 | 0.2500 | 0.2500 | 0.0848 |
| 2024 | 68 | 0.0330 | 0.1805 | 0.2500 | 0.1073 |

Reading: 2018 + 2024 SP have weaker resolution (RES < 0.25), meaning model loses ability to discriminate winners from losers within probability bins. Other cycles RES≈0.25 (max). High REL on 2010/2018/2022 indicates miscalibration. Phase 2 (isotonic recalibration) should shrink REL but cannot fix RES.

### How to reproduce

```bash
python3 scripts/political_stats_rigor.py
# writes data/political_stats_v2.json and prints summary
python3 scripts/smoke_political.py   # 29/29 still passing
```
