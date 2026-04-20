"""
Calibração via grid search — Onda 8.

Otimiza hiperparâmetros do predictor (boost de keyword, offset de prior)
minimizando Brier score no dataset de treino.
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.backtest.dataset import carregar_dataset
from engine.backtest.metricas import brier_score


@dataclass
class ResultadoCalibracao:
    dataset: str
    parametros_otimos: dict
    brier_otimo: float
    brier_default: float
    ganho_pct: float


def _predict_com_params(contexto: str, prior: float, boost_pos: float, boost_neg: float) -> float:
    ctx = contexto.lower()
    b = 0.0
    kws_pos = ["forte", "crescimento", "vitória", "apoio massivo",
               "rejeitado concorrente", "campanha robusta"]
    kws_neg = ["crise", "escândalo", "rejeição", "perda", "fraco", "contestação"]
    for k in kws_pos:
        if k in ctx:
            b += boost_pos
    for k in kws_neg:
        if k in ctx:
            b -= boost_neg
    return max(0.01, min(0.99, prior + b))


def grid_search_simples(dataset: str, grid_resolution: int = 5, base_dir: str = "data/backtest") -> dict:
    """
    Varre grid 2D (boost_pos, boost_neg) ∈ [0, 0.3], encontra mínimo Brier.
    Retorna dict com params ótimos + comparação com default (0.1, 0.1).
    """
    ds = carregar_dataset(dataset, base_dir=base_dir)
    passos = [i / (grid_resolution * 2) for i in range(1, grid_resolution + 1)]  # 0.1 .. 0.5

    melhor = (float("inf"), {"boost_pos": 0.1, "boost_neg": 0.1})
    for bp in passos:
        for bn in passos:
            probs = [_predict_com_params(e.contexto, e.prior, bp, bn) for e in ds.eventos]
            outcomes = [e.outcome_real for e in ds.eventos]
            b = brier_score(probs, outcomes)
            if b < melhor[0]:
                melhor = (b, {"boost_pos": bp, "boost_neg": bn})

    # Default baseline
    probs_def = [_predict_com_params(e.contexto, e.prior, 0.1, 0.1) for e in ds.eventos]
    brier_def = brier_score(probs_def, [e.outcome_real for e in ds.eventos])
    ganho = (brier_def - melhor[0]) / brier_def * 100 if brier_def > 0 else 0

    return {
        "dataset": ds.nome,
        "parametros_otimos": melhor[1],
        "brier_otimo": melhor[0],
        "brier_default": brier_def,
        "ganho_pct": round(ganho, 2),
    }
