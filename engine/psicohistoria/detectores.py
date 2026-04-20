"""
Detectores de anomalias — "Mules" em termos asimovianos.

Na ficção, The Mule é um mutante cujas habilidades não estavam previstas no
Plano de Seldon, causando desvio massivo. Aqui, detectamos:

    - Eventos de baixíssima probabilidade prevista que ocorreram na realidade
    - Agentes (habitantes) cujo comportamento destoa do agregado
    - Transições de estado não catalogadas no grafo

Estes são sinais de estresse ou colapso do modelo e sugerem recalibração.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from engine.psicohistoria.grafo_eventos import GrafoPsicohistoria


@dataclass
class MuleEvento:
    tipo: str                      # "transicao_rara", "agente_discrepante", "cascata_inesperada"
    descricao: str
    passo: int
    z_score: float                 # quão anômalo (desvios-padrão)
    evidencias: list[str]          # IDs/refs


def detectar_mule(
    trajetoria_real: list[str],
    trajetoria_prevista: np.ndarray,
    grafo: GrafoPsicohistoria,
    z_score_limite: float = 3.0,
) -> list[MuleEvento]:
    """
    Compara trajetória real vs distribuição prevista a cada passo.
    Se probabilidade prevista do estado observado for < e^{-z*σ}, sinaliza Mule.

    trajetoria_prevista: shape (T, n_estados) — output de prever_trajetoria ou plano
    """
    mules: list[MuleEvento] = []
    T = min(len(trajetoria_real), trajetoria_prevista.shape[0])
    for t in range(T):
        idx_real = grafo.estado_para_index(trajetoria_real[t])
        p_previsto = trajetoria_prevista[t, idx_real]
        if p_previsto < np.exp(-z_score_limite * 1.5):
            z = -np.log(max(p_previsto, 1e-12)) / 1.5
            mules.append(MuleEvento(
                tipo="transicao_rara",
                descricao=f"estado '{trajetoria_real[t]}' no passo {t} tinha prob. prevista {p_previsto:.4f}",
                passo=t,
                z_score=float(z),
                evidencias=[trajetoria_real[t]],
            ))
    return mules


def criticidade_evento(
    grafo: GrafoPsicohistoria,
    estado: str,
) -> float:
    """
    Criticidade = quão reversível é sair deste estado (fraction of outgoing prob).

    Alta criticidade (prob alta de estar em loop ou estados absorventes)
    = mais difícil de sair.
    Retorna valor em [0, 1]. 1 = totalmente absorvente.
    """
    if grafo.matriz is None or estado not in grafo._idx_de:
        return 0.0
    i = grafo.estado_para_index(estado)
    return float(grafo.matriz[i, i])


def agentes_anomalos_por_comportamento(
    comportamentos: dict[str, dict[str, float]],
    n_desvios: float = 2.5,
) -> list[str]:
    """
    Detecta agentes cujos atributos (saída por fase, custo/step, taxa resposta)
    desviam significativamente da média populacional.

    comportamentos[agente_id] = {metric: value}
    Retorna IDs de agentes z-score > n_desvios em pelo menos 1 métrica.
    """
    if not comportamentos:
        return []
    metricas = set()
    for d in comportamentos.values():
        metricas.update(d.keys())
    agentes_anomalos = set()
    for m in metricas:
        valores = [d.get(m, 0.0) for d in comportamentos.values()]
        if not valores:
            continue
        media = float(np.mean(valores))
        dp = float(np.std(valores)) or 1e-9
        for aid, d in comportamentos.items():
            z = abs((d.get(m, 0.0) - media) / dp)
            if z > n_desvios:
                agentes_anomalos.add(aid)
    return sorted(agentes_anomalos)
