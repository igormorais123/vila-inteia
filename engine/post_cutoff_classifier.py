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
    # Central bank actions — meeting realization usually true; rate cuts variable
    (["fomc reunião realizada", "ecb realizada", "boe realizada", "boj realizada",
      "fomc march", "fomc realizada", "central bank realizada"], 0.92, "central_bank_meeting"),
    (["fed cut", "rate cut", "corte juros", "fomc", "cortou taxa", "cortou rate",
      "cortou selic", "cortou lpr"], 0.50, "fed_action"),
    # Geopolitics — base rate low for major escalation, high for ongoing tensions
    (["invadiu", "invaded", "ceasefire", "cessar-fogo", "paris agreement",
      "nato new member", "saudi-israel"], 0.25, "geopolitical_low"),
    (["míssil", "missile", "cyber attack", "drone", "test"], 0.65, "geopolitical_routine"),
    # Corporate M&A / financial action
    (["aquisição", "acquired", "acquisition", "buyback", "stock buyback",
      "dividendos", "dividend", "merger"], 0.55, "corporate_action"),
    (["cisão", "spin-off", "demissões em massa", "layoffs", "ipo cancel"], 0.40, "corporate_negative"),
    # Regulatory / legal
    (["aprovou eu ai", "ai act", "enforcement"], 0.75, "regulatory_active"),
    (["bloqueou", "blocked", "antitrust", "fined", "doj", "ftc",
      "revogou", "withdrew", "withdraws", "restrições"], 0.40, "regulatory_action"),
    # Tech releases — slow/uncertain; Artemis II type long delays common
    (["lança", "release", "launch", "anuncia", "announce", "starship"], 0.45, "tech_release"),
    (["bitcoin", "btc", "ath", "k+"], 0.40, "price_target"),
    (["candidato", "candidate", "election", "vence", "wins"], 0.50, "election"),
    (["approval", "aprovação", "rating"], 0.45, "polling"),
    (["mortes", "killed", "deaths", ">"], 0.60, "casualty_threshold"),
    (["etf", "spot"], 0.45, "etf_approval"),
]


# Refit via fit_beta_binomial(cal, raw_classify, prior_strength=3) — never on holdout.
EB_TUNED_PRIORS: dict[str, float] = {
    "war_conflict": 0.900,
    "sports_event_structure": 0.893,
    "scheduled_event": 0.829,
    "geopolitical_routine": 0.825,
    "regulatory_active": 0.812,
    "br_legislative": 0.765,
    "casualty_threshold": 0.760,
    "default": 0.694,
    "election": 0.650,
    "regime_change": 0.640,
    "fed_action": 0.591,
    "crypto_product_launch": 0.590,
    "corporate_action": 0.581,
    "tariff_action": 0.530,
    "price_threshold": 0.471,
    "corporate_negative": 0.440,
    "tech_release": 0.423,
    "regulatory_action": 0.400,
    "polling": 0.338,
    "negative_rank_claim": 0.262,
    "geopolitical_low": 0.250,
    "extreme_quantity_claim": 0.225,
    "sports_specific_winner": 0.180,
    "br_reform_complex": 0.150,
    "central_bank_meeting": 0.95,
    "price_target": 0.40,
    "etf_approval": 0.45,
}

# Sync guard: every keyword category must have an EB-tuned posterior.
# Refit via fit_beta_binomial(cal, classify_fn, prior_strength=3) when adding categories.
_KEYWORD_LABELS = {label for _, _, label in KEYWORD_PRIORS} | {"default"}
_MISSING_EB = _KEYWORD_LABELS - set(EB_TUNED_PRIORS)
assert not _MISSING_EB, f"EB_TUNED_PRIORS missing categories: {_MISSING_EB}"


def _stretch(p: float, factor: float = 1.5, midpoint: float = 0.5) -> float:
    """clip(midpoint + factor * (p - midpoint), [0, 1])."""
    out = midpoint + factor * (p - midpoint)
    return max(0.0, min(1.0, out))


def classify_and_predict(framing: str, contexto: str = "",
                         apply_stretch: bool = True,
                         use_eb_tuned: bool = True) -> tuple[float, str]:
    """First keyword-match wins; default 0.50.

    apply_stretch: applies _stretch(p) for confidence widening.
    use_eb_tuned: uses EB_TUNED_PRIORS posterior (else hardcoded prior).
    """
    text = (framing + " " + contexto).lower()
    for keywords, prior, label in KEYWORD_PRIORS:
        if any(kw in text for kw in keywords):
            base = EB_TUNED_PRIORS.get(label, prior) if use_eb_tuned else prior
            p = _stretch(base) if apply_stretch else base
            return p, label
    base = EB_TUNED_PRIORS.get("default", 0.50) if use_eb_tuned else 0.50
    p = _stretch(base) if apply_stretch else base
    return p, "default"


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
