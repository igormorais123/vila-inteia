"""Testes multi-plataforma social (Onda 7)."""

from __future__ import annotations
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.plataformas import (
    TwitterLike, RedditLike, LinkedInLike, TikTokLike,
    PerfilPlataforma,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _popular(p):
    p.cadastrar_perfil(PerfilPlataforma(agente_id="a", nome_exibicao="A"))
    p.cadastrar_perfil(PerfilPlataforma(agente_id="b", nome_exibicao="B"))
    p.cadastrar_perfil(PerfilPlataforma(agente_id="c", nome_exibicao="C"))
    p.seguir("a", "b")
    p1 = p.postar("b", "Post de B")
    p2 = p.postar("c", "Post de C")
    p.reagir(p1.id, "a", "like" if p.nome == "twitter_like" else "upvote" if p.nome == "reddit_like" else "like")
    return p1, p2


def t_twitter_prioriza_seguidos():
    p = TwitterLike()
    p1, p2 = _popular(p)
    feed = p.ranking_feed("a", limite=10)
    teste("twitter: post do seguido 'b' aparece antes de 'c'",
          feed[0].autor_id == "b", f"got {feed[0].autor_id}")


def t_reddit_hot_score():
    p = RedditLike()
    p1, p2 = _popular(p)
    p.reagir(p1.id, "c", "upvote")
    feed = p.ranking_feed("a", limite=10)
    teste("reddit: post com mais upvotes ranked primeiro",
          feed[0].id == p1.id, f"got {feed[0].id}")


def t_linkedin_endorsement():
    p = LinkedInLike()
    p1, p2 = _popular(p)
    p.reagir(p1.id, "a", "like")
    p.reagir(p2.id, "a", "like")
    feed = p.ranking_feed("a", limite=10)
    teste("linkedin: 1st-degree (b) antes de 2nd-degree",
          feed[0].autor_id == "b")


def t_tiktok_viral_shares():
    p = TikTokLike()
    p1 = p.postar("a", "short viral")
    p2 = p.postar("a", "short quieto")
    for _ in range(5):
        p.reagir(p1.id, "x", "share")
    for _ in range(10):
        p.reagir(p2.id, "x", "heart")
    v1 = p.viral_score(p1)
    v2 = p.viral_score(p2)
    # 5 shares * 5 = 25 vs 10 hearts * 1 = 10
    teste("tiktok: shares dominam hearts",
          v1 > v2, f"v1={v1} v2={v2}")


def t_post_engajamento():
    p = TwitterLike()
    p.cadastrar_perfil(PerfilPlataforma(agente_id="a", nome_exibicao="A"))
    post = p.postar("a", "x")
    p.reagir(post.id, "b", "like")
    p.reagir(post.id, "c", "dislike")
    p.responder(post.id, "d", "resposta")
    teste("engajamento = 1*1 + 2*1 - 0.5*1 = 2.5",
          abs(post.engajamento - 2.5) < 1e-9, f"got {post.engajamento}")


def t_stats_plataforma():
    p = TwitterLike()
    p.cadastrar_perfil(PerfilPlataforma(agente_id="a", nome_exibicao="A"))
    p.postar("a", "x")
    s = p.stats()
    teste("stats.plataforma", s["plataforma"] == "twitter_like")
    teste("stats.n_posts=1", s["n_posts"] == 1)


def main():
    print("=== test_plataformas ===")
    for fn in [t_twitter_prioriza_seguidos, t_reddit_hot_score, t_linkedin_endorsement,
               t_tiktok_viral_shares, t_post_engajamento, t_stats_plataforma]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
