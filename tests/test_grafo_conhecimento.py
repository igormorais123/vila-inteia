"""Testes GraphRAG (Onda 6)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.memoria.grafo import (
    GrafoConhecimento, NoGrafo, Aresta,
    extrair_entidades, extrair_relacoes, indexar_texto,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_extracao_nomes_proprios():
    texto = "Sun Tzu debateu com Cleópatra sobre a estratégia de Steve Jobs."
    ents = extrair_entidades(texto)
    rotulos = {e.rotulo for e in ents}
    teste("extrai Sun Tzu", "Sun Tzu" in rotulos, f"got {rotulos}")
    teste("extrai Cleópatra", "Cleópatra" in rotulos)
    teste("extrai Steve Jobs", "Steve Jobs" in rotulos)


def t_stopwords_ignoradas():
    texto = "Vila INTEIA debate Brasil."
    ents = extrair_entidades(texto)
    rotulos = {e.rotulo for e in ents}
    teste("Vila ignorado", "Vila" not in rotulos)
    teste("INTEIA ignorado", "INTEIA" not in rotulos)
    teste("Brasil ignorado", "Brasil" not in rotulos)


def t_relacoes_coocorrencia():
    texto = "Sun Tzu respeita Cleópatra. Steve Jobs é diferente."
    ents = extrair_entidades(texto)
    arestas = extrair_relacoes(texto, ents)
    # Sun Tzu-Cleópatra em sentença 1; Steve Jobs sozinho em 2
    teste("1 aresta Sun Tzu-Cleópatra",
          len(arestas) == 1, f"got {len(arestas)}")


def t_grafo_add_busca():
    g = GrafoConhecimento()
    g.add_no(NoGrafo(id="a", tipo="pessoa", rotulo="Alice"))
    g.add_no(NoGrafo(id="b", tipo="pessoa", rotulo="Bob"))
    g.add_aresta(Aresta(origem="a", destino="b", relacao="conhece"))
    teste("vizinhos 1-hop", g.vizinhos("a", 1) == {"b"})
    teste("busca case-insensitive", len(g.buscar_por_rotulo("ali")) == 1)


def t_subgrafo_2hops():
    g = GrafoConhecimento()
    for i in ["a", "b", "c", "d"]:
        g.add_no(NoGrafo(id=i, tipo="x", rotulo=i.upper()))
    g.add_aresta(Aresta(origem="a", destino="b", relacao="r"))
    g.add_aresta(Aresta(origem="b", destino="c", relacao="r"))
    g.add_aresta(Aresta(origem="c", destino="d", relacao="r"))
    nos, arestas = g.subgrafo("a", hops=2)
    ids = {n.id for n in nos}
    teste("2-hops alcança a,b,c", ids == {"a", "b", "c"}, f"got {ids}")


def t_indexar_texto():
    g = GrafoConhecimento()
    texto = "Marco Aurélio e Sócrates debateram virtude. Sun Tzu ouviu calado."
    r = indexar_texto(g, texto)
    teste("indexa entidades",
          r["n_entidades"] >= 3, f"n={r['n_entidades']}")


def main():
    print("=== test_grafo_conhecimento ===")
    for fn in [t_extracao_nomes_proprios, t_stopwords_ignoradas, t_relacoes_coocorrencia,
               t_grafo_add_busca, t_subgrafo_2hops, t_indexar_texto]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
