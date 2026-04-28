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

print("\n[2] classify_and_predict — war/conflict (raw=0.80)")
p, lbl = classify_and_predict("Israel attack Iran", apply_stretch=False, use_eb_tuned=False)
check(lbl == "war_conflict", f"war detected (got {lbl})")
check(p == 0.80, f"raw prior (got {p})")
# EB-tuned prior 0.880 + stretch: 0.5 + 1.5*(0.88-0.5) = 1.07 clipped to 1.0
p_s, _ = classify_and_predict("Israel attack Iran")
check(p_s == 1.0, f"EB+stretch (got {p_s})")

print("\n[3] tech release (raw=0.45)")
p, lbl = classify_and_predict("Apple lança new product", apply_stretch=False, use_eb_tuned=False)
check(lbl == "tech_release", f"tech release (got {lbl})")
check(p == 0.45, f"raw prior (got {p})")

print("\n[4] scheduled event (raw=0.92)")
p, lbl = classify_and_predict("Olympics summit held in March", apply_stretch=False, use_eb_tuned=False)
check(lbl == "scheduled_event", f"scheduled (got {lbl})")
check(p == 0.92, f"raw prior (got {p})")
# EB-tuned scheduled_event 0.829, stretch: 0.5 + 1.5*(0.829-0.5) ≈ 0.99
p_s, _ = classify_and_predict("Olympics summit held in March")
check(p_s > 0.95, f"EB+stretch high (got {p_s})")

print("\n[5] price target / threshold (raw=0.40)")
p, lbl = classify_and_predict("Bitcoin ATH hits k+", apply_stretch=False, use_eb_tuned=False)
check(lbl == "price_target", f"price target (got {lbl})")
check(p == 0.40, f"raw prior (got {p})")

p, lbl = classify_and_predict("AAPL fecha acima de $250", apply_stretch=False, use_eb_tuned=False)
check(lbl == "price_threshold", f"price threshold (got {lbl})")
check(p == 0.50, f"chance prior (got {p})")

print("\n[6] default fallback (raw=0.50)")
p, lbl = classify_and_predict("Generic event without keywords", apply_stretch=False, use_eb_tuned=False)
check(lbl == "default", f"default (got {lbl})")
check(p == 0.50, f"baseline prior (got {p})")
# EB-tuned default ≈ 0.694, stretch: 0.5 + 1.5*(0.694-0.5) ≈ 0.79
p_s, _ = classify_and_predict("Generic event without keywords")
check(0.75 < p_s < 0.85, f"EB+stretch (got {p_s})")

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
