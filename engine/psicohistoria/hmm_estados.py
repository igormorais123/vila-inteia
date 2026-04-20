"""
Descoberta não-supervisionada de estados via HMM (Onda 15).

Em vez de aceitar os 8 estados canônicos heurísticos, aprende K estados
latentes diretamente das métricas observadas por step. Aplica K-Means
+ HMM-like smoothing.

Uso:
    from engine.psicohistoria.hmm_estados import descobrir_estados
    r = descobrir_estados(metricas_por_step, k=8)
    print(r.labels_por_step)    # [0, 0, 2, 2, 5, ...]
    print(r.centroides)         # features médias de cada estado
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class EstadoLatente:
    id: int
    n_membros: int
    centroide: np.ndarray             # vetor de features médias
    rotulo_auto: str = ""             # nome inferido (ex: "alta_atividade", "latencia")


@dataclass
class ResultadoHMM:
    k: int
    labels_por_step: list[int]
    estados_latentes: list[EstadoLatente]
    inercia: float                    # soma de distâncias ao centroide (quanto menor, melhor)
    iteracoes: int


def _extrair_features(metricas: list[dict]) -> np.ndarray:
    """Converte dict de métricas em matriz NxD."""
    features = []
    for m in metricas:
        features.append([
            m.get("n_conversas", 0),
            m.get("n_reflexoes", 0),
            m.get("n_agentes_ativos", 0),
            m.get("n_agentes_latentes", 0),
            m.get("polarizacao_media", 0),
            m.get("gini_economia", 0),
            m.get("propostas_constituintes_ativas", 0),
            m.get("contribuicoes_ao_desafio", 0),
        ])
    return np.array(features, dtype=float)


def _normalizar(X: np.ndarray) -> np.ndarray:
    """Z-score por feature (robusto a magnitudes diferentes)."""
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std = np.where(std < 1e-9, 1.0, std)
    return (X - mean) / std


def kmeans_simples(
    X: np.ndarray,
    k: int,
    max_iter: int = 100,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, float, int]:
    """K-Means puro-numpy. Retorna (labels, centroides, inércia, iteracoes)."""
    rng = np.random.default_rng(seed)
    n, d = X.shape
    if n < k:
        k = max(1, n)
    idx_iniciais = rng.choice(n, size=k, replace=False)
    centroides = X[idx_iniciais].copy()
    labels = np.zeros(n, dtype=int)

    for it in range(max_iter):
        # Atribuir: cada ponto → centroide mais próximo
        dists = np.linalg.norm(X[:, None, :] - centroides[None, :, :], axis=2)
        novo_labels = dists.argmin(axis=1)
        if np.all(novo_labels == labels) and it > 0:
            labels = novo_labels
            break
        labels = novo_labels
        # Atualizar centroides
        for j in range(k):
            membros = X[labels == j]
            if len(membros) > 0:
                centroides[j] = membros.mean(axis=0)

    # Inércia total
    inercia = float(np.sum([np.linalg.norm(X[i] - centroides[labels[i]]) ** 2
                             for i in range(n)]))
    return labels, centroides, inercia, it + 1


def smoothing_hmm_like(labels: np.ndarray, janela: int = 3) -> np.ndarray:
    """
    Smoothing temporal: cada label vira moda dos vizinhos numa janela.
    Emula comportamento HMM (estados não pulam aleatoriamente).
    """
    n = len(labels)
    if n == 0:
        return labels
    novo = labels.copy()
    half = max(1, janela // 2)
    for i in range(n):
        ini = max(0, i - half)
        fim = min(n, i + half + 1)
        vizinhos = labels[ini:fim]
        # moda simples
        vals, counts = np.unique(vizinhos, return_counts=True)
        novo[i] = vals[counts.argmax()]
    return novo


def inferir_rotulo(centroide: np.ndarray) -> str:
    """Heurística: nome baseado em features dominantes."""
    FEATS = ["n_conversas", "n_reflexoes", "n_ativos", "n_latentes",
             "polarizacao", "gini", "propostas_const", "contribs"]
    top = np.argsort(centroide)[-2:][::-1]
    return f"{FEATS[top[0]]}↑+{FEATS[top[1]]}↑"


def descobrir_estados(
    metricas_por_step: list[dict],
    k: int = 8,
    smoothing_janela: int = 3,
    seed: int = 42,
) -> ResultadoHMM:
    """Pipeline completo: features → normalização → K-Means → smoothing."""
    if len(metricas_por_step) < k:
        k = max(2, len(metricas_por_step))

    X = _extrair_features(metricas_por_step)
    Xn = _normalizar(X)
    labels, centroides, inercia, its = kmeans_simples(Xn, k, seed=seed)
    labels = smoothing_hmm_like(labels, janela=smoothing_janela)

    estados = []
    for j in range(k):
        membros = (labels == j).sum()
        # Denormalizar para reportar centroide nas unidades originais
        mean = X.mean(axis=0)
        std = X.std(axis=0)
        std = np.where(std < 1e-9, 1.0, std)
        c_real = centroides[j] * std + mean
        estados.append(EstadoLatente(
            id=j, n_membros=int(membros), centroide=c_real,
            rotulo_auto=inferir_rotulo(centroides[j]),
        ))
    return ResultadoHMM(
        k=k, labels_por_step=labels.tolist(),
        estados_latentes=estados, inercia=inercia, iteracoes=its,
    )
