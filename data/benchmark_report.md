# Vila INTEIA Benchmark Report

**Datasets**: 11 · **Total events**: 110

## Comparison vs Baselines

| Method | Accuracy | Brier | NLL | ECE | Skill vs Prior |
|---|---|---|---|---|---|
| **vila** | 92.7% | 0.0664 | 0.2581 | 0.1019 | +55.4% |
| **prior_humano** | 90.0% | 0.1489 | 0.4760 | 0.2532 | +0.0% |
| **chance** | 73.6% | 0.2500 | 0.6931 | 0.2364 | -67.8% |
| **majority** | 73.6% | 0.2636 | 5.4634 | 0.2636 | -77.0% |
| **random** | 56.4% | 0.3236 | 1.0328 | 0.3287 | -117.2% |

## Per-Dataset Vila Accuracy

| Dataset | N | Hits | Acc |
|---|---|---|---|
| americanas_crise_2023 | 10 | 10 | 100% |
| crypto_bitcoin_2024 | 10 | 10 | 100% |
| eleicao_presidencial_br_2022 | 10 | 10 | 100% |
| impeachment_dilma_2016 | 10 | 10 | 100% |
| lancamento_apple_vpro_2024 | 10 | 10 | 100% |
| lava_jato_2014_2018 | 10 | 10 | 100% |
| pix_adoption_2020 | 10 | 10 | 100% |
| post_cutoff_q1_2026 | 10 | 2 | 20% |
| seed_eleicao_municipal_sp_2024 | 10 | 10 | 100% |
| tiktok_viral_2024 | 10 | 10 | 100% |
| twitter_musk_2022_2024 | 10 | 10 | 100% |

## ⚠ Knowledge Leak Audit (Onda 229)
- **Pré-cutoff** (2026-01-01): 100 events
- **Pós-cutoff**: 10 events
- **Leak ratio**: 90.9%

> ⚠ KNOWLEDGE LEAK RISK: events ocorreram antes do LLM cutoff. Resultados refletem memorização, não forecasting. Para validação rigorosa, use eventos POST-cutoff (ForecastBench-style).

## Diebold-Mariano Tests (Vila vs Baselines)

| Comparison | DM Stat | p-value | Significant (p<0.05) |
|---|---|---|---|
| Vila vs prior_humano | -5.827 | 0.0000 | ✓ |
| Vila vs chance | -12.841 | 0.0000 | ✓ |
| Vila vs majority | -5.277 | 0.0000 | ✓ |
| Vila vs random | -7.977 | 0.0000 | ✓ |

## Vila — Murphy Decomposition
- **Brier** = REL (0.0124) − RES (0.1385) + UNC (0.1941) = 0.0680
- **Reliability** baixo melhor (calibração)
- **Resolution** alto melhor (discriminação)
- **Uncertainty** = obs base rate × (1 - base rate)

## Vila — Bootstrap 95% CI (1000 resamples)
- **Brier**: 0.0664 [0.0415, 0.0931]
- **Accuracy**: 92.7% [88.2%, 97.3%]

## Vila — ROC AUC
- **AUC** = 0.9691 (n_pos=81, n_neg=29)