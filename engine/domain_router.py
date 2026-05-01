"""Onda 285 — Domain router para forecasting.

Decide entre 3 forecasters (Vila / LLM / Hybrid) por evento, com base em
features léxicas do framing. Determinístico, sem LLM. Treinado nas
descobertas das Ondas 280-284:

  - Eventos geopolíticos / políticos / históricos → LLM puro
    (Onda 284: geopolitics_q1_2026 LLM brier 0.044 vs Vila 0.287)
  - Eventos BTC-specific quantitativos → Vila
    (Onda 283: Vila bate climatology -10% em BTC)
  - Genéricos (sports, science, q-bench) → Hybrid
    (Onda 281: w_llm=0.85 ótimo)

Uso:
    from engine.domain_router import route, predict_routed
    route(framing) → 'vila' | 'llm' | 'hybrid'
    predict_routed(framing, contexto) → (prob, route_label)
"""

from __future__ import annotations

import re
from typing import Literal

Route = Literal["vila", "llm", "hybrid"]

# Heurísticas baseadas em lift empírico Vila→LLM (Onda 284):
#   geopolitics: -85% brier
#   impeachment/political-history: -58%
#   crypto: -60% (LLM bate Vila genérica, mas Vila BTC-specific bate climatology)
#   apple_vpro/corporate: -16% (margem menor)

LLM_KEYWORDS = (
    # Política / governo
    "eleição", "eleicao", "election", "vota", "voto", "candidato", "presidente",
    "ministro", "congresso", "senado", "câmara", "camara", "impeachment",
    "destituiç", "destituic", "destitut",
    # Geopolítica / guerra
    "guerra", "war", "conflito", "sanção", "sancao", "sanction", "embargo",
    "tropa", "invasão", "invasao", "invasion", "ataque militar", "missile",
    "ucrânia", "ucrania", "ukraine", "russia", "rússia", "china", "iran",
    "irã", "ira", "israel", "gaza", "palestina", "palestin", "taiwan",
    "otan", "nato", "onu", "un security",
    # Decisões regulatórias / jurídicas que dependem de contexto político
    "stf", "supremo", "tribunal", "lava jato", "operacao", "operação",
    "indictment", "indiciament", "cpi", "comissao parlamentar",
    # Lançamento corporativo grande / M&A — prefixos cobrem conjugações
    # ("lança", "lançará", "lançamento", "lançou" todos viram "lança...")
    "lança", "lanca", "launch", "release", "fusão", "fusao",
    "merger", "acquisition", "aquisição", "aquisicao", "ipo",
)

VILA_KEYWORDS = (
    # Cripto on-chain quantitativo (Onda 283 BTC-specific)
    "bitcoin price", "btc price", "btc funding", "btc dominance", "hashrate",
    "on-chain", "onchain", "mvrv", "nupl", "halving",
    # Estatística pura / agregada
    "média histórica", "media historica", "base rate", "frequência média",
    "frequencia media", "rolling average",
)


def _norm(s: str) -> str:
    return s.lower() if s else ""


def _has_any(text: str, keywords: tuple[str, ...]) -> bool:
    t = _norm(text)
    return any(kw in t for kw in keywords)


def route(framing: str, contexto: str = "") -> Route:
    """Decide roteamento. Ordem de precedência: Vila-specific > LLM > Hybrid (default)."""
    blob = f"{framing} {contexto}"
    if _has_any(blob, VILA_KEYWORDS):
        return "vila"
    if _has_any(blob, LLM_KEYWORDS):
        return "llm"
    return "hybrid"


def predict_routed(framing: str, contexto: str = "") -> tuple[float, Route]:
    """Roteia o evento e retorna (prob, route_label).

    Lazy-import dos forecasters pra evitar custo de inicialização quando não usados.
    """
    r = route(framing, contexto)
    if r == "vila":
        from engine.post_cutoff_classifier import classify_and_predict
        p, _ = classify_and_predict(framing, contexto)
        return p, r
    if r == "llm":
        from engine.llm_forecaster import llm_predict
        from engine.post_cutoff_classifier import classify_and_predict
        p_v, label = classify_and_predict(framing, contexto)
        p_l = llm_predict(framing, contexto, vila_hint=(label, p_v))
        return (p_l if p_l is not None else p_v), r
    # hybrid
    from engine.vila_llm_hybrid import vila_llm_hybrid_predict
    p = vila_llm_hybrid_predict(framing, contexto)
    return p, r


def route_stats(events: list) -> dict:
    """Conta distribuição de routes em uma lista de eventos."""
    counts = {"vila": 0, "llm": 0, "hybrid": 0}
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        ctx = e.get("contexto", "")
        counts[route(framing, ctx)] += 1
    total = sum(counts.values()) or 1
    return {**counts, "total": total,
            "pct": {k: round(v / total, 3) for k, v in counts.items()}}
