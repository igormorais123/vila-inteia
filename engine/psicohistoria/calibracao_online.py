"""
Calibração online da matriz de transição Markov a partir de trajetórias reais.

Onda 13. Substitui baseline sintético da Vila por matriz aprendida dos
dados reais coletados durante execução.

Estratégias:
    1. Contagem simples (MLE): M[i,j] = count(i→j) / count(i→*)
    2. Laplace smoothing: adiciona α a cada contagem (evita prob=0)
    3. Atualização online: EWMA pondera recente sobre antigo

Integra com engine.psicohistoria.grafo_eventos.GrafoPsicohistoria.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict

import numpy as np

from engine.psicohistoria.grafo_eventos import (
    GrafoPsicohistoria, Estado, construir_grafo_vila,
)


@dataclass
class CalibracaoResultado:
    n_transicoes: int
    estados_observados: list[str]
    matriz_original: np.ndarray
    matriz_calibrada: np.ndarray
    divergencia_frobenius: float
    cobertura_pct: float   # % dos 8 estados canônicos observados


def mle_simples(
    grafo: GrafoPsicohistoria,
    trajetoria: list[str],
    alpha: float = 0.0,
) -> np.ndarray:
    """
    Estima M via contagem simples (+ Laplace smoothing opcional).

    alpha=0: MLE puro (prob=0 p/ transições não observadas)
    alpha>0: smoothing — adiciona alpha a cada célula antes de normalizar
    """
    if grafo.matriz is None:
        raise ValueError("grafo sem matriz")
    n = len(grafo.estados)
    counts = np.full((n, n), alpha, dtype=float)
    for a, b in zip(trajetoria[:-1], trajetoria[1:]):
        if a in grafo._idx_de and b in grafo._idx_de:
            i, j = grafo._idx_de[a], grafo._idx_de[b]
            counts[i, j] += 1
    # Normalizar linhas
    M = counts.copy()
    for i in range(n):
        s = M[i].sum()
        if s > 0:
            M[i] /= s
        else:
            M[i, i] = 1.0  # self-loop absorvente
    return M


def ewma_online(
    matriz_atual: np.ndarray,
    nova_transicao: tuple[str, str],
    grafo: GrafoPsicohistoria,
    peso_novo: float = 0.05,
) -> np.ndarray:
    """
    Atualização exponencial: M' = (1-α)·M + α·one_hot(observação)

    Preserva matriz estocástica ao longo do tempo.
    """
    a, b = nova_transicao
    if a not in grafo._idx_de or b not in grafo._idx_de:
        return matriz_atual
    i, j = grafo._idx_de[a], grafo._idx_de[b]
    n = matriz_atual.shape[0]
    one_hot = np.zeros((n, n))
    one_hot[i, j] = 1.0
    # Update apenas a linha i
    nova = matriz_atual.copy()
    nova[i] = (1 - peso_novo) * nova[i] + peso_novo * one_hot[i]
    # Re-normaliza (eventuais erros de ponto flutuante)
    s = nova[i].sum()
    if s > 0:
        nova[i] /= s
    return nova


def calibrar(
    trajetoria: list[str],
    metodo: str = "mle",
    alpha: float = 0.1,
) -> CalibracaoResultado:
    """
    Retorna matriz calibrada + comparação com baseline.

    metodo: "mle" (puro) | "laplace" (smoothing) | "ewma" (online)
    """
    grafo = construir_grafo_vila()
    matriz_original = grafo.matriz.copy()

    if metodo == "mle":
        M_novo = mle_simples(grafo, trajetoria, alpha=0.0)
    elif metodo == "laplace":
        M_novo = mle_simples(grafo, trajetoria, alpha=alpha)
    elif metodo == "ewma":
        M_novo = matriz_original.copy()
        for a, b in zip(trajetoria[:-1], trajetoria[1:]):
            M_novo = ewma_online(M_novo, (a, b), grafo, peso_novo=alpha)
    else:
        raise ValueError(f"método desconhecido: {metodo}")

    n_trans = len(trajetoria) - 1 if len(trajetoria) >= 2 else 0
    estados_vistos = sorted(set(trajetoria))
    cobertura = len(estados_vistos) / len(grafo.estados) * 100
    frob = float(np.linalg.norm(M_novo - matriz_original, "fro"))

    return CalibracaoResultado(
        n_transicoes=n_trans,
        estados_observados=estados_vistos,
        matriz_original=matriz_original,
        matriz_calibrada=M_novo,
        divergencia_frobenius=frob,
        cobertura_pct=cobertura,
    )


def perplexity(trajetoria: list[str], matriz: np.ndarray, grafo: GrafoPsicohistoria) -> float:
    """
    Perplexity da trajetória sob matriz M. Menor = M explica melhor dados.
    PP = exp(-1/N · sum_i log P(a_i+1 | a_i))
    """
    if len(trajetoria) < 2:
        return float("inf")
    eps = 1e-12
    log_total = 0.0
    N = 0
    for a, b in zip(trajetoria[:-1], trajetoria[1:]):
        if a not in grafo._idx_de or b not in grafo._idx_de:
            continue
        i, j = grafo._idx_de[a], grafo._idx_de[b]
        p = matriz[i, j]
        log_total += -np.log(max(p, eps))
        N += 1
    if N == 0:
        return float("inf")
    return float(np.exp(log_total / N))
