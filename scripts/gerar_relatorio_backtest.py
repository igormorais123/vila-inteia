#!/usr/bin/env python3
"""
Onda 94: gera relatório markdown do backtest real.

Input: JSON produzido por rodar_backtest_real.py
Output: markdown com tabelas por dataset + agregado + calibração + eventos

Uso:
    python scripts/gerar_relatorio_backtest.py --in ~/Downloads/vila_backtest_FULL.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def fmt_num(v, nd=4):
    if v is None: return "—"
    if isinstance(v, (int, float)): return f"{v:.{nd}f}"
    return str(v)


def fmt_pct(v):
    if v is None: return "—"
    return f"{v*100:.1f}%"


def gerar(data: dict) -> str:
    linhas = [
        "# Vila INTEIA — Backtest de Previsão em Eventos Reais",
        "",
        f"Gerado em {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Metodologia",
        "",
        "- Datasets: eventos históricos reais com outcome verificável",
        "- Panel: N personas lendárias respondendo P(outcome=1) para cada evento",
        "- Regex extrai probabilidade da resposta LLM",
        "- Agregado = média das respostas válidas",
        "- Comparado com prob_prior humana e outcome_real {0,1}",
        "- Métricas: accuracy, Brier score, skill vs prior",
        "- Calibração: Platt logistic sigmoid fit",
        "",
        "## Agregado global",
        "",
    ]

    ag = data.get("agregado", {})
    if ag:
        linhas.extend([
            f"- **Datasets**: {ag.get('n_datasets', 0)}",
            f"- **Eventos totais**: {ag.get('n_eventos_total', 0)}",
            f"- **Accuracy global**: {fmt_pct(ag.get('accuracy_global'))}",
            f"- **Brier Vila (macro)**: {fmt_num(ag.get('brier_vila_macro_avg'))}",
            f"- **Brier Prior (macro)**: {fmt_num(ag.get('brier_prior_macro_avg'))}",
            f"- **Skill vs prior (macro)**: `{fmt_num(ag.get('skill_brier_vs_prior_macro'))}`",
            "",
        ])

    cal = data.get("calibracao_platt", {})
    if cal:
        linhas.extend([
            "## Calibração Platt (Onda 93)",
            "",
            f"- **n amostras**: {cal.get('n', 0)}",
            f"- **Platt parâmetros**: a = {fmt_num(cal.get('platt_a'), 3)}, b = {fmt_num(cal.get('platt_b'), 3)}",
            "",
            "| Métrica | Antes | Depois | Δ |",
            "|---|---:|---:|---:|",
            f"| Brier    | {fmt_num(cal.get('brier_antes'))} | {fmt_num(cal.get('brier_depois'))} | "
             f"{fmt_num(cal.get('brier_antes', 0) - cal.get('brier_depois', 0))} |",
            f"| Log-loss | {fmt_num(cal.get('log_loss_antes'))} | {fmt_num(cal.get('log_loss_depois'))} | "
             f"{fmt_num(cal.get('log_loss_antes', 0) - cal.get('log_loss_depois', 0))} |",
            f"| ECE      | {fmt_num(cal.get('ece_antes'))} | {fmt_num(cal.get('ece_depois'))} | "
             f"{fmt_num(cal.get('ece_antes', 0) - cal.get('ece_depois', 0))} |",
            "",
        ])

    linhas.extend(["## Resultados por dataset", ""])
    for ds in data.get("datasets", []):
        name = Path(ds.get("dataset", "?")).stem
        linhas.append(f"### {name}")
        linhas.append("")
        if "erro" in ds:
            linhas.append(f"ERRO: {ds['erro']}")
            linhas.append("")
            continue
        linhas.extend([
            f"- n_eventos: {ds.get('n_eventos', 0)}",
            f"- n_respondidos: {ds.get('n_respondidos', 0)}",
            f"- accuracy: {fmt_pct(ds.get('accuracy_vila'))}",
            f"- Brier Vila: {fmt_num(ds.get('brier_vila_avg'))}",
            f"- Brier Prior: {fmt_num(ds.get('brier_prior_avg'))}",
            f"- Skill vs prior: {fmt_num(ds.get('skill_brier_vs_prior'))}",
            "",
            "| evento | data | real | prior | vila | ✓ | contexto |",
            "|---|---|:-:|---:|---:|:-:|---|",
        ])
        for e in ds.get("eventos", []):
            mk = "✓" if e.get("acertou_vila") else "✗"
            pv = e.get("prob_vila")
            pv_s = fmt_num(pv, 2) if pv is not None else "—"
            linhas.append(
                f"| `{e['evento_id']}` | {e['data']} | {e['outcome_real']} | "
                f"{fmt_num(e['prob_prior'], 2)} | {pv_s} | {mk} | "
                f"{e['contexto'][:80]} |"
            )
        linhas.append("")

    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="entrada", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    with open(args.entrada) as f:
        data = json.load(f)

    md = gerar(data)
    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"Relatório: {args.out} ({len(md.encode('utf-8'))} bytes)")
    else:
        print(md)


if __name__ == "__main__":
    main()
