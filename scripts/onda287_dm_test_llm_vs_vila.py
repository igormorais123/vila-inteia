"""Onda 287 — Diebold-Mariano formal: LLM vs Vila.

Re-roda predições por evento (cache do LLM forecaster reaproveita) e aplica
o teste DM expondo preds como list, validando a Onda 286 com p-valor formal.

Uso:
    python scripts/onda287_dm_test_llm_vs_vila.py [--dataset NAME] [--max N]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.backtest_real import carregar_dataset
from engine.diebold_mariano import diebold_mariano
from engine.llm_forecaster import llm_predict
from engine.post_cutoff_classifier import classify_and_predict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="post_cutoff_q1_2027_holdout_v5.csv")
    ap.add_argument("--max", type=int, default=30)
    ap.add_argument("--out", default="data/onda287_dm_test.json")
    args = ap.parse_args()

    fp = f"data/backtest/{args.dataset}"
    evs = carregar_dataset(fp)[: args.max]

    preds_vila: list[float] = []
    preds_llm: list[float] = []
    reals: list[int] = []
    for e in evs:
        framing = e.get("outcome_framing") or e.get("framing", "")
        ctx = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        p_v, label = classify_and_predict(framing, ctx)
        p_l = llm_predict(framing, ctx, vila_hint=(label, p_v))
        if p_l is None:
            continue
        preds_vila.append(p_v)
        preds_llm.append(p_l)
        reals.append(int(y))

    n = len(reals)
    if n < 5:
        raise SystemExit(f"insufficient n={n}")

    # DM test em 3 losses: brier, log, abs
    out = {"dataset": args.dataset, "n": n,
           "preds_vila": preds_vila, "preds_llm": preds_llm, "reals": reals}
    for loss in ("brier", "log", "abs"):
        # H0: mean(loss_LLM - loss_Vila) == 0
        # mean_diff < 0 ↔ LLM tem loss menor (vence Vila)
        dm = diebold_mariano(preds_llm, preds_vila, reals, loss=loss)
        out[f"dm_{loss}"] = dm

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2))

    # Print summary
    print(f"# Onda 287 — DM test LLM vs Vila ({args.dataset}, n={n})\n")
    print("| loss | mean_diff | dm_stat | p_value | reject_h0? |")
    print("|---|---:|---:|---:|:-:|")
    for loss in ("brier", "log", "abs"):
        dm = out[f"dm_{loss}"]
        if "erro" in dm:
            print(f"| {loss} | ERR: {dm['erro']} |")
            continue
        winner = "LLM" if dm["mean_diff"] < 0 else "Vila"
        print(f"| {loss} | {dm['mean_diff']:+.4f} ({winner} ganha) "
              f"| {dm['dm_stat']:+.3f} | {dm['p_value']:.4f} "
              f"| {'SIM' if dm['reject_h0'] else 'não'} |")


if __name__ == "__main__":
    main()
