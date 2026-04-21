"""
Onda 170: compare 2 backtest JSONs side-by-side.

Uso:
    python scripts/compare_backtests.py A.json B.json

Output tabela: per-evento brier_A, brier_B, delta, ganhador.
Agrega por dataset + total. Flags big deltas (>10%).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _extract_eventos(payload: dict) -> list[dict]:
    """Aceita JSON individual OU wrapper com datasets[]."""
    datasets = payload.get("datasets") or [payload]
    out = []
    for ds in datasets:
        if "erro" in ds:
            continue
        ds_name = ds.get("dataset", "?")
        for ev in ds.get("eventos", []):
            out.append({
                "dataset": ds_name,
                "evento_id": ev.get("evento_id"),
                "outcome_real": ev.get("outcome_real"),
                "prob_vila_raw": ev.get("prob_vila_raw"),
                "prob_vila_cal": ev.get("prob_vila_calibrada"),
                "prob_blend": ev.get("prob_blend_final"),
                "acertou_blend": ev.get("acertou_blend"),
            })
    return out


def _brier(p, y):
    if p is None or y is None:
        return None
    return (float(p) - int(y)) ** 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_a")
    parser.add_argument("file_b")
    parser.add_argument("--label-a", default="A")
    parser.add_argument("--label-b", default="B")
    parser.add_argument("--metric", default="prob_blend", choices=["prob_blend", "prob_vila_cal", "prob_vila_raw"])
    args = parser.parse_args()

    a = _extract_eventos(_load(args.file_a))
    b = _extract_eventos(_load(args.file_b))

    # Index by evento_id
    b_map = {(e["dataset"], e["evento_id"]): e for e in b}

    print(f"{'dataset':<30s} {'evento':<10s} {'y':>2s} {args.label_a:>8s} {args.label_b:>8s} {'ΔBrier':>10s} {'win':>4s}")
    print("-" * 84)

    totals_a = []
    totals_b = []
    wins_a = 0
    wins_b = 0
    ties = 0

    for ev in a:
        key = (ev["dataset"], ev["evento_id"])
        ev_b = b_map.get(key)
        if not ev_b:
            continue
        y = ev["outcome_real"]
        pa = ev.get(args.metric)
        pb = ev_b.get(args.metric)
        if pa is None or pb is None:
            continue
        br_a = _brier(pa, y)
        br_b = _brier(pb, y)
        delta = br_b - br_a
        if delta < -0.01:
            win = args.label_b
            wins_b += 1
        elif delta > 0.01:
            win = args.label_a
            wins_a += 1
        else:
            win = "="
            ties += 1
        ds_short = ev["dataset"].split("/")[-1].replace(".csv", "")[:30]
        print(f"{ds_short:<30s} {str(ev['evento_id']):<10s} {y:>2d} {br_a:>8.4f} {br_b:>8.4f} {delta:>+10.4f} {win:>4s}")
        totals_a.append(br_a)
        totals_b.append(br_b)

    if totals_a:
        avg_a = sum(totals_a) / len(totals_a)
        avg_b = sum(totals_b) / len(totals_b)
        print("-" * 84)
        print(f"{'AVG':<30s} {'':>10s} {'':>2s} {avg_a:>8.4f} {avg_b:>8.4f} {avg_b-avg_a:>+10.4f}")
        print(f"\n{args.label_a} wins: {wins_a}, {args.label_b} wins: {wins_b}, ties: {ties}")
        if avg_a > 0:
            delta_pct = (avg_b - avg_a) / avg_a * 100
            print(f"Delta agregado: {delta_pct:+.1f}% ({args.label_b} vs {args.label_a})")
    else:
        print("Nenhum evento match entre os arquivos")


if __name__ == "__main__":
    main()
