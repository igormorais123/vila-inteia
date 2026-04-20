"""
Orquestrador multi-plataforma (Onda 22).

Coordena as 4 plataformas (Twitter/Reddit/LinkedIn/TikTok-like) num único
serviço. Implementa propagação cross-platform: post que viraliza em uma
plataforma tem chance de spillover para as demais.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
import threading

from engine.plataformas import (
    TwitterLike, RedditLike, LinkedInLike, TikTokLike,
    PerfilPlataforma,
)


@dataclass
class EstatisticasPlataforma:
    nome: str
    n_posts: int
    n_perfis: int
    viral_top_3: list[dict]        # top-3 posts por viral score
    engajamento_total: float


class OrquestradorPlataformas:
    """
    Mantém as 4 plataformas sincronizadas. Fornece API única para
    engine.simulacao.SimulacaoVila postar + medir virality.
    """

    def __init__(self):
        self.twitter = TwitterLike()
        self.reddit = RedditLike()
        self.linkedin = LinkedInLike()
        self.tiktok = TikTokLike()
        self.plataformas = {
            "twitter": self.twitter, "reddit": self.reddit,
            "linkedin": self.linkedin, "tiktok": self.tiktok,
        }
        self._lock = threading.Lock()
        self._spillover_historico: list[dict] = []

    def registrar_habitante(self, agente_id: str, nome: str, bio: str = "") -> None:
        """Cria perfil em todas as plataformas (nomes variam por estilo)."""
        with self._lock:
            for nome_p, plat in self.plataformas.items():
                plat.cadastrar_perfil(PerfilPlataforma(
                    agente_id=agente_id,
                    nome_exibicao=self._adaptar_nome(nome, nome_p),
                    bio=self._adaptar_bio(bio, nome_p),
                ))

    def _adaptar_nome(self, nome: str, plataforma: str) -> str:
        """Estilo de nome varia: TikTok = emoji handle, LinkedIn = formal."""
        if plataforma == "tiktok":
            return f"@{nome.lower().replace(' ', '')}"
        if plataforma == "linkedin":
            return nome  # formal full name
        if plataforma == "reddit":
            return f"u/{nome.split()[0].lower()}"
        return nome  # twitter default

    def _adaptar_bio(self, bio: str, plataforma: str) -> str:
        if plataforma == "linkedin":
            return bio  # full professional
        if plataforma == "tiktok":
            return "🌊 viral content" if not bio else bio[:60]
        return bio[:160]  # twitter/reddit

    def postar_em(self, plataforma: str, autor_id: str, conteudo: str) -> str | None:
        """Posta em 1 plataforma específica. Retorna post_id."""
        with self._lock:
            plat = self.plataformas.get(plataforma)
            if plat is None:
                return None
            post = plat.postar(autor_id, conteudo)
            return post.id

    def postar_primario_com_spillover(
        self,
        plataforma_origem: str,
        autor_id: str,
        conteudo: str,
        taxa_spillover: dict[str, float] | None = None,
    ) -> dict:
        """
        Posta primeiro numa plataforma. Se viralizar (heurístico), replica
        nas outras com probabilidade taxa_spillover[destino].

        Default taxas:
            twitter → reddit 0.3, linkedin 0.1, tiktok 0.2
            reddit → twitter 0.4, linkedin 0.05, tiktok 0.15
            tiktok → twitter 0.5, reddit 0.2, linkedin 0.01
            linkedin → twitter 0.3, reddit 0.15, tiktok 0.0
        """
        defaults = {
            "twitter":  {"reddit": 0.3,  "linkedin": 0.1,  "tiktok": 0.2},
            "reddit":   {"twitter": 0.4, "linkedin": 0.05, "tiktok": 0.15},
            "linkedin": {"twitter": 0.3, "reddit": 0.15,   "tiktok": 0.0},
            "tiktok":   {"twitter": 0.5, "reddit": 0.2,    "linkedin": 0.01},
        }
        taxas = taxa_spillover or defaults.get(plataforma_origem, {})

        pid_origem = self.postar_em(plataforma_origem, autor_id, conteudo)
        spillovers: list[str] = []
        for destino, prob in taxas.items():
            if random.random() < prob:
                pid = self.postar_em(destino, autor_id, f"[x-post] {conteudo}")
                if pid:
                    spillovers.append(destino)
                    self._spillover_historico.append({
                        "origem": plataforma_origem, "destino": destino,
                        "autor_id": autor_id,
                    })

        return {
            "post_id_origem": pid_origem,
            "plataforma_origem": plataforma_origem,
            "spillovers": spillovers,
        }

    def stats_todas(self) -> list[EstatisticasPlataforma]:
        with self._lock:
            out = []
            for nome, plat in self.plataformas.items():
                posts_ord = sorted(plat.posts.values(),
                                    key=plat.viral_score, reverse=True)[:3]
                out.append(EstatisticasPlataforma(
                    nome=nome,
                    n_posts=len(plat.posts),
                    n_perfis=len(plat.perfis),
                    viral_top_3=[
                        {"id": p.id, "autor_id": p.autor_id,
                         "score": plat.viral_score(p),
                         "conteudo": p.conteudo[:80]}
                        for p in posts_ord
                    ],
                    engajamento_total=sum(p.engajamento for p in plat.posts.values()),
                ))
            return out

    def estatisticas_spillover(self) -> dict:
        with self._lock:
            from collections import Counter
            pares = Counter((s["origem"], s["destino"]) for s in self._spillover_historico)
            return {
                "total": len(self._spillover_historico),
                "pares_mais_frequentes": sorted(
                    [{"par": f"{o}→{d}", "n": n} for (o, d), n in pares.items()],
                    key=lambda x: x["n"], reverse=True,
                )[:5],
            }


ORQUESTRADOR_GLOBAL = OrquestradorPlataformas()
