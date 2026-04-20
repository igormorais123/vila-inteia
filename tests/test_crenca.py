"""
Testes do tracker de crenças (Onda 10 integração).
Rodar: PYTHONPATH=. python tests/test_crenca.py
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.cognitivo.crenca import TrackerCrencas


ok = 0
fail = 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {nome}")
    else:
        fail += 1
        print(f"  FAIL {nome} {det}")


def t_inicializar_e_obter():
    t = TrackerCrencas()
    t.inicializar_agente("a", "ia", 0.3)
    teste("obter crença inicializada", abs(t.obter("a", "ia") - 0.3) < 1e-9)
    teste("default p/ agente desconhecido", t.obter("x", "ia") == 0.5)


def t_atualizacao_aproxima_crencas():
    # Duas crenças dentro do epsilon → aproximam
    t = TrackerCrencas()
    t.inicializar_agente("a", "ia", 0.3)
    t.inicializar_agente("b", "ia", 0.6)
    na, nb = t.atualizar_apos_conversa("a", "b", "ia", influencia=0.3, epsilon=0.5)
    teste("a sobe em direção a b", na > 0.3 and na < 0.6, f"a={na}")
    teste("b desce em direção a a", nb < 0.6 and nb > 0.3, f"b={nb}")


def t_nao_atualiza_fora_do_epsilon():
    # Diferença grande → não muda
    t = TrackerCrencas()
    t.inicializar_agente("a", "ia", 0.1)
    t.inicializar_agente("b", "ia", 0.9)
    na, nb = t.atualizar_apos_conversa("a", "b", "ia", influencia=0.3, epsilon=0.3)
    teste("crenças distantes não mudam", abs(na - 0.1) < 1e-9 and abs(nb - 0.9) < 1e-9,
          f"na={na} nb={nb}")


def t_snapshot_captura_polarizacao():
    t = TrackerCrencas()
    for i in range(10):
        t.inicializar_agente(f"a{i}", "ia", 0.0)
        t.inicializar_agente(f"b{i}", "ia", 1.0)
    s = t.snapshot(step=1, topico="ia")
    teste("snapshot: 20 agentes", s.n_agentes == 20)
    teste("snapshot: valor_medio ≈ 0.5", abs(s.valor_medio - 0.5) < 1e-9)
    teste("snapshot: polarização alta", s.polarizacao > 0.9, f"pol={s.polarizacao}")


def t_historico_filtra_topico():
    t = TrackerCrencas()
    t.inicializar_agente("a", "ia", 0.5)
    t.inicializar_agente("a", "cripto", 0.3)
    t.snapshot(1, "ia")
    t.snapshot(1, "cripto")
    t.snapshot(2, "ia")
    teste("histórico ia: 2", len(t.historico("ia")) == 2)
    teste("histórico cripto: 1", len(t.historico("cripto")) == 1)
    teste("histórico total: 3", len(t.historico()) == 3)


def t_topicos_rastreados():
    t = TrackerCrencas()
    t.inicializar_agente("a", "t1", 0.5)
    t.inicializar_agente("b", "t2", 0.5)
    topicos = t.topicos_rastreados()
    teste("topicos rastreados", topicos == {"t1", "t2"}, f"got {topicos}")


def main():
    print("=== test_crenca ===")
    for fn in [
        t_inicializar_e_obter,
        t_atualizacao_aproxima_crencas,
        t_nao_atualiza_fora_do_epsilon,
        t_snapshot_captura_polarizacao,
        t_historico_filtra_topico,
        t_topicos_rastreados,
    ]:
        try:
            fn()
        except Exception as e:
            global fail
            fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")

    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
