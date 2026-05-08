#!/usr/bin/env python3
"""Consolidated model comparison.

Loads all model results from data/*.json and writes single comparison
table to docs/BENCHMARKS.md.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_safe(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def main():
    rows = []

    # 1. Vila MRP from political_stats_v2.json
    stats = load_safe(ROOT / "data" / "political_stats_v2.json")
    if stats:
        b = stats.get("summary", {}).get("baseline", {})
        m = stats.get("summary", {}).get("mrp", {})
        rows.append({
            "model": "Vila baseline (cohort+Linzer, no MRP)",
            "brier": b.get("brier"), "acc": b.get("acc"),
            "n": b.get("n"), "source": "political_stats_v2.json",
        })
        rows.append({
            "model": "Vila MRP tuned (this paper)",
            "brier": m.get("brier"), "acc": m.get("acc"),
            "n": m.get("n"), "source": "political_stats_v2.json",
        })

    # 2. Baseline gauntlet
    bg = load_safe(ROOT / "data" / "baseline_gauntlet.json")
    if bg and "models" in bg:
        for name, data in bg["models"].items():
            rows.append({
                "model": name,
                "brier": data.get("avg", {}).get("brier") or data.get("pooled", {}).get("brier"),
                "acc": data.get("avg", {}).get("acc") or data.get("pooled", {}).get("acc"),
                "n": data.get("avg", {}).get("n") or data.get("pooled", {}).get("n"),
                "source": "baseline_gauntlet.json",
            })

    # 3. BART
    bart = load_safe(ROOT / "data" / "bench_bart.json")
    if bart:
        a = bart.get("avg") or bart.get("summary") or {}
        backend = bart.get('backend', bart.get('model', 'proxy'))
        rows.append({
            "model": f"BART ({backend})",
            "brier": a.get("brier") or a.get("brier_avg"),
            "acc": a.get("acc") or a.get("acc_avg"),
            "n": a.get("n"),
            "fit_time_s": a.get("fit_time_s") or a.get("fit_time_s_total"),
            "predict_time_ms": a.get("predict_time_ms_per_event") or a.get("predict_time_ms_per_event_avg"),
            "source": "bench_bart.json",
        })

    # 4. Stan DLM
    stan = load_safe(ROOT / "data" / "bench_stan_dlm.json")
    if stan and "avg" in stan:
        a = stan["avg"]
        rows.append({
            "model": "Stan DLM (Kalman, Linzer 2013)",
            "brier": a["brier"], "acc": a["acc"], "n": a["n"],
            "fit_time_s": a.get("fit_time_s"),
            "predict_time_ms": a.get("predict_time_ms_per_event"),
            "source": "bench_stan_dlm.json",
        })

    # Sort by acc descending
    rows.sort(key=lambda r: -(r.get("acc") or 0))

    # Write markdown
    md_lines = ["# Model comparison (year-fold CV, n=394, T<=30, seed=42)", ""]
    md_lines.append("| Model | Brier ↓ | Acc ↑ | n | Fit (s) | Predict (ms/ev) | Source |")
    md_lines.append("|-------|--------:|------:|--:|--------:|----------------:|--------|")
    for r in rows:
        b = f"{r['brier']:.4f}" if r.get("brier") is not None else "-"
        a = f"{r['acc']*100:.2f}%" if r.get("acc") is not None else "-"
        n = str(r.get("n") or "-")
        ft = f"{r['fit_time_s']:.2f}" if r.get("fit_time_s") else "-"
        pt = f"{r['predict_time_ms']:.4f}" if r.get("predict_time_ms") else "-"
        md_lines.append(f"| {r['model']} | {b} | {a} | {n} | {ft} | {pt} | {r['source']} |")

    out_path = ROOT / "docs" / "MODEL_COMPARISON.md"
    out_path.write_text("\n".join(md_lines) + "\n")
    print(f"Saved -> {out_path}")
    print()
    print("\n".join(md_lines))


if __name__ == "__main__":
    main()
