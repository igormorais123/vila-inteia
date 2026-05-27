# Vila Long AutoResearch Cycle

- Generated: `2026-05-14T01:36:04`
- Iterations: `20`/`20`
- Population x generations: `8` x `2`
- Promotions: `0`
- Runtime: `2.81` seconds

## Best Seen

- Iteration: `1`
- Score: `4.435099`
- Config: `{"stein_shrink": 0.4, "w_linzer": 0.7, "sigma_intercept_pp": 3.0, "sigma_slope_pp_per_day": 0.005, "w_state_mrp": 0.36}`

## Iterations

| iter | seed | promoted | score | acc | brier | ece | mcc | gate |
|---:|---:|---|---:|---:|---:|---:|---:|---|
| 1 | 4201 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 2 | 4202 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 3 | 4203 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 4 | 4204 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 5 | 4205 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 6 | 4206 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 7 | 4207 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 8 | 4208 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 9 | 4209 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 10 | 4210 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 11 | 4211 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 12 | 4212 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 13 | 4213 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 14 | 4214 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 15 | 4215 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 16 | 4216 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 17 | 4217 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 18 | 4218 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 19 | 4219 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |
| 20 | 4220 | False | 4.435099 | 0.9721 | 0.1046 | 0.2610 | 0.9442 | incumbent retained |

## Final Diagnostic

- Political evolved acc: `0.9721`
- Political evolved Brier: `0.1046`
- Political evolved AUC: `0.9916`
- Political evolved MCC: `0.9442`
- Political evolved ECE: `0.2610`

## Actions

1. **politica**: Use MRP as classifier edge and add a calibrated probability layer before exposing raw probabilities. Evidence: MRP acc 0.9721 > baseline 0.9188, but Brier 0.1046 > baseline 0.0722.
2. **calibracao**: Open a year-fold calibration task focused on the highest-ECE cycle. Evidence: Year 2018 ECE=0.4124, Brier=0.1840, n=70.
3. **dados**: Review the worst dataset by prior Brier and add it to the next focused validation batch. Evidence: post_cutoff_q1_2026_v2 prior_brier=0.3553, n=10.
4. **testes**: Keep the slowest test in a performance watchlist and split it if it grows further. Evidence: test_llm_forecaster.py took 91.465s.
