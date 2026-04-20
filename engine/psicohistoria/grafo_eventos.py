"""
Grafo de estados sociais + matriz de transição Markov.

Cada nó é um ESTADO da Vila (não de um agente individual) — isto é crucial para
manter o espírito de Asimov: previsão estatística coletiva, não individual.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter

import numpy as np


@dataclass(frozen=True)
class Estado:
    """Estado psico-histórico (ex: 'polarização alta', 'crise editorial')."""
    id: str
    descricao: str = ""
    atributos: tuple = field(default_factory=tuple)  # tuple para ser hashable


@dataclass
class Transicao:
    """Aresta ponderada entre 2 estados."""
    origem: str
    destino: str
    probabilidade: float
    observacoes: int = 0          # quantas vezes foi observada (para calibração)


class GrafoPsicohistoria:
    """
    Grafo direcionado ponderado com matriz de transição estocástica.

    Pode ser construído a partir de observações históricas (contagens) ou
    especificado diretamente com probabilidades.
    """

    def __init__(self) -> None:
        self.estados: dict[str, Estado] = {}
        self._idx_de: dict[str, int] = {}
        self._estado_de: dict[int, str] = {}
        self.matriz: np.ndarray | None = None
        self._contagens: dict[tuple[str, str], int] = {}

    def adicionar_estado(self, estado: Estado) -> None:
        if estado.id in self.estados:
            return
        self.estados[estado.id] = estado
        i = len(self._idx_de)
        self._idx_de[estado.id] = i
        self._estado_de[i] = estado.id

    def observar_transicao(self, origem: str, destino: str) -> None:
        """Registra que uma transição origem→destino ocorreu (para calibração)."""
        if origem not in self.estados:
            self.adicionar_estado(Estado(id=origem))
        if destino not in self.estados:
            self.adicionar_estado(Estado(id=destino))
        self._contagens[(origem, destino)] = self._contagens.get((origem, destino), 0) + 1

    def montar_matriz(self) -> np.ndarray:
        """
        Constroi matriz estocástica a partir das contagens.
        Linhas sem observação = loop absorvente (fica no mesmo estado).
        """
        n = len(self.estados)
        if n == 0:
            raise ValueError("grafo vazio")
        M = np.zeros((n, n))
        for (o, d), c in self._contagens.items():
            i, j = self._idx_de[o], self._idx_de[d]
            M[i, j] = c
        for i in range(n):
            total = M[i].sum()
            if total > 0:
                M[i] /= total
            else:
                M[i, i] = 1.0
        self.matriz = M
        return M

    def set_transicao(self, origem: str, destino: str, prob: float) -> None:
        """Define probabilidade diretamente (bypass de observações)."""
        if origem not in self.estados:
            self.adicionar_estado(Estado(id=origem))
        if destino not in self.estados:
            self.adicionar_estado(Estado(id=destino))
        if self.matriz is None:
            self.montar_matriz()
        i, j = self._idx_de[origem], self._idx_de[destino]
        self.matriz[i, j] = prob

    def normalizar(self) -> None:
        """Re-normaliza linhas após set_transicao manual."""
        if self.matriz is None:
            return
        for i in range(self.matriz.shape[0]):
            s = self.matriz[i].sum()
            if s > 0:
                self.matriz[i] /= s
            else:
                self.matriz[i, i] = 1.0

    def vetor_estado(self, estado_id: str) -> np.ndarray:
        """One-hot do estado."""
        v = np.zeros(len(self.estados))
        if estado_id in self._idx_de:
            v[self._idx_de[estado_id]] = 1.0
        return v

    def index_para_estado(self, i: int) -> str:
        return self._estado_de[i]

    def estado_para_index(self, estado_id: str) -> int:
        return self._idx_de[estado_id]


def construir_grafo_vila(
    historico: list[tuple[str, str]] | None = None,
) -> GrafoPsicohistoria:
    """
    Factory: cria grafo baseline com 8 estados canônicos da Vila + observações
    opcionais para calibrar matriz de transição.

    8 estados sociais:
        bootstrap, recrutamento, expansao, consenso_fragil, polarizacao,
        crise_economica, renovacao_constituinte, equilibrio
    """
    grafo = GrafoPsicohistoria()
    for eid, desc in [
        ("bootstrap",              "Vila recém-instanciada, baixa atividade"),
        ("recrutamento",           "Novos habitantes sendo onboardados"),
        ("expansao",               "Crescimento de produção (contribuições/hora)"),
        ("consenso_fragil",        "Maioria concorda; discordância pontual"),
        ("polarizacao",            "2+ facções polarizadas"),
        ("crise_economica",        "Colmeia em déficit, inflação coin"),
        ("renovacao_constituinte", "Proposta de artigo constitucional"),
        ("equilibrio",             "Steady-state, métricas estáveis"),
    ]:
        grafo.adicionar_estado(Estado(id=eid, descricao=desc))

    if historico:
        for origem, destino in historico:
            grafo.observar_transicao(origem, destino)
        grafo.montar_matriz()
    else:
        # baseline sintético — transições típicas calibradas por inspeção
        baseline: dict[tuple[str, str], float] = {
            ("bootstrap", "recrutamento"):      0.7,
            ("bootstrap", "bootstrap"):         0.3,
            ("recrutamento", "expansao"):       0.6,
            ("recrutamento", "recrutamento"):   0.25,
            ("recrutamento", "crise_economica"): 0.15,
            ("expansao", "consenso_fragil"):    0.45,
            ("expansao", "polarizacao"):        0.30,
            ("expansao", "expansao"):           0.25,
            ("consenso_fragil", "equilibrio"):  0.50,
            ("consenso_fragil", "polarizacao"): 0.30,
            ("consenso_fragil", "consenso_fragil"): 0.20,
            ("polarizacao", "renovacao_constituinte"): 0.40,
            ("polarizacao", "crise_economica"): 0.20,
            ("polarizacao", "polarizacao"):     0.40,
            ("crise_economica", "renovacao_constituinte"): 0.60,
            ("crise_economica", "crise_economica"): 0.40,
            ("renovacao_constituinte", "equilibrio"): 0.70,
            ("renovacao_constituinte", "renovacao_constituinte"): 0.30,
            ("equilibrio", "equilibrio"):       0.75,
            ("equilibrio", "polarizacao"):      0.10,
            ("equilibrio", "expansao"):         0.15,
        }
        grafo.montar_matriz()
        for (o, d), p in baseline.items():
            i, j = grafo._idx_de[o], grafo._idx_de[d]
            grafo.matriz[i, j] = p
        grafo.normalizar()

    return grafo


def contagens_de_lista(eventos: list[str]) -> list[tuple[str, str]]:
    """Converte sequência de eventos [s1, s2, s3, ...] em pares (s1→s2), (s2→s3), ..."""
    return list(zip(eventos[:-1], eventos[1:]))
