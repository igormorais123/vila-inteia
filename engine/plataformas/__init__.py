"""
engine.plataformas — múltiplas plataformas sociais paralelas (Onda 7).

Cada plataforma mantém seu próprio feed, algoritmo de ranking, dinâmica de
viralização. O mesmo habitante pode ter perfis distintos em cada uma, com
tom/registro/estilo adaptados.

Plataformas implementadas:
    - twitter_like   : feed temporal + viral score (engajamento rápido)
    - reddit_like    : threaded, upvote/downvote, sub-oficinas
    - linkedin_like  : endorsement, prioriza conexões profissionais
    - tiktok_like    : engagement-only, for-you algoritmo, short-form
"""

from engine.plataformas.base import (
    Post, Reacao, PlataformaSocial, PerfilPlataforma,
)
from engine.plataformas.twitter_like import TwitterLike
from engine.plataformas.reddit_like import RedditLike
from engine.plataformas.linkedin_like import LinkedInLike
from engine.plataformas.tiktok_like import TikTokLike

__all__ = [
    "Post", "Reacao", "PlataformaSocial", "PerfilPlataforma",
    "TwitterLike", "RedditLike", "LinkedInLike", "TikTokLike",
]
