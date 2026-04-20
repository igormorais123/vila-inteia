"""
Topologias de rede social: small-world, preferential attachment, community detection.

Referências:
    Watts & Strogatz (1998).
    Barabási & Albert (1999).
    Girvan & Newman (2002); Louvain (Blondel 2008).
"""

from __future__ import annotations

import random


def small_world(
    n: int,
    k: int = 4,
    p_rewire: float = 0.1,
    seed: int = 42,
) -> dict[int, list[int]]:
    """
    Watts-Strogatz small-world: anel com k vizinhos, reconectar com prob p.

    Retorna dict adj: id -> lista de vizinhos.
    """
    rng = random.Random(seed)
    adj: dict[int, list[int]] = {i: [] for i in range(n)}
    for i in range(n):
        for delta in range(1, k // 2 + 1):
            j = (i + delta) % n
            adj[i].append(j)
            adj[j].append(i)
    for i in range(n):
        for idx, j in enumerate(list(adj[i])):
            if rng.random() < p_rewire:
                novo = rng.randrange(n)
                if novo != i and novo not in adj[i]:
                    adj[i][idx] = novo
                    adj[novo].append(i)
                    try:
                        adj[j].remove(i)
                    except ValueError:
                        pass
    return adj


def preferential_attachment(n: int, m: int = 3, seed: int = 42) -> dict[int, list[int]]:
    """
    Barabási-Albert: começa com m nós completos; cada novo nó conecta a m existentes,
    com probabilidade proporcional ao grau.

    Gera distribuição power-law (hubs emergem).
    """
    if n <= m:
        raise ValueError("n > m")
    rng = random.Random(seed)
    adj: dict[int, list[int]] = {i: [] for i in range(n)}
    for i in range(m):
        for j in range(i + 1, m):
            adj[i].append(j)
            adj[j].append(i)

    degrees = [len(adj[i]) for i in range(m)] + [0] * (n - m)

    for novo in range(m, n):
        escolhidos: set[int] = set()
        while len(escolhidos) < m:
            total = sum(degrees[:novo]) or 1
            r = rng.uniform(0, total)
            acc = 0.0
            for cand in range(novo):
                acc += degrees[cand]
                if acc >= r:
                    escolhidos.add(cand)
                    break
        for alvo in escolhidos:
            adj[novo].append(alvo)
            adj[alvo].append(novo)
            degrees[alvo] += 1
        degrees[novo] = len(escolhidos)
    return adj


def detectar_comunidades(adj: dict[int, list[int]]) -> dict[int, int]:
    """
    Detecção de comunidades via Louvain (networkx).
    Retorna node_id -> community_id (0..k-1).
    """
    try:
        import networkx as nx
    except ImportError:
        raise RuntimeError("networkx não instalado")
    g = nx.Graph()
    for n, viz in adj.items():
        g.add_node(n)
        for v in viz:
            g.add_edge(n, v)
    try:
        from networkx.algorithms.community import louvain_communities
        comms = louvain_communities(g, seed=42)
    except (ImportError, AttributeError):
        # Fallback: connected components
        comms = list(nx.connected_components(g))
    mapeamento: dict[int, int] = {}
    for cid, membros in enumerate(comms):
        for m in membros:
            mapeamento[m] = cid
    return mapeamento


def grau_clustering(adj: dict[int, list[int]], node: int) -> float:
    """Coeficiente de clustering local: fração de pares de vizinhos conectados."""
    vizinhos = adj.get(node, [])
    k = len(vizinhos)
    if k < 2:
        return 0.0
    cnt = 0
    for i, v1 in enumerate(vizinhos):
        for v2 in vizinhos[i + 1:]:
            if v2 in adj.get(v1, []):
                cnt += 1
    possivel = k * (k - 1) / 2
    return cnt / possivel if possivel > 0 else 0.0
