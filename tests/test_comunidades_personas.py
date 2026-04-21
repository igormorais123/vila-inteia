"""Testes Onda 84: comunidades-personas (Louvain)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.comunidades_personas import detectar_comunidades

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _conv(ini, parc, n=4):
    return {"parceiro_nome": parc, "topico": "x",
             "turnos": [(ini, "oi") for _ in range(n)]}


def t_grafo_vazio():
    out = detectar_comunidades([])
    teste("vazio: n_personas=0", out["n_personas"] == 0)
    teste("vazio: n_comunidades=0", out["n_comunidades"] == 0)


def t_uma_clique_uma_comunidade():
    convs = [_conv("A","B"), _conv("B","C"), _conv("A","C")]
    out = detectar_comunidades(convs, seed=1)
    teste("clique tudo conectado: 1 comunidade", out["n_comunidades"] == 1)
    teste("comunidade tem 3 personas", out["comunidades"][0]["tamanho"] == 3)


def t_dois_grupos_separados():
    """A-B-C isolado de X-Y-Z."""
    convs = [
        _conv("A","B"), _conv("B","C"), _conv("A","C"),
        _conv("X","Y"), _conv("Y","Z"), _conv("X","Z"),
    ]
    out = detectar_comunidades(convs, seed=1)
    teste("2 grupos disjuntos: ≥2 comunidades", out["n_comunidades"] >= 2)


def t_modularidade_positiva_em_grupos():
    convs = [
        _conv("A","B"), _conv("B","C"), _conv("A","C"),
        _conv("X","Y"), _conv("Y","Z"), _conv("X","Z"),
    ]
    out = detectar_comunidades(convs, seed=1)
    teste("modularidade > 0 em estrutura clara",
          out["modularidade"] > 0)


def t_personas_ordenadas():
    convs = [_conv("Z","A"), _conv("A","M"), _conv("Z","M")]
    out = detectar_comunidades(convs, seed=1)
    com = out["comunidades"][0]
    teste("personas ordenadas alfabeticamente",
          com["personas"] == sorted(com["personas"]))


def t_densidade_interna_clique_eq_1():
    convs = [_conv("A","B"), _conv("A","C"), _conv("B","C")]
    out = detectar_comunidades(convs, seed=1)
    teste("clique 3-personas: densidade ≈ 1.0",
          abs(out["comunidades"][0]["densidade_interna"] - 1.0) < 1e-9)


def t_n_conversas_contado():
    convs = [_conv("A","B"), _conv("A","B"), _conv("A","C")]
    out = detectar_comunidades(convs, seed=1)
    total = sum(c["n_conversas_total"] for c in out["comunidades"])
    teste("soma conv por comunidade = 6 (3 conv * 2 lados)", total == 6)


def t_resolution_afeta_n_comunidades():
    """Resolution maior → mais comunidades."""
    convs = [_conv(f"A{i}", f"B{i}") for i in range(5)]
    out_low = detectar_comunidades(convs, seed=1, resolution=0.5)
    out_high = detectar_comunidades(convs, seed=1, resolution=3.0)
    teste("resolution alta ≥ baixa em n_comunidades",
          out_high["n_comunidades"] >= out_low["n_comunidades"])


def main():
    print("=== test_comunidades_personas ===")
    for fn in [t_grafo_vazio, t_uma_clique_uma_comunidade,
               t_dois_grupos_separados, t_modularidade_positiva_em_grupos,
               t_personas_ordenadas, t_densidade_interna_clique_eq_1,
               t_n_conversas_contado, t_resolution_afeta_n_comunidades]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
