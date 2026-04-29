"""Test hybrid_autotune."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.hybrid_autotune import (
    autotune_hybrid, autotune_predict, evaluate_autotuned,
    _hybrid_with_params, GATE_GRID, W_LLM_GRID,
)

ok = fail = 0
def check(c, m):
    global ok, fail
    if c: ok += 1; print(f"  OK  {m}")
    else: fail += 1; print(f"  FAIL {m}")

print("=== test_hybrid_autotune ===")

print("\n[1] _hybrid_with_params behavior")
# Vila confident → returns Vila
p = _hybrid_with_params(0.95, 0.20, gate=0.30, w_llm=0.7)
check(p == 0.95, f"vila confident returned (got {p})")
# Vila uncertain → log-pool
p = _hybrid_with_params(0.5, 0.8, gate=0.30, w_llm=0.7)
check(p > 0.5, f"uncertain → log-pool toward llm (got {p:.3f})")

print("\n[2] gate=0 always pools")
p = _hybrid_with_params(0.95, 0.05, gate=0.0, w_llm=0.5)
check(p < 0.95, f"gate=0 pools even when confident (got {p:.3f})")

print("\n[3] GATE_GRID and W_LLM_GRID structure")
check(len(GATE_GRID) >= 5, f"≥5 gates (got {len(GATE_GRID)})")
check(len(W_LLM_GRID) >= 5, f"≥5 w_llm (got {len(W_LLM_GRID)})")
check(0.0 in GATE_GRID and 0.50 in GATE_GRID, "endpoints present")

print("\n[4] autotune_hybrid empty events")
res = autotune_hybrid([])
check("gate" in res and "w_llm" in res, "returns dict with gate, w_llm")
check(res["n"] == 0, f"n=0 (got {res['n']})")

print("\n[5] autotune_predict falls back to Vila when no LLM")
# Empty params → use defaults
p = autotune_predict("Olympics summit held in March 2026", "scheduled",
                     {"gate": 0.5, "w_llm": 0.85})
check(0 < p < 1, f"valid prob (got {p:.3f})")

print("\n[6] autotune_predict with high gate trusts Vila")
p = autotune_predict("Olympics summit held in March 2026", "scheduled",
                     {"gate": 0.5, "w_llm": 0.85})
# Vila gives ~0.99 → confident → returns Vila
check(p > 0.9, f"confident scheduled → high (got {p:.3f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
