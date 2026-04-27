"""Onda 167: power analysis para decisão de tamanho do holdout.

Helena P2.6 questionou se N=40 holdout é suficiente para o critério
"IC 95% superior <= 0.14" com brier esperado 0.13-0.18. Este script
simula brier bootstrap com diferentes N e baseline, mostra IC esperado.

Uso:
    python scripts/power_analysis.py [--brier 0.18] [--n-min 20] [--n-max 100]

Saída: tabela markdown com largura média do IC 95% para cada (N, brier).
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.bootstrap_gate import _media, _percentile


def simular_ic(brier_esperado: float, n: int, n_iter: int, seed: int) -> dict:
    """Simula um experimento Brier com N eventos, retorna IC 95% típico.

    Modelo: brier por evento ~ Beta calibrada com média=brier_esperado,
    variância proporcional a brier_esperado * (0.25 - brier_esperado).
    Aproximação: gauss(brier_esperado, sigma) clip [0, 1].
    """
    rng = random.Random(seed)
    sigma = max(0.04, (brier_esperado * (0.25 - brier_esperado * 0.5)) ** 0.5 * 0.5)

    # 1 simulação de "experimento real"
    brier_real = [max(0.0, min(1.0, rng.gauss(brier_esperado, sigma))) for _ in range(n)]
    brier_obs = _media(brier_real)

    # Bootstrap dentro do experimento simulado
    brier_bs: list[float] = []
    for _ in range(n_iter):
        sample = [brier_real[rng.randrange(n)] for _ in range(n)]
        brier_bs.append(_media(sample))
    ic_low = _percentile(brier_bs, 0.025)
    ic_high = _percentile(brier_bs, 0.975)
    return {
        "n": n,
        "brier_esperado": brier_esperado,
        "brier_observado": brier_obs,
        "ic_95_inferior": ic_low,
        "ic_95_superior": ic_high,
        "largura_ic": ic_high - ic_low,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-iter", type=int, default=2000, help="iterações bootstrap")
    ap.add_argument("--n-replicas", type=int, default=20,
                    help="quantos experimentos simular para cada (N, brier)")
    ap.add_argument("--briers", type=str, default="0.10,0.13,0.18,0.22",
                    help="brier baselines a testar (separado por vírgula)")
    ap.add_argument("--ns", type=str, default="20,30,40,50,75,100",
                    help="tamanhos N a testar")
    args = ap.parse_args()

    briers = [float(b) for b in args.briers.split(",")]
    ns = [int(n) for n in args.ns.split(",")]

    print(f"# Power Analysis — Vila INTEIA Holdout (Onda 167)\n")
    print(f"Iter bootstrap: {args.n_iter}, réplicas por célula: {args.n_replicas}\n")

    print("## Tabela: largura média do IC 95% por (N, brier_esperado)\n")
    header = "| N \\ Brier | " + " | ".join(f"{b:.2f}" for b in briers) + " |"
    sep = "|---|" + "|".join(["---:" for _ in briers]) + "|"
    print(header)
    print(sep)

    todas: list[dict] = []
    for n in ns:
        row = [f"| **{n}** "]
        for b in briers:
            larguras = []
            for r_idx in range(args.n_replicas):
                seed = (n * 1000 + int(b * 10000) + r_idx * 7919) & 0xFFFFFFFF
                r = simular_ic(b, n, args.n_iter, seed)
                larguras.append(r["largura_ic"])
                todas.append(r)
            larg_media = _media(larguras)
            row.append(f"| {larg_media:.3f} ")
        row.append("|")
        print("".join(row))

    print(f"\n## Recomendação Helena P2.6\n")
    print(f"Critério: IC95% superior <= 0.14 com brier_pontual esperado ~0.15.")
    print(f"Largura tolerável: ~0.06-0.08 (para que pontual+meia-largura < 0.14).\n")
    # Encontra o menor N que entrega largura < 0.07 para brier=0.15
    target_b = min(briers, key=lambda b: abs(b - 0.15))
    candidatos = [r for r in todas if abs(r["brier_esperado"] - target_b) < 1e-6]
    by_n = {}
    for r in candidatos:
        by_n.setdefault(r["n"], []).append(r["largura_ic"])
    for n in sorted(by_n):
        avg = _media(by_n[n])
        flag = " ✓ ATINGE" if avg <= 0.07 else ""
        print(f"- N={n}, brier≈{target_b:.2f}: largura média {avg:.3f}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
