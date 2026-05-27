#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.practical_quant_vila import render_markdown, run_diagnosis, write_outputs


ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {msg}")
    else:
        fail += 1
        print(f"  FAIL {msg}")


print("=== test_practical_quant_vila ===")

report, df = run_diagnosis()

meta = report["backtest"]["meta"]
check(meta["released_rows"] > 7000, f"released rows > 7000 (got {meta['released_rows']})")
check(meta["files"] >= 60, f"uses broad backtest corpus (got {meta['files']})")
check(len(df) == meta["released_rows"], "dataframe row count matches meta")

print("\n[1] quant outputs")
quant = report["quant"]
check("correlations" in quant and quant["correlations"]["pairs"], "correlation pairs present")
check("glm_outcome" in quant or "glm_outcome_error" in quant, "glm attempted")
check("lm_prior_brier" in quant or "lm_prior_brier_error" in quant, "lm attempted")

print("\n[2] operational diagnostics")
check(report["political"]["best_metrics"]["n"] == 394, "political evolution metrics loaded")
check(report["gauntlet"]["summary"]["total"]["pass"] >= 173, "gauntlet summary loaded")
check(len(report["recommendations"]) >= 3, "recommendations generated")

print("\n[3] render/write")
md = render_markdown(report)
check("# Vila Practical Quant Run" in md, "markdown header")
check("Practical Actions" in md, "markdown actions section")

with TemporaryDirectory() as td:
    out_json = Path(td) / "report.json"
    out_md = Path(td) / "report.md"
    out_csv = Path(td) / "events.csv"
    write_outputs(report, df, out_json=out_json, out_md=out_md, out_csv=out_csv)
    check(out_json.exists(), "json written")
    check(out_md.exists(), "md written")
    check(out_csv.exists(), "csv written")
    loaded = json.loads(out_json.read_text(encoding="utf-8"))
    check(loaded["backtest"]["meta"]["released_rows"] == meta["released_rows"], "json roundtrip")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
