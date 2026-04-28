# Forecast Mega Bench

- Datasets: 5
- Total events: 140

## 1. Combined Report

- n: 140
- base_acc: 0.736
- base_brier: 0.2282
- bootstrap_brier_ci (95%): [0.1811, 0.2784]

### Selective forecasting

| tau | coverage | selective_acc | abstained |
|---|---|---|---|
| 0.00 | 100.00% | 73.57% | 0 |
| 0.15 | 65.71% | 73.91% | 48 |
| 0.30 | 40.00% | 71.43% | 84 |
| 0.40 | 27.86% | 74.36% | 101 |

### Conformal

- coverage: 96.43% (target 80.00%)
- mean_width: 0.869
- singleton_acc: 100.00%
- abstain_rate: 90.71%

### Murphy decomposition (global)

- brier: 0.2269
- reliability (REL): 0.0506
- resolution (RES): 0.0663
- uncertainty (UNC): 0.2427
- base_rate: 0.586

### Time-series CV

- folds: 4
- mean_acc: 75.00% ± 11.01%
- mean_brier: 0.2186 ± 0.0793

## 2. Per-Category Murphy

| dataset | n | brier | REL | RES | UNC |
|---|---|---|---|---|---|
| post_cutoff_q1_2027_holdout_v5 | 30 | 0.287 | 0.0747 | 0.0365 | 0.2489 |
| post_cutoff_q2_2026_holdout | 10 | 0.0279 | 0.0279 | 0.0 | 0.0 |
| post_cutoff_q2_2026_holdout_v2 | 40 | 0.1925 | 0.0097 | 0.0573 | 0.24 |
| post_cutoff_q3_2026_holdout_v3 | 30 | 0.1856 | 0.0506 | 0.0872 | 0.2222 |
| post_cutoff_q4_2026_holdout_v4 | 30 | 0.3242 | 0.1308 | 0.0466 | 0.24 |

## 3. Diebold-Mariano vs base-rate baseline

- loss: brier
- n: 140
- dm_stat: -0.662
- p_value: 0.5080
- mean_diff (Vila - baseline): -0.0144
- reject_h0 (alpha=0.05): False
- interpretation: Vila < baseline brier (better)

## 4. Hosmer-Lemeshow GoF

- n: 140
- chi_square: 152.372
- df: 8
- p_value (approx): 0.0
- reject_h0 (alpha=0.05): True

| g | n | mean_p | obs_rate | component |
|---|---|---|---|---|
| 0 | 14 | 0.215 | 0.214 | 0.0 |
| 1 | 14 | 0.427 | 0.214 | 2.6 |
| 2 | 14 | 0.486 | 0.286 | 2.257 |
| 3 | 14 | 0.634 | 0.786 | 1.386 |
| 4 | 14 | 0.76 | 0.429 | 8.394 |
| 5 | 14 | 0.791 | 1.0 | 3.699 |
| 6 | 14 | 0.841 | 0.571 | 7.561 |
| 7 | 14 | 0.964 | 0.5 | 86.088 |
| 8 | 14 | 0.993 | 0.857 | 40.309 |
| 9 | 14 | 0.994 | 1.0 | 0.078 |

## 5. PIT Histogram

- n: 140
- chi_square: 34.43
- slope: -0.082
- u_score: 0.571
- diagnosis: underconfident (U-shape)

| bin | count |
|---|---|
| [0.0, 0.1) | 31 |
| [0.1, 0.2) | 16 |
| [0.2, 0.3) | 15 |
| [0.3, 0.4) | 7 |
| [0.4, 0.5) | 8 |
| [0.5, 0.6) | 19 |
| [0.6, 0.7) | 6 |
| [0.7, 0.8) | 11 |
| [0.8, 0.9) | 15 |
| [0.9, 1.0) | 12 |

## 6. Reliability Diagram

| bin | mean_p | observed_rate | n | ci_lo | ci_hi |
|---|---|---|---|---|---|
| [0.0, 0.1) | 0.020 | 1.000 | 1 | 0.207 | 1.000 |
| [0.1, 0.2) | 0.125 | 0.000 | 6 | 0.000 | 0.390 |
| [0.2, 0.3) | 0.257 | 0.000 | 3 | 0.000 | 0.562 |
| [0.3, 0.4) | 0.377 | 0.444 | 9 | 0.189 | 0.733 |
| [0.4, 0.5) | 0.454 | 0.200 | 20 | 0.081 | 0.416 |
| [0.5, 0.6) | 0.545 | 1.000 | 1 | 0.207 | 1.000 |
| [0.6, 0.7) | 0.633 | 0.722 | 18 | 0.491 | 0.875 |
| [0.7, 0.8) | 0.787 | 0.758 | 33 | 0.590 | 0.872 |
| [0.8, 0.9) | 0.891 | 0.455 | 11 | 0.213 | 0.720 |
| [0.9, 1.0) | 0.993 | 0.763 | 38 | 0.608 | 0.870 |
