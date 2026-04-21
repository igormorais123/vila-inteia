"""
Onda 95: per-persona prediction skill analysis.

Input: lista de eventos com per_persona preenchido (backtest_real).
Output: ranking de personas por accuracy + Brier + calibração.

Onda 140: agora expõe também ranking_por_categoria —
matriz persona x domain (política, crypto, tech_launch, social_rejection, etc).

Quem entre as 144 lendárias prevê melhor? E em qual domínio?
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


def _brier(p: float, y: int) -> float:
    return (p - y) ** 2


_CATEGORIAS_KEYWORDS = {
    "politica_br": ["impeachment", "eleicao", "eleicao_presidencial", "lava_jato"],
    "crypto": ["bitcoin", "btc", "crypto", "ethereum"],
    "tech_launch": ["apple", "vpro", "vision_pro", "lancamento"],
    "fintech_br": ["pix", "americanas"],
    "social_media": ["twitter", "musk", "tiktok", "viral"],
    "municipal_br": ["municipal", "seed_eleicao", "sp_2024"],
}


def categorizar_dataset(dataset_name_or_path: str) -> str:
    """Mapeia nome/path de dataset para categoria conhecida. Fallback: 'geral'."""
    name = (dataset_name_or_path or "").lower()
    # Normaliza: path → basename sem extensão
    name = re.sub(r".*[\\/]", "", name)
    name = re.sub(r"\.csv$|\.json$", "", name)
    for cat, kws in _CATEGORIAS_KEYWORDS.items():
        if any(kw in name for kw in kws):
            return cat
    return "geral"


def _novo_bucket():
    return {
        "persona_id": None, "persona_nome": None,
        "n_previsoes": 0, "n_validas": 0,
        "acertos": 0, "briers": [], "probs": [], "outcomes": [],
    }


def _bucket_to_row(b: dict) -> dict:
    n_val = b["n_validas"]
    return {
        "persona_id": b["persona_id"],
        "persona_nome": b["persona_nome"],
        "n_previsoes": b["n_previsoes"],
        "n_validas": n_val,
        "accuracy": b["acertos"] / n_val if n_val else 0.0,
        "brier_avg": sum(b["briers"]) / n_val if n_val else None,
        "media_prob_emitida": sum(b["probs"]) / n_val if n_val else None,
        "outcome_medio": sum(b["outcomes"]) / n_val if n_val else None,
    }


def _sort_por_brier(ranking: list[dict]) -> list[dict]:
    def _k(r):
        b = r["brier_avg"] if r["brier_avg"] is not None else 1e9
        return (b, -r["accuracy"])
    return sorted(ranking, key=_k)


def analisar_skill_personas(datasets: list[dict]) -> dict:
    """
    Agrega previsões per-persona de todos eventos em todos datasets.

    Args:
        datasets: lista de dicts com "eventos" → "per_persona"

    Returns dict com:
        n_personas_ativas, ranking: [{persona_id, persona_nome,
            n_previsoes, n_validas, accuracy, brier_avg,
            media_prob_emitida, outcome_medio}],
        ranking_por_categoria: {categoria: [ranking rows]}  (Onda 140)
    """
    por_persona: dict[str, dict] = defaultdict(_novo_bucket)
    por_cat_persona: dict[str, dict[str, dict]] = defaultdict(
        lambda: defaultdict(_novo_bucket)
    )

    for ds in datasets:
        if "erro" in ds:
            continue
        cat = categorizar_dataset(ds.get("dataset") or "")
        for ev in ds.get("eventos", []):
            y = ev.get("outcome_real")
            per_persona = ev.get("per_persona") or []
            for p in per_persona:
                pid = p.get("persona_id")
                if not pid:
                    continue
                for bucket in (por_persona[pid], por_cat_persona[cat][pid]):
                    bucket["persona_id"] = pid
                    bucket["persona_nome"] = p.get("persona_nome")
                    bucket["n_previsoes"] += 1
                prob = p.get("prob_extraida")
                if prob is None:
                    continue
                acertou = (prob >= 0.5) == (y == 1)
                for bucket in (por_persona[pid], por_cat_persona[cat][pid]):
                    bucket["n_validas"] += 1
                    bucket["probs"].append(prob)
                    bucket["outcomes"].append(y)
                    if acertou:
                        bucket["acertos"] += 1
                    bucket["briers"].append(_brier(prob, y))

    ranking = _sort_por_brier([_bucket_to_row(b) for b in por_persona.values()])
    ranking_por_categoria = {
        cat: _sort_por_brier([_bucket_to_row(b) for b in d.values()])
        for cat, d in por_cat_persona.items()
    }

    return {
        "n_personas_ativas": len(ranking),
        "ranking": ranking,
        "ranking_por_categoria": ranking_por_categoria,
    }
