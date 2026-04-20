"""
engine.memoria.grafo — GraphRAG nativo (Onda 6).

Extrai entidades + relações de texto (posts, conversas, matérias) e armazena
como grafo direcionado. Usa nós e arestas simples (sem depender de Neo4j).
Pode persistir em Supabase (vila_grafo_nos, vila_grafo_arestas).

Consulta 2-hops usada em engine.cognitivo.recuperar para aterrar respostas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from collections import defaultdict


_PAT_ENTIDADE_NOMEADA = re.compile(r"\b([A-Z][a-zà-ü]{2,}(?:\s+[A-Z][a-zà-ü]+)*)\b")
_STOPWORDS_NOMES = {
    "Vila", "INTEIA", "Colmeia", "Mirante", "News", "Brasil", "Rio", "São",
    "De", "Do", "Da", "Dos", "Das", "E", "Ou", "Que", "Por", "Em", "A", "O",
}


@dataclass
class NoGrafo:
    id: str
    tipo: str                        # "pessoa" | "org" | "local" | "conceito" | "evento"
    rotulo: str
    props: dict = field(default_factory=dict)


@dataclass
class Aresta:
    origem: str
    destino: str
    relacao: str
    peso: float = 1.0
    props: dict = field(default_factory=dict)


class GrafoConhecimento:
    """Grafo direcionado in-memory. Persistência externa opcional."""

    def __init__(self) -> None:
        self.nos: dict[str, NoGrafo] = {}
        self.arestas_por_origem: dict[str, list[Aresta]] = defaultdict(list)
        self.arestas_por_destino: dict[str, list[Aresta]] = defaultdict(list)
        self._arestas_todas: list[Aresta] = []

    def add_no(self, n: NoGrafo) -> None:
        self.nos[n.id] = n

    def add_aresta(self, a: Aresta) -> None:
        self.arestas_por_origem[a.origem].append(a)
        self.arestas_por_destino[a.destino].append(a)
        self._arestas_todas.append(a)

    def vizinhos(self, no_id: str, hops: int = 1) -> set[str]:
        """IDs de nós alcançáveis em até `hops` passos (ida+volta)."""
        fronteira = {no_id}
        alcancado = {no_id}
        for _ in range(hops):
            nova = set()
            for n in fronteira:
                for a in self.arestas_por_origem.get(n, []):
                    nova.add(a.destino)
                for a in self.arestas_por_destino.get(n, []):
                    nova.add(a.origem)
            fronteira = nova - alcancado
            alcancado |= nova
        return alcancado - {no_id}

    def subgrafo(self, no_id: str, hops: int = 2) -> tuple[list[NoGrafo], list[Aresta]]:
        ids = self.vizinhos(no_id, hops) | {no_id}
        nos = [self.nos[i] for i in ids if i in self.nos]
        arestas = [a for a in self._arestas_todas
                   if a.origem in ids and a.destino in ids]
        return nos, arestas

    def buscar_por_rotulo(self, termo: str) -> list[NoGrafo]:
        t = termo.lower()
        return [n for n in self.nos.values() if t in n.rotulo.lower()]


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def extrair_entidades(texto: str) -> list[NoGrafo]:
    """
    Extração simples via regex de nomes próprios (primeira maiúscula consecutiva).
    Versão Onda 6.2: substituir por spaCy pt_core_news_lg ou LLM JSON structured.
    """
    vistos: set[str] = set()
    nos: list[NoGrafo] = []
    for match in _PAT_ENTIDADE_NOMEADA.findall(texto):
        m = match.strip()
        if m in _STOPWORDS_NOMES or len(m) < 3:
            continue
        if m in vistos:
            continue
        vistos.add(m)
        nos.append(NoGrafo(id=_slug(m), tipo="entidade", rotulo=m))
    return nos


def extrair_relacoes(
    texto: str,
    entidades: list[NoGrafo] | None = None,
) -> list[Aresta]:
    """
    Co-ocorrência simples: se duas entidades aparecem na mesma sentença,
    cria-se aresta `relacionada_a` com peso 1.
    Onda 6.2: substituir por relation extraction via LLM.
    """
    if entidades is None:
        entidades = extrair_entidades(texto)
    if len(entidades) < 2:
        return []
    arestas: list[Aresta] = []
    # Divide em sentenças aproximadas
    sentencas = re.split(r"(?<=[.!?])\s+", texto)
    for s in sentencas:
        presentes = [e for e in entidades if e.rotulo in s]
        for i in range(len(presentes)):
            for j in range(i + 1, len(presentes)):
                arestas.append(Aresta(
                    origem=presentes[i].id,
                    destino=presentes[j].id,
                    relacao="coocorrencia",
                    peso=1.0,
                ))
    return arestas


def indexar_texto(grafo: GrafoConhecimento, texto: str) -> dict:
    """Adiciona entidades + co-ocorrências ao grafo. Retorna sumário."""
    ents = extrair_entidades(texto)
    arestas = extrair_relacoes(texto, ents)
    for e in ents:
        grafo.add_no(e)
    for a in arestas:
        grafo.add_aresta(a)
    return {"n_entidades": len(ents), "n_arestas": len(arestas)}


# Singleton global para uso em runtime
GRAFO_GLOBAL = GrafoConhecimento()
