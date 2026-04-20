#!/usr/bin/env python3
"""
Validador de calibração via trajetórias sintéticas (Onda 56).

Pipeline:
    1. Gera trajetória sintética de N steps a partir da matriz M_true conhecida
    2. Calibra matriz M_estimada usando MLE/Laplace/EWMA
    3. Mede erro Frobenius e KL entre M_true e M_estimada
    4. Relatório de acurácia da calibração

Uso:
    python scripts/validar_calibracao.py --n-steps 5000 --metodo laplace --alpha 0.1
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from engine.psicohistoria.grafo_eventos import construir_grafo_vila
from engine.psicohistoria.calibracao_online import calibrar, perplexity


def kl_divergencia_linhas(M_true: np.ndarray, M_est: np.ndarray) -> np.ndarray:
    """KL linha-por-linha entre M_true e M_est."""
    eps = 1e-12
    Mt = np.clip(M_true, eps, None)
    Me = np.clip(M_est, eps, None)
    return (Mt * np.log(Mt / Me)).sum(axis=1)


def gerar_trajetoria(M: np.ndarray, estados: list[str], n: int,
                      inicial: str, seed: int = 42) -> list[str]:
    """Amostra trajetória Markov a partir de M."""
    rng = np.random.default_rng(seed)
    idx_nome = {e: i for i, e in enumerate(estados)}
    idx = idx_nome[inicial]
    traj = [estados[idx]]
    for _ in range(n - 1):
        idx = int(rng.choice(len(estados), p=M[idx]))
        traj.append(estados[idx])
    return traj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-steps", type=int, default=5000)
    ap.add_argument("--metodo", default="laplace", choices=["mle", "laplace", "ewma"])
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--estado-inicial", default="bootstrap")
    args = ap.parse_args()

    grafo = construir_grafo_vila()
    M_true = grafo.matriz.copy()
    estados = list(grafo.estados.keys())

    print(f"=== Validação Calibração ===")
    print(f"n_steps: {args.n_steps} · método: {args.metodo} · α: {args.alpha}")
    print()

    traj = gerar_trajetoria(M_true, estados, args.n_steps,
                              args.estado_inicial, seed=args.seed)

    r = calibrar(traj, metodo=args.metodo, alpha=args.alpha)
    M_est = r.matriz_calibrada

    # Métricas
    frob = float(np.linalg.norm(M_true - M_est, "fro"))
    kl_linhas = kl_divergencia_linhas(M_true, M_est)
    kl_medio = float(kl_linhas.mean())
    kl_max = float(kl_linhas.max())
    pp_true = perplexity(traj, M_true, grafo)
    pp_est = perplexity(traj, M_est, grafo)
    cobertura = len(r.estados_observados) / len(estados) * 100

    print(f"Cobertura (estados visitados): {cobertura:.1f}%")
    print(f"Frobenius ‖M_true − M_est‖: {frob:.4f}")
    print(f"KL médio linha-a-linha:    {kl_medio:.4f}")
    print(f"KL máximo linha:           {kl_max:.4f}")
    print(f"Perplexity (true):         {pp_true:.3f}")
    print(f"Perplexity (estimada):     {pp_est:.3f}")
    print(f"Gap perplexity:            {abs(pp_est - pp_true):.3f}")
    print()

    # Top-3 linhas com maior KL (onde estimativa errou mais)
    top3_idx = kl_linhas.argsort()[-3:][::-1]
    print("Top-3 estados com maior erro:")
    for i in top3_idx:
        print(f"  {estados[i]:<25} KL={kl_linhas[i]:.4f}")

    # Critério de aceite
    aceita = kl_medio < 0.1 and frob < 0.5
    print()
    print(f"VEREDITO: {'PASSA' if aceita else 'FALHA'} "
           f"(critério: KL_medio<0.1 AND Frobenius<0.5)")

    sys.exit(0 if aceita else 1)


if __name__ == "__main__":
    main()
