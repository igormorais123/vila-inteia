"""
Onda 165: prompt variant ensemble.

Em vez de query única, gera N rephrasings do outcome_framing, query
cada uma, aggregate via median. Reduz bias associado a fraseamento
específico.

Exemplo:
  original: "Dilma sofrerá impeachment?"
  variants: [
    "Dilma sofrerá impeachment?",
    "A remoção de Dilma da presidência se concretizará?",
    "Haverá afastamento definitivo da presidente Dilma?",
  ]

Cada persona × N variants = distribuição mais robusta.

Templates de rephrasing via rules simples (sem LLM call extra):
- SIM/afirmativo → interrogativo
- Verbo → sinônimo
- Substantivo → paráfrase
"""

from __future__ import annotations

import re
from typing import Iterable


# Templates rephrasing manual (sem LLM call extra)
_PREFIXOS_ALTERNATIVOS = [
    "",  # original
    "Na sua avaliação, ",
    "Considerando o contexto completo, ",
]


def gerar_variants(framing_original: str, n: int = 3) -> list[str]:
    """
    Retorna lista de até n rephrasings do framing original.
    Sem LLM — rules-based. Sempre inclui original como variante 0.
    """
    if not framing_original:
        return []

    variants = [framing_original]

    # Variant 1: troca "sofrerá" / "atingirá" por sinônimos
    sinonimos_verb = [
        (r"\bsofrerá\b", "terá"),
        (r"\batingirá\b", "alcançará"),
        (r"\bserá aprovad[oa]\b", "receberá aprovação"),
        (r"\bocorrerá\b", "se concretizará"),
        (r"\bvencerá\b", "conquistará vitória em"),
        (r"\bfará\b", "realizará"),
    ]
    v1 = framing_original
    for pat, rep in sinonimos_verb:
        if re.search(pat, v1, flags=re.IGNORECASE):
            v1 = re.sub(pat, rep, v1, count=1, flags=re.IGNORECASE)
            break
    if v1 != framing_original:
        variants.append(v1)

    # Variant 2: adiciona prefixo reflexivo
    if len(variants) < n:
        v2 = _PREFIXOS_ALTERNATIVOS[1] + framing_original[0].lower() + framing_original[1:]
        variants.append(v2)

    # Variant 3: explícito re-framing
    if len(variants) < n:
        v3 = _PREFIXOS_ALTERNATIVOS[2] + framing_original[0].lower() + framing_original[1:]
        variants.append(v3)

    return variants[:n]


def agregar_probs_variants(probs_por_variant: Iterable[float | None]) -> float | None:
    """Median das probs válidas. None se todas inválidas."""
    validos = [p for p in probs_por_variant if p is not None]
    if not validos:
        return None
    validos.sort()
    n = len(validos)
    if n % 2 == 1:
        return validos[n // 2]
    return (validos[n // 2 - 1] + validos[n // 2]) / 2


def query_persona_com_variants(
    persona_id: str,
    framing_original: str,
    contexto: str,
    sim,
    llm_fn=None,
    n_variants: int = 3,
    max_tokens: int = 250,
    temperatura: float = 0.4,
    extrair_fn=None,
) -> dict:
    """
    Query mesma persona com N variants do framing. Retorna {variants, probs, median}.
    """
    from engine.persona_chat import chat_com_persona, resetar_historico
    if extrair_fn is None:
        from engine.backtest_real import extrair_probabilidade
        extrair_fn = extrair_probabilidade

    variants = gerar_variants(framing_original, n=n_variants)
    respostas = []
    probs = []

    for v in variants:
        resetar_historico()  # isolar cada variant
        pergunta = (
            f"Contexto: \"{contexto}\"\n\n"
            f"Pergunta específica: {v}\n"
            f"Qual a probabilidade (0% a 100%) da resposta ser SIM?"
        )
        r = chat_com_persona(
            persona_id=persona_id, pergunta=pergunta, sim=sim,
            llm_fn=llm_fn, max_tokens=max_tokens, temperatura=temperatura,
        )
        resp_txt = r.get("resposta") or ""
        p = extrair_fn(resp_txt)
        respostas.append({"variant": v, "resposta": resp_txt, "prob_extraida": p})
        if p is not None:
            probs.append(p)

    median = agregar_probs_variants(probs)
    return {
        "variants_queried": variants,
        "respostas": respostas,
        "probs": probs,
        "median": median,
        "n_validas": len(probs),
    }
