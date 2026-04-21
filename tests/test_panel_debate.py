"""Testes Onda 124: multi-step debate."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.panel_debate import debate_panel, _dispersao, _format_round1_block

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


class _MockPersona:
    def __init__(self, nome): self.nome_exibicao = nome
    def gerar_prompt_sistema(self): return f"Você é {self.nome_exibicao}."


class _MockSim:
    def __init__(self, personas): self.personas = personas


def t_dispersao_basica():
    teste("1 prob std=0", _dispersao([0.5]) == 0)
    teste("iguais std=0", _dispersao([0.5, 0.5, 0.5]) == 0)
    teste("[0.2, 0.8] std > 0.3", _dispersao([0.2, 0.8]) > 0.3)


def t_format_round1_contem_respostas():
    per_persona = [
        {"persona_id": "A", "persona_nome": "Musk", "prob_extraida": 0.8,
         "resposta": "acho que sim"},
        {"persona_id": "B", "persona_nome": "Jobs", "prob_extraida": 0.3,
         "resposta": "acho que não"},
    ]
    block = _format_round1_block(per_persona)
    teste("inclui Musk 80%", "Musk" in block and "80%" in block)
    teste("inclui Jobs 30%", "Jobs" in block and "30%" in block)
    teste("pede revisão", "revise" in block.lower())


def t_debate_convergencia_baixa_disp_pula_r2():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A"), "B": _MockPersona("B")})
    calls = []
    def mock(**k):
        calls.append(k["mensagens"][-1]["content"])
        return "PROBABILIDADE FINAL: 70%"  # Todos concordam
    r = debate_panel("evento", ["A","B"], sim, llm_fn=mock,
                      dispersao_threshold=0.15)
    teste("baixa disp → 1 round", r["n_rounds"] == 1)
    teste("só 2 LLM calls (um por persona)", len(calls) == 2)


def t_debate_alta_disp_dispara_r2():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A"), "B": _MockPersona("B")})
    respostas = ["PROBABILIDADE FINAL: 90%", "PROBABILIDADE FINAL: 20%",
                 "PROBABILIDADE FINAL: 75%", "PROBABILIDADE FINAL: 65%"]
    i = [0]
    def mock(**k):
        r = respostas[i[0] % len(respostas)]; i[0] += 1
        return r
    r = debate_panel("x", ["A","B"], sim, llm_fn=mock,
                      dispersao_threshold=0.15)
    teste("alta disp → 2 rounds", r["n_rounds"] == 2)
    teste("rounds list size 2", len(r["rounds"]) == 2)
    teste("convergiu (r2 disp < r1)", r.get("convergiu") is True)


def t_debate_max_rounds_1_nunca_debate():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A"), "B": _MockPersona("B")})
    i = [0]
    def mock(**k):
        respostas = ["PROBABILIDADE FINAL: 90%", "PROBABILIDADE FINAL: 10%"]
        r = respostas[i[0] % 2]; i[0] += 1
        return r
    r = debate_panel("x", ["A","B"], sim, llm_fn=mock,
                      max_rounds=1)
    teste("max_rounds=1: sempre 1 round", r["n_rounds"] == 1)


def t_debate_retorna_dict_completo():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A")})
    def mock(**k): return "PROBABILIDADE FINAL: 50%"
    r = debate_panel("x", ["A"], sim, llm_fn=mock)
    for k in ["prob_agregada", "per_persona", "n_rounds", "dispersao_inicial"]:
        teste(f"campo {k} presente", k in r)


def main():
    print("=== test_panel_debate ===")
    for fn in [t_dispersao_basica, t_format_round1_contem_respostas,
               t_debate_convergencia_baixa_disp_pula_r2,
               t_debate_alta_disp_dispara_r2,
               t_debate_max_rounds_1_nunca_debate,
               t_debate_retorna_dict_completo]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
