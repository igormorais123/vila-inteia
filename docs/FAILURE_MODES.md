# Vila MRP Ensemble - Failure Mode Analysis

**Phase 4 publish-grade work. 11 misses out of 394 events (97.21% acc).**

## 1. Operative configuration

```
stein_shrink   = 0.4
w_linzer       = 0.7
sigma_int      = 3.0
sigma_slope    = 0.01
w_state_mrp    = 0.36   (MRP-style state-regime baseline blend)
house_effects  = disabled
operational T  <= 30 days from election
```

This config reproduces the published 97.21% / 11-miss number under year-fold
leave-one-out CV.

> **Note on `data/political_best_config.json`.** That file documents
> `stein_shrink=0.05, w_linzer=0.5, sigma_int=4.0, sigma_slope=0.05` along
> with the 97.21% / 11-miss validation block. Empirically the validation
> numbers do not match those hyperparameters: only the operative config
> above reproduces them. The JSON appears to mix metadata from one run
> with validation from another. `scripts/failure_analysis.py` uses the
> reproducible config and prints the score for verification on every run.

## 2. Per-year confusion

| year | n   | acc    | misses |
|------|-----|--------|--------|
| 2010 | 86  | 1.0000 | 0      |
| 2016 | 20  | 0.8500 | 3      |
| 2018 | 70  | 0.9857 | 1      |
| 2020 | 30  | 1.0000 | 0      |
| 2022 | 120 | 1.0000 | 0      |
| 2024 | 68  | 0.8971 | 7      |
| avg  | 394 | 0.9721 | 11     |

All federal/state elections in 2010, 2020, 2022 hit. All misses concentrate in
**SP municipal mayor** races (10 of 11) plus one 2018 BR-presidential CNT/MDA
poll near the day of the election.

## 3. Category breakdown of the 11 misses

Definitions (applied in `scripts/failure_analysis.py:classify_miss`):

| category        | trigger                                                                                                  |
|-----------------|----------------------------------------------------------------------------------------------------------|
| `tossup`        | `|poll_lead_pp| < 3 pp` (model cannot dominate noise)                                                    |
| `realignment`   | `p_state` and polls disagree, AND outcome aligns with **polls** (i.e., MRP HURT the prediction)          |
| `industry_bias` | `|lead| >= 3`, polls and model agree on a winner, outcome diverges (the 2024 SP residual cluster)        |
| `sparse_cohort` | `n_cohort < 5` events in the matched (cargo, days_bin, lead_bin, incumbente, regime) cell                |

| category        | count |
|-----------------|-------|
| industry_bias   | 10    |
| realignment     | 1     |
| tossup          | 0     |
| sparse_cohort   | 0     |

The cluster is dominated by 2024 SP municipal polls where Datafolha, Quaest,
AtlasIntel, and InstitutoVeritá all agreed Boulos (left) was leading or tied;
Nunes (center) won. The state-baseline correctly says SP-center wins almost
always (49/49 historical), so MRP **rescued 22 of these polls** but 10 stayed
miscalibrated because the poll signal was very strong.

## 4. The 11 misses (full context)

| year | event                                                                | UF | regime | lead pp | days | outcome | p_cohort | p_linzer | p_state | p_pred | tier       | n_coh | state_cell_n | category      | MRP impact     |
|------|----------------------------------------------------------------------|----|--------|---------|------|---------|----------|----------|---------|--------|------------|-------|--------------|---------------|----------------|
| 2016 | pressp_mayor_2016_09-13_Ibope_w (Doria/center)                       | SP | center | -13.0   | 19   | 1       | 0.513    | 0.000    | 0.980   | 0.452  | cargo_days | 34    | 49           | industry_bias | mrp_unchanged  |
| 2016 | pressp_mayor_2016_09-13_Ibope_l (Haddad/left)                        | SP | left   | +13.0   | 19   | 0       | 0.513    | 1.000    | 0.019   | 0.553  | cargo_days | 34    | 50           | industry_bias | mrp_unchanged  |
| 2016 | pressp_mayor_2016_09-08_Datafolha_w (Doria/center)                   | SP | center | -10.0   | 24   | 1       | 0.513    | 0.001    | 0.980   | 0.452  | cargo_days | 34    | 49           | industry_bias | mrp_unchanged  |
| 2018 | pres2018_09-28_CNT/MDA_haddad                                        | BR | left   | -3.0    | 9    | 0       | 0.515    | 0.166    | 0.977   | 0.525  | cargo_days | 34    | 83           | realignment   | mrp_introduced |
| 2024 | pressp_mayor_2024_10-05_Datafolha_w (Nunes/center)                   | SP | center | -3.0    | 1    | 1       | 0.215    | 0.160    | 0.963   | 0.459  | full       | 5     | 25           | industry_bias | mrp_unchanged  |
| 2024 | pressp_mayor_2024_10-04_AtlasIntel_w (Nunes/center)                  | SP | center | -11.1   | 2    | 1       | 0.515    | 0.000    | 0.963   | 0.446  | cargo_days | 38    | 25           | industry_bias | mrp_unchanged  |
| 2024 | pressp_mayor_2024_10-04_AtlasIntel_l (Boulos/left)                   | SP | left   | +11.1   | 2    | 0       | 0.515    | 1.000    | 0.036   | 0.560  | cargo_days | 38    | 26           | industry_bias | mrp_unchanged  |
| 2024 | pressp_mayor_2024_10-02_InstitutoVerit_l (Boulos/left)               | SP | left   | +5.8    | 4    | 0       | 0.515    | 0.972    | 0.036   | 0.547  | cargo_days | 38    | 26           | industry_bias | mrp_unchanged  |
| 2024 | pressp_mayor_2024_09-29_AtlasIntel_l (Boulos/left)                   | SP | left   | +6.5    | 7    | 0       | 0.515    | 0.983    | 0.036   | 0.552  | cargo_days | 38    | 26           | industry_bias | mrp_unchanged  |
| 2024 | pressp_mayor_2024_09-15_InstitutoVerit_w (Nunes/center)              | SP | center | -7.9    | 21   | 1       | 0.515    | 0.007    | 0.963   | 0.449  | cargo_days | 12    | 25           | industry_bias | mrp_unchanged  |
| 2024 | pressp_mayor_2024_09-10_AtlasIntel_w (Nunes/center)                  | SP | center | -7.9    | 26   | 1       | 0.515    | 0.008    | 0.963   | 0.449  | cargo_days | 12    | 25           | industry_bias | mrp_unchanged  |

## 5. MRP impact buckets

For every event we predict twice: `p_no_mrp = (1-w_lin)*p_cohort + w_lin*p_linzer`,
and `p_with_mrp = (1-w_state)*p_no_mrp + w_state*p_state`. Comparing hits:

| bucket          | count | meaning                                              |
|-----------------|-------|------------------------------------------------------|
| mrp_recovered   | 22    | miss without MRP, hit with MRP (MRP HELPED)          |
| mrp_unchanged   | 10    | miss in both (intrinsic poll-vs-fundamentals split)  |
| mrp_introduced  |  1    | hit without MRP, miss with MRP (MRP HURT)            |
| mrp_unchanged_hit | 361 | hit in both (MRP NEUTRAL)                            |

**Net +21 hits from MRP** (22 recovered, 1 introduced). Ratio 22:1 in favor of
keeping MRP on.

The single `mrp_introduced` case is the 2018 CNT/MDA Haddad poll: BR-left
historical baseline is 82/83 wins (Lula era), MRP pulled the prediction up to
0.525 even though Haddad lost (Bolsonaro won). This is a true realignment signal
the polls captured but the (UF, regime) prior could not.

## 6. Severity matrix - when to use MRP

Per `(uf, regime)` signature, miss-rate with and without MRP, plus the minimum
state-regime cell size in train:

| signature  | n   | miss_mrp | miss_no_mrp | min_cell_n |
|------------|-----|---------|-------------|------------|
| SP\|center | 59  | 6       | 16          | 25         |
| SP\|left   | 60  | 4       | 16          | 26         |
| BR\|left   | 111 | 1       | 0           | 75         |
| all others | 164 | 0       | 0           | varies     |

Rules of thumb:

1. **Use MRP** when `state_cell_n >= 25` AND there is no realignment-shock
   signal in recent polls. Default for all 27 BR states + BR federal.
2. **Default OFF (`w_state=0`)** when `state_cell_n < 5`. There are not enough
   historical events to anchor a sensible prior.
3. **Caution zone** (`5 <= state_cell_n < 25`): attenuate `w_state`
   proportionally (see formula below).
4. **Override OFF** if user signals a realignment scenario (e.g., BR-left in
   2018 after Lava Jato). Polls already contain that information; the prior
   pulls in the wrong direction.

## 7. Recommended adaptive `w_state` rule

```
w_state(uf, regime) = 0.36 * min(1.0, state_cell_n / 5)
```

- `state_cell_n >= 5` -> use `0.36` (current default).
- `state_cell_n < 5`  -> linearly attenuate.
- `state_cell_n == 0` -> `w_state = 0` (cohort + linzer only).

This mirrors the existing `state_baseline_p` `min_n=3` guard but extends it
into a soft schedule rather than a hard cliff. Since MRP recovers 22 events
and introduces 1, **the rule is conservative**: we only weaken MRP where the
prior is unreliable.

### Adoption note (paper Discussion)

The cluster of 10 unrecovered industry-bias misses in 2024 SP indicates that
when **all major institutos converge on the same wrong call**, neither the
cohort base rate nor a state-regime prior can override the poll signal at
`w_linzer=0.7`. This is an open problem; possibilities for future work:

- **Selective abstention** (`tau >= 0.15`): already supported. At
  `tau=0.40` the system reaches 100% acc at 11% coverage, meaning these
  misses are concentrated in the low-confidence band the system already
  flags.
- **Asymmetric MRP**: blend MRP only when polls and prior agree in
  *direction* (skip blend on conflict). This would reduce variance but
  miss most of the 22 recoveries.
- **Industry-disagreement detector**: flag predictions where >=3 institutos
  agree but the (UF, regime) prior disagrees by >50pp; surface as
  "industry-vs-fundamentals split" rather than committing to a single
  number.

## 8. Reproduction

```bash
cd /home/pedroafonso/vila-inteia
python3 scripts/failure_analysis.py
# wrote data/failure_analysis.json
# avg_acc with MRP    = 0.9721 (383/394)
# avg_acc without MRP = 0.9188 (362/394)
# misses with MRP     = 11
```

Smoke remains 29/29 (`python3 scripts/smoke_political.py`).
