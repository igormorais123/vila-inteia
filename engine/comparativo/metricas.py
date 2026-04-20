"""Métricas comparativas entre runs."""

from __future__ import annotations

import math
from collections import Counter


def _distribuicao(estados: list[str]) -> dict[str, float]:
    if not estados:
        return {}
    c = Counter(estados)
    n = len(estados)
    return {k: v / n for k, v in c.items()}


def comparar_trajetorias(
    traj_a: list[str],
    traj_b: list[str],
) -> dict:
    """
    KL divergence + TV distance + overlap das distribuições.
    """
    dist_a = _distribuicao(traj_a)
    dist_b = _distribuicao(traj_b)

    eps = 1e-12
    kl = sum(p * math.log(p / max(dist_b.get(k, eps), eps))
              for k, p in dist_a.items() if p > 0)
    tv = 0.5 * sum(abs(dist_a.get(k, 0) - dist_b.get(k, 0))
                    for k in set(dist_a) | set(dist_b))
    overlap = len(set(dist_a) & set(dist_b))
    total_unico = len(set(dist_a) | set(dist_b))

    return {
        "kl_divergence": kl,
        "total_variation": tv,
        "estados_comuns": overlap,
        "estados_totais": total_unico,
        "overlap_pct": overlap / total_unico * 100 if total_unico else 0,
        "n_a": len(traj_a),
        "n_b": len(traj_b),
    }


def diferenca_convergencia(
    crencas_finais_a: dict[str, float],
    crencas_finais_b: dict[str, float],
) -> float:
    """
    Distância L1 média entre vetores de crenças finais dos mesmos agentes.
    0 = mesma convergência; maior = divergência.
    """
    agentes_comuns = set(crencas_finais_a) & set(crencas_finais_b)
    if not agentes_comuns:
        return float("inf")
    total = sum(abs(crencas_finais_a[a] - crencas_finais_b[a])
                 for a in agentes_comuns)
    return total / len(agentes_comuns)
