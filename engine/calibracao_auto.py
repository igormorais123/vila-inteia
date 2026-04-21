"""
Onda 150: auto-select melhor calibrador (Platt vs isotonic).

Fita ambos sobre mesmo data, compara brier, escolhe vencedor.
Resultado pronto pra salvamento via calibracao_runtime.
"""

from __future__ import annotations

import logging
from typing import Iterable

logger = logging.getLogger(__name__)


def fit_melhor_calibrador(
    probs: Iterable[float],
    y: Iterable[int],
) -> dict:
    """
    Fita Platt + isotonic, retorna melhor por brier.

    Returns dict com:
        vencedor: 'platt' | 'isotonic' | 'nenhum'
        platt: {a, b, brier}
        isotonic: {mapping, brier}
        delta_brier: platt - isotonic (positivo = iso melhor)
        n_amostras: int
    """
    from engine.calibracao_platt import fit_platt, aplicar_platt, brier
    from engine.calibracao_stats import isotonic_fit, isotonic_aplicar

    probs = list(probs)
    ys = list(y)

    if len(probs) < 5:
        return {"vencedor": "nenhum", "motivo": "poucos amostras", "n_amostras": len(probs)}

    # Baseline: prob raw
    brier_raw = brier(probs, ys)

    # Platt
    try:
        a, b = fit_platt(probs, ys)
        probs_platt = aplicar_platt(probs, a, b)
        brier_platt = brier(probs_platt, ys)
    except Exception as e:
        logger.debug(f"Platt fit falhou: {e}")
        a, b, brier_platt = None, None, float("inf")

    # Isotonic
    try:
        mapping = isotonic_fit(probs, ys)
        probs_iso = [isotonic_aplicar(p, mapping) for p in probs]
        brier_iso = brier(probs_iso, ys)
    except Exception as e:
        logger.debug(f"Isotonic fit falhou: {e}")
        mapping, brier_iso = [], float("inf")

    # Escolhe menor
    if brier_platt <= brier_iso and a is not None:
        vencedor = "platt"
    elif mapping:
        vencedor = "isotonic"
    else:
        vencedor = "nenhum"

    return {
        "vencedor": vencedor,
        "brier_raw": brier_raw,
        "platt": {"a": a, "b": b, "brier": brier_platt},
        "isotonic": {"mapping": mapping, "brier": brier_iso},
        "delta_brier_platt_vs_iso": brier_platt - brier_iso,
        "n_amostras": len(probs),
    }


def salvar_melhor_calibrador(
    probs: Iterable[float],
    y: Iterable[int],
    fonte: str = "auto_fit",
    path: str | None = None,
) -> dict:
    """
    Fita melhor + salva no path. Returns resumo do que foi salvo.
    """
    from engine.calibracao_runtime import salvar_coefs, salvar_isotonic

    r = fit_melhor_calibrador(probs, y)
    n = r["n_amostras"]

    if r["vencedor"] == "platt":
        salvar_coefs(
            a=r["platt"]["a"], b=r["platt"]["b"],
            n_amostras=n, fonte=f"{fonte}_platt", path=path,
        )
        r["salvo_como"] = "platt"
    elif r["vencedor"] == "isotonic":
        salvar_isotonic(
            mapping=r["isotonic"]["mapping"],
            n_amostras=n, fonte=f"{fonte}_isotonic", path=path,
        )
        r["salvo_como"] = "isotonic"
    else:
        r["salvo_como"] = None

    return r
