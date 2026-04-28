"""Test engine/vila_llm_hybrid.py + log_pool."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.log_pool import log_pool, log_pool_predict, _logit, _sigmoid
from engine.vila_llm_hybrid import vila_llm_hybrid_predict, evaluate_hybrid

ok = fail = 0
def check(c, m):
    global ok, fail
    if c: ok += 1; print(f"  OK  {m}")
    else: fail += 1; print(f"  FAIL {m}")

print("=== test_vila_llm_hybrid ===")

print("\n[1] log_pool symmetry: equal probs → same prob")
p = log_pool({"a": 0.7, "b": 0.7})
check(abs(p - 0.7) < 1e-9, f"equal in → equal out (got {p:.4f})")

print("\n[2] log_pool extremes pulled by majority")
p = log_pool({"a": 0.9, "b": 0.5, "c": 0.5})
check(0.5 < p < 0.9, f"between (got {p:.3f})")

print("\n[3] log_pool_predict two forecaster")
p = log_pool_predict(0.8, 0.2, w_a=0.5)
check(abs(p - 0.5) < 1e-9, f"opposite at 50/50 → 0.5 (got {p:.4f})")

p = log_pool_predict(0.8, 0.2, w_a=1.0)
check(abs(p - 0.8) < 1e-3, f"w_a=1 → first (got {p:.3f})")

print("\n[4] _logit / _sigmoid round-trip")
for x in [0.1, 0.3, 0.5, 0.7, 0.9]:
    rt = _sigmoid(_logit(x))
    check(abs(rt - x) < 1e-6, f"round-trip {x} → {rt:.4f}")

print("\n[5] vila_llm_hybrid falls back to Vila when LLM unavailable")
import os
saved = {k: os.environ.pop(k, None) for k in ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"]}
import shutil as _sh
old_which = _sh.which
_sh.which = lambda x: None  # disable claude CLI lookup
try:
    p = vila_llm_hybrid_predict("Olympics summit held in March 2026",
                                "scheduled event")
    check(0 < p < 1, f"hybrid returns valid prob (got {p:.3f})")
finally:
    _sh.which = old_which
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
