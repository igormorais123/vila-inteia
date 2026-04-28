"""Online ensemble of 5 forecasters via AdaHedge.

Models:
1. Vila — engine/post_cutoff_classifier.classify_and_predict (apply_stretch, eb_tuned)
2. Base-rate — overall TRAIN base rate (0.68)
3. Lindy — engine/lindy.lindy_for_event; falls back to base rate if None
4. Market-implied — event's `probabilidade_prior` (treated as crowd-sourced market prior)
5. TF-IDF kNN — engine/tfidf_neighbors over Q1 TRAIN events (lazy build)

Online: weights start uniform and update event-by-event.
Regret = ensemble_loss - best_model_loss.
"""

from __future__ import annotations

from typing import Optional

from engine.adahedge import AdaHedge
from engine.lindy import lindy_for_event
from engine.post_cutoff_classifier import classify_and_predict
from engine.tfidf_neighbors import build_tfidf_index, tfidf_predict


BASE_RATE = 0.68  # overall TRAIN base rate


def model_vila(framing: str, contexto: str = "",
               prior_field: Optional[float] = None) -> float:
    p, _ = classify_and_predict(framing, contexto,
                                apply_stretch=True, use_eb_tuned=True)
    return p


def model_base_rate(framing: str, contexto: str = "",
                    prior_field: Optional[float] = None) -> float:
    return BASE_RATE


def model_lindy(framing: str, contexto: str = "",
                prior_field: Optional[float] = None) -> float:
    p = lindy_for_event(framing, contexto)
    if p is None:
        return BASE_RATE
    return p


def model_market_implied(framing: str, contexto: str = "",
                         prior_field: Optional[float] = None) -> float:
    if prior_field is None:
        return BASE_RATE
    try:
        return max(0.0, min(1.0, float(prior_field)))
    except (TypeError, ValueError):
        return BASE_RATE


# TF-IDF kNN over Q1 TRAIN. Lazily built and cached.
_TFIDF_INDEX: Optional[dict] = None


def _q1_train_paths() -> list[str]:
    return [
        "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q1_2026.csv",
        "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q1_2026_v2.csv",
    ]


def _load_q1_train() -> list[dict]:
    import csv as _csv
    out: list[dict] = []
    for fp in _q1_train_paths():
        try:
            with open(fp) as f:
                for r in _csv.DictReader(f):
                    try:
                        out.append({
                            "outcome_framing": r.get("outcome_framing")
                                or r.get("framing", ""),
                            "contexto": r.get("contexto", ""),
                            "outcome_real": int(r["outcome_real"]),
                        })
                    except (ValueError, KeyError):
                        pass
        except FileNotFoundError:
            continue
    return out


def get_tfidf_index() -> dict:
    """Lazy-loaded Q1 TRAIN TF-IDF index. Cached at module level."""
    global _TFIDF_INDEX
    if _TFIDF_INDEX is None:
        _TFIDF_INDEX = build_tfidf_index(_load_q1_train())
    return _TFIDF_INDEX


def set_tfidf_index(index: dict) -> None:
    """Override the cached index (useful for tests)."""
    global _TFIDF_INDEX
    _TFIDF_INDEX = index


def model_tfidf(framing: str, contexto: str = "",
                prior_field: Optional[float] = None) -> float:
    idx = get_tfidf_index()
    if idx.get("n_docs", 0) == 0:
        return BASE_RATE
    return tfidf_predict(framing, contexto, idx, k=5, default=BASE_RATE)


MODELS = {
    "vila": model_vila,
    "base_rate": model_base_rate,
    "lindy": model_lindy,
    "market": model_market_implied,
    "tfidf": model_tfidf,
}


def evaluate_ensemble_4(events: list) -> dict:
    """Run AdaHedge online over the 4 models on events.

    events: list of dicts with keys outcome_framing/framing, contexto,
            outcome_real, probabilidade_prior.
    """
    agg = AdaHedge(list(MODELS.keys()))
    n = 0
    hits = 0
    brier_ensemble = 0.0
    per_model_brier = {name: 0.0 for name in MODELS}
    per_model_hits = {name: 0 for name in MODELS}

    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        prior = e.get("probabilidade_prior")

        preds = {name: fn(framing, contexto, prior)
                 for name, fn in MODELS.items()}
        p_ens = agg.predict(preds)

        n += 1
        if (p_ens >= 0.5) == bool(y):
            hits += 1
        brier_ensemble += (p_ens - y) ** 2

        for name, p_m in preds.items():
            per_model_brier[name] += (p_m - y) ** 2
            if (p_m >= 0.5) == bool(y):
                per_model_hits[name] += 1

        agg.update(preds, int(y))

    if n == 0:
        return {"n": 0, "error": "no events"}

    per_model_brier_avg = {name: v / n for name, v in per_model_brier.items()}
    per_model_acc = {name: per_model_hits[name] / n for name in MODELS}

    best_name = min(per_model_brier_avg.items(), key=lambda kv: kv[1])[0]
    best_brier = per_model_brier_avg[best_name]
    ens_brier = brier_ensemble / n
    regret = ens_brier - best_brier

    return {
        "n": n,
        "hits": hits,
        "acc": hits / n,
        "brier": ens_brier,
        "per_model_brier": per_model_brier_avg,
        "per_model_acc": per_model_acc,
        "best_model": best_name,
        "best_model_brier": best_brier,
        "regret": regret,
        "final_weights": agg._weights(),
        "final_eta": agg._eta(),
    }
