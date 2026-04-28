"""Tests for engine/bayes_factor.py."""
import sys, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.bayes_factor import bayes_factor
from engine.post_cutoff_classifier import classify_and_predict
from engine._pred_utils import pairs_from_events

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_bayes_factor ===")

print("\n[1] Empty / size mismatch")
r = bayes_factor([], [], [])
check(r["log_bf"] is None, f"empty -> log_bf None")
r = bayes_factor([0.5, 0.5], [0.5], [1, 0])
check(r["log_bf"] is None, "mismatch -> None")

print("\n[2] Identical -> log_bf == 0, bf == 1, weak/tie")
r = bayes_factor([0.3, 0.7, 0.5], [0.3, 0.7, 0.5], [1, 1, 0])
check(abs(r["log_bf"]) < 1e-12, f"log_bf=0 (got {r['log_bf']})")
check(abs(r["bf"] - 1.0) < 1e-9, f"bf=1 (got {r['bf']})")
check(r["favors"] == "tie", f"favors=tie")

print("\n[3] A clearly better -> log_bf > 0, favors a")
y = [1, 1, 1, 0, 0, 0]
pa = [0.9, 0.9, 0.9, 0.1, 0.1, 0.1]  # near-perfect
pb = [0.5] * 6  # uninformative
r = bayes_factor(pa, pb, y)
check(r["log_bf"] > 0, f"log_bf>0 (got {r['log_bf']:.3f})")
check(r["favors"] == "a", f"favors=a")
check(r["evidence_strength"] in ("strong", "very_strong", "decisive"),
      f"strong evidence (got {r['evidence_strength']})")

print("\n[4] B better -> log_bf < 0, favors b")
r = bayes_factor(pb, pa, y)
check(r["log_bf"] < 0, f"log_bf<0 (got {r['log_bf']:.3f})")
check(r["favors"] == "b", "favors=b")

print("\n[5] Anti-symmetry: swap a,b -> log_bf flips sign")
r1 = bayes_factor(pa, pb, y)
r2 = bayes_factor(pb, pa, y)
check(abs(r1["log_bf"] + r2["log_bf"]) < 1e-9,
      f"anti-symmetry (got {r1['log_bf']:+.3f} vs {r2['log_bf']:+.3f})")

print("\n[6] Evidence labels boundary check")
# log_bf for tiny advantage -> bf in [1,3) -> weak
y = [1, 0]
pa = [0.55, 0.45]
pb = [0.5, 0.5]
r = bayes_factor(pa, pb, y)
print(f"  log_bf={r['log_bf']:.4f} bf={r['bf']:.4f} -> {r['evidence_strength']}")
check(r["evidence_strength"] in ("weak", "negative"),
      f"small advantage -> weak/neg (got {r['evidence_strength']})")

print("\n[7] Real bench: stretch=True vs stretch=False on holdout v2")
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
check(len(events) >= 40, f"holdout n>=40 (got {len(events)})")

def clf_stretch(framing, contexto=""):
    return classify_and_predict(framing, contexto, apply_stretch=True)

def clf_no_stretch(framing, contexto=""):
    return classify_and_predict(framing, contexto, apply_stretch=False)

pairs_a = pairs_from_events(events, clf_stretch)
pairs_b = pairs_from_events(events, clf_no_stretch)
preds_a = [p for p, _ in pairs_a]
preds_b = [p for p, _ in pairs_b]
reals = [y for _, y in pairs_a]

r = bayes_factor(preds_a, preds_b, reals)
print(f"  n={r['n']} log_bf={r['log_bf']:+.3f} bf={r['bf']:.4g} "
      f"-> {r['evidence_strength']} (favors {r['favors']})")
check(r["n"] >= 40, f"n>=40")
check(math.isfinite(r["log_bf"]), "log_bf finite")
check(r["evidence_strength"] in
      ("negative", "weak", "substantial", "strong", "very_strong", "decisive"),
      f"valid label (got {r['evidence_strength']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
