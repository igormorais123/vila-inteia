"""
Spatial voter model (Hotelling 1929, Downs 1957).

Eleitores/agentes posicionados num espaço ideológico [0, 1].
Candidatos ganham votos proporcionalmente a proximidade.
Teorema do Eleitor Mediano: em 1D, candidato no ponto médio ganha.
"""

from __future__ import annotations

import numpy as np


def median_voter(preferencias: np.ndarray) -> float:
    """Teorema: melhor posição estratégica é a mediana."""
    if len(preferencias) == 0:
        return 0.5
    return float(np.median(preferencias))


def hotelling_equilibrio(n_candidatos: int = 2, dim: int = 1) -> np.ndarray:
    """
    Equilíbrio espacial de Hotelling.

    1D, 2 candidatos: convergência ao mediano (0.5 em [0, 1]).
    1D, N>2 candidatos: não há NE estável (Eaton-Lipsey).
    2D+, qualquer N: não há NE genericamente (Plott 1967 impossibility).

    Por convenção retorna NaN quando não converge, 0.5 * ones quando converge.
    """
    if dim == 1 and n_candidatos == 2:
        return np.full((n_candidatos, 1), 0.5)
    if dim == 1 and n_candidatos > 2:
        # NE instável; retorna distribuição uniforme como aproximação
        return np.linspace(0, 1, n_candidatos).reshape(-1, 1)
    # Multi-dim: sem NE puro
    return np.full((n_candidatos, dim), np.nan)


def distancia_ideologica(
    agente_pos: np.ndarray,
    candidato_pos: np.ndarray,
    metrica: str = "euclidean",
) -> float:
    """Distância no espaço ideológico (1D ou multi-dim)."""
    if metrica == "euclidean":
        return float(np.linalg.norm(agente_pos - candidato_pos))
    elif metrica == "manhattan":
        return float(np.abs(agente_pos - candidato_pos).sum())
    raise ValueError(f"métrica desconhecida: {metrica}")


def votacao_espacial(
    posicoes_eleitores: np.ndarray,    # shape (n,) ou (n, dim)
    posicoes_candidatos: np.ndarray,   # shape (c,) ou (c, dim)
) -> dict[int, int]:
    """
    Cada eleitor vota no candidato mais próximo.
    Retorna candidato_idx -> n_votos.
    """
    votos: dict[int, int] = {}
    for voter in posicoes_eleitores:
        dists = [
            distancia_ideologica(np.atleast_1d(voter), np.atleast_1d(cand))
            for cand in posicoes_candidatos
        ]
        vencedor = int(np.argmin(dists))
        votos[vencedor] = votos.get(vencedor, 0) + 1
    return votos
