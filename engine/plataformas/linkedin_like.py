"""LinkedIn-like: endorsement, prioriza conexões profissionais + tom corporate."""

from __future__ import annotations

from engine.plataformas.base import PlataformaSocial, Post


class LinkedInLike(PlataformaSocial):
    nome = "linkedin_like"

    def ranking_feed(self, usuario_id: str, limite: int = 50) -> list[Post]:
        """Prioriza 1st-degree + 2nd-degree connections + engajamento."""
        perfil = self.perfis.get(usuario_id)
        if perfil is None:
            return list(self.posts.values())[:limite]
        primeiros = perfil.following
        # 2nd-degree: conexões dos meus conectados
        segundos: set[str] = set()
        for p in primeiros:
            p_perfil = self.perfis.get(p)
            if p_perfil:
                segundos |= p_perfil.following
        segundos -= primeiros
        segundos.discard(usuario_id)

        def score(post: Post) -> float:
            s = post.engajamento
            if post.autor_id in primeiros:
                s += 10
            elif post.autor_id in segundos:
                s += 3
            return s
        posts = sorted(self.posts.values(), key=score, reverse=True)
        return posts[:limite]

    def viral_score(self, post: Post) -> float:
        """Endorsement-weighted: likes valem mais que shares."""
        return 2.5 * post.contagem_pos + 0.5 * len(post.respostas)
