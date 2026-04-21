"""
Onda 83: influencia personas — ranking de influência baseado em grafo
de conversas.

Diferencial vs MiroFish: identifica OS "Primeiros Motores" da Vila —
quem puxa as ideias, quem é ponte entre grupos, quem tem autoridade
cumulativa.

Métricas (NetworkX):
- degree_centrality: quantas relações diretas
- betweenness_centrality: ponte entre grupos (controla fluxo info)
- eigenvector_centrality: influência recursiva (quem te conecta importa)
- pagerank: influência direcional
- n_conversas: count absoluto
- n_parceiros_unicos: diversidade social

Score composto:
  score = 0.25*degree + 0.25*betweenness + 0.25*eigenvector + 0.25*pagerank

Ranking desc por score.
"""

from __future__ import annotations

from collections import Counter
from typing import Any
import logging

import networkx as nx

logger = logging.getLogger(__name__)


def construir_grafo_conversas(conversas: list[dict]) -> nx.Graph:
    """
    Grafo não-direcionado de persona-persona com weight = n_conversas.
    Aceita conversas no formato sim.conversas_recentes (dict com turnos).
    """
    g = nx.Graph()
    for c in conversas:
        turnos = c.get("turnos", [])
        if not turnos:
            continue
        # Nome do iniciador: turn 0 first element
        iniciador = None
        if isinstance(turnos[0], (list, tuple)) and len(turnos[0]) >= 2:
            iniciador = turnos[0][0]
        parceiro = c.get("parceiro_nome")
        if not iniciador or not parceiro or iniciador == parceiro:
            continue
        if g.has_edge(iniciador, parceiro):
            g[iniciador][parceiro]["weight"] += 1
        else:
            g.add_edge(iniciador, parceiro, weight=1)
    return g


def ranking_influencia(
    conversas: list[dict] | None = None,
    top_n: int = 20,
) -> dict:
    """
    Retorna dict com:
        n_personas, n_edges, n_conversas,
        ranking: [{persona, score, degree_centrality, betweenness_centrality,
                    eigenvector_centrality, pagerank,
                    n_conversas, n_parceiros_unicos}, ...]
    """
    conversas = list(conversas or [])
    g = construir_grafo_conversas(conversas)

    if g.number_of_nodes() == 0:
        return {
            "n_personas": 0, "n_edges": 0, "n_conversas": len(conversas),
            "ranking": [], "aviso": "grafo vazio",
        }

    # Centralities
    deg = nx.degree_centrality(g)
    try:
        bet = nx.betweenness_centrality(g, weight="weight")
    except Exception:
        bet = {n: 0.0 for n in g.nodes()}
    try:
        eig = nx.eigenvector_centrality(g, max_iter=300, tol=1e-6, weight="weight")
    except Exception:
        # Convergência falha em grafos desconectados; usa zero
        eig = {n: 0.0 for n in g.nodes()}
    pr = nx.pagerank(g, weight="weight")

    # Counts absolutos
    counter_conv = Counter()
    parceiros_unicos = {n: set() for n in g.nodes()}
    for c in conversas:
        turnos = c.get("turnos", [])
        if not turnos or not isinstance(turnos[0], (list, tuple)) or len(turnos[0]) < 2:
            continue
        ini = turnos[0][0]
        parc = c.get("parceiro_nome")
        if ini in g.nodes:
            counter_conv[ini] += 1
            if parc: parceiros_unicos[ini].add(parc)
        if parc in g.nodes:
            counter_conv[parc] += 1
            if ini: parceiros_unicos[parc].add(ini)

    linhas = []
    for n in g.nodes():
        score = 0.25 * deg[n] + 0.25 * bet[n] + 0.25 * eig[n] + 0.25 * pr[n]
        linhas.append({
            "persona": n,
            "score": float(score),
            "degree_centrality": float(deg[n]),
            "betweenness_centrality": float(bet[n]),
            "eigenvector_centrality": float(eig[n]),
            "pagerank": float(pr[n]),
            "n_conversas": int(counter_conv[n]),
            "n_parceiros_unicos": len(parceiros_unicos[n]),
        })
    linhas.sort(key=lambda r: -r["score"])

    return {
        "n_personas": g.number_of_nodes(),
        "n_edges": g.number_of_edges(),
        "n_conversas": len(conversas),
        "ranking": linhas[:top_n],
    }
