"""Tests for engine/comparative_ranking.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.comparative_ranking import rank_forecasters, pairwise_dm

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_comparative_ranking ===")

print("\n[1] Empty reals -> []")
r = rank_forecasters({"a": [0.5]}, [])
check(r == [], f"empty -> [] (got {r})")

print("\n[2] Three forecasters: perfect, climatology, anti")
y = [1, 0, 1, 0, 1, 0]
preds_dict = {
    "perfect": [1.0, 0.0, 1.0, 0.0, 1.0, 0.0],
    "climatology": [0.5] * 6,
    "anti": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
}
r = rank_forecasters(preds_dict, y, metric="brier")
print(f"  ranking: {r}")
check(r[0][0] == "perfect", f"perfect rank 1 (got {r[0][0]})")
check(r[-1][0] == "anti", f"anti rank last (got {r[-1][0]})")
check(r[0][2] == 1 and r[-1][2] == 3, f"ranks 1..3 (got {[x[2] for x in r]})")

print("\n[3] Metric=log -> same ordering on this set")
r = rank_forecasters(preds_dict, y, metric="log")
check(r[0][0] in ("perfect", "climatology"), f"first is perfect/clim (got {r[0][0]})")

print("\n[4] Metric=spherical")
r = rank_forecasters(preds_dict, y, metric="spherical")
check(r[0][0] == "perfect", f"perfect best spherical (got {r[0][0]})")

print("\n[5] Unknown metric -> []")
r = rank_forecasters(preds_dict, y, metric="bogus")
check(r == [], "unknown metric -> []")

print("\n[6] Pairwise DM")
dm = pairwise_dm(preds_dict, y, loss="brier")
check(len(dm) == 3, f"3 pairs for 3 forecasters (got {len(dm)})")
check(all("a" in d and "b" in d for d in dm), "each pair labeled")

print("\n[7] Real classifier on holdout v2 — stretch True vs False vs flat 0.5")
sys.path.insert(0, "/home/pedroafonso/vila-inteia")
from engine.post_cutoff_classifier import classify_and_predict


def load_csv(fp):
    out = []
    with open(fp) as f:
        for r in csv.DictReader(f):
            try:
                out.append({
                    "outcome_framing": r.get("outcome_framing") or r.get("framing", ""),
                    "contexto": r.get("contexto", ""),
                    "outcome_real": int(r["outcome_real"]),
                })
            except (ValueError, KeyError):
                pass
    return out


events = load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv")
preds_stretch, preds_raw, reals = [], [], []
for e in events:
    p_t, _ = classify_and_predict(e["outcome_framing"], e["contexto"], apply_stretch=True)
    p_f, _ = classify_and_predict(e["outcome_framing"], e["contexto"], apply_stretch=False)
    preds_stretch.append(p_t)
    preds_raw.append(p_f)
    reals.append(e["outcome_real"])

base = sum(reals) / len(reals)
predictors = {
    "stretch_on": preds_stretch,
    "stretch_off": preds_raw,
    "climatology": [base] * len(reals),
}
ranking = rank_forecasters(predictors, reals, metric="brier")
print(f"  N={len(reals)} ranking (brier):")
for name, score, rank in ranking:
    print(f"    #{rank} {name}: {score:.4f}")
check(len(ranking) == 3, "3 forecasters ranked")
check(all(ranking[i][1] <= ranking[i+1][1] for i in range(len(ranking)-1)),
      "ranking sorted ascending")

dm = pairwise_dm(predictors, reals, loss="brier")
print(f"  Pairwise DM: {len(dm)} comparisons")
for d in dm:
    if "p_value" in d:
        print(f"    {d['a']} vs {d['b']}: dm={d['dm_stat']:.3f} p={d['p_value']:.3f}")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
