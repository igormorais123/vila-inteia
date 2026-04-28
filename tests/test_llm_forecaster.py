"""Test engine/llm_forecaster.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.llm_forecaster import llm_predict, evaluate_llm_forecaster, _CACHE

ok = fail = 0
def check(c, m):
    global ok, fail
    if c: ok += 1; print(f"  OK  {m}")
    else: fail += 1; print(f"  FAIL {m}")

print("=== test_llm_forecaster ===")

print("\n[1] llm_predict — no key returns None or 0.5 fallback")
import os
saved = {k: os.environ.pop(k, None) for k in ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "OMNIROUTE_KEY"]}
_CACHE.clear()
p = llm_predict("Test event", "Test context")
check(p is None or 0 <= p <= 1, f"None or valid prob (got {p})")
for k, v in saved.items():
    if v is not None:
        os.environ[k] = v

print("\n[2] cache stores results")
_CACHE["test|"] = 0.7
p = llm_predict("test", "")
check(p == 0.7, f"cached value returned ({p})")

print("\n[3] evaluate fallback handles no-LLM")
events = [
    {"outcome_framing": "test1", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "test2", "outcome_real": 0, "contexto": ""},
]
_CACHE.clear()
res = evaluate_llm_forecaster(events, max_events=2)
check("n" in res, "returns dict")
check(res["n"] == 2, f"n=2 (got {res['n']})")

print("\n[4] eval returns brier in [0,1]")
check(0 <= res["brier"] <= 1, f"brier valid ({res['brier']:.3f})")

print("\n[5] llm_available flag set correctly")
check("llm_available" in res, "flag present")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
