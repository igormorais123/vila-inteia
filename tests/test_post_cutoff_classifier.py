"""Onda 249: testa engine/post_cutoff_classifier.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.post_cutoff_classifier import (
    classify_and_predict, evaluate_classifier_on_events,
    KEYWORD_PRIORS,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_post_cutoff_classifier ===")

print("\n[1] KEYWORD_PRIORS estrutura")
check(len(KEYWORD_PRIORS) >= 10, f"10+ categories (got {len(KEYWORD_PRIORS)})")
for kws, prior, label in KEYWORD_PRIORS:
    check(0 <= prior <= 1, f"{label} prior in [0,1] (got {prior})")
    check(isinstance(kws, list) and len(kws) > 0, f"{label} keywords list non-empty")

print("\n[2] classify_and_predict — war/conflict")
p, lbl = classify_and_predict("Israel attack Iran")
check(lbl == "war_conflict", f"war detected (got {lbl})")
check(p == 0.80, f"high prior (got {p})")

print("\n[3] tech release")
p, lbl = classify_and_predict("Apple lança new product")
check(lbl == "tech_release", f"tech release (got {lbl})")
check(p == 0.45, f"moderate-low (got {p})")

print("\n[4] scheduled event")
p, lbl = classify_and_predict("Olympics summit held in March")
check(lbl == "scheduled_event", f"scheduled (got {lbl})")
check(p == 0.95, f"very high (got {p})")

print("\n[5] price target / threshold")
p, lbl = classify_and_predict("Bitcoin ATH hits k+")  # avoid $ trigger
check(lbl == "price_target", f"price target (got {lbl})")
check(p == 0.40, f"low prior (got {p})")

# Threshold-style price events go to price_threshold
p, lbl = classify_and_predict("AAPL fecha acima de $250")
check(lbl == "price_threshold", f"price threshold (got {lbl})")
check(p == 0.50, f"chance prior (got {p})")

print("\n[6] default fallback")
p, lbl = classify_and_predict("Generic event without keywords")
check(lbl == "default", f"default (got {lbl})")
check(p == 0.50, f"baseline prior (got {p})")

print("\n[7] evaluate_classifier_on_events")
events = [
    {"outcome_framing": "Israel attack Iran", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Apple launches gizmo", "outcome_real": 0, "contexto": ""},
    {"outcome_framing": "Generic", "outcome_real": 1, "contexto": ""},
]
res = evaluate_classifier_on_events(events)
check(res["n"] == 3, f"3 events (got {res['n']})")
# Israel hit (0.80 → cls 1, real 1) ✓
# Apple miss (0.45 → cls 0, real 0) ✓
# Generic (0.50 → cls 1, real 1) ✓
check(res["hits"] == 3, f"3 hits expected (got {res['hits']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
