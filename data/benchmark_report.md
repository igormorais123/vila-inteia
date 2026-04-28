# Vila INTEIA Benchmark Report

**Datasets**: 10 · **Total events**: 100

## Comparison vs Baselines

| Method | Accuracy | Brier | NLL | ECE | Skill vs Prior |
|---|---|---|---|---|---|
| **vila** | 100.0% | 0.0256 | 0.1639 | 0.1492 | +82.4% |
| **prior_humano** | 93.0% | 0.1455 | 0.4690 | 0.2810 | +0.0% |
| **chance** | 80.0% | 0.2500 | 0.6931 | 0.3000 | -71.8% |
| **majority** | 80.0% | 0.2000 | 4.1447 | 0.2000 | -37.4% |
| **random** | 56.0% | 0.3398 | 1.0616 | 0.3806 | -133.5% |

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
| seed_eleicao_municipal_sp_2024 | 10 | 10 | 100% |
| tiktok_viral_2024 | 10 | 10 | 100% |
| twitter_musk_2022_2024 | 10 | 10 | 100% |

## ⚠ Knowledge Leak Audit (Onda 229)
- **Pré-cutoff** (2026-01-01): 100 events
- **Pós-cutoff**: 0 events
- **Leak ratio**: 100.0%

> ⚠ KNOWLEDGE LEAK RISK: events ocorreram antes do LLM cutoff. Resultados refletem memorização, não forecasting. Para validação rigorosa, use eventos POST-cutoff (ForecastBench-style).

## Diebold-Mariano Tests (Vila vs Baselines)

| Comparison | DM Stat | p-value | Significant (p<0.05) |
|---|---|---|---|
| Vila vs prior_humano | -15.913 | 0.0000 | ✓ |
| Vila vs chance | -114.184 | 0.0000 | ✓ |
| Vila vs majority | -4.390 | 0.0000 | ✓ |
| Vila vs random | -9.797 | 0.0000 | ✓ |

## Vila — Murphy Decomposition
- **Brier** = REL (0.0251) − RES (0.1600) + UNC (0.1600) = 0.0251
- **Reliability** baixo melhor (calibração)
- **Resolution** alto melhor (discriminação)
- **Uncertainty** = obs base rate × (1 - base rate)

## Vila — Bootstrap 95% CI (1000 resamples)
- **Brier**: 0.0256 [0.0221, 0.0294]
- **Accuracy**: 100.0% [100.0%, 100.0%]

## Vila — ROC AUC
- **AUC** = 1.0000 (n_pos=80, n_neg=20)