# Forecast Mega Bench

- Datasets: 3
- Total events: 80

## 1. Combined Report

- n: 80
- base_acc: 0.8
- base_brier: 0.172
- bootstrap_brier_ci (95%): [0.1184, 0.2268]

### Selective forecasting

| tau | coverage | selective_acc | abstained |
|---|---|---|---|
| 0.00 | 100.00% | 80.00% | 0 |
| 0.15 | 65.00% | 84.62% | 28 |
| 0.30 | 42.50% | 85.29% | 46 |
| 0.40 | 32.50% | 84.62% | 54 |

### Conformal

- coverage: 88.75% (target 80.00%)
- mean_width: 0.452
- singleton_acc: 85.11%
- abstain_rate: 41.25%

### Murphy decomposition (global)

- brier: 0.1699
- reliability (REL): 0.019
- resolution (RES): 0.0685
- uncertainty (UNC): 0.2194
- base_rate: 0.675

### Time-series CV

- folds: 4
- mean_acc: 75.00% ± 7.65%
- mean_brier: 0.2085 ± 0.0480

## 2. Per-Category Murphy

| dataset | n | brier | REL | RES | UNC |
|---|---|---|---|---|---|
| post_cutoff_q2_2026_holdout | 10 | 0.0279 | 0.0279 | 0.0 | 0.0 |
| post_cutoff_q2_2026_holdout_v2 | 40 | 0.1925 | 0.0097 | 0.0573 | 0.24 |
| post_cutoff_q3_2026_holdout_v3 | 30 | 0.1856 | 0.0506 | 0.0872 | 0.2222 |

## 3. Diebold-Mariano vs base-rate baseline

- loss: brier
- n: 80
- dm_stat: -2.001
- p_value: 0.0454
- mean_diff (Vila - baseline): -0.0474
- reject_h0 (alpha=0.05): True
- interpretation: Vila < baseline brier (better)

## 4. Hosmer-Lemeshow GoF

- n: 80
- chi_square: 308.343
- df: 8
- p_value (approx): 0.0
- reject_h0 (alpha=0.05): True

| g | n | mean_p | obs_rate | component |
|---|---|---|---|---|
| 0 | 8 | 0.23 | 0.25 | 0.018 |
| 1 | 8 | 0.415 | 0.25 | 0.894 |
| 2 | 8 | 0.529 | 0.375 | 0.766 |
| 3 | 8 | 0.634 | 0.875 | 1.999 |
| 4 | 8 | 0.755 | 0.625 | 0.733 |
| 5 | 8 | 0.791 | 1.0 | 2.114 |
| 6 | 8 | 0.891 | 0.875 | 0.023 |
| 7 | 8 | 0.993 | 0.5 | 301.705 |
| 8 | 8 | 0.993 | 1.0 | 0.052 |
| 9 | 8 | 0.995 | 1.0 | 0.039 |

## 5. PIT Histogram

- n: 80
- chi_square: 7.25
- slope: -0.047
- u_score: 0.188
- diagnosis: well-calibrated

| bin | count |
|---|---|
| [0.0, 0.1) | 10 |
| [0.1, 0.2) | 9 |
| [0.2, 0.3) | 12 |
| [0.3, 0.4) | 8 |
| [0.4, 0.5) | 3 |
| [0.5, 0.6) | 9 |
| [0.6, 0.7) | 7 |
| [0.7, 0.8) | 8 |
| [0.8, 0.9) | 9 |
| [0.9, 1.0) | 5 |

## 6. Reliability Diagram

| bin | mean_p | observed_rate | n | ci_lo | ci_hi |
|---|---|---|---|---|---|
| [0.1, 0.2) | 0.125 | 0.000 | 4 | 0.000 | 0.490 |
| [0.2, 0.3) | 0.257 | 0.000 | 1 | 0.000 | 0.793 |
| [0.3, 0.4) | 0.375 | 0.429 | 7 | 0.158 | 0.750 |
| [0.4, 0.5) | 0.451 | 0.250 | 8 | 0.071 | 0.591 |
| [0.5, 0.6) | 0.545 | 1.000 | 1 | 0.207 | 1.000 |
| [0.6, 0.7) | 0.631 | 0.750 | 12 | 0.468 | 0.911 |
| [0.7, 0.8) | 0.783 | 0.824 | 17 | 0.590 | 0.938 |
| [0.8, 0.9) | 0.894 | 0.750 | 4 | 0.301 | 0.954 |
| [0.9, 1.0) | 0.994 | 0.846 | 26 | 0.665 | 0.939 |
