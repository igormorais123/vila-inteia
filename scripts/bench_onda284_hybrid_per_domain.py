"""Onda 284 — Vila vs LLM vs Hybrid por holdout.

Roda evaluate_hybrid em cada holdout post_cutoff_* e gera tabela comparativa.
Caro: ~25s/evento via LLM forecaster. 170 eventos = ~70min total.

Uso:
    python scripts/bench_onda284_hybrid_per_domain.py [--max-events N]
                                                       [--datasets a,b,c]
                                                       [--out FILE]

Output: data/onda284_hybrid_per_domain.json + tabela markdown no stdout.
"""

from __future__ import annotations

import argparse
import glob
import json
import time
from pathlib import Path

from engine.backtest_real import carregar_dataset
from engine.vila_llm_hybrid import evaluate_hybrid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-events", type=int, default=30,
                    help="cap por dataset (default 30)")
    ap.add_argument("--datasets", default="",
                    help="csv subset; vazio = todos post_cutoff_*holdout*.csv")
    ap.add_argument("--out", default="data/onda284_hybrid_per_domain.json")
    args = ap.parse_args()

    if args.datasets:
        files = [f"data/backtest/{d.strip()}" for d in args.datasets.split(",")]
    else:
        files = sorted(glob.glob("data/backtest/post_cutoff_*holdout*.csv"))

    results = []
    t0 = time.time()
    for fp in files:
        name = Path(fp).stem.replace("post_cutoff_", "")
        evs = carregar_dataset(fp)
        if not evs:
            continue
        t = time.time()
        r = evaluate_hybrid(evs, max_events=args.max_events)
        r["dataset"] = name
        r["elapsed_sec"] = round(time.time() - t, 1)
        results.append(r)
        print(f"[{name}] n={r['n']} vila_brier={r['vila']['brier']:.4f} "
              f"llm_brier={r['llm']['brier']:.4f} "
              f"hyb_brier={r['hybrid']['brier']:.4f} "
              f"({r['elapsed_sec']}s)")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=2))

    # Markdown table
    print("\n## Onda 284 — Vila vs LLM vs Hybrid por domínio\n")
    print("| dataset | n | Vila brier | LLM brier | Hybrid brier | melhor | ganho hyb-vila |")
    print("|---|---:|---:|---:|---:|:-:|---:|")
    for r in results:
        v, l, h = r["vila"]["brier"], r["llm"]["brier"], r["hybrid"]["brier"]
        best = min((v, "Vila"), (l, "LLM"), (h, "Hybrid"))[1]
        delta_hv = h - v
        print(f"| {r['dataset']} | {r['n']} | {v:.4f} | {l:.4f} | {h:.4f} "
              f"| {best} | {delta_hv:+.4f} |")
    print(f"\n_total elapsed: {round(time.time() - t0, 1)}s_")


if __name__ == "__main__":
    main()
