"""Twitter-like: feed temporal + viral score por engajamento rápido."""

from __future__ import annotations
import time

from engine.plataformas.base import PlataformaSocial, Post


class TwitterLike(PlataformaSocial):
    nome = "twitter_like"

    def ranking_feed(self, usuario_id: str, limite: int = 50) -> list[Post]:
        """Feed temporal inverso + boost para quem o usuário segue."""
        perfil = self.perfis.get(usuario_id)
        segue = perfil.following if perfil else set()
        posts = list(self.posts.values())
        # Score = recência + 0.5 se autor é seguido
        agora = time.time()
        def score(p: Post) -> float:
            idade_h = (agora - p.timestamp) / 3600
            s = -idade_h
            if p.autor_id in segue:
                s += 0.5
            return s
        posts.sort(key=score, reverse=True)
        return posts[:limite]

    def viral_score(self, post: Post) -> float:
        """Viral = engajamento / (idade + 1h)^1.5 (decay rápido)."""
        agora = time.time()
        idade_h = max(0.1, (agora - post.timestamp) / 3600)
        return post.engajamento / (idade_h + 1) ** 1.5
