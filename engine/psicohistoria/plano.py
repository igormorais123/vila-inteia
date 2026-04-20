"""
Plano Seldon: trajetória agregada prevista para a Vila num horizonte longo.

Na ficção, o Plano é uma trajetória através da história galáctica com pontos
de crise previstos (Seldon Crises) que agentes não podem evitar mas podem
acelerar/retardar. Aqui: trajetória de distribuições de estado ao longo de
N passos, com "checkpoints" marcando mudanças de estado-modal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from engine.psicohistoria.grafo_eventos import GrafoPsicohistoria
from engine.psicohistoria.equacoes import prever_trajetoria


@dataclass
class CrisePrevista:
    passo: int
    estado_antes: str
    estado_depois: str
    probabilidade: float


@dataclass
class PlanoSeldon:
    horizonte: int
    estado_inicial: str
    trajetoria: np.ndarray                     # shape (horizonte + 1, n_estados)
    estados_modais: list[str]                  # estado mais provável em cada passo
    crises: list[CrisePrevista] = field(default_factory=list)
    destino_provavel: str = ""
    probabilidade_destino: float = 0.0


def plano_seldon(
    grafo: GrafoPsicohistoria,
    estado_inicial: str,
    horizonte: int = 500,
    threshold_crise: float = 0.05,
) -> PlanoSeldon:
    """
    Gera Plano de longo prazo. Identifica crises (mudanças de estado-modal).

    threshold_crise: probabilidade mínima de mudança para considerar uma crise.
    """
    traj = prever_trajetoria(grafo, estado_inicial, horizonte)
    estados_modais = [
        grafo.index_para_estado(int(np.argmax(traj[t])))
        for t in range(traj.shape[0])
    ]
    crises = []
    for t in range(1, len(estados_modais)):
        if estados_modais[t] != estados_modais[t - 1]:
            idx = grafo.estado_para_index(estados_modais[t])
            crises.append(CrisePrevista(
                passo=t,
                estado_antes=estados_modais[t - 1],
                estado_depois=estados_modais[t],
                probabilidade=float(traj[t, idx]),
            ))
    dest_idx = int(np.argmax(traj[-1]))
    return PlanoSeldon(
        horizonte=horizonte,
        estado_inicial=estado_inicial,
        trajetoria=traj,
        estados_modais=estados_modais,
        crises=crises,
        destino_provavel=grafo.index_para_estado(dest_idx),
        probabilidade_destino=float(traj[-1, dest_idx]),
    )


def divergencia_plano_realidade(
    plano: PlanoSeldon,
    trajetoria_real: list[str],
    grafo: GrafoPsicohistoria,
) -> dict:
    """
    Compara trajetória real observada vs plano previsto.

    Retorna:
        - passos_divergentes: quantos steps diferem do estado-modal
        - divergencia_kl: KL divergence média entre previsto e realidade
                          (realidade = one-hot do estado observado)
        - primeiro_desvio: índice do primeiro step divergente
    """
    if not trajetoria_real:
        return {"passos_divergentes": 0, "divergencia_kl": 0.0, "primeiro_desvio": -1}
    n = min(len(plano.estados_modais), len(trajetoria_real))
    divergentes = 0
    primeiro = -1
    kl_total = 0.0
    eps = 1e-9
    for t in range(n):
        if trajetoria_real[t] != plano.estados_modais[t]:
            divergentes += 1
            if primeiro == -1:
                primeiro = t
        # KL(real || plano)
        idx_real = grafo.estado_para_index(trajetoria_real[t])
        prob_previsto = plano.trajetoria[t, idx_real]
        kl_total += -np.log(max(prob_previsto, eps))
    return {
        "passos_divergentes": divergentes,
        "divergencia_kl_media": kl_total / n if n > 0 else 0.0,
        "primeiro_desvio": primeiro,
        "fracao_divergente": divergentes / n if n > 0 else 0.0,
    }
