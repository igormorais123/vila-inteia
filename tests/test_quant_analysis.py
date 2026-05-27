#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from engine.quant_analysis import (
    analyze_dataframe,
    r_chisq_test,
    r_cor,
    r_glm_binomial,
    r_lm,
    r_partial_cor,
    r_t_test,
)


passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = ""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {detail}")


print("=== test_quant_analysis ===\n")

x_vals = list(range(1, 41))
z_vals = [(i * 7) % 11 for i in x_vals]
noise = [0.15 if i % 2 else -0.10 for i in x_vals]
df = pd.DataFrame({
    "x": x_vals,
    "z": z_vals,
    "y": [2.0 * x + 0.35 * z + e for x, z, e in zip(x_vals, z_vals, noise)],
    "g": ["a"] * 20 + ["b"] * 20,
    "flag": [1 if i in {5, 11, 17} or i >= 24 and i not in {27, 34, 39} else 0 for i in x_vals],
})

print("[1] summary + cor")
report = analyze_dataframe(df, target="y", group="g")
check("summary rows", report["summary"]["n_rows"] == 40)
cor = r_cor(df, columns=["x", "y", "z"])
top = cor["pairs"][0]
check("x/y strongest positive", {top["x"], top["y"]} == {"x", "y"} and top["r"] > 0.99)

print("\n[2] lm")
lm = r_lm(df, formula="y ~ x + z")
coef_x = next(c for c in lm["coefficients"] if c["term"] == "x")
check("lm slope x approx 2", abs(coef_x["estimate"] - 2.0) < 0.05, str(coef_x))
check("lm r2 high", lm["metrics"]["r_squared"] > 0.999)

print("\n[3] glm binomial")
glm = r_glm_binomial(df, formula="flag ~ x")
check("glm has coeffs", len(glm["coefficients"]) >= 2)
check("glm acc high", glm["metrics"]["accuracy_0_5"] >= 0.8)

print("\n[4] tests")
tt = r_t_test(df, value="y", group="g")
check("t-test detects group diff", tt["p"] < 0.01, str(tt))
chi = r_chisq_test(df, row="g", col="flag")
check("chisq association", chi["p"] < 0.05, str(chi))

print("\n[5] partial correlation")
pc = r_partial_cor(df, x="x", y="y", covar=["z"])
check("partial cor remains high", pc["r"] is not None and pc["r"] > 0.99, str(pc))

print(f"\n== {passed} passed, {failed} failed ==")
sys.exit(0 if failed == 0 else 1)
