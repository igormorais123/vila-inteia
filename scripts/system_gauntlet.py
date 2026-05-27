#!/usr/bin/env python3
"""Run the Vila INTEIA system gauntlet.

The repository uses many script-style tests. This runner executes each test in
an isolated Python process, classifies results by area, and writes a compact
evolution report for follow-up fixes.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
DATA = ROOT / "data"
GAUNTLET_SITE = ROOT / "scripts" / "gauntlet_site"


AREA_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("politica", ("politic", "btc", "claude_motor", "lodo")),
    ("quant", ("quant", "cor", "regress", "brier", "calibr", "roc", "mcnemar", "wilson", "wasserstein", "ks", "mann", "wilcoxon", "fisher", "hosmer", "pit", "sharpe", "var")),
    ("forecasting", ("forecast", "backtest", "ensemble", "market", "llm", "lindy", "conformal", "selective", "pre_registration", "reliability", "predictive", "time_decay", "outcome")),
    ("game_theory", ("game", "opinion", "shapley", "thompson", "ucb", "exp3", "adahedge", "regret", "kelly", "hedge", "online")),
    ("vila_sim", ("vila", "persona", "personagens", "panel", "bateria", "conversas", "rede", "colmeia", "onda", "ondas", "simulacao")),
    ("psicohistoria", ("psico", "crenca", "detector_estado", "forecast_narrativo", "counterfactual", "super_intelligence", "recomendacao")),
    ("infra", ("auth", "webhook", "workspace", "event_log", "snapshot", "replay", "external", "provider", "groq", "gemini", "pdf", "proveniencia", "micro_events")),
]


def classify(path: Path) -> str:
    name = path.name.lower()
    for area, needles in AREA_RULES:
        if any(n in name for n in needles):
            return area
    return "core"


def run_cmd(name: str, cmd: list[str], *, cwd: Path, timeout: int) -> dict[str, Any]:
    start = time.time()
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env["VILA_REPO_ROOT"] = str(ROOT)
    py_path = [str(GAUNTLET_SITE), str(ROOT)]
    if env.get("PYTHONPATH"):
        py_path.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(py_path)
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        status = "pass" if p.returncode == 0 else "fail"
        code = p.returncode
        output = p.stdout or ""
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        code = None
        raw = exc.stdout or ""
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        output = raw + "\nTIMEOUT"
    return {
        "name": name,
        "cmd": cmd,
        "cwd": str(cwd.relative_to(ROOT) if ROOT in cwd.parents or cwd == ROOT else cwd),
        "status": status,
        "returncode": code,
        "seconds": round(time.time() - start, 3),
        "output_tail": output[-4000:],
    }


def run_test(path: Path, timeout: int) -> dict[str, Any]:
    r = run_cmd(path.name, [sys.executable, str(path)], cwd=ROOT, timeout=timeout)
    r["area"] = classify(path)
    r["path"] = str(path.relative_to(ROOT))
    return r


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_area: dict[str, dict[str, int]] = {}
    for r in results:
        area = r.get("area", "system")
        by_area.setdefault(area, {"pass": 0, "fail": 0, "timeout": 0, "total": 0})
        by_area[area][r["status"]] = by_area[area].get(r["status"], 0) + 1
        by_area[area]["total"] += 1
    total = {"pass": 0, "fail": 0, "timeout": 0, "total": 0}
    for counts in by_area.values():
        for k in total:
            total[k] += counts.get(k, 0)
    return {"total": total, "by_area": by_area}


def render_md(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# Vila System Gauntlet",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Total: {s['total']['pass']}/{s['total']['total']} pass; "
        f"{s['total']['fail']} fail; {s['total']['timeout']} timeout",
        "",
        "## Areas",
        "",
        "| area | pass | fail | timeout | total |",
        "|---|---:|---:|---:|---:|",
    ]
    for area, counts in sorted(s["by_area"].items()):
        lines.append(
            f"| {area} | {counts.get('pass', 0)} | {counts.get('fail', 0)} | "
            f"{counts.get('timeout', 0)} | {counts.get('total', 0)} |"
        )
    bad = [r for r in report["results"] if r["status"] != "pass"]
    if bad:
        lines += ["", "## Failures", ""]
        for r in bad:
            lines.append(f"### {r['path']} [{r['status']}]")
            lines.append("")
            lines.append("```text")
            lines.append(r.get("output_tail", "").strip()[-1800:])
            lines.append("```")
            lines.append("")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run all Vila script-style tests.")
    p.add_argument("--pattern", default="test_*.py")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--area", action="append", help="run only this classified area")
    p.add_argument("--include-frontend", action="store_true")
    p.add_argument("--out", default=str(DATA / "system_gauntlet_latest.json"))
    p.add_argument("--md", default=str(DATA / "system_gauntlet_latest.md"))
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tests = sorted(TESTS.glob(args.pattern))
    if args.area:
        areas = set(args.area)
        tests = [t for t in tests if classify(t) in areas]

    results: list[dict[str, Any]] = []
    start = time.time()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(run_test, path, args.timeout) for path in tests]
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            print(f"[{r['status'].upper():7}] {r.get('area','?'):14} {r['name']} ({r['seconds']}s)")

    if args.include_frontend:
        results.append(run_cmd("python_compile", [sys.executable, "-m", "compileall", "api", "engine", "scripts", "-q"], cwd=ROOT, timeout=120) | {"area": "system"})
        results.append(run_cmd("npm_lint", ["npm.cmd", "run", "lint"], cwd=ROOT / "frontend-next", timeout=120) | {"area": "frontend"})
        results.append(run_cmd("npm_build", ["npm.cmd", "run", "build"], cwd=ROOT / "frontend-next", timeout=180) | {"area": "frontend"})

    results.sort(key=lambda r: (r.get("area", ""), r.get("name", "")))
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "seconds": round(time.time() - start, 3),
        "workers": args.workers,
        "timeout": args.timeout,
        "summary": summarize(results),
        "results": results,
    }
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md = Path(args.md)
    if not md.is_absolute():
        md = ROOT / md
    md.write_text(render_md(report), encoding="utf-8")
    print(f"\nSaved -> {out}")
    print(f"Saved -> {md}")
    total = report["summary"]["total"]
    print(f"TOTAL {total['pass']}/{total['total']} pass; fail={total['fail']} timeout={total['timeout']}")
    return 0 if total["fail"] == 0 and total["timeout"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
