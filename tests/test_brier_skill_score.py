"""Tests for engine/brier_skill_score.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.brier_skill_score import brier_skill_score, brier

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_brier_skill_score ===")

print("\n[1] Empty -> bss=None")
r = brier_skill_score([], [])
check(r["bss"] is None, "empty bss=None")

print("\n[2] Perfect predictions -> BSS = 1.0")
r = brier_skill_score([0.0, 1.0, 0.0, 1.0], [0, 1, 0, 1])
check(abs(r["bss"] - 1.0) < 1e-9, f"BSS=1 perfect (got {r['bss']})")

print("\n[3] Climatology forecast -> BSS = 0")
# Forecast = base rate constant
y = [1, 1, 0, 0, 1, 0]
base = sum(y) / len(y)
preds = [base] * len(y)
r = brier_skill_score(preds, y)
check(abs(r["bss"] - 0.0) < 1e-9, f"BSS=0 climatology (got {r['bss']})")

print("\n[4] Worse-than-climatology -> BSS < 0")
y = [1, 1, 1, 0, 0, 0]
preds = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]  # opposite
r = brier_skill_score(preds, y)
check(r["bss"] < 0, f"BSS < 0 anti-correlated (got {r['bss']})")

print("\n[5] BSS = 1 - bs_model/bs_clim arithmetic check")
y = [1, 0, 1, 0]
preds = [0.7, 0.4, 0.6, 0.3]
r = brier_skill_score(preds, y)
expected = 1.0 - r["bs_model"] / r["bs_clim"]
check(abs(r["bss"] - expected) < 1e-12, f"arithmetic ok (bss={r['bss']})")

print("\n[6] base_rate override")
r = brier_skill_score([0.5, 0.5], [1, 0], base_rate=0.5)
# bs_model = 0.25 * 2 / 2 = 0.25; bs_clim same since base=0.5 = preds
check(abs(r["bss"] - 0.0) < 1e-9, f"override base_rate (got {r['bss']})")

print("\n[7] Real classifier on holdout — expect BSS > 0")
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


events = []
for fn in ["post_cutoff_q2_2026_holdout", "post_cutoff_q1_2026",
           "brazil_votes_q1_2026", "tech_releases_q1_2026"]:
    events += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")

preds = []
reals = []
for e in events:
    p, _ = classify_and_predict(e["outcome_framing"], e["contexto"])
    preds.append(p)
    reals.append(e["outcome_real"])

r = brier_skill_score(preds, reals)
print(f"  N={r['n']} bs_model={r['bs_model']:.4f} bs_clim={r['bs_clim']:.4f} BSS={r['bss']:.4f}")
check(r["bss"] is not None, "BSS finite")
check(r["bss"] > 0, f"BSS > 0 (better than climatology) got {r['bss']}")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
