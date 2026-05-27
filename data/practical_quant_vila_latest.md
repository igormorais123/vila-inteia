# Vila Practical Quant Run

- Generated: `2026-05-14T01:36:04`
- Released backtest rows: `7679` from `63` CSV files
- Future rows held out: `169`

## Political Operating Edge

| model | n | acc | brier | auc | mcc | ece |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 394 | 0.9188 | 0.0722 | - | - | - |
| mrp | 394 | 0.9721 | 0.1046 | - | - | - |
| evolved_best | 394 | 0.9721 | 0.1046 | 0.9916 | 0.9442 | 0.2610 |

## Dataset Hotspots

| dataset | n | prior_acc | prior_brier | outcome_rate | mean_abs_lead |
|---|---:|---:|---:|---:|---:|
| post_cutoff_q1_2026_v2 | 10 | 0.4000 | 0.3553 | 1.0000 | - |
| uk_2019_general | 192 | 0.5365 | 0.2955 | 0.5000 | 15.3635 |
| price_predictions_q1_2026 | 30 | 0.5000 | 0.2500 | 0.5000 | - |
| seed_eleicao_municipal_sp_2024 | 10 | 0.7000 | 0.2497 | 0.5000 | - |
| brazil_votes_q1_2026 | 10 | 0.6000 | 0.2280 | 0.6000 | - |
| post_cutoff_q2_2026_holdout | 9 | 0.5556 | 0.2064 | 1.0000 | - |
| eleicoes_br_real_polls | 648 | 1.0000 | 0.2025 | 0.5000 | 10.7354 |
| pharma_drugtrials_q1_2026 | 6 | 0.6667 | 0.1879 | 0.3333 | - |
| post_cutoff_q1_2026 | 10 | 0.6000 | 0.1833 | 0.1000 | - |
| manufacturing_industrial_q1_2026 | 10 | 1.0000 | 0.1800 | 0.8000 | - |
| corporate_ma_q1_2026 | 10 | 0.9000 | 0.1728 | 0.6000 | - |
| insurance_reinsurance_q1_2026 | 10 | 1.0000 | 0.1695 | 0.8000 | - |

## Quant Signals

| x | y | n | spearman_r | q_bh |
|---|---|---:|---:|---:|
| probabilidade_prior | poll_lead_pp | 7138 | 0.9750 | 0.0000 |
| abs_poll_lead_pp | prior_confidence | 7138 | 0.9227 | 0.0000 |
| prior_brier | prior_confidence | 7679 | -0.8936 | 0.0000 |
| abs_poll_lead_pp | prior_brier | 7138 | -0.8273 | 0.0000 |
| outcome_real | probabilidade_prior | 7679 | 0.7966 | 0.0000 |
| outcome_real | poll_lead_pp | 7138 | 0.7841 | 0.0000 |
| prior_brier | prior_correct | 7679 | -0.4989 | 0.0000 |
| abs_poll_lead_pp | prior_correct | 7138 | 0.3299 | 0.0000 |
| incumbente | context_len | 7679 | -0.3282 | 0.0000 |
| prior_correct | prior_confidence | 7679 | 0.3117 | 0.0000 |

### GLM Outcome

- Formula: `outcome_real ~ probabilidade_prior + poll_lead_pp + incumbente`

| term | estimate | odds_ratio | p |
|---|---:|---:|---:|
| Intercept | -9.4337 | 0.0001 | 0.0000 |
| probabilidade_prior | 18.7280 | 135983836.5606 | 0.0000 |
| poll_lead_pp | 0.0366 | 1.0372 | 0.0000 |
| incumbente | 0.3392 | 1.4038 | 0.0011 |

## Gauntlet Runtime

- Total: `174`/`174` passed
- Runtime: `134.176` seconds

| slow test | area | seconds |
|---|---|---:|
| test_llm_forecaster.py | forecasting | 91.465 |
| test_benchmark.py | core | 50.901 |
| test_hybrid_autotune.py | core | 32.908 |
| npm_build | frontend | 26.107 |
| test_bateria.py | vila_sim | 21.321 |
| test_ondas_28_30.py | vila_sim | 10.848 |
| test_practical_quant_vila.py | quant | 9.518 |
| test_quant_analysis.py | quant | 8.360 |

## Practical Actions

1. **politica**: Use MRP as classifier edge and add a calibrated probability layer before exposing raw probabilities. Evidence: MRP acc 0.9721 > baseline 0.9188, but Brier 0.1046 > baseline 0.0722.
2. **calibracao**: Open a year-fold calibration task focused on the highest-ECE cycle. Evidence: Year 2018 ECE=0.4124, Brier=0.1840, n=70.
3. **dados**: Review the worst dataset by prior Brier and add it to the next focused validation batch. Evidence: post_cutoff_q1_2026_v2 prior_brier=0.3553, n=10.
4. **testes**: Keep the slowest test in a performance watchlist and split it if it grows further. Evidence: test_llm_forecaster.py took 91.465s.
