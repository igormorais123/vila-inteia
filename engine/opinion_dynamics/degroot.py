"""
DeGroot linear consensus model.

Referência: DeGroot (1974), Reaching a Consensus.

Cada agente i tem crença x_i no intervalo [0, 1].
Matriz W estocástica (linhas somam 1) representa confiança: W[i, j] = quanto
o agente i pondera a crença do agente j.

Atualização: x^{t+1} = W @ x^t

Converge para consenso (todos acreditam no mesmo valor) se W é:
    - estocástica
    - irredutível
    - aperiódica
"""

from __future__ import annotations

import numpy as np


def degroot_step(crencas: np.ndarray, W: np.ndarray) -> np.ndarray:
    """
    Um passo de atualização DeGroot.

    crencas: shape (n,) — crenças atuais em [0, 1]
    W: shape (n, n) — matriz de confiança, linhas somam 1

    Retorna novas crenças.
    """
    if crencas.ndim != 1 or W.ndim != 2:
        raise ValueError("dims incorretas")
    if W.shape[0] != W.shape[1] or W.shape[0] != crencas.shape[0]:
        raise ValueError("shape mismatch")
    return W @ crencas


def degroot_convergencia(
    crencas_inicial: np.ndarray,
    W: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-8,
) -> tuple[np.ndarray, int]:
    """
    Itera DeGroot até estabilidade.
    Retorna (crenças finais, iterações).
    """
    cr = crencas_inicial.copy()
    for it in range(max_iter):
        nova = degroot_step(cr, W)
        if np.abs(nova - cr).max() < tol:
            return nova, it
        cr = nova
    return cr, max_iter


def matriz_confianca_vila(
    habitantes: list[dict],
    relacoes: dict[str, dict[str, str]],
    peso_mentor: float = 0.45,
    peso_rival: float = 0.05,
    peso_colega: float = 0.1,
) -> np.ndarray:
    """
    Monta matriz W estocástica a partir das relações da Vila.

    habitantes: lista de dicts com 'id'
    relacoes[agente_a][agente_b] = tipo ("mentor", "rival", "colega", "discipulo")

    Auto-confiança = 1 - soma das confianças alheias (garante linha soma 1).
    """
    n = len(habitantes)
    W = np.zeros((n, n))
    id_para_idx = {h["id"]: i for i, h in enumerate(habitantes)}
    mapa_pesos = {"mentor": peso_mentor, "rival": peso_rival, "colega": peso_colega}

    for i, h in enumerate(habitantes):
        rel_i = relacoes.get(h["id"], {})
        for outro_id, tipo in rel_i.items():
            if outro_id in id_para_idx:
                j = id_para_idx[outro_id]
                W[i, j] = mapa_pesos.get(tipo, 0)
        resto = W[i].sum()
        W[i, i] = max(0, 1 - resto)
        if W[i].sum() > 0:
            W[i] /= W[i].sum()
    return W
