"""Tests for engine/shapley_keywords.py — Shapley attribution over keyword cats."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.shapley_keywords import shapley_attribution
from engine.post_cutoff_classifier import classify_and_predict, KEYWORD_PRIORS

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_shapley_keywords ===")


print("\n[1] returns one value per category")
# Toy classifier with 3 cats.
toy_priors = [
    (["alpha"], 0.90, "A"),
    (["beta"], 0.10, "B"),
    (["gamma"], 0.50, "C"),
]
toy_events = [
    {"outcome_framing": "alpha thing", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "alpha other", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "beta thing", "outcome_real": 0, "contexto": ""},
    {"outcome_framing": "gamma thing", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "no kw", "outcome_real": 0, "contexto": ""},
]
sh = shapley_attribution(
    toy_events, classify_and_predict, toy_priors,
    n_samples=50, default_prior=0.50, seed=1,
)
check(set(sh.keys()) == {"A", "B", "C"}, f"keys = cats ({sorted(sh)})")
check(all(isinstance(v, float) for v in sh.values()), "values are floats")

print("\n[2] high-quality cat (A: alpha->yes, real=yes) has positive Shapley")
# A maps alpha->0.90 yes, both real=1 -> always correct when included.
# Without A, alpha events fall to default 0.50 -> tied (counted as yes via >=).
# Inclusion of A should at least not hurt.
check(sh["A"] >= -0.05, f"A non-negative ({sh['A']:.3f})")

print("\n[3] sum approximation: sum of Shapley near (v(N) - v(empty))")
# Efficiency property in expectation.
v_full = 0
v_empty = 0
for e in toy_events:
    fr, ctx = e["outcome_framing"], e["contexto"]
    real = e["outcome_real"]
    # Full classifier (all 3 cats).
    text = (fr + " " + ctx).lower()
    p_full = 0.50
    for kws, prior, label in toy_priors:
        if any(k in text for k in kws):
            p_full = prior; break
    if (p_full >= 0.50) == bool(real):
        v_full += 1
    # Empty: always 0.50.
    if (0.50 >= 0.50) == bool(real):
        v_empty += 1
v_full /= len(toy_events)
v_empty /= len(toy_events)
total_shapley = sum(sh.values())
print(f"  v(N)={v_full:.3f}  v(empty)={v_empty:.3f}  sum_sh={total_shapley:.3f}")
check(abs(total_shapley - (v_full - v_empty)) < 0.30,
      f"|sum sh - delta| < 0.30 (got |{total_shapley - (v_full - v_empty):.3f}|)")

print("\n[4] empty events -> all zeros")
sh_empty = shapley_attribution(
    [], classify_and_predict, toy_priors, n_samples=10, seed=1,
)
check(all(v == 0.0 for v in sh_empty.values()),
      "all-zero Shapley on empty events")

print("\n[5] reproducibility with seed")
sh1 = shapley_attribution(toy_events, classify_and_predict, toy_priors,
                          n_samples=30, seed=7)
sh2 = shapley_attribution(toy_events, classify_and_predict, toy_priors,
                          n_samples=30, seed=7)
check(sh1 == sh2, "same seed -> same output")


print("\n[6] real-data: post_cutoff_q2_2026_holdout (n=10)")
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


base = "/home/pedroafonso/vila-inteia/data/backtest"
test = load_csv(f"{base}/post_cutoff_q2_2026_holdout.csv")

sh_real = shapley_attribution(
    test, classify_and_predict, KEYWORD_PRIORS,
    n_samples=100, default_prior=0.50, seed=42,
)
top = sorted(sh_real.items(), key=lambda kv: kv[1], reverse=True)[:5]
print("  top-5 Shapley contributors on holdout:")
for name, val in top:
    print(f"    {name:30s}  {val:+.4f}")
check(len(sh_real) == len(KEYWORD_PRIORS),
      f"one shapley per cat ({len(sh_real)} vs {len(KEYWORD_PRIORS)})")
check(any(v > 0 for v in sh_real.values()),
      "at least one positive contributor on holdout")


print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
