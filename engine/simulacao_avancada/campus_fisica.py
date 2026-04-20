"""
Pathfinding + congestion para o campus de 19 locais.

Hoje, habitantes "teleportam" para locais em engine/cognitivo/executar.py.
Com esta camada, movimento respeita grafo do campus + congestão em tempo real.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field


@dataclass
class GrafoCampus:
    """
    Grafo não-direcionado do campus.
    vertices: set de local_id
    arestas: dict adj — {local_id: [(vizinho_id, peso), ...]}
    """
    vertices: set[str] = field(default_factory=set)
    arestas: dict[str, list[tuple[str, float]]] = field(default_factory=dict)

    def adicionar_aresta(self, a: str, b: str, peso: float = 1.0) -> None:
        self.vertices.add(a)
        self.vertices.add(b)
        self.arestas.setdefault(a, []).append((b, peso))
        self.arestas.setdefault(b, []).append((a, peso))


def rota_otima(
    grafo: GrafoCampus,
    origem: str,
    destino: str,
    congestao_atual: dict[str, float] | None = None,
    peso_congestao: float = 0.5,
) -> list[str]:
    """
    A* simplificado (Dijkstra + heurística opcional).
    congestao_atual[local_id] = ocupação atual do local (0 a inf)
    peso_congestao = quanto adicionar ao peso por unidade de congestão.
    Retorna lista de local_ids da rota. Lista vazia se inacessível.
    """
    if origem == destino:
        return [origem]
    if origem not in grafo.vertices or destino not in grafo.vertices:
        return []
    if congestao_atual is None:
        congestao_atual = {}

    dist = {v: float("inf") for v in grafo.vertices}
    dist[origem] = 0
    prev: dict[str, str | None] = {v: None for v in grafo.vertices}
    heap: list[tuple[float, str]] = [(0, origem)]

    while heap:
        d, u = heapq.heappop(heap)
        if u == destino:
            break
        if d > dist[u]:
            continue
        for (v, w) in grafo.arestas.get(u, []):
            peso_total = w + peso_congestao * congestao_atual.get(v, 0)
            nova = d + peso_total
            if nova < dist[v]:
                dist[v] = nova
                prev[v] = u
                heapq.heappush(heap, (nova, v))

    if dist[destino] == float("inf"):
        return []
    rota = []
    atual: str | None = destino
    while atual is not None:
        rota.append(atual)
        atual = prev[atual]
    return list(reversed(rota))


def congestao(
    local_id: str,
    ocupacao: int,
    capacidade: int,
) -> float:
    """
    Custo de congestão: 0 se vazio, explode se acima da capacidade.
    Fórmula: max(0, (ocupacao - capacidade) / capacidade) + ocupacao / capacidade
    """
    if capacidade <= 0:
        return float("inf")
    base = ocupacao / capacidade
    overflow = max(0, (ocupacao - capacidade) / capacidade)
    return base + overflow * 3   # multiplicador de penalidade para overflow


def grafo_campus_default() -> GrafoCampus:
    """
    Stub: constrói grafo a partir de engine/campus.py LOCAIS.
    TODO Onda 10.2: carregar adjacências reais.
    """
    g = GrafoCampus()
    # placeholder: todas adjacentes por default (será sobrescrito quando integrar)
    locais = ["agora", "biblioteca", "laboratorio", "torre_estrategia",
              "tribunal", "arena_debates", "redacao_mirante"]
    for i, a in enumerate(locais):
        for b in locais[i + 1:]:
            g.adicionar_aresta(a, b, peso=1.0)
    return g
