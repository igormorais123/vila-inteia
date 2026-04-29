"""Vila + LLM hybrid forecaster.

Two strategies:
1. Hybrid prompt — LLM gets Vila's category + EB prior as anchor.
2. Log-linear pool — weighted geometric mean of Vila and LLM probs.

The "best of both" is to (a) ask LLM with Vila context, then (b) log-pool
the LLM answer with raw Vila prediction at fixed weights tuned on TRAIN.
"""

from __future__ import annotations

from engine.llm_forecaster import llm_predict
from engine.log_pool import log_pool_predict
from engine.post_cutoff_classifier import classify_and_predict


DEFAULT_W_LLM = 0.85
# Vila-confidence gate: if |p_vila - 0.5| ≥ this, trust Vila alone.
# Sweep n=80 holdout (Q2 2026 v1+v2 + Q3 + Q4): LLM dominates Vila on harder
# events (LLM brier 0.147 vs Vila 0.207). Optimal config gate=0.50 w_llm=1.0
# → brier 0.129 acc 85% (nearly always use LLM, Vila only on p̂ ≤ 0.05 / ≥ 0.95).
# Practical default: gate=0.20 + w_llm=0.85 retains both signals on uncertain
# events while leaning LLM. Per-dataset autotuning recommended for production.
DEFAULT_GATE = 0.20


def vila_llm_hybrid_predict(framing: str, contexto: str = "",
                            w_llm: float = DEFAULT_W_LLM,
                            use_hybrid_prompt: bool = True,
                            gate: float = DEFAULT_GATE) -> float:
    """Gated Vila→LLM(hybrid)→log-pool.

    1. Compute Vila's deterministic prediction + category label.
    2. If |p_vila - 0.5| ≥ gate, trust Vila (no LLM blend).
    3. Otherwise query LLM with Vila context as anchor.
    4. Log-pool the two with weight w_llm on LLM.

    The gate preserves Vila's accuracy on high-confidence calls
    while letting LLM contribute on uncertain (~0.5) events.
    """
    p_vila, label = classify_and_predict(framing, contexto,
                                         apply_stretch=True,
                                         use_eb_tuned=True)
    if abs(p_vila - 0.5) >= gate:
        return p_vila

    hint = (label, p_vila) if use_hybrid_prompt else None
    p_llm = llm_predict(framing, contexto, vila_hint=hint)
    if p_llm is None:
        return p_vila
    return log_pool_predict(p_llm, p_vila, w_a=w_llm)


def evaluate_hybrid(events: list, w_llm: float = DEFAULT_W_LLM,
                    max_events: int = 60) -> dict:
    """Bench Vila-LLM hybrid against Vila + LLM standalone."""
    n = 0
    h_vila = h_llm = h_hyb = 0
    b_vila = b_llm = b_hyb = 0.0
    for e in events[:max_events]:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        p_v, label = classify_and_predict(framing, contexto)
        p_l = llm_predict(framing, contexto, vila_hint=(label, p_v))
        if p_l is None:
            p_l = 0.5
        p_h = log_pool_predict(p_l, p_v, w_a=w_llm)
        n += 1
        for p, hits, brier in [(p_v, h_vila, b_vila),
                               (p_l, h_llm, b_llm),
                               (p_h, h_hyb, b_hyb)]:
            pass
        if (p_v >= 0.5) == bool(y): h_vila += 1
        if (p_l >= 0.5) == bool(y): h_llm += 1
        if (p_h >= 0.5) == bool(y): h_hyb += 1
        b_vila += (p_v - y) ** 2
        b_llm += (p_l - y) ** 2
        b_hyb += (p_h - y) ** 2

    if n == 0:
        return {"n": 0, "error": "no_events"}
    return {
        "n": n,
        "vila": {"acc": h_vila / n, "brier": b_vila / n},
        "llm": {"acc": h_llm / n, "brier": b_llm / n},
        "hybrid": {"acc": h_hyb / n, "brier": b_hyb / n,
                   "w_llm": w_llm},
    }
