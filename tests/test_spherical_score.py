"""Tests for engine/spherical_score.py."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.spherical_score import spherical_score

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_spherical_score ===")

print("\n[1] Empty -> 0.0")
s = spherical_score([], [])
check(s == 0.0, f"empty=0 (got {s})")

print("\n[2] Perfect prediction (p=1, y=1) -> SS = -1")
s = spherical_score([1.0], [1])
# norm = sqrt(1+0)=1; py=1; ss=-1
check(abs(s - (-1.0)) < 1e-9, f"perfect=-1 (got {s})")

print("\n[3] Worst prediction (p=0, y=1) -> SS = 0 (py=0)")
s = spherical_score([0.0], [1])
check(abs(s - 0.0) < 1e-9, f"worst=0 (got {s})")

print("\n[4] Uniform 0.5 -> SS = -1/sqrt(2)")
s = spherical_score([0.5, 0.5, 0.5], [1, 0, 1])
expected = -1.0 / math.sqrt(2.0)
check(abs(s - expected) < 1e-9, f"0.5 -> -1/sqrt(2) (got {s})")

print("\n[5] Strict propriety: forecasting your true belief beats lying")
# True p=0.7. Honest forecaster scores better (lower) than dishonest.
# Expected SS at p_forecast given truth p_true=0.7:
# E[SS] = -[0.7 * p_forecast + 0.3 * (1-p_forecast)] / sqrt(p_forecast^2 + (1-p_forecast)^2)
def expected_ss(pf, pt=0.7):
    norm = math.sqrt(pf * pf + (1 - pf) ** 2)
    return -(pt * pf + (1 - pt) * (1 - pf)) / norm

honest = expected_ss(0.7)
liar_a = expected_ss(0.5)
liar_b = expected_ss(0.9)
check(honest <= liar_a and honest <= liar_b,
      f"honest({honest:.4f}) beats liars ({liar_a:.4f}, {liar_b:.4f})")

print("\n[6] Real classifier on holdout v2 — apply_stretch True vs False")
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

preds_t, preds_f, reals = [], [], []
for e in events:
    p_t, _ = classify_and_predict(e["outcome_framing"], e["contexto"], apply_stretch=True)
    p_f, _ = classify_and_predict(e["outcome_framing"], e["contexto"], apply_stretch=False)
    preds_t.append(p_t)
    preds_f.append(p_f)
    reals.append(e["outcome_real"])

ss_t = spherical_score(preds_t, reals)
ss_f = spherical_score(preds_f, reals)
print(f"  N={len(reals)} SS(stretch=True)={ss_t:.4f} SS(stretch=False)={ss_f:.4f}")
check(-1.0 <= ss_t <= 0.0, f"SS_t in [-1,0] (got {ss_t})")
check(-1.0 <= ss_f <= 0.0, f"SS_f in [-1,0] (got {ss_f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
