#!/usr/bin/env python3
"""
Gera relatório Markdown a partir de JSONL coletado via coletar_dados_real.py (Onda 69).

Uso:
    python scripts/gerar_relatorio_coleta.py --in /tmp/dados_groq.jsonl [--out relatorio.md]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def carregar(arquivo: str) -> list[dict]:
    out = []
    with open(arquivo, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                out.append(json.loads(linha))
            except json.JSONDecodeError:
                pass
    return out


def formatar_relatorio(snaps: list[dict]) -> str:
    if not snaps:
        return "# Relatório de coleta\n\nSem snapshots.\n"

    n = len(snaps)
    inicio = snaps[0]["ts"]
    fim = snaps[-1]["ts"]
    duracao = fim - inicio

    primeiro = snaps[0]
    ultimo = snaps[-1]

    # Deltas
    def _dot(snap, k1, k2):
        d = snap.get(k1, {})
        return d.get(k2, 0) if isinstance(d, dict) else 0

    delta_steps = _dot(ultimo["trajetoria"], "n_steps_rastreados", "") - \
                   _dot(primeiro["trajetoria"], "n_steps_rastreados", "")
    # Correção: trajetoria é dict, não nested
    delta_steps = ultimo["trajetoria"].get("n_steps_rastreados", 0) - \
                   primeiro["trajetoria"].get("n_steps_rastreados", 0)

    b_ini = primeiro["llm"].get("budget", {}) or {}
    b_fim = ultimo["llm"].get("budget", {}) or {}
    delta_chamadas = b_fim.get("n_chamadas", 0) - b_ini.get("n_chamadas", 0)
    delta_tokens_in = b_fim.get("total_tokens_in", 0) - b_ini.get("total_tokens_in", 0)
    delta_tokens_out = b_fim.get("total_tokens_out", 0) - b_ini.get("total_tokens_out", 0)
    delta_usd = b_fim.get("total_usd", 0) - b_ini.get("total_usd", 0)

    c_fim = ultimo["llm"].get("cache", {}) or {}
    t_fim = ultimo["llm"].get("tier", {}) or {}
    p_fim = ultimo["llm"].get("provider", {}) or {}

    distrib = ultimo["trajetoria"].get("distribuicao_historica", {})

    linhas = [
        "# Relatório de coleta Vila INTEIA",
        "",
        f"- Snapshots: **{n}**",
        f"- Duração: **{duracao:.0f}s** ({duracao/60:.1f} min)",
        f"- Provider LLM: **{p_fim.get('ativo', 'N/A')}**",
        f"- Steps rastreados (fim): **{ultimo['trajetoria'].get('n_steps_rastreados', 0)}**",
        f"- Delta steps na coleta: **+{delta_steps}**",
        "",
        "## LLM usage (delta coleta)",
        "",
        f"- Chamadas: **+{delta_chamadas}**",
        f"- Tokens in: **+{delta_tokens_in:,}**",
        f"- Tokens out: **+{delta_tokens_out:,}**",
        f"- Custo USD: **+${delta_usd:.6f}**",
        "",
        "## Cache",
        "",
        f"- Size: {c_fim.get('size', 0)} / {c_fim.get('capacity', 0)}",
        f"- Hits: {c_fim.get('hits', 0)}",
        f"- Misses: {c_fim.get('misses', 0)}",
        f"- Hit rate: {(c_fim.get('hit_rate', 0) * 100):.1f}%",
        "",
        "## Tier gate",
        "",
        f"- Hot: {t_fim.get('n_hot', 0)} / {t_fim.get('n_total', 0)}",
        f"- Fração hot: {(t_fim.get('fracao_hot', 0) * 100):.1f}%",
        f"- Rotate steps: {t_fim.get('rotate_steps', 0)}",
        "",
        "## Distribuição de estados (trajetória)",
        "",
    ]
    for estado, frac in sorted(distrib.items(), key=lambda x: -x[1]):
        linhas.append(f"- `{estado}`: {frac*100:.1f}%")

    linhas.extend([
        "",
        "## Timeline de chamadas LLM",
        "",
        "| t (s) | steps | LLM calls | tokens_in | USD |",
        "|---:|---:|---:|---:|---:|",
    ])
    for s in snaps:
        t_rel = s["ts"] - inicio
        b = s["llm"].get("budget", {}) or {}
        linhas.append(f"| {t_rel:.0f} | "
                       f"{s['trajetoria'].get('n_steps_rastreados', 0)} | "
                       f"{b.get('n_chamadas', 0)} | "
                       f"{b.get('total_tokens_in', 0):,} | "
                       f"${b.get('total_usd', 0):.6f} |")

    linhas.append("")
    linhas.append(f"*Gerado em {time.strftime('%Y-%m-%d %H:%M:%S')}*")
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="entrada", required=True)
    ap.add_argument("--out", default=None,
                     help="Stdout se omitido")
    args = ap.parse_args()

    snaps = carregar(args.entrada)
    relatorio = formatar_relatorio(snaps)

    if args.out:
        Path(args.out).write_text(relatorio, encoding="utf-8")
        print(f"Relatório gravado: {args.out} ({len(relatorio.encode('utf-8'))} bytes)")
    else:
        print(relatorio)


if __name__ == "__main__":
    main()
