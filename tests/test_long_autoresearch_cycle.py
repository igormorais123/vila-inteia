#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.long_autoresearch_cycle import render_markdown, run_long_cycle


ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {msg}")
    else:
        fail += 1
        print(f"  FAIL {msg}")


print("=== test_long_autoresearch_cycle ===")

with TemporaryDirectory() as td:
    out_json = Path(td) / "cycle.json"
    out_md = Path(td) / "cycle.md"
    cycle = run_long_cycle(
        iterations=1,
        population=4,
        generations=1,
        seed=900,
        apply=False,
        enforce_minimum=False,
        diagnostics=False,
        out_json=out_json,
        out_md=out_md,
    )
    check(cycle["protocol"]["iterations_completed"] == 1, "one iteration completed")
    check(cycle["iterations"][0]["best"]["score"] is not None, "best score present")
    check("acc_not_worse" in cycle["iterations"][0]["gate"]["checks"], "gate checks present")
    check(out_json.exists(), "json written")
    check(out_md.exists(), "md written")

    loaded = json.loads(out_json.read_text(encoding="utf-8"))
    check(loaded["protocol"]["iterations_requested"] == 1, "json roundtrip")
    md = render_markdown(cycle)
    check("# Vila Long AutoResearch Cycle" in md, "markdown header")
    check("Iterations" in md, "markdown table section")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
