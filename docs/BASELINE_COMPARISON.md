# Vila MRP vs Ablation Baselines

Phase 2 of publish-grade comparison. Five models, identical year-fold cross-validation on Brazilian elections 2010-2024 with T<=30 day polling horizon. Test year is **never** in the cohort training pool.

## Configuration

- Seed: `42`
- Stein shrink (M2/M4/M5): `0.05`
- Stein shrink (M5b tuned): `0.4`
- Vila w_linzer (M4/M5): `0.5`
- Vila w_linzer (M5b tuned): `0.7`
- Linzer sigma (M1/M4/M5): `4.0 + 0.05 * days_to_election`
- Linzer sigma (M5b tuned): `3.0 + 0.005 * days_to_election`
- W_STATE (MRP, both M5 and M5b): `0.36`
- Selective tau (high-confidence): `0.4`
- House effects: `False` (disabled in best config)

## Models

| ID | Description |
|----|-------------|
| M1 Linzer-only | `p = Phi(lead_pp / sigma(days))`, sigma = 4 + 0.05*days |
| M2 Cohort-only | `p = p_cohort` (Stein-shrunk empirical base rates) |
| M3 Naive poll | `p = sigmoid(lead_pp / 10)` clamped to `[0.05, 0.95]` |
| M4 Vila baseline (no MRP) | `0.5*cohort + 0.5*linzer`, no state baseline |
| M5 Vila MRP (legacy ablation) | `(1-W_STATE)*(0.5 cohort + 0.5 linzer) + W_STATE*p_state`, shrink=0.05, sigma=4+0.05d |
| M5b Vila MRP (tuned) | same blend at the promoted operating point (version=v1.4-evo, shrink=0.4, w_linzer=0.7, sigma=3.0+0.005d) that yields the published 97.21% headline |

## Brier score per cycle (lower = better)

| Model | 2010 | 2016 | 2018 | 2020 | 2022 | 2024 | **Pooled avg** |
|---|---|---|---|---|---|---|---|
| M1 Linzer-only | **0.0000** | 0.2889 | **0.0047** | 0.0305 | **0.0088** | 0.3158 | **0.0750** |
| M2 Cohort-only | 0.2401 | **0.0380** | 0.2375 | 0.1252 | 0.2405 | 0.1180 | 0.1997 |
| M3 Naive poll | 0.0074 | 0.2229 | 0.0686 | 0.0751 | 0.0756 | 0.2649 | 0.0996 |
| M4 Vila baseline (no MRP) | 0.0600 | 0.1212 | 0.0687 | 0.0546 | 0.0759 | 0.1749 | 0.0889 |
| M5 Vila MRP (legacy ablation wlin=0.5) | 0.1439 | 0.0517 | 0.2444 | 0.0241 | 0.1377 | **0.0775** | 0.1346 |
| M5b Vila MRP (tuned wlin=0.7) | 0.1015 | 0.0846 | 0.1840 | **0.0170** | 0.0843 | 0.1072 | 0.1046 |

## Accuracy per cycle (higher = better)

| Model | 2010 | 2016 | 2018 | 2020 | 2022 | 2024 | **Pooled avg** |
|---|---|---|---|---|---|---|---|
| M1 Linzer-only | **1.0000** | 0.7000 | **1.0000** | 0.9333 | **1.0000** | 0.6471 | 0.9188 |
| M2 Cohort-only | 0.5000 | 0.9500 | 0.5000 | 0.8000 | 0.5000 | 0.7941 | 0.5964 |
| M3 Naive poll | **1.0000** | 0.7000 | **1.0000** | 0.9333 | **1.0000** | 0.6471 | 0.9188 |
| M4 Vila baseline (no MRP) | **1.0000** | 0.8500 | **1.0000** | 0.9333 | **1.0000** | 0.7353 | 0.9416 |
| M5 Vila MRP (legacy ablation wlin=0.5) | **1.0000** | **1.0000** | 0.4714 | **1.0000** | 0.7250 | **0.9265** | 0.8096 |
| M5b Vila MRP (tuned wlin=0.7) | **1.0000** | 0.8500 | 0.9857 | **1.0000** | **1.0000** | 0.8971 | **0.9721** |

## Log-loss per cycle (lower = better)

| Model | 2010 | 2016 | 2018 | 2020 | 2022 | 2024 | **Pooled avg** |
|---|---|---|---|---|---|---|---|
| M1 Linzer-only | **0.0000** | 1.2195 | **0.0376** | **0.1092** | **0.0602** | 1.0350 | **0.2739** |
| M2 Cohort-only | 0.6634 | **0.1254** | 0.6560 | 0.3591 | 0.6643 | 0.4174 | 0.5694 |
| M3 Naive poll | 0.0836 | 0.6252 | 0.2913 | 0.2877 | 0.3027 | 0.7271 | 0.3413 |
| M4 Vila baseline (no MRP) | 0.2742 | 0.3408 | 0.2950 | 0.2114 | 0.3131 | 0.5196 | 0.3307 |
| M5 Vila MRP (legacy ablation wlin=0.5) | 0.4722 | 0.1847 | 0.6811 | 0.1336 | 0.4523 | **0.2873** | 0.4310 |
| M5b Vila MRP (tuned wlin=0.7) | 0.3795 | 0.2668 | 0.5596 | 0.1126 | 0.3220 | 0.3619 | 0.3649 |

## Selective acc at tau=0.40 (high-confidence subset)

Only events where |p - 0.5| >= 0.40 are scored. Coverage is the fraction of events that meet the threshold.

| Model | Selective acc | Coverage | n_kept |
|-------|---------------|----------|--------|
| M1 Linzer-only | 0.9388 | 0.746 | 294 |
| M2 Cohort-only | 0.9519 | 0.264 | 104 |
| M3 Naive poll | 1.0000 | 0.254 | 100 |
| M4 Vila baseline (no MRP) | 1.0000 | 0.112 | 44 |
| M5 Vila MRP (legacy ablation wlin=0.5) | 1.0000 | 0.091 | 36 |
| M5b Vila MRP (tuned wlin=0.7) | 1.0000 | 0.079 | 31 |

## Headline

- **Pooled Brier winner**: M1 Linzer-only (0.0750); runner-up M4 Vila baseline (no MRP) at 0.0889 (delta +0.0139).
- **Pooled accuracy winner**: M5b Vila MRP (tuned wlin=0.7) (0.9721); runner-up M4 Vila baseline (no MRP) at 0.9416 (delta +0.0305).

## Operating notes

- M3 naive (sigmoid of lead/10, clamped) is intentionally too simple and exists as a floor anchor. It cannot use cohort base rates or vary calibration with days-to-election.
- M1 Linzer-only and M2 cohort-only are single-signal baselines. If either matches Vila MRP within noise, the ensemble adds little.
- The Phase-2 ablation keeps `w_linzer=0.5` for M4/M5. The production headline uses the persisted `v1.4-evo` operating point in `data/political_best_config.json`: `w_linzer=0.7, shrink=0.4, sigma=3.0+0.005d, w_state=0.36`. M5b is the production model.
- The fact that M5 legacy underperforms M4 at `w_linzer=0.5` is a real ablation finding: at this operating point the MRP state baseline pulls predictions toward state-level priors that hurt close-but-confident races. At the production `v1.4-evo` operating point (M5b) the MRP blend recovers and wins on accuracy.
- Evolution now promotes only against fixed incumbent gates: accuracy and MCC cannot regress, AUC cannot materially regress, Brier cannot materially worsen, and the composite score must improve.
- All five models are evaluated on the **same** events (T<=30 days), with the **same** no-leak protocol. The cohort training pool excludes the test year for every model that uses cohort signal.
- BART and Stan hierarchical baselines are deferred to phase 3 to keep this comparison dependency-free (no R, no PyStan).

## Reproduce

```bash
python3 scripts/baseline_gauntlet.py
# writes data/baseline_gauntlet.json + docs/BASELINE_COMPARISON.md
```
