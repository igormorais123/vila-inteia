"""Testes filtro /conversas/llm-only (Onda 76)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


PADROES_HEURISTICA = (
    "Como eu sempre digo",
    "Boa conversa. Devemos continuar",
    "Essa é uma perspectiva válida. Mas considere também",
    "Conte-me mais sobre sua visão",
)


def filtrar(convs, limite=20):
    """Replica filtro de api/rotas_vila.py:conversas_llm_only."""
    out = []
    for c in convs[-limite * 3:]:
        turnos = c.get("turnos", [])
        if len(turnos) >= 4:
            tem_template = any(
                isinstance(t, (list, tuple)) and len(t) >= 2
                and any(p in str(t[1]) for p in PADROES_HEURISTICA)
                for t in turnos
            )
            if not tem_template:
                out.append(c)
        if len(out) >= limite:
            break
    return out


def t_filtra_template_como_eu_sempre_digo():
    convs = [{
        "parceiro_nome": "Steve Jobs",
        "turnos": [
            ("Oprah", "Olá Steve."),
            ("Steve", "Claro Oprah."),
            ("Oprah", "Como eu sempre digo: 'You get a...'"),
            ("Steve", "Essa é uma perspectiva válida. Mas considere também..."),
            ("Oprah", "Boa conversa. Devemos continuar isso em breve."),
        ],
    }]
    teste("template heurística filtrada", len(filtrar(convs)) == 0)


def t_aceita_llm_rica():
    convs = [{
        "parceiro_nome": "Satya Nadella",
        "turnos": [
            ("Munger", "Inversão sempre. Pense de trás para frente."),
            ("Nadella", "Don't be a know-it-all; be a learn-it-all."),
            ("Munger", "Concorda Charlie."),
            ("Nadella", "Aplicar conhecimento prá vida."),
        ],
    }]
    teste("conversa LLM aceita", len(filtrar(convs)) == 1)


def t_filtra_curtas_menos_4_turnos():
    convs = [{
        "parceiro_nome": "X",
        "turnos": [("A", "oi"), ("B", "oi")],
    }]
    teste("3 turnos: rejeita", len(filtrar(convs)) == 0)


def t_lista_e_tupla_aceitos():
    convs = [
        {"parceiro_nome": "A", "turnos": [["X","oi"],["Y","tudo"],["X","ok"],["Y","fim"]]},
        {"parceiro_nome": "B", "turnos": [("X","oi"),("Y","tudo"),("X","ok"),("Y","fim")]},
    ]
    teste("list e tuple ambos passam", len(filtrar(convs)) == 2)


def t_respeita_limite():
    convs = [
        {"parceiro_nome": str(i), "turnos": [("A","x"),("B","y"),("A","z"),("B","w")]}
        for i in range(50)
    ]
    teste("limite=10 cap result", len(filtrar(convs, limite=10)) == 10)


def t_padrao_essa_e_perspectiva_filtra():
    convs = [{
        "parceiro_nome": "Z",
        "turnos": [
            ("A", "oi"), ("B", "oi"),
            ("A", "tema"),
            ("B", "Essa é uma perspectiva válida. Mas considere também..."),
        ],
    }]
    teste("padrão 'Essa é uma perspectiva' filtra", len(filtrar(convs)) == 0)


def main():
    print("=== test_conversas_llm_only ===")
    for fn in [t_filtra_template_como_eu_sempre_digo, t_aceita_llm_rica,
               t_filtra_curtas_menos_4_turnos, t_lista_e_tupla_aceitos,
               t_respeita_limite, t_padrao_essa_e_perspectiva_filtra]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
