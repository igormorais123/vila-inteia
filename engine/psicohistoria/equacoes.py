"""
Equações psico-históricas: potência da matriz de transição + cálculos espectrais.

Principais operações:
    - prever_trajetoria: simulação de distribuição de probabilidades N passos à frente
    - distribuicao_estacionaria: equilíbrio de longo prazo (autovetor esquerdo de λ=1)
    - tempo_ate_absorver: tempo médio para atingir estado absorvente

Estas são as "equações de Seldon" num sentido computacional.
"""

from __future__ import annotations

import numpy as np

from engine.psicohistoria.grafo_eventos import GrafoPsicohistoria


def prever_trajetoria(
    grafo: GrafoPsicohistoria,
    estado_inicial: str,
    passos: int = 50,
) -> np.ndarray:
    """
    Simula distribuição ao longo do tempo.

    Retorna shape (passos + 1, n_estados) — linha i = distribuição no step i.
    """
    if grafo.matriz is None:
        raise ValueError("grafo sem matriz; chame montar_matriz primeiro")
    n = len(grafo.estados)
    traj = np.zeros((passos + 1, n))
    traj[0] = grafo.vetor_estado(estado_inicial)
    M = grafo.matriz
    for t in range(passos):
        traj[t + 1] = traj[t] @ M
    return traj


def distribuicao_estacionaria(grafo: GrafoPsicohistoria) -> dict[str, float]:
    """
    Autovetor esquerdo de λ=1 (distribuição estacionária π).

    π @ M = π. Resolve via autovetor da transposta.
    Se cadeia é irredutível + aperiódica, único π. Senão, retorna aproximação.
    """
    if grafo.matriz is None:
        raise ValueError("grafo sem matriz")
    M = grafo.matriz
    vals, vecs = np.linalg.eig(M.T)
    # Acha autovetor com autovalor mais próximo de 1
    idx = int(np.argmin(np.abs(vals - 1.0)))
    pi = np.real(vecs[:, idx])
    pi = np.abs(pi)
    pi /= pi.sum() if pi.sum() > 0 else 1
    return {grafo.index_para_estado(i): float(pi[i]) for i in range(len(pi))}


def tempo_ate_absorver(
    grafo: GrafoPsicohistoria,
    estado_inicial: str,
    estado_absorvente: str,
    max_passos: int = 10000,
    limiar: float = 0.99,
) -> int | None:
    """
    Quantos passos até probabilidade(estado_absorvente) >= limiar.
    Retorna None se não atingir em max_passos.
    """
    if grafo.matriz is None:
        raise ValueError("grafo sem matriz")
    dist = grafo.vetor_estado(estado_inicial)
    M = grafo.matriz
    idx_abs = grafo.estado_para_index(estado_absorvente)
    for t in range(1, max_passos + 1):
        dist = dist @ M
        if dist[idx_abs] >= limiar:
            return t
    return None


def entropia_trajetoria(traj: np.ndarray, base: float = 2.0) -> np.ndarray:
    """
    Entropia de Shannon ao longo do tempo. Converge → concentração em poucos estados.
    base=2 → bits.
    """
    eps = 1e-12
    p = np.clip(traj, eps, 1.0)
    H = -(p * np.log(p) / np.log(base)).sum(axis=1)
    return H


def predizer_estado_provavel(
    grafo: GrafoPsicohistoria,
    estado_inicial: str,
    passos: int,
) -> tuple[str, float]:
    """
    Estado mais provável em `passos` e sua probabilidade.
    """
    traj = prever_trajetoria(grafo, estado_inicial, passos)
    dist_final = traj[-1]
    idx = int(np.argmax(dist_final))
    return grafo.index_para_estado(idx), float(dist_final[idx])
