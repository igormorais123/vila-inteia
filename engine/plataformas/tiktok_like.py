"""TikTok-like: For-You algorithm, viralização pura por engagement."""

from __future__ import annotations

from engine.plataformas.base import PlataformaSocial, Post


class TikTokLike(PlataformaSocial):
    nome = "tiktok_like"

    def ranking_feed(self, usuario_id: str, limite: int = 50) -> list[Post]:
        """For-You: engajamento puro, sem filtro de follow. Peso maior pra watch-time (reshares)."""
        posts = list(self.posts.values())
        posts.sort(key=self.viral_score, reverse=True)
        return posts[:limite]

    def viral_score(self, post: Post) -> float:
        shares = sum(1 for r in post.reacoes if r.tipo == "share")
        hearts = sum(1 for r in post.reacoes if r.tipo == "heart")
        respostas = len(post.respostas)
        # Fator de explosão: shares têm peso 5
        return hearts + 3 * respostas + 5 * shares
