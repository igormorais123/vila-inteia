"""Tests for engine/wilson_ci.py."""
import sys, csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.wilson_ci import wilson_ci, _z_from_alpha

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_wilson_ci ===")

print("\n[1] z(0.05) ≈ 1.96")
z = _z_from_alpha(0.05)
check(abs(z - 1.95996) < 1e-3, f"z(0.05)≈1.96 (got {z:.5f})")

print("\n[2] z(0.01) ≈ 2.576")
z = _z_from_alpha(0.01)
check(abs(z - 2.5758) < 1e-3, f"z(0.01)≈2.576 (got {z:.5f})")

print("\n[3] n=0 -> [0,1]")
r = wilson_ci(0.5, 0)
check(r["lo"] == 0.0 and r["hi"] == 1.0, f"n=0 widest CI (got {r['lo']},{r['hi']})")

print("\n[4] Standard 95% CI matches known textbook value")
# Wilson 95% CI for p_hat=0.5, n=100: ~ [0.404, 0.596]
r = wilson_ci(0.5, 100, alpha=0.05)
check(abs(r["lo"] - 0.4038) < 5e-3, f"lo≈0.404 (got {r['lo']:.4f})")
check(abs(r["hi"] - 0.5962) < 5e-3, f"hi≈0.596 (got {r['hi']:.4f})")

print("\n[5] CI shrinks with larger n")
r_small = wilson_ci(0.5, 10)
r_big = wilson_ci(0.5, 1000)
width_small = r_small["hi"] - r_small["lo"]
width_big = r_big["hi"] - r_big["lo"]
check(width_big < width_small, f"width(1000)<width(10) ({width_big:.3f}<{width_small:.3f})")

print("\n[6] Boundary p_hat=0 -> lo=0, hi>0")
r = wilson_ci(0.0, 20)
check(r["lo"] == 0.0, f"p=0 lo=0 (got {r['lo']})")
check(r["hi"] > 0.0 and r["hi"] < 0.3, f"p=0 hi>0 small (got {r['hi']:.3f})")

print("\n[7] Boundary p_hat=1 -> hi=1, lo<1")
r = wilson_ci(1.0, 20)
check(r["hi"] == 1.0, f"p=1 hi=1 (got {r['hi']})")
check(r["lo"] < 1.0 and r["lo"] > 0.7, f"p=1 lo<1 (got {r['lo']:.3f})")

print("\n[8] Real classifier — accuracy CI on holdout events")
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
           "brazil_votes_q1_2026"]:
    events += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")

hits = 0
for e in events:
    p, _ = classify_and_predict(e["outcome_framing"], e["contexto"])
    if (p >= 0.5) == bool(e["outcome_real"]):
        hits += 1
n = len(events)
acc = hits / n
r = wilson_ci(acc, n)
print(f"  N={n} acc={acc:.3f} 95% CI = [{r['lo']:.3f}, {r['hi']:.3f}]")
check(0.0 <= r["lo"] <= acc <= r["hi"] <= 1.0,
      f"lo<=acc<=hi (got [{r['lo']},{r['hi']}], acc={acc})")
check(r["hi"] - r["lo"] > 0, "CI has nonzero width")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
