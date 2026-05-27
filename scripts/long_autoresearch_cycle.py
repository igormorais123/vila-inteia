#!/usr/bin/env python3
"""Long autoresearch/evolution cycle for Vila.

Runs repeated gated evolutionary searches over the political predictor, records
quantitative indicators, applies only promoted candidates, and refreshes the
practical quant diagnosis at the end.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.evolve_political_model import _apply_promotion, run_evolution  # noqa: E402
from scripts.practical_quant_vila import run_diagnosis, write_outputs  # noqa: E402


def _jsonify(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _jsonify(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_jsonify(v) for v in x]
    if isinstance(x, tuple):
        return [_jsonify(v) for v in x]
    if hasattr(x, "item"):
        try:
            return _jsonify(x.item())
        except Exception:
            pass
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _compact_metrics(m: dict) -> dict:
    return {
        "n": m.get("n"),
        "score": m.get("score"),
        "acc": m.get("acc"),
        "brier": m.get("brier"),
        "log_loss": m.get("log_loss"),
        "auc": m.get("auc"),
        "mcc": m.get("mcc"),
        "ece": m.get("ece"),
        "brier_skill_vs_climatology": m.get("brier_skill_vs_climatology"),
        "config": m.get("config", {}),
    }


def _worst_years(m: dict, field: str, limit: int = 3) -> list[dict]:
    rows = []
    for year, vals in (m.get("per_year") or {}).items():
        row = {"year": str(year), **vals}
        rows.append(row)
    rows.sort(key=lambda r: r.get(field) or -1, reverse=True)
    return rows[:limit]


def _summarize_iteration(iteration: int, seed: int, report: dict, applied_path: Path | None, seconds: float) -> dict:
    best = report.get("best", {})
    incumbent = report.get("incumbent", {})
    return _jsonify({
        "iteration": iteration,
        "seed": seed,
        "seconds": round(seconds, 3),
        "promoted": bool(applied_path),
        "applied_path": str(applied_path) if applied_path else None,
        "gate": report.get("gate", {}),
        "incumbent": _compact_metrics(incumbent),
        "best": _compact_metrics(best),
        "delta": {
            "score": (best.get("score") or 0) - (incumbent.get("score") or 0),
            "acc": (best.get("acc") or 0) - (incumbent.get("acc") or 0),
            "brier": (best.get("brier") or 0) - (incumbent.get("brier") or 0),
            "ece": (best.get("ece") or 0) - (incumbent.get("ece") or 0),
            "mcc": (best.get("mcc") or 0) - (incumbent.get("mcc") or 0),
        },
        "worst_ece_years": _worst_years(best, "ece"),
        "worst_brier_years": _worst_years(best, "brier"),
        "leaderboard_top": [_compact_metrics(x) for x in report.get("leaderboard", [])[:5]],
    })


def _best_seen(iterations: list[dict]) -> dict:
    if not iterations:
        return {}
    return max(iterations, key=lambda r: r.get("best", {}).get("score") or float("-inf"))


def _count_gate_checks(iterations: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for row in iterations:
        for key, val in (row.get("gate", {}).get("checks") or {}).items():
            if val:
                counts[key] = counts.get(key, 0) + 1
    return counts


def run_long_cycle(
    *,
    iterations: int = 20,
    population: int = 24,
    generations: int = 8,
    seed: int = 4200,
    apply: bool = False,
    enforce_minimum: bool = True,
    diagnostics: bool = True,
    out_json: str | Path = "data/long_autoresearch_cycle_latest.json",
    out_md: str | Path = "data/long_autoresearch_cycle_latest.md",
    practical_json: str | Path = "data/practical_quant_vila_latest.json",
    practical_md: str | Path = "data/practical_quant_vila_latest.md",
    practical_csv: str | Path = "data/practical_quant_backtest_events.csv",
) -> dict:
    if enforce_minimum and iterations < 20:
        raise ValueError("long cycle requires at least 20 iterations")

    started = time.time()
    start_diag = None
    if diagnostics:
        start_diag, _ = run_diagnosis()

    iteration_rows: list[dict] = []
    full_reports: list[dict] = []
    last_promoted_report: dict | None = None
    for i in range(1, iterations + 1):
        iter_seed = seed + i
        t0 = time.time()
        report = run_evolution(population_size=population, generations=generations, seed=iter_seed)
        applied_path = _apply_promotion(report) if apply else None
        if applied_path:
            last_promoted_report = report
            (ROOT / "data" / "political_evolution.json").write_text(
                json.dumps(report, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        iteration_rows.append(_summarize_iteration(i, iter_seed, report, applied_path, time.time() - t0))
        full_reports.append(report)

    end_diag = None
    if diagnostics:
        end_diag, df = run_diagnosis()
        write_outputs(
            end_diag,
            df,
            out_json=practical_json,
            out_md=practical_md,
            out_csv=practical_csv,
        )

    best_row = _best_seen(iteration_rows)
    cycle = _jsonify({
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "protocol": {
            "type": "long_autoresearch_evolution",
            "iterations_requested": iterations,
            "iterations_completed": len(iteration_rows),
            "population": population,
            "generations": generations,
            "seed_start": seed,
            "apply_promotions": apply,
            "gate": "acc/mcc/auc not worse, brier not materially worse, composite better",
            "indicators": [
                "composite_score",
                "accuracy",
                "MCC",
                "ROC_AUC",
                "Brier",
                "log_loss",
                "ECE",
                "Brier_skill_vs_climatology",
                "worst_year_ECE",
                "worst_year_Brier",
                "gauntlet_pass_rate",
            ],
        },
        "runtime_seconds": round(time.time() - started, 3),
        "summary": {
            "promotions": sum(1 for row in iteration_rows if row["promoted"]),
            "best_seen_iteration": best_row.get("iteration"),
            "best_seen_score": best_row.get("best", {}).get("score"),
            "best_seen_config": best_row.get("best", {}).get("config", {}),
            "gate_checks_passed_counts": _count_gate_checks(iteration_rows),
            "last_promoted_report_written": bool(last_promoted_report),
        },
        "diagnostics_before": start_diag,
        "diagnostics_after": end_diag,
        "iterations": iteration_rows,
        "full_evolution_reports": full_reports,
    })

    json_path = Path(out_json)
    md_path = Path(out_md)
    if not json_path.is_absolute():
        json_path = ROOT / json_path
    if not md_path.is_absolute():
        md_path = ROOT / md_path
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(cycle, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(cycle), encoding="utf-8")
    return cycle


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "-"
    try:
        f = float(v)
    except Exception:
        return str(v)
    if not math.isfinite(f):
        return "-"
    return f"{f:.{digits}f}"


def render_markdown(cycle: dict) -> str:
    summary = cycle.get("summary", {})
    proto = cycle.get("protocol", {})
    lines = [
        "# Vila Long AutoResearch Cycle",
        "",
        f"- Generated: `{cycle.get('generated_at')}`",
        f"- Iterations: `{proto.get('iterations_completed')}`/`{proto.get('iterations_requested')}`",
        f"- Population x generations: `{proto.get('population')}` x `{proto.get('generations')}`",
        f"- Promotions: `{summary.get('promotions')}`",
        f"- Runtime: `{cycle.get('runtime_seconds')}` seconds",
        "",
        "## Best Seen",
        "",
        f"- Iteration: `{summary.get('best_seen_iteration')}`",
        f"- Score: `{_fmt(summary.get('best_seen_score'), 6)}`",
        f"- Config: `{json.dumps(summary.get('best_seen_config', {}), ensure_ascii=False)}`",
        "",
        "## Iterations",
        "",
        "| iter | seed | promoted | score | acc | brier | ece | mcc | gate |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in cycle.get("iterations", []):
        best = row.get("best", {})
        gate = row.get("gate", {})
        gate_label = "promoted" if row.get("promoted") else gate.get("reason", "retained")
        lines.append(
            f"| {row.get('iteration')} | {row.get('seed')} | {row.get('promoted')} | "
            f"{_fmt(best.get('score'), 6)} | {_fmt(best.get('acc'))} | "
            f"{_fmt(best.get('brier'))} | {_fmt(best.get('ece'))} | "
            f"{_fmt(best.get('mcc'))} | {gate_label} |"
        )

    after = cycle.get("diagnostics_after") or {}
    if after:
        pol = after.get("political", {})
        best = pol.get("best_metrics", {})
        lines += [
            "",
            "## Final Diagnostic",
            "",
            f"- Political evolved acc: `{_fmt(best.get('acc'))}`",
            f"- Political evolved Brier: `{_fmt(best.get('brier'))}`",
            f"- Political evolved AUC: `{_fmt(best.get('auc'))}`",
            f"- Political evolved MCC: `{_fmt(best.get('mcc'))}`",
            f"- Political evolved ECE: `{_fmt(best.get('ece'))}`",
            "",
            "## Actions",
            "",
        ]
        for rec in after.get("recommendations", []):
            lines.append(f"{rec.get('priority')}. **{rec.get('area')}**: {rec.get('action')} Evidence: {rec.get('evidence')}")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run a long gated autoresearch cycle.")
    p.add_argument("--iterations", type=int, default=20)
    p.add_argument("--population", type=int, default=24)
    p.add_argument("--generations", type=int, default=8)
    p.add_argument("--seed", type=int, default=4200)
    p.add_argument("--apply", action="store_true", help="apply candidates that pass gates")
    p.add_argument("--allow-short", action="store_true", help="allow fewer than 20 iterations")
    p.add_argument("--no-diagnostics", action="store_true")
    p.add_argument("--out-json", default="data/long_autoresearch_cycle_latest.json")
    p.add_argument("--out-md", default="data/long_autoresearch_cycle_latest.md")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cycle = run_long_cycle(
        iterations=args.iterations,
        population=args.population,
        generations=args.generations,
        seed=args.seed,
        apply=args.apply,
        enforce_minimum=not args.allow_short,
        diagnostics=not args.no_diagnostics,
        out_json=args.out_json,
        out_md=args.out_md,
    )
    summary = cycle["summary"]
    print(f"Iterations: {cycle['protocol']['iterations_completed']}/{cycle['protocol']['iterations_requested']}")
    print(f"Promotions: {summary['promotions']}")
    print(f"Best score: {summary['best_seen_score']:.6f}")
    print(f"Saved -> {ROOT / args.out_json if not Path(args.out_json).is_absolute() else Path(args.out_json)}")
    print(f"Saved -> {ROOT / args.out_md if not Path(args.out_md).is_absolute() else Path(args.out_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
