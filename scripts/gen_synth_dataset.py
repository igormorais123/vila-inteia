#!/usr/bin/env python3
"""
Gerador de trajetórias sintéticas p/ stress test calibração (Onda 54).

Amostra trajetórias de estados a partir da matriz Markov canônica da Vila,
com ruído opcional (Mules injetados aleatoriamente). Útil para:
    - Validar calibrador online com ground truth conhecida
    - Benchmark de escala (trajetórias 10k steps)
    - Teste de HMM não-supervisionado

Uso:
    python scripts/gen_synth_dataset.py --n-steps 1000 --vila-id synth_A \\
        --mule-rate 0.05 --out data/synth/run_A.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from engine.psicohistoria.grafo_eventos import construir_grafo_vila


ESTADOS = [
    "bootstrap", "recrutamento", "expansao", "consenso_fragil",
    "polarizacao", "crise_economica", "renovacao_constituinte", "equilibrio",
]


def gerar(n_steps: int, estado_inicial: str = "bootstrap",
          mule_rate: float = 0.0, seed: int = 42) -> dict:
    """
    Amostra trajetória Markov + opcional injeção de Mules (transições raras).
    """
    rng = np.random.default_rng(seed)
    py_rng = random.Random(seed)
    grafo = construir_grafo_vila()
    M = grafo.matriz

    idx_atual = grafo.estado_para_index(estado_inicial)
    trajetoria = [grafo.index_para_estado(idx_atual)]
    steps = [0]
    mules_injetados = []

    for t in range(1, n_steps):
        if py_rng.random() < mule_rate:
            # Mule: pula para estado aleatório não-adjacente
            idx_atual = py_rng.randrange(len(ESTADOS))
            mules_injetados.append({"passo": t, "estado_forcado": ESTADOS[idx_atual]})
        else:
            # Amostra próximo estado via M[idx_atual, :]
            probs = M[idx_atual]
            idx_atual = int(rng.choice(len(ESTADOS), p=probs))
        trajetoria.append(grafo.index_para_estado(idx_atual))
        steps.append(t)

    return {
        "tipo": "trajetoria_sintetica",
        "n_steps": n_steps,
        "estado_inicial": estado_inicial,
        "mule_rate": mule_rate,
        "seed": seed,
        "mules_injetados": mules_injetados,
        "trajetoria": trajetoria,
        "steps": steps,
        "gerado_em": time.time(),
    }


def estatisticas(trajetoria: list[str]) -> dict:
    from collections import Counter
    c = Counter(trajetoria)
    n = len(trajetoria)
    return {k: v / n for k, v in c.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-steps", type=int, default=1000)
    ap.add_argument("--vila-id", default="synth")
    ap.add_argument("--estado-inicial", default="bootstrap",
                     choices=ESTADOS)
    ap.add_argument("--mule-rate", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/synth/run.json")
    args = ap.parse_args()

    dados = gerar(args.n_steps, args.estado_inicial, args.mule_rate, args.seed)
    dados["vila_id"] = args.vila_id
    stats = estatisticas(dados["trajetoria"])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(dados, fh, indent=2, ensure_ascii=False)

    size_kb = out.stat().st_size / 1024
    print(f"Trajetória sintética gerada: {out} ({size_kb:.1f} KB)")
    print(f"  n_steps: {args.n_steps}")
    print(f"  Mules injetados: {len(dados['mules_injetados'])}")
    print(f"  Distribuição:")
    for estado, frac in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"    {estado}: {frac*100:.1f}%")


if __name__ == "__main__":
    main()
