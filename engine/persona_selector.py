"""
Onda 127: dataset-conditional persona selection.

Categoriza dataset + recomenda panel ideal por domínio.
Backed by Onda 95 per-persona skill rankings + domain fit heuristics.

Categorias:
- politica_br: impeachment, eleições, Lava Jato → Bezos, Jobs, Jesus, Lula
- financeiro: Americanas, crypto, PIX → Buffett, Munger, Dalio, Icahn
- tech: Apple VPro, TikTok, Twitter → Musk, Jobs, Zuck, Ellison
- geopolitica: crises globais → Sun Tzu, Cleopatra, Kissinger
- generico: fallback → Bezos, Jobs, Buffett (top 3 skill)
"""

from __future__ import annotations

from typing import Any


# Mapeamento categoria → persona_ids recomendados
# Baseado em Onda 95 findings + domain expertise fit
PANELS_POR_CATEGORIA: dict[str, list[str]] = {
    "politica_br": [
        "CL007",  # Bezos (top Onda 95 impeachment, 100% acc)
        "CL002",  # Jobs (100% acc)
        "CL001",  # Musk (80%)
    ],
    "financeiro": [
        "CL020",  # Buffett (value investing)
        "CL021",  # Munger (Buffett partner)
        "CL015",  # Dalio (macro)
    ],
    "tech": [
        "CL001",  # Musk
        "CL002",  # Jobs
        "CL023",  # Zuckerberg
    ],
    "crypto": [
        "CL001",  # Musk
        "CL020",  # Buffett (skeptic)
        "CL019",  # Icahn
    ],
    "geopolitica": [
        "CL030",  # Sun Tzu
        "CL035",  # Marco Aurélio
        "CL002",  # Jobs (strategic)
    ],
    "generico": [
        "CL007",  # Bezos
        "CL002",  # Jobs
        "CL020",  # Buffett
    ],
}


# Keywords por categoria pra auto-detect
KEYWORDS_CATEGORIA: dict[str, list[str]] = {
    "politica_br": [
        "impeachment", "dilma", "lula", "bolsonaro", "eleição", "eleicao",
        "cunha", "moro", "lava", "congresso", "stf", "brasilia",
    ],
    "financeiro": [
        "americanas", "ações", "acoes", "ipo", "balanço", "balanco",
        "ceo", "receita", "lucro", "pix", "banco", "investidor",
    ],
    "tech": [
        "apple", "vision pro", "iphone", "facebook", "meta", "google",
        "openai", "gpt", "lançamento", "lancamento", "produto", "startup",
    ],
    "crypto": [
        "bitcoin", "btc", "ethereum", "eth", "halving", "sec",
        "etf", "satoshi", "blockchain", "binance",
    ],
    "geopolitica": [
        "guerra", "ucrânia", "rússia", "otan", "china", "taiwan",
        "sanção", "diplomacy", "onu", "g20",
    ],
}


def detectar_categoria(dataset_name: str, eventos_sample: list[dict] | None = None) -> str:
    """
    Heurística: prefixo filename + keywords no conteúdo.
    Retorna categoria string ou 'generico' se sem match.
    """
    name_lower = dataset_name.lower()

    # Direct filename match
    if "impeachment" in name_lower or "eleicao" in name_lower or "eleicao_presidencial" in name_lower or "lava_jato" in name_lower:
        return "politica_br"
    if "americanas" in name_lower or "pix" in name_lower:
        return "financeiro"
    if "crypto" in name_lower or "bitcoin" in name_lower:
        return "crypto"
    if "apple" in name_lower or "tiktok" in name_lower or "twitter" in name_lower or "musk" in name_lower:
        return "tech"

    # Keyword scan on sample events
    if eventos_sample:
        texto_sample = " ".join(
            (e.get("contexto", "") or "").lower()
            for e in eventos_sample[:3]
        )
        scores: dict[str, int] = {}
        for cat, kws in KEYWORDS_CATEGORIA.items():
            scores[cat] = sum(1 for kw in kws if kw in texto_sample)
        melhor = max(scores.items(), key=lambda kv: kv[1], default=(None, 0))
        if melhor[1] >= 2:
            return melhor[0]

    return "generico"


def selecionar_panel(
    dataset_name: str,
    eventos_sample: list[dict] | None = None,
    personas_validas: set[str] | None = None,
) -> dict:
    """
    Retorna dict com:
        categoria: str detectada
        persona_ids: list ideal panel (filtrado por validas se fornecido)
        panel_padrao: list completa (pre-filter)
    """
    cat = detectar_categoria(dataset_name, eventos_sample)
    panel = PANELS_POR_CATEGORIA.get(cat, PANELS_POR_CATEGORIA["generico"])

    if personas_validas:
        panel_filtrado = [p for p in panel if p in personas_validas]
        # Fallback: se nenhum dos ideais disponível, usa generic filtrado
        if not panel_filtrado:
            gen = PANELS_POR_CATEGORIA["generico"]
            panel_filtrado = [p for p in gen if p in personas_validas]
        # Fallback-fallback: primeiros 3 validos
        if not panel_filtrado:
            panel_filtrado = sorted(personas_validas)[:3]
    else:
        panel_filtrado = panel

    return {
        "categoria": cat,
        "persona_ids": panel_filtrado,
        "panel_padrao_categoria": panel,
    }


def panels_por_dataset(datasets: list[str]) -> dict[str, dict]:
    """Aplica selecionar_panel em todos datasets. Útil pra CLI."""
    return {ds: selecionar_panel(ds) for ds in datasets}
