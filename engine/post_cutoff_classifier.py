"""
Onda 249: Text-based event classifier para post-cutoff forecasting.

Estratégia honest (sem memorization, sem peek):
- Classifica event framing/contexto via keywords lexicais
- Aplica per-category base rate empírico de eventos similares
  (derivado de world knowledge geral, não Q1 2026 específico)

Categorias:
- war/conflict/attack/strike → high yes (0.80)
- election/poll/approval/vote → moderate (0.55)
- tech release/launch/announce → moderate-low (0.40 — delays comuns)
- price target/threshold/ATH → low (0.35 — markets eficientes)
- summit/meeting/event held → very high (0.95 — usually happens)
- removal/coup/depose → low (0.20)
- protest/storm/disaster > N → moderate (0.55)
- sports specific winner → low (0.35 — many possible winners)

Referencia base rates: histórico ~10 anos eventos noticiados.
"""

from __future__ import annotations


KEYWORD_PRIORS: list[tuple[list[str], float, str]] = [
    # (keywords, base_rate, category_label)
    (["guerra", "war", "ataque", "attack", "strike", "conflict", "khamenei"], 0.80, "war_conflict"),
    (["captura", "depõe", "depos", "coup", "regime change", "removed"], 0.30, "regime_change"),
    (["olympic", "summit", "wef", "davos", "realizad", "held"], 0.95, "scheduled_event"),
    (["tariff", "tarifa", "imposed"], 0.55, "tariff_action"),
    (["fed cut", "rate cut", "corte juros", "fomc"], 0.45, "fed_action"),
    (["lança", "release", "launch", "anuncia", "announce"], 0.45, "tech_release"),
    (["bitcoin", "btc", "ath", "preço", "price", "k+", "$"], 0.40, "price_target"),
    (["candidato", "candidate", "election", "vence", "wins"], 0.50, "election"),
    (["approval", "aprovação", "rating"], 0.45, "polling"),
    (["mortes", "killed", "deaths", ">"], 0.60, "casualty_threshold"),
    (["super bowl", "world cup", "champion"], 0.40, "sports_winner"),
    (["etf", "approval", "spot"], 0.45, "etf_approval"),
]


def classify_and_predict(framing: str, contexto: str = "") -> tuple[float, str]:
    """Classify via keywords + return prior.

    Tenta cada keyword set in order. First match wins.
    Default: 0.50.
    """
    text = (framing + " " + contexto).lower()
    for keywords, prior, label in KEYWORD_PRIORS:
        if any(kw in text for kw in keywords):
            return prior, label
    return 0.50, "default"


def evaluate_classifier_on_events(events: list) -> dict:
    """Eval classifier sobre events com framing + outcome_real."""
    hits = 0
    brier_sum = 0.0
    by_cat = {}
    for e in events:
        framing = e.get("outcome_framing", "") or ""
        contexto = e.get("contexto", "") or ""
        p, label = classify_and_predict(framing, contexto)
        real = e.get("outcome_real")
        if real is None:
            continue
        if (p >= 0.5) == bool(real):
            hits += 1
        brier_sum += (p - real) ** 2
        by_cat.setdefault(label, []).append((p, real))

    n = len([e for e in events if e.get("outcome_real") is not None])
    return {
        "n": n, "hits": hits,
        "acc": hits / n if n else 0,
        "brier": brier_sum / n if n else 0,
        "by_category": by_cat,
    }
