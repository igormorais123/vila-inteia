"""
Do-calculus simplificado para modelos Markov da Vila.

Operações:
    do(X=x): força distribuição atual a ter X em valor x, propaga pela cadeia
    counterfactual: "teria acontecido Y se X fosse x' em vez de x?"
    ATE: average treatment effect = E[Y|do(X=1)] - E[Y|do(X=0)]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class VariavelCausal:
    """Variável discreta: id + lista de valores possíveis."""
    id: str
    valores: list[Any]

    @property
    def cardinalidade(self) -> int:
        return len(self.valores)


def intervir(
    matriz_transicao: np.ndarray,
    estado_forcado_idx: int,
    n_estados: int,
) -> np.ndarray:
    """
    do(X = estado_forcado): retorna matriz com linhas correspondentes ao
    estado forçado tendo self-loop prob 1.0 (sistema fica preso no estado).

    Esta é a forma canônica de intervenção em Markov chain.
    """
    if not 0 <= estado_forcado_idx < n_estados:
        raise ValueError(f"idx fora: {estado_forcado_idx}")
    M = matriz_transicao.copy()
    # Força linha do estado forçado a ser identidade
    M[estado_forcado_idx] = 0.0
    M[estado_forcado_idx, estado_forcado_idx] = 1.0
    return M


def counterfactual(
    matriz: np.ndarray,
    trajetoria_factual: list[int],
    ponto_intervencao: int,
    valor_alternativo: int,
    passos_depois: int = 10,
) -> dict:
    """
    "Se no step T (ponto_intervencao) o estado fosse Y (valor_alternativo)
    em vez de X (trajetoria_factual[T]), qual seria trajetória?"

    Retorna:
        trajetoria_factual_futura: cálculo real da cadeia sob factual
        trajetoria_counterfactual: cálculo sob intervenção
        divergencia: TV distance entre distribuições no último step
    """
    if ponto_intervencao >= len(trajetoria_factual):
        raise ValueError("ponto de intervenção fora da trajetória")
    n = matriz.shape[0]
    # Distribuição factual partindo do estado real
    dist_factual = np.zeros(n)
    dist_factual[trajetoria_factual[ponto_intervencao]] = 1.0
    dist_cf = np.zeros(n)
    dist_cf[valor_alternativo] = 1.0

    hist_factual = [dist_factual.copy()]
    hist_cf = [dist_cf.copy()]
    for _ in range(passos_depois):
        dist_factual = dist_factual @ matriz
        dist_cf = dist_cf @ matriz
        hist_factual.append(dist_factual.copy())
        hist_cf.append(dist_cf.copy())

    tv = 0.5 * float(np.abs(dist_factual - dist_cf).sum())
    return {
        "trajetoria_factual": [d.tolist() for d in hist_factual],
        "trajetoria_counterfactual": [d.tolist() for d in hist_cf],
        "divergencia_tv_final": tv,
        "estado_original": trajetoria_factual[ponto_intervencao],
        "estado_alternativo": valor_alternativo,
        "passos": passos_depois,
    }


def ate(
    matriz: np.ndarray,
    estado_tratamento_idx: int,
    estado_controle_idx: int,
    estado_outcome_idx: int,
    horizonte: int = 20,
) -> float:
    """
    Average Treatment Effect:
        ATE = P(Y | do(X=tratamento)) - P(Y | do(X=controle))

    em horizonte N passos, onde Y é outcome_idx.
    Positivo: tratamento aumenta prob do outcome. Negativo: diminui.
    """
    n = matriz.shape[0]

    def prob_outcome_sob_do(idx_forcado: int) -> float:
        dist = np.zeros(n)
        dist[idx_forcado] = 1.0
        M = matriz  # intervenção não precisa modificar linha se dist já é one-hot em t=0
        for _ in range(horizonte):
            dist = dist @ M
        return float(dist[estado_outcome_idx])

    p_tratado = prob_outcome_sob_do(estado_tratamento_idx)
    p_controle = prob_outcome_sob_do(estado_controle_idx)
    return p_tratado - p_controle


@dataclass
class ResultadoIntervencao:
    estado_forcado: int
    probabilidades_finais: np.ndarray
    estado_mais_provavel: int
    prob_mais_provavel: float


def intervention_sweep(
    matriz: np.ndarray,
    estado_outcome_idx: int,
    horizonte: int = 20,
) -> list[ResultadoIntervencao]:
    """
    Para cada possível intervenção (forçar cada estado), mede prob do outcome.
    Retorna ordenado por prob do outcome (maior impacto primeiro).
    """
    n = matriz.shape[0]
    resultados = []
    for i in range(n):
        dist = np.zeros(n)
        dist[i] = 1.0
        for _ in range(horizonte):
            dist = dist @ matriz
        idx_max = int(np.argmax(dist))
        resultados.append(ResultadoIntervencao(
            estado_forcado=i,
            probabilidades_finais=dist,
            estado_mais_provavel=idx_max,
            prob_mais_provavel=float(dist[idx_max]),
        ))
    # Ordena por prob do outcome
    resultados.sort(key=lambda r: r.probabilidades_finais[estado_outcome_idx],
                     reverse=True)
    return resultados
