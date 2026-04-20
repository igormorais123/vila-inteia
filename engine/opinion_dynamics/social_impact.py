"""
Social Impact Theory (Latané 1981, Nowak et al 1990).

Impacto de uma fonte sobre alvo =
    strength (força/status da fonte) × immediacy² (proximidade) × sqrt(número de fontes)

Uso na Vila: quantifica influência de post sobre leitor sem recorrer a LLM.
"""

from __future__ import annotations

import math


def impacto_social(
    forca: float,              # 0 a 1 (reputação/patente normalizada)
    imediacy: float,           # 0 a 1 (proximidade no grafo social)
    n_fontes: int = 1,
) -> float:
    """
    Fórmula Latané:
        I = s * i² * sqrt(n)

    Decay quadrático na proximidade (distance matters a lot).
    Sqrt no número de fontes (diminishing returns).
    """
    if n_fontes < 1:
        return 0.0
    return forca * (imediacy ** 2) * math.sqrt(n_fontes)


def influencia_agregada(
    fontes: list[dict],    # [{forca, imediacy}, ...]
) -> float:
    """
    Soma impactos múltiplos com lei de Latané.
    Note: não é soma simples — Latané argumenta que muitas fontes pequenas
    não igualam poucas fortes (o sqrt já captura isso parcialmente).
    """
    if not fontes:
        return 0.0
    forca_media = sum(f["forca"] for f in fontes) / len(fontes)
    imediacy_media = sum(f["imediacy"] for f in fontes) / len(fontes)
    return impacto_social(forca_media, imediacy_media, len(fontes))
