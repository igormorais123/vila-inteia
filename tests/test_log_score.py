"""Tests for engine/log_score.py."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.log_score import log_score, log_score_skill
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_log_score ===")

print("\n[1] Empty -> 0.0")
check(log_score([], []) == 0.0, "log_score empty -> 0")
check(log_score_skill([], []) == 0.0, "skill empty -> 0")

print("\n[2] Perfect predictions -> log_score ≈ 0")
ls = log_score([1.0, 0.0, 1.0, 0.0], [1, 0, 1, 0])
# clipped, so will be -log(1-eps) ≈ eps
check(ls < 1e-6, f"perfect ≈ 0 (got {ls})")

print("\n[3] All wrong -> log_score large")
ls = log_score([1.0, 0.0, 1.0, 0.0], [0, 1, 0, 1])
# -log(eps) ~ 20.7
check(ls > 5.0, f"adversarial high (got {ls:.2f})")

print("\n[4] p=0.5 constant -> log_score = log(2) ≈ 0.6931")
ls = log_score([0.5] * 10, [1, 0] * 5)
check(abs(ls - math.log(2)) < 1e-6, f"log(2) (got {ls:.4f})")

print("\n[5] Climatology baseline -> skill = 0")
y = [1, 1, 0, 0, 1, 0, 1, 0]
base = sum(y) / len(y)
preds = [base] * len(y)
skill = log_score_skill(preds, y)
check(abs(skill) < 1e-9, f"skill=0 climatology (got {skill})")

print("\n[6] Perfect model -> skill ≈ 1")
preds = [1.0 if yi else 0.0 for yi in y]
skill = log_score_skill(preds, y)
check(skill > 0.99, f"skill→1 perfect (got {skill:.4f})")

print("\n[7] Worse than baseline -> skill < 0")
y = [1, 0, 1, 0]
preds = [0.1, 0.9, 0.1, 0.9]  # opposite
skill = log_score_skill(preds, y)
check(skill < 0, f"skill<0 anti-corr (got {skill:.3f})")

print("\n[8] baseline_rate override")
ls_base = log_score([0.5, 0.5], [1, 0])
skill = log_score_skill([0.5, 0.5], [1, 0], baseline_rate=0.5)
# preds == baseline -> skill = 0
check(abs(skill) < 1e-9, f"override (got {skill})")

print("\n[9] Real bench: classifier on holdout v2")
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
check(len(events) >= 40, f"n>=40 (got {len(events)})")

pairs = pairs_from_events(events, classify_and_predict)
preds = [p for p, _ in pairs]
reals = [y for _, y in pairs]

ls = log_score(preds, reals)
skill = log_score_skill(preds, reals)
print(f"  n={len(reals)} log_score={ls:.4f} skill={skill:+.4f}")
check(math.isfinite(ls) and ls >= 0, f"log_score finite>=0 (got {ls})")
check(math.isfinite(skill), f"skill finite (got {skill})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
