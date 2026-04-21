"""Testes Onda 83: influencia personas (NetworkX centrality)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.influencia_personas import ranking_influencia, construir_grafo_conversas

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _conv(ini, parc, n_turnos=4):
    return {
        "parceiro_nome": parc,
        "topico": "x",
        "turnos": [(ini, "oi") for _ in range(n_turnos)],
    }


def t_grafo_vazio():
    g = construir_grafo_conversas([])
    teste("grafo vazio: 0 nós", g.number_of_nodes() == 0)
    out = ranking_influencia([])
    teste("ranking vazio: aviso", "aviso" in out)
    teste("ranking vazio: ranking=[]", out["ranking"] == [])


def t_grafo_simples_dois_nos():
    convs = [_conv("Steve Jobs", "Bill Gates")]
    g = construir_grafo_conversas(convs)
    teste("2 nós", g.number_of_nodes() == 2)
    teste("1 edge", g.number_of_edges() == 1)


def t_weight_acumula():
    convs = [_conv("A", "B"), _conv("A", "B"), _conv("A", "B")]
    g = construir_grafo_conversas(convs)
    teste("weight acumula 3", g["A"]["B"]["weight"] == 3)


def t_ignora_self_loop():
    convs = [_conv("A", "A")]
    g = construir_grafo_conversas(convs)
    teste("self-loop ignorado", g.number_of_edges() == 0)


def t_ranking_ordenado_desc():
    # A é hub: conversa com B, C, D, E
    convs = [_conv("A", "B"), _conv("A", "C"), _conv("A", "D"), _conv("A", "E")]
    out = ranking_influencia(convs, top_n=10)
    teste("hub A no top-1", out["ranking"][0]["persona"] == "A")
    scores = [r["score"] for r in out["ranking"]]
    teste("scores ordenados desc",
          all(scores[i] >= scores[i+1] for i in range(len(scores)-1)))


def t_n_parceiros_unicos():
    convs = [_conv("A", "B"), _conv("A", "C"), _conv("A", "B")]
    out = ranking_influencia(convs, top_n=10)
    a = next(r for r in out["ranking"] if r["persona"] == "A")
    teste("A: 2 parceiros únicos (B, C)", a["n_parceiros_unicos"] == 2)
    teste("A: 3 conversas", a["n_conversas"] == 3)


def t_top_n_limita():
    convs = [_conv(f"P{i}", f"Q{i}") for i in range(20)]
    out = ranking_influencia(convs, top_n=5)
    teste("top_n=5 limita", len(out["ranking"]) == 5)


def t_centralities_presentes():
    convs = [_conv("A", "B"), _conv("B", "C")]
    out = ranking_influencia(convs, top_n=10)
    r = out["ranking"][0]
    chaves = {"persona", "score", "degree_centrality", "betweenness_centrality",
              "eigenvector_centrality", "pagerank", "n_conversas", "n_parceiros_unicos"}
    teste("todas chaves presentes", chaves.issubset(set(r.keys())))


def t_ponte_tem_betweenness_alto():
    """B é a única ponte entre {A,A2} e {C,C2} → betweenness alto."""
    convs = [_conv("A", "B"), _conv("A2", "B"),
             _conv("B", "C"), _conv("B", "C2")]
    out = ranking_influencia(convs, top_n=10)
    b = next(r for r in out["ranking"] if r["persona"] == "B")
    others = [r["betweenness_centrality"] for r in out["ranking"] if r["persona"] != "B"]
    teste("B é a ponte (betweenness alto)",
          b["betweenness_centrality"] >= max(others))


def t_n_personas_e_n_edges():
    convs = [_conv("A", "B"), _conv("B", "C"), _conv("C", "D")]
    out = ranking_influencia(convs, top_n=20)
    teste("n_personas = 4", out["n_personas"] == 4)
    teste("n_edges = 3", out["n_edges"] == 3)
    teste("n_conversas = 3", out["n_conversas"] == 3)


def t_conversa_sem_turnos_ignorada():
    convs = [{"parceiro_nome": "X", "topico": "y", "turnos": []}]
    out = ranking_influencia(convs)
    teste("conversa sem turnos: ranking vazio", out["ranking"] == [])


def main():
    print("=== test_influencia_personas ===")
    for fn in [t_grafo_vazio, t_grafo_simples_dois_nos, t_weight_acumula,
               t_ignora_self_loop, t_ranking_ordenado_desc, t_n_parceiros_unicos,
               t_top_n_limita, t_centralities_presentes,
               t_ponte_tem_betweenness_alto, t_n_personas_e_n_edges,
               t_conversa_sem_turnos_ignorada]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
