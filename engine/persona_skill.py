"""
Onda 95: per-persona prediction skill analysis.

Input: lista de eventos com per_persona preenchido (backtest_real).
Output: ranking de personas por accuracy + Brier + calibração.

Quem entre as 144 lendárias prevê melhor?
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def _brier(p: float, y: int) -> float:
    return (p - y) ** 2


def analisar_skill_personas(datasets: list[dict]) -> dict:
    """
    Agrega previsões per-persona de todos eventos em todos datasets.

    Args:
        datasets: lista de dicts com "eventos" → "per_persona"

    Returns dict com:
        n_personas_ativas, ranking: [{persona_id, persona_nome,
            n_previsoes, n_validas, accuracy, brier_avg,
            media_prob_emitida, outcome_medio}]
    """
    por_persona: dict[str, dict] = defaultdict(lambda: {
        "persona_id": None, "persona_nome": None,
        "n_previsoes": 0, "n_validas": 0,
        "acertos": 0, "briers": [], "probs": [], "outcomes": [],
    })

    for ds in datasets:
        if "erro" in ds:
            continue
        for ev in ds.get("eventos", []):
            y = ev.get("outcome_real")
            per_persona = ev.get("per_persona") or []
            for p in per_persona:
                pid = p.get("persona_id")
                if not pid:
                    continue
                bucket = por_persona[pid]
                bucket["persona_id"] = pid
                bucket["persona_nome"] = p.get("persona_nome")
                bucket["n_previsoes"] += 1
                prob = p.get("prob_extraida")
                if prob is None:
                    continue
                bucket["n_validas"] += 1
                bucket["probs"].append(prob)
                bucket["outcomes"].append(y)
                acertou = (prob >= 0.5) == (y == 1)
                if acertou:
                    bucket["acertos"] += 1
                bucket["briers"].append(_brier(prob, y))

    ranking = []
    for pid, b in por_persona.items():
        n_val = b["n_validas"]
        row = {
            "persona_id": b["persona_id"],
            "persona_nome": b["persona_nome"],
            "n_previsoes": b["n_previsoes"],
            "n_validas": n_val,
            "accuracy": b["acertos"] / n_val if n_val else 0.0,
            "brier_avg": sum(b["briers"]) / n_val if n_val else None,
            "media_prob_emitida": sum(b["probs"]) / n_val if n_val else None,
            "outcome_medio": sum(b["outcomes"]) / n_val if n_val else None,
        }
        ranking.append(row)

    # Ranking por Brier (lower better); empates desempatam por accuracy desc
    def _sort_key(r):
        b = r["brier_avg"] if r["brier_avg"] is not None else 1e9
        return (b, -r["accuracy"])
    ranking.sort(key=_sort_key)

    return {
        "n_personas_ativas": len(ranking),
        "ranking": ranking,
    }
