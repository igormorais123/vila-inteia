"""Tests for engine/forecast_result.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.forecast_result import ForecastResult
from engine.combined_pipeline import combined_report
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_forecast_result ===")

print("\n[1] Construction + frozen")
r = ForecastResult(
    n=10,
    base_acc=0.8,
    base_brier=0.15,
    bootstrap_brier_ci=(0.10, 0.20),
    selective={0.3: {"selective_acc": 0.9}},
    conformal={"singleton_acc": 0.95},
    murphy={"reliability": 0.05},
    time_series_cv={"mean_acc": 0.75},
)
check(r.n == 10, f"n=10 (got {r.n})")
check(r.base_acc == 0.8, "base_acc=0.8")
check(r.bootstrap_brier_ci == (0.10, 0.20), "tuple CI")

frozen_caught = False
try:
    r.n = 99  # type: ignore[misc]
except Exception:
    frozen_caught = True
check(frozen_caught, "dataclass is frozen")

print("\n[2] as_dict() round-trip")
d = r.as_dict()
check(set(d.keys()) == {"n", "base_acc", "base_brier", "bootstrap_brier_ci",
                          "selective", "conformal", "murphy", "time_series_cv"},
      "all keys present")
check(d["n"] == 10 and d["base_acc"] == 0.8, "values match")
check(d["selective"][0.3]["selective_acc"] == 0.9, "nested dict preserved")

print("\n[3] Subscript backcompat")
check(r["n"] == 10, "r['n']")
check(r["selective"][0.3]["selective_acc"] == 0.9, "r['selective'][...]")
check("conformal" in r, "'conformal' in r")
check("missing_key" not in r, "missing key absent")

print("\n[4] Integration with combined_report")
events = [
    {"outcome_framing": "war event", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Olympics held", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "tech launches", "outcome_real": 0, "contexto": ""},
    {"outcome_framing": "Bitcoin > $200k", "outcome_real": 0, "contexto": ""},
    {"outcome_framing": "FOMC reunião realizada", "outcome_real": 1, "contexto": ""},
] * 4  # 20

res = combined_report(events, classify_and_predict)
check(isinstance(res, ForecastResult), "combined_report returns ForecastResult")
check(res.n == 20, f"n=20 (got {res.n})")
check(0.0 <= res.base_acc <= 1.0, f"base_acc in [0,1]")
check(isinstance(res.selective, dict) and 0.30 in res.selective, "selective has tau=0.30")
check(isinstance(res.conformal, dict), "conformal is dict")
check(isinstance(res.murphy, dict) and "reliability" in res.murphy, "murphy has reliability")

print("\n[5] Backward-compat dict consumption")
# Old code may use d['selective'][0.3] or d['n'] — check both work via subscript
check(res["n"] == res.n, "subscript == attr (n)")
check(res["base_brier"] == res.base_brier, "subscript == attr (base_brier)")
d2 = res.as_dict()
check(d2["bootstrap_brier_ci"] == res.bootstrap_brier_ci, "as_dict CI matches")
check(isinstance(d2, dict), "as_dict is plain dict")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
