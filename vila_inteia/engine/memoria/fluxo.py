"""
Fluxo de Memória (Memory Stream) - Memória Associativa de Longo Prazo.

Inspirado no Generative Agents (Stanford) mas com melhorias INTEIA:
- Pontuação tripla: Relevância semântica + Recência + Importância
- Tipos: evento, pensamento, conversa, insight, sintese
- Relacionamentos como memórias de alta importância
- Filtragem por expertise do consultor
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class NoMemoria:
    """Um nó na memória do agente (evento, pensamento ou conversa)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tipo: str = "evento"  # evento, pensamento, conversa, insight, sintese
    criado_em: datetime = field(default_factory=datetime.now)
    expiracao: Optional[datetime] = None

    # Tripla Semântica (Sujeito-Predicado-Objeto)
    sujeito: str = ""
    predicado: str = ""
    objeto: str = ""

    # Conteúdo
    descricao: str = ""
    local_id: str = ""

    # Metadados
    importancia: int = 5  # 1-10 (poignancy)
    palavras_chave: set[str] = field(default_factory=set)
    embedding: Optional[list[float]] = None

    # Evidências (para pensamentos/insights)
    evidencias: list[str] = field(default_factory=list)  # IDs de nós que suportam

    # Conversas
    participantes: list[str] = field(default_factory=list)

    def esta_expirado(self, agora: datetime) -> bool:
        if self.expiracao is None:
            return False
        return agora > self.expiracao

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "criado_em": self.criado_em.isoformat(),
            "expiracao": self.expiracao.isoformat() if self.expiracao else None,
            "sujeito": self.sujeito,
            "predicado": self.predicado,
            "objeto": self.objeto,
            "descricao": self.descricao,
            "local_id": self.local_id,
            "importancia": self.importancia,
            "palavras_chave": list(self.palavras_chave),
            "embedding": self.embedding,
            "evidencias": self.evidencias,
            "participantes": self.participantes,
        }

    @classmethod
    def from_dict(cls, dados: dict) -> NoMemoria:
        dados = dados.copy()
        dados["criado_em"] = datetime.fromisoformat(dados["criado_em"])
        if dados.get("expiracao"):
            dados["expiracao"] = datetime.fromisoformat(dados["expiracao"])
        dados["palavras_chave"] = set(dados.get("palavras_chave", []))
        return cls(**dados)


class FluxoMemoria:
    """
    Fluxo de Memória Associativa.

    Armazena todos os eventos, pensamentos e conversas do agente.
    Permite recuperação por relevância, recência e importância.
    """

    def __init__(
        self,
        decay: float = 0.995,
        max_memorias: int = 5000,
    ):
        self.decay = decay
        self.max_memorias = max_memorias

        # Sequências por tipo
        self.eventos: list[NoMemoria] = []
        self.pensamentos: list[NoMemoria] = []
        self.conversas: list[NoMemoria] = []

        # Índices para recuperação rápida
        self._por_palavra_chave: dict[str, list[NoMemoria]] = {}
        self._por_local: dict[str, list[NoMemoria]] = {}
        self._por_participante: dict[str, list[NoMemoria]] = {}
        self._todos: list[NoMemoria] = []

        # Contadores
        self.importancia_acumulada: float = 0.0

    @property
    def total(self) -> int:
        return len(self._todos)

    def adicionar(self, no: NoMemoria) -> NoMemoria:
        """Adiciona um nó de memória ao fluxo."""
        # Adicionar à sequência correta
        if no.tipo in ("evento",):
            self.eventos.append(no)
        elif no.tipo in ("pensamento", "insight", "sintese"):
            self.pensamentos.append(no)
        elif no.tipo == "conversa":
            self.conversas.append(no)

        # Indexar
        self._todos.append(no)
        for kw in no.palavras_chave:
            kw_lower = kw.lower()
            if kw_lower not in self._por_palavra_chave:
                self._por_palavra_chave[kw_lower] = []
            self._por_palavra_chave[kw_lower].append(no)

        if no.local_id:
            if no.local_id not in self._por_local:
                self._por_local[no.local_id] = []
            self._por_local[no.local_id].append(no)

        for p in no.participantes:
            if p not in self._por_participante:
                self._por_participante[p] = []
            self._por_participante[p].append(no)

        # Acumular importância para trigger de reflexão
        self.importancia_acumulada += no.importancia

        # Limitar tamanho
        if len(self._todos) > self.max_memorias:
            self._podar()

        return no

    def adicionar_evento(
        self,
        descricao: str,
        sujeito: str = "",
        predicado: str = "",
        objeto: str = "",
        local_id: str = "",
        importancia: int = 5,
        palavras_chave: set[str] | None = None,
    ) -> NoMemoria:
        """Atalho para adicionar um evento."""
        no = NoMemoria(
            tipo="evento",
            descricao=descricao,
            sujeito=sujeito,
            predicado=predicado,
            objeto=objeto,
            local_id=local_id,
            importancia=importancia,
            palavras_chave=palavras_chave or set(),
        )
        return self.adicionar(no)

    def adicionar_pensamento(
        self,
        descricao: str,
        importancia: int = 7,
        evidencias: list[str] | None = None,
        palavras_chave: set[str] | None = None,
    ) -> NoMemoria:
        """Atalho para adicionar um pensamento/reflexão."""
        no = NoMemoria(
            tipo="pensamento",
            descricao=descricao,
            importancia=importancia,
            evidencias=evidencias or [],
            palavras_chave=palavras_chave or set(),
            expiracao=datetime.now() + timedelta(days=30),
        )
        return self.adicionar(no)

    def adicionar_conversa(
        self,
        descricao: str,
        participantes: list[str],
        local_id: str = "",
        importancia: int = 6,
        palavras_chave: set[str] | None = None,
    ) -> NoMemoria:
        """Atalho para adicionar uma conversa."""
        no = NoMemoria(
            tipo="conversa",
            descricao=descricao,
            participantes=participantes,
            local_id=local_id,
            importancia=importancia,
            palavras_chave=palavras_chave or set(),
        )
        return self.adicionar(no)

    def recuperar(
        self,
        consulta: str,
        n: int = 10,
        peso_relevancia: float = 1.0,
        peso_recencia: float = 1.0,
        peso_importancia: float = 1.0,
        tipos: list[str] | None = None,
        agora: datetime | None = None,
    ) -> list[tuple[NoMemoria, float]]:
        """
        Recupera memórias relevantes usando pontuação tripla.

        Score = (w_rel * relevância) + (w_rec * recência) + (w_imp * importância)

        Sem embeddings, usa keyword matching para relevância.
        """
        agora = agora or datetime.now()
        palavras_consulta = set(consulta.lower().split())

        candidatos = self._todos
        if tipos:
            candidatos = [m for m in candidatos if m.tipo in tipos]

        resultados = []
        for memoria in candidatos:
            if memoria.esta_expirado(agora):
                continue

            # 1. Relevância (keyword overlap)
            palavras_memoria = set(
                w.lower() for w in memoria.palavras_chave
            ) | set(memoria.descricao.lower().split())
            overlap = len(palavras_consulta & palavras_memoria)
            total = max(len(palavras_consulta), 1)
            relevancia = min(overlap / total, 1.0)

            # 2. Recência (exponential decay)
            delta_horas = max(
                (agora - memoria.criado_em).total_seconds() / 3600, 0
            )
            recencia = self.decay ** delta_horas

            # 3. Importância (normalizada 0-1)
            importancia = memoria.importancia / 10.0

            # Score composto
            score = (
                peso_relevancia * relevancia
                + peso_recencia * recencia
                + peso_importancia * importancia
            )

            resultados.append((memoria, score))

        # Ordenar por score decrescente
        resultados.sort(key=lambda x: x[1], reverse=True)
        return resultados[:n]

    def recuperar_por_participante(
        self, nome: str, n: int = 20
    ) -> list[NoMemoria]:
        """Recupera memórias envolvendo um participante específico."""
        return self._por_participante.get(nome, [])[-n:]

    def recuperar_por_local(self, local_id: str, n: int = 20) -> list[NoMemoria]:
        """Recupera memórias de um local específico."""
        return self._por_local.get(local_id, [])[-n:]

    def ultimas(self, n: int = 10, tipos: list[str] | None = None) -> list[NoMemoria]:
        """Retorna as últimas N memórias."""
        if tipos:
            filtradas = [m for m in self._todos if m.tipo in tipos]
            return filtradas[-n:]
        return self._todos[-n:]

    def deve_refletir(self, limiar: float = 100.0) -> bool:
        """Verifica se acumulou importância suficiente para reflexão."""
        return self.importancia_acumulada >= limiar

    def resetar_acumulador(self):
        """Reseta o acumulador de importância após reflexão."""
        self.importancia_acumulada = 0.0

    def pontos_focais(self, n: int = 3) -> list[str]:
        """Retorna os N temas mais importantes recentes (para reflexão)."""
        recentes = self._todos[-50:]
        recentes.sort(key=lambda m: m.importancia, reverse=True)
        focais = []
        vistos = set()
        for m in recentes:
            tema = m.sujeito or m.descricao[:50]
            if tema not in vistos:
                focais.append(tema)
                vistos.add(tema)
            if len(focais) >= n:
                break
        return focais

    def _podar(self):
        """Remove memórias menos importantes quando excede o limite."""
        # Manter pensamentos/insights por mais tempo
        self._todos.sort(
            key=lambda m: (
                m.importancia * (2 if m.tipo in ("pensamento", "insight") else 1),
                m.criado_em.timestamp(),
            )
        )
        excesso = len(self._todos) - self.max_memorias
        if excesso > 0:
            removidos = set(id(m) for m in self._todos[:excesso])
            self._todos = self._todos[excesso:]
            # Limpar índices (lazy - serão reconstruídos se necessário)
            self.eventos = [e for e in self.eventos if id(e) not in removidos]
            self.pensamentos = [p for p in self.pensamentos if id(p) not in removidos]
            self.conversas = [c for c in self.conversas if id(c) not in removidos]

    def salvar(self, caminho: str):
        """Persiste o fluxo de memória em JSON."""
        dados = {
            "decay": self.decay,
            "max_memorias": self.max_memorias,
            "importancia_acumulada": self.importancia_acumulada,
            "memorias": [m.to_dict() for m in self._todos],
        }
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    @classmethod
    def carregar(cls, caminho: str) -> FluxoMemoria:
        """Carrega um fluxo de memória de JSON."""
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)

        fluxo = cls(
            decay=dados.get("decay", 0.995),
            max_memorias=dados.get("max_memorias", 5000),
        )
        fluxo.importancia_acumulada = dados.get("importancia_acumulada", 0.0)

        for m_dict in dados.get("memorias", []):
            no = NoMemoria.from_dict(m_dict)
            fluxo.adicionar(no)

        return fluxo

    def resumo(self) -> dict:
        """Retorna resumo estatístico da memória."""
        return {
            "total": self.total,
            "eventos": len(self.eventos),
            "pensamentos": len(self.pensamentos),
            "conversas": len(self.conversas),
            "importancia_acumulada": round(self.importancia_acumulada, 1),
            "palavras_chave_unicas": len(self._por_palavra_chave),
            "locais_visitados": len(self._por_local),
            "pessoas_interagidas": len(self._por_participante),
        }
