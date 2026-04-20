"""Interface comum das plataformas sociais."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class Reacao:
    tipo: str                  # "like", "dislike", "upvote", "downvote", "heart", "share"
    autor_id: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Post:
    id: str
    autor_id: str
    conteudo: str
    timestamp: float = field(default_factory=time.time)
    reacoes: list[Reacao] = field(default_factory=list)
    respostas: list["Post"] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    @property
    def contagem_pos(self) -> int:
        return sum(1 for r in self.reacoes if r.tipo in ("like", "upvote", "heart"))

    @property
    def contagem_neg(self) -> int:
        return sum(1 for r in self.reacoes if r.tipo in ("dislike", "downvote"))

    @property
    def engajamento(self) -> float:
        return self.contagem_pos + 2 * len(self.respostas) - 0.5 * self.contagem_neg


@dataclass
class PerfilPlataforma:
    agente_id: str
    nome_exibicao: str
    bio: str = ""
    followers: set[str] = field(default_factory=set)
    following: set[str] = field(default_factory=set)
    meta: dict = field(default_factory=dict)


class PlataformaSocial(ABC):
    """Interface comum — cada plataforma concreta override ranking_feed + viral_score."""

    nome: str = "base"

    def __init__(self) -> None:
        self.posts: dict[str, Post] = {}
        self.perfis: dict[str, PerfilPlataforma] = {}
        self._contador = 0

    def cadastrar_perfil(self, perfil: PerfilPlataforma) -> None:
        self.perfis[perfil.agente_id] = perfil

    def seguir(self, seguidor_id: str, alvo_id: str) -> None:
        if seguidor_id in self.perfis and alvo_id in self.perfis:
            self.perfis[seguidor_id].following.add(alvo_id)
            self.perfis[alvo_id].followers.add(seguidor_id)

    def postar(self, autor_id: str, conteudo: str, **meta: Any) -> Post:
        self._contador += 1
        pid = f"{self.nome}_{self._contador}"
        p = Post(id=pid, autor_id=autor_id, conteudo=conteudo, meta=dict(meta))
        self.posts[pid] = p
        return p

    def reagir(self, post_id: str, autor_id: str, tipo: str) -> None:
        if post_id in self.posts:
            self.posts[post_id].reacoes.append(Reacao(tipo=tipo, autor_id=autor_id))

    def responder(self, post_id: str, autor_id: str, conteudo: str) -> Post | None:
        if post_id not in self.posts:
            return None
        self._contador += 1
        rid = f"{self.nome}_{self._contador}"
        resp = Post(id=rid, autor_id=autor_id, conteudo=conteudo)
        self.posts[post_id].respostas.append(resp)
        self.posts[rid] = resp
        return resp

    @abstractmethod
    def ranking_feed(self, usuario_id: str, limite: int = 50) -> list[Post]:
        """Retorna posts ordenados pelo algoritmo desta plataforma."""
        ...

    @abstractmethod
    def viral_score(self, post: Post) -> float:
        """Score de viralização específico da plataforma."""
        ...

    def stats(self) -> dict:
        return {
            "plataforma": self.nome,
            "n_posts": len(self.posts),
            "n_perfis": len(self.perfis),
            "engajamento_total": sum(p.engajamento for p in self.posts.values()),
        }
