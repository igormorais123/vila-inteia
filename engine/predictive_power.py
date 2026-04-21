"""
Onda 82: predictive power scoring.

Compara accuracy do Markov de Vila contra baselines:
- random: distribuição uniforme
- naive_last_state: assume próximo estado = último observado (one-hot)

Métricas (proper scoring rules):
- Brier score (lower better, range [0, 2])
- Log loss (lower better)
- Accuracy top-1

Diferencial vs MiroFish: MiroFish prevê. Vila quantifica QUANTO MELHOR
prevê vs baselines triviais. Skill score positivo = Vila supera baseline.

Backtest: pega histórico de N steps, faz walk-forward predict-1-step-ahead,
compara predição vs verdade.
"""

from __future__ import annotations

from typing import Any
import numpy as np


def brier_score(prob_dist: np.ndarray, observado_idx: int) -> float:
    """Brier score multi-classe = sum((p_i - y_i)^2). Lower=better."""
    n = len(prob_dist)
    y = np.zeros(n)
    y[observado_idx] = 1.0
    return float(np.sum((prob_dist - y) ** 2))


def log_loss(prob_dist: np.ndarray, observado_idx: int, eps: float = 1e-12) -> float:
    """Cross-entropy. Lower=better."""
    p = max(float(prob_dist[observado_idx]), eps)
    return -float(np.log(p))


def accuracy_top1(prob_dist: np.ndarray, observado_idx: int) -> int:
    return int(int(np.argmax(prob_dist)) == observado_idx)


def skill_score(score_modelo: float, score_baseline: float, eps: float = 1e-12) -> float:
    """
    Skill = 1 - score_modelo / score_baseline.
    >0: modelo melhor. =0: igual. <0: pior.
    Para scores onde lower=better.
    """
    if abs(score_baseline) < eps:
        return 0.0
    return 1.0 - score_modelo / score_baseline


def avaliar_predictive_power(
    estados_observados: list[str],
    rastreador: Any | None = None,
) -> dict:
    """
    Walk-forward backtest.
    Para cada step t (a partir do 1º), prediz t+1 a partir de t,
    calcula scores de Markov vs random vs naive.

    Args:
        estados_observados: lista de estados (≥2 pra calcular ≥1 score).
        rastreador: ignored (compat futuro).

    Returns dict:
        n_predicoes (int)
        markov: {brier_avg, log_loss_avg, accuracy}
        random: {idem}
        naive_last_state: {idem}
        skill_brier_vs_random, skill_brier_vs_naive
        skill_logloss_vs_random, skill_logloss_vs_naive
    """
    if len(estados_observados) < 2:
        return {
            "n_predicoes": 0,
            "markov": None,
            "random": None,
            "naive_last_state": None,
            "skill_brier_vs_random": 0.0,
            "skill_brier_vs_naive": 0.0,
            "skill_logloss_vs_random": 0.0,
            "skill_logloss_vs_naive": 0.0,
            "aviso": "min 2 estados para 1 predição",
        }

    from engine.psicohistoria.grafo_eventos import construir_grafo_vila

    grafo = construir_grafo_vila()
    estados_ordem = list(grafo.estados.keys())
    n_estados = len(estados_ordem)

    estados_validos = [e for e in estados_observados if e in grafo.estados]
    if len(estados_validos) < 2:
        return {
            "n_predicoes": 0,
            "markov": None,
            "aviso": f"sem estados válidos ({estados_observados})",
        }

    M = grafo.matriz
    p_uniforme = np.ones(n_estados) / n_estados

    scores_markov = {"brier": [], "log_loss": [], "acc": []}
    scores_random = {"brier": [], "log_loss": [], "acc": []}
    scores_naive = {"brier": [], "log_loss": [], "acc": []}

    for i in range(len(estados_validos) - 1):
        atual = estados_validos[i]
        proximo = estados_validos[i + 1]
        idx_atual = grafo.estado_para_index(atual)
        idx_proximo = grafo.estado_para_index(proximo)

        # Markov: predição = linha do estado atual
        pred_markov = M[idx_atual]
        scores_markov["brier"].append(brier_score(pred_markov, idx_proximo))
        scores_markov["log_loss"].append(log_loss(pred_markov, idx_proximo))
        scores_markov["acc"].append(accuracy_top1(pred_markov, idx_proximo))

        # Random: uniforme
        scores_random["brier"].append(brier_score(p_uniforme, idx_proximo))
        scores_random["log_loss"].append(log_loss(p_uniforme, idx_proximo))
        scores_random["acc"].append(accuracy_top1(p_uniforme, idx_proximo))

        # Naive: probabilidade 1.0 no estado atual
        pred_naive = np.zeros(n_estados)
        pred_naive[idx_atual] = 1.0
        scores_naive["brier"].append(brier_score(pred_naive, idx_proximo))
        scores_naive["log_loss"].append(log_loss(pred_naive, idx_proximo))
        scores_naive["acc"].append(accuracy_top1(pred_naive, idx_proximo))

    def _avg(d):
        return {
            "brier_avg": float(np.mean(d["brier"])),
            "log_loss_avg": float(np.mean(d["log_loss"])),
            "accuracy": float(np.mean(d["acc"])),
        }

    avg_markov = _avg(scores_markov)
    avg_random = _avg(scores_random)
    avg_naive = _avg(scores_naive)

    return {
        "n_predicoes": len(scores_markov["brier"]),
        "n_estados": n_estados,
        "estados_ordem": estados_ordem,
        "markov": avg_markov,
        "random": avg_random,
        "naive_last_state": avg_naive,
        "skill_brier_vs_random": skill_score(
            avg_markov["brier_avg"], avg_random["brier_avg"]),
        "skill_brier_vs_naive": skill_score(
            avg_markov["brier_avg"], avg_naive["brier_avg"]),
        "skill_logloss_vs_random": skill_score(
            avg_markov["log_loss_avg"], avg_random["log_loss_avg"]),
        "skill_logloss_vs_naive": skill_score(
            avg_markov["log_loss_avg"], avg_naive["log_loss_avg"]),
    }
