"""Test engine/llm_coordinator.py + strategy_autoresearch.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.llm_coordinator import _parse_plan, llm_pick_strategy
from engine.strategy_autoresearch import (
    candidate_weight_combos, evaluate_combo_per_event,
    discover_best_per_category, autoresearch_predict,
)
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(c, m):
    global ok, fail
    if c: ok += 1; print(f"  OK  {m}")
    else: fail += 1; print(f"  FAIL {m}")

print("=== test_llm_coordinator + strategy_autoresearch ===")

print("\n[1] _parse_plan handles valid JSON")
text = '{"weights": {"vila": 0.5, "llm_direct": 0.5}, "rationale": "test"}'
p = _parse_plan(text)
check(p is not None, f"parsed (got {p})")
check(p["weights"]["vila"] == 0.5, "weights extracted")

print("\n[2] _parse_plan handles fenced output")
text = "```json\n{\"weights\": {\"vila\": 0.7, \"lindy\": 0.3}, \"rationale\": \"x\"}\n```"
p = _parse_plan(text)
check(p is not None and "weights" in p, f"fenced parsed")

print("\n[3] _parse_plan returns None on bad input")
check(_parse_plan("garbage") is None, "garbage → None")
check(_parse_plan("") is None, "empty → None")

print("\n[4] candidate_weight_combos generates valid combos")
combos = candidate_weight_combos(step=0.5)
check(len(combos) > 5, f"≥5 combos (got {len(combos)})")
for c in combos:
    s = sum(c.values())
    check(abs(s - 1.0) < 1e-9, f"sums to 1 (got {s:.3f})")
    if not (abs(s - 1.0) < 1e-9):
        break

print("\n[5] evaluate_combo_per_event with synthetic events")
events = [
    {"outcome_framing": "Olympics held in 2026", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Olympics held in 2026", "outcome_real": 1, "contexto": ""},
]
b = evaluate_combo_per_event(events, {"vila": 1.0})
check(0 <= b <= 1, f"brier in [0,1] (got {b:.3f})")

print("\n[6] discover_best_per_category returns dict")
best = discover_best_per_category(events)
check(isinstance(best, dict), "dict returned")
check(len(best) >= 1, f"≥1 category (got {len(best)})")

print("\n[7] autoresearch_predict uses discovered weights")
p = autoresearch_predict("Olympics held in 2026", "scheduled event", best)
check(0 < p < 1, f"valid prob (got {p:.3f})")

print("\n[8] autoresearch_predict falls back when category unseen")
p = autoresearch_predict("Random unseen event", "", best)
check(0 < p < 1, f"fallback to vila (got {p:.3f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
