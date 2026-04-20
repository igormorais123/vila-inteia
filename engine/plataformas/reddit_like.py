"""Reddit-like: threaded, upvote/downvote, ranking por hot score."""

from __future__ import annotations
import math
import time

from engine.plataformas.base import PlataformaSocial, Post


class RedditLike(PlataformaSocial):
    nome = "reddit_like"

    def ranking_feed(self, usuario_id: str, limite: int = 50) -> list[Post]:
        """Hot ranking de Reddit: log10(score) + tempo/45000s."""
        posts = list(self.posts.values())
        posts.sort(key=self._hot_score, reverse=True)
        return posts[:limite]

    def _hot_score(self, p: Post) -> float:
        s = p.contagem_pos - p.contagem_neg
        order = math.log10(max(abs(s), 1))
        sign = 1 if s > 0 else (-1 if s < 0 else 0)
        # Timestamp base: 2005-12-08 (Reddit launch, tradicional)
        epoch = 1134028003
        seconds = p.timestamp - epoch
        return round(sign * order + seconds / 45000, 7)

    def viral_score(self, post: Post) -> float:
        """Viral por profundidade de thread + engajamento."""
        def profundidade_max(p: Post, d: int = 0) -> int:
            if not p.respostas:
                return d
            return max(profundidade_max(r, d + 1) for r in p.respostas)
        return post.engajamento + 3 * profundidade_max(post)
