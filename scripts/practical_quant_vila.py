#!/usr/bin/env python3
"""Practical quantitative run over Vila's own data.

This script turns the quantitative toolkit into an operational diagnostic:
released backtest events, political evolution metrics and gauntlet timings are
processed into JSON/Markdown/CSV artifacts that can feed the next evolution
cycle.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.quant_analysis import (  # noqa: E402
    r_aov,
    r_chisq_test,
    r_cor,
    r_glm_binomial,
    r_lm,
    r_partial_cor,
)


def _jsonify(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _jsonify(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_jsonify(v) for v in x]
    if isinstance(x, tuple):
        return [_jsonify(v) for v in x]
    if pd.isna(x):
        return None
    if hasattr(x, "item"):
        try:
            return _jsonify(x.item())
        except Exception:
            pass
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _read_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        out = float(str(value).replace(",", "."))
    except ValueError:
        return None
    return out if math.isfinite(out) else None


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(",", ".")))
    except ValueError:
        return None


def _event_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def load_backtest_events(base_dir: str | Path, *, today: date | None = None) -> tuple[pd.DataFrame, dict]:
    """Load released rows from data/backtest while preserving extra columns."""
    base = Path(base_dir)
    if not base.is_absolute():
        base = ROOT / base
    today = today or date.today()

    rows: list[dict[str, Any]] = []
    skipped_future = 0
    skipped_missing = 0
    files = sorted(base.glob("*.csv"))
    for path in files:
        with path.open(newline="", encoding="utf-8") as f:
            for raw in csv.DictReader(f):
                outcome = _to_int(raw.get("outcome_real"))
                if outcome not in (0, 1):
                    skipped_missing += 1
                    continue
                dt = _event_date(raw.get("data"))
                if dt and dt > today:
                    skipped_future += 1
                    continue

                prior = _to_float(raw.get("probabilidade_prior"))
                lead = _to_float(raw.get("poll_lead_pp"))
                inc = _to_int(raw.get("incumbente")) or 0
                year = _to_int(raw.get("ano")) or (dt.year if dt else None)
                abs_lead = abs(lead) if lead is not None else None
                lead_sign = "missing"
                if lead is not None:
                    if lead > 0:
                        lead_sign = "positive"
                    elif lead < 0:
                        lead_sign = "negative"
                    else:
                        lead_sign = "zero"

                row = {
                    "dataset": path.stem,
                    "evento_id": raw.get("evento_id"),
                    "data": raw.get("data"),
                    "ano": year,
                    "uf": raw.get("uf") or "NA",
                    "turno": _to_int(raw.get("turno")),
                    "partido": raw.get("partido") or "NA",
                    "incumbente": inc,
                    "poll_lead_pp": lead,
                    "abs_poll_lead_pp": abs_lead,
                    "lead_sign": lead_sign,
                    "probabilidade_prior": prior,
                    "outcome_real": outcome,
                    "prior_brier": ((prior - outcome) ** 2) if prior is not None else None,
                    "prior_correct": int((prior >= 0.5) == bool(outcome)) if prior is not None else None,
                    "prior_confidence": abs(prior - 0.5) if prior is not None else None,
                    "context_len": len(raw.get("contexto") or ""),
                }
                rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        numeric = [
            "ano",
            "turno",
            "incumbente",
            "poll_lead_pp",
            "abs_poll_lead_pp",
            "probabilidade_prior",
            "outcome_real",
            "prior_brier",
            "prior_correct",
            "prior_confidence",
            "context_len",
        ]
        for col in numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    meta = {
        "files": len(files),
        "released_rows": int(len(df)),
        "skipped_future_rows": skipped_future,
        "skipped_missing_outcome_rows": skipped_missing,
        "as_of": today.isoformat(),
    }
    return df, meta


def dataset_rollup(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    g = df.groupby("dataset", dropna=False).agg(
        n=("outcome_real", "size"),
        outcome_rate=("outcome_real", "mean"),
        prior_acc=("prior_correct", "mean"),
        prior_brier=("prior_brier", "mean"),
        prior_mean=("probabilidade_prior", "mean"),
        mean_abs_lead=("abs_poll_lead_pp", "mean"),
    )
    g = g.reset_index().sort_values(["prior_brier", "n"], ascending=[False, False])
    return _jsonify(g.to_dict(orient="records"))


def year_rollup(df: pd.DataFrame) -> list[dict]:
    if df.empty or "ano" not in df:
        return []
    g = df.dropna(subset=["ano"]).groupby("ano").agg(
        n=("outcome_real", "size"),
        outcome_rate=("outcome_real", "mean"),
        prior_acc=("prior_correct", "mean"),
        prior_brier=("prior_brier", "mean"),
        mean_abs_lead=("abs_poll_lead_pp", "mean"),
    )
    g = g.reset_index().sort_values("ano")
    return _jsonify(g.to_dict(orient="records"))


def run_quant_models(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    out: dict[str, Any] = {}
    cols = [
        "outcome_real",
        "probabilidade_prior",
        "poll_lead_pp",
        "abs_poll_lead_pp",
        "incumbente",
        "prior_brier",
        "prior_correct",
        "prior_confidence",
        "context_len",
    ]
    present = [c for c in cols if c in df.columns]
    data = df[present + ["dataset", "lead_sign"]].copy()
    out["correlations"] = r_cor(data, columns=present, method="spearman")

    try:
        out["glm_outcome"] = r_glm_binomial(
            data,
            formula="outcome_real ~ probabilidade_prior + poll_lead_pp + incumbente",
        )
    except Exception as exc:
        out["glm_outcome_error"] = str(exc)

    try:
        out["lm_prior_brier"] = r_lm(
            data,
            formula="prior_brier ~ prior_confidence + abs_poll_lead_pp + incumbente + context_len",
        )
    except Exception as exc:
        out["lm_prior_brier_error"] = str(exc)

    try:
        out["partial_prior_vs_outcome_controlling_lead"] = r_partial_cor(
            data.dropna(subset=["outcome_real", "probabilidade_prior", "abs_poll_lead_pp"]),
            x="probabilidade_prior",
            y="outcome_real",
            covar=["abs_poll_lead_pp"],
            method="spearman",
        )
    except Exception as exc:
        out["partial_error"] = str(exc)

    try:
        out["chisq_lead_sign_vs_outcome"] = r_chisq_test(data, row="lead_sign", col="outcome_real")
    except Exception as exc:
        out["chisq_error"] = str(exc)

    try:
        top_datasets = set(df["dataset"].value_counts().head(12).index)
        aov_data = df[df["dataset"].isin(top_datasets)].copy()
        out["anova_prior_brier_by_dataset_top12"] = r_aov(aov_data, y="prior_brier", group="dataset")
    except Exception as exc:
        out["anova_error"] = str(exc)

    return _jsonify(out)


def political_diagnosis(stats: dict, evolution: dict) -> dict:
    summary = stats.get("summary", {})
    baseline = summary.get("baseline", {})
    mrp = summary.get("mrp", {})
    best = evolution.get("best", {})
    per_year = []
    for year, row in (best.get("per_year") or {}).items():
        vals = dict(row)
        vals["year"] = year
        per_year.append(vals)
    per_year.sort(key=lambda r: str(r.get("year")))

    worst_brier = sorted(per_year, key=lambda r: r.get("brier") or -1, reverse=True)[:3]
    worst_ece = sorted(per_year, key=lambda r: r.get("ece") or -1, reverse=True)[:3]
    return _jsonify({
        "baseline": baseline,
        "mrp": mrp,
        "lift_vs_baseline": stats.get("quality_indicators", {}).get("lift_vs_baseline", {}),
        "decision_edge": stats.get("quality_indicators", {}).get("decision_edge", {}),
        "evolution_gate": evolution.get("gate", {}),
        "best_config": best.get("config", {}),
        "best_metrics": {k: best.get(k) for k in ("n", "acc", "brier", "log_loss", "auc", "mcc", "ece")},
        "per_year": per_year,
        "worst_brier_years": worst_brier,
        "worst_ece_years": worst_ece,
    })


def gauntlet_diagnosis(gauntlet: dict) -> dict:
    results = gauntlet.get("results") or []
    by_area_time: dict[str, dict[str, Any]] = {}
    for row in results:
        area = row.get("area", "system")
        slot = by_area_time.setdefault(area, {"tests": 0, "seconds": 0.0, "max_seconds": 0.0})
        slot["tests"] += 1
        sec = float(row.get("seconds") or 0.0)
        slot["seconds"] += sec
        slot["max_seconds"] = max(slot["max_seconds"], sec)
    for area, slot in by_area_time.items():
        slot["avg_seconds"] = slot["seconds"] / slot["tests"] if slot["tests"] else 0.0
        slot["seconds"] = round(slot["seconds"], 3)
        slot["avg_seconds"] = round(slot["avg_seconds"], 3)
        slot["max_seconds"] = round(slot["max_seconds"], 3)

    slow = sorted(results, key=lambda r: float(r.get("seconds") or 0.0), reverse=True)[:12]
    return _jsonify({
        "summary": gauntlet.get("summary", {}),
        "seconds": gauntlet.get("seconds"),
        "by_area_time": by_area_time,
        "slow_tests": [
            {
                "name": r.get("name"),
                "area": r.get("area"),
                "seconds": r.get("seconds"),
                "status": r.get("status"),
            }
            for r in slow
        ],
    })


def build_recommendations(report: dict) -> list[dict]:
    recs: list[dict] = []
    pol = report.get("political", {})
    base = pol.get("baseline") or {}
    mrp = pol.get("mrp") or {}
    if mrp.get("acc", 0) > base.get("acc", 0) and mrp.get("brier", 1) > base.get("brier", 1):
        recs.append({
            "priority": 1,
            "area": "politica",
            "action": "Use MRP as classifier edge and add a calibrated probability layer before exposing raw probabilities.",
            "evidence": f"MRP acc {mrp.get('acc'):.4f} > baseline {base.get('acc'):.4f}, but Brier {mrp.get('brier'):.4f} > baseline {base.get('brier'):.4f}.",
        })

    worst_ece = (pol.get("worst_ece_years") or [])[:1]
    if worst_ece:
        row = worst_ece[0]
        recs.append({
            "priority": 2,
            "area": "calibracao",
            "action": "Open a year-fold calibration task focused on the highest-ECE cycle.",
            "evidence": f"Year {row.get('year')} ECE={row.get('ece'):.4f}, Brier={row.get('brier'):.4f}, n={row.get('n')}.",
        })

    hotspots = report.get("backtest", {}).get("dataset_hotspots") or []
    if hotspots:
        top = hotspots[0]
        recs.append({
            "priority": 3,
            "area": "dados",
            "action": "Review the worst dataset by prior Brier and add it to the next focused validation batch.",
            "evidence": f"{top.get('dataset')} prior_brier={top.get('prior_brier'):.4f}, n={top.get('n')}.",
        })

    slow = report.get("gauntlet", {}).get("slow_tests") or []
    if slow:
        top = slow[0]
        recs.append({
            "priority": 4,
            "area": "testes",
            "action": "Keep the slowest test in a performance watchlist and split it if it grows further.",
            "evidence": f"{top.get('name')} took {top.get('seconds')}s.",
        })

    return recs


def run_diagnosis(
    *,
    backtest_dir: str | Path = "data/backtest",
    political_stats_path: str | Path = "data/political_stats_v2.json",
    political_evolution_path: str | Path = "data/political_evolution.json",
    gauntlet_path: str | Path = "data/system_gauntlet_latest.json",
    today: date | None = None,
) -> tuple[dict, pd.DataFrame]:
    df, meta = load_backtest_events(backtest_dir, today=today)
    stats = _read_json(political_stats_path)
    evolution = _read_json(political_evolution_path)
    gauntlet = _read_json(gauntlet_path)

    report: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "backtest": {
            "meta": meta,
            "dataset_hotspots": dataset_rollup(df)[:20],
            "year_rollup": year_rollup(df),
        },
        "quant": run_quant_models(df),
        "political": political_diagnosis(stats, evolution),
        "gauntlet": gauntlet_diagnosis(gauntlet),
    }
    report["recommendations"] = build_recommendations(report)
    return _jsonify(report), df


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "-"
    try:
        f = float(value)
    except Exception:
        return str(value)
    if not math.isfinite(f):
        return "-"
    return f"{f:.{digits}f}"


def render_markdown(report: dict) -> str:
    meta = report["backtest"]["meta"]
    pol = report["political"]
    gauntlet = report["gauntlet"]
    lines = [
        "# Vila Practical Quant Run",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Released backtest rows: `{meta['released_rows']}` from `{meta['files']}` CSV files",
        f"- Future rows held out: `{meta['skipped_future_rows']}`",
        "",
        "## Political Operating Edge",
        "",
        "| model | n | acc | brier | auc | mcc | ece |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("baseline", "mrp"):
        row = pol.get(name, {})
        lines.append(
            f"| {name} | {row.get('n', '-')} | {_fmt(row.get('acc'))} | "
            f"{_fmt(row.get('brier'))} | - | - | - |"
        )
    best = pol.get("best_metrics", {})
    lines.append(
        f"| evolved_best | {best.get('n', '-')} | {_fmt(best.get('acc'))} | "
        f"{_fmt(best.get('brier'))} | {_fmt(best.get('auc'))} | "
        f"{_fmt(best.get('mcc'))} | {_fmt(best.get('ece'))} |"
    )

    lines += [
        "",
        "## Dataset Hotspots",
        "",
        "| dataset | n | prior_acc | prior_brier | outcome_rate | mean_abs_lead |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in report["backtest"]["dataset_hotspots"][:12]:
        lines.append(
            f"| {row.get('dataset')} | {row.get('n')} | {_fmt(row.get('prior_acc'))} | "
            f"{_fmt(row.get('prior_brier'))} | {_fmt(row.get('outcome_rate'))} | "
            f"{_fmt(row.get('mean_abs_lead'))} |"
        )

    lines += [
        "",
        "## Quant Signals",
        "",
        "| x | y | n | spearman_r | q_bh |",
        "|---|---|---:|---:|---:|",
    ]
    for row in report.get("quant", {}).get("correlations", {}).get("pairs", [])[:10]:
        lines.append(
            f"| {row.get('x')} | {row.get('y')} | {row.get('n')} | "
            f"{_fmt(row.get('r'))} | {_fmt(row.get('q_bh'))} |"
        )

    glm = report.get("quant", {}).get("glm_outcome", {})
    if glm:
        lines += ["", "### GLM Outcome", "", f"- Formula: `{glm.get('formula')}`"]
        lines += ["", "| term | estimate | odds_ratio | p |", "|---|---:|---:|---:|"]
        for row in glm.get("coefficients", [])[:8]:
            lines.append(
                f"| {row.get('term')} | {_fmt(row.get('estimate'))} | "
                f"{_fmt(row.get('odds_ratio'))} | {_fmt(row.get('p'))} |"
            )

    lines += [
        "",
        "## Gauntlet Runtime",
        "",
        f"- Total: `{gauntlet.get('summary', {}).get('total', {}).get('pass')}`/"
        f"`{gauntlet.get('summary', {}).get('total', {}).get('total')}` passed",
        f"- Runtime: `{gauntlet.get('seconds')}` seconds",
        "",
        "| slow test | area | seconds |",
        "|---|---|---:|",
    ]
    for row in gauntlet.get("slow_tests", [])[:8]:
        lines.append(f"| {row.get('name')} | {row.get('area')} | {_fmt(row.get('seconds'), 3)} |")

    lines += ["", "## Practical Actions", ""]
    for rec in report.get("recommendations", []):
        lines.append(
            f"{rec['priority']}. **{rec['area']}**: {rec['action']} "
            f"Evidence: {rec['evidence']}"
        )
    return "\n".join(lines) + "\n"


def write_outputs(report: dict, df: pd.DataFrame, *, out_json: str | Path, out_md: str | Path, out_csv: str | Path) -> None:
    json_path = Path(out_json)
    md_path = Path(out_md)
    csv_path = Path(out_csv)
    for path in (json_path, md_path, csv_path):
        if not path.is_absolute():
            path = ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)

    if not json_path.is_absolute():
        json_path = ROOT / json_path
    if not md_path.is_absolute():
        md_path = ROOT / md_path
    if not csv_path.is_absolute():
        csv_path = ROOT / csv_path

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    df.to_csv(csv_path, index=False)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run practical quant diagnostics on Vila data.")
    p.add_argument("--backtest-dir", default="data/backtest")
    p.add_argument("--political-stats", default="data/political_stats_v2.json")
    p.add_argument("--political-evolution", default="data/political_evolution.json")
    p.add_argument("--gauntlet", default="data/system_gauntlet_latest.json")
    p.add_argument("--out-json", default="data/practical_quant_vila_latest.json")
    p.add_argument("--out-md", default="data/practical_quant_vila_latest.md")
    p.add_argument("--out-csv", default="data/practical_quant_backtest_events.csv")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report, df = run_diagnosis(
        backtest_dir=args.backtest_dir,
        political_stats_path=args.political_stats,
        political_evolution_path=args.political_evolution,
        gauntlet_path=args.gauntlet,
    )
    write_outputs(report, df, out_json=args.out_json, out_md=args.out_md, out_csv=args.out_csv)
    print(f"Released rows: {report['backtest']['meta']['released_rows']}")
    print(f"Recommendations: {len(report['recommendations'])}")
    print(f"Saved -> {ROOT / args.out_json if not Path(args.out_json).is_absolute() else Path(args.out_json)}")
    print(f"Saved -> {ROOT / args.out_md if not Path(args.out_md).is_absolute() else Path(args.out_md)}")
    print(f"Saved -> {ROOT / args.out_csv if not Path(args.out_csv).is_absolute() else Path(args.out_csv)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
