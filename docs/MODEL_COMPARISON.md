# Model comparison (year-fold CV, n=394, T<=30, seed=42)

| Model | Brier ↓ | Acc ↑ | n | Fit (s) | Predict (ms/ev) | Source |
|-------|--------:|------:|--:|--------:|----------------:|--------|
| M5b_vila_mrp_tuned | 0.1048 | 97.21% | 394 | - | - | baseline_gauntlet.json |
| Vila MRP tuned (this paper) | 0.1048 | 97.21% | 394 | - | - | political_stats_v2.json |
| M4_vila_baseline | 0.0889 | 94.16% | 394 | - | - | baseline_gauntlet.json |
| M1_linzer | 0.0750 | 91.88% | 394 | - | - | baseline_gauntlet.json |
| M3_naive | 0.0996 | 91.88% | 394 | - | - | baseline_gauntlet.json |
| Vila baseline (cohort+Linzer, no MRP) | 0.0725 | 91.88% | 394 | - | - | political_stats_v2.json |
| Stan DLM (Kalman, Linzer 2013) | 0.0786 | 86.80% | 394 | 0.06 | 0.0671 | bench_stan_dlm.json |
| BART (pymc_bart) | 0.1108 | 85.03% | 394 | 140.00 | - | bench_bart.json |
| M5_vila_mrp | 0.1346 | 80.96% | 394 | - | - | baseline_gauntlet.json |
| M2_cohort | 0.1997 | 59.64% | 394 | - | - | baseline_gauntlet.json |
