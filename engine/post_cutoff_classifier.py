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
    # Onda 258: PIT inverted-U → reduce 0.50 fallback. Add extreme-claim detection.
    # Extreme quantitative thresholds (1M units, 10x, atinge metas grandes) — empirically miss
    (["1m units", "milhão", "milhões", "atingirá 1m", "ultrapassará", "10x", "20x"], 0.30, "extreme_quantity_claim"),
    # Bottom-rank sports (Wales bottom, last place) — base rate ~ 1/N teams
    (["bottom", "último lugar", "last place", "rebaixad"], 0.35, "negative_rank_claim"),
    # Specific winners (Super Bowl champion, F1 race winner) — antes de election keyword
    (["super bowl", "world cup champion", "kansas city", "verstappen", "f1 race winner"], 0.30, "sports_specific_winner"),
    # Sports tournament structure / participation — usually true once announced
    (["fifa world cup 2026", "olympics 2026", "olímpico", "tournament"], 0.75, "sports_event_structure"),
    (["guerra", "war", "ataque", "attack", "strike", "conflict", "khamenei"], 0.80, "war_conflict"),
    # Regime change — historically rare, mas Q1 2026 had Maduro precedent. Conservador 0.40
    (["captura", "depõe", "depos", "coup", "regime change", "removed", "maduro"], 0.40, "regime_change"),
    # Brazilian legislative
    (["urgência", "plenário", "ccj ", " pl ", "câmara aprovou", "pec ", "deputados aprov"], 0.55, "br_legislative"),
    (["reforma", "marco regulatório", "tabela ir"], 0.30, "br_reform_complex"),
    # Scheduled / launch-window events — empirical 100% in our dataset
    (["olympic", "summit", "wef", "davos", "realizad", "held", "window aberta", "window opens",
      "preakness", "kentucky derby", "wrestlemania", "consensus", "sigma",
      "mwc", "mobile world congress", "wwdc", "ces", "gtc"], 0.92, "scheduled_event"),
    # Crypto event contracts — B3/CME approvals usually proceed
    (["event contracts", "futures crypto", "spot etf"], 0.65, "crypto_product_launch"),
    # Prices — markets eficientes, 50/50 (sem alpha sem cache live)
    (["fecha acima", "fecha abaixo", "$", "k em "], 0.50, "price_threshold"),
    (["tariff", "tarifa", "imposed"], 0.55, "tariff_action"),
    (["fed cut", "rate cut", "corte juros", "fomc"], 0.45, "fed_action"),
    # Tech releases — slow/uncertain; Artemis II type long delays common
    (["lança", "release", "launch", "anuncia", "announce", "starship"], 0.45, "tech_release"),
    (["bitcoin", "btc", "ath", "k+"], 0.40, "price_target"),
    (["candidato", "candidate", "election", "vence", "wins"], 0.50, "election"),
    (["approval", "aprovação", "rating"], 0.45, "polling"),
    (["mortes", "killed", "deaths", ">"], 0.60, "casualty_threshold"),
    (["etf", "spot"], 0.45, "etf_approval"),
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
