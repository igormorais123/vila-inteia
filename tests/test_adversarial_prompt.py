"""Testes Onda 130: adversarial prompt debias."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.adversarial_prompt import consulta_adversarial, panel_adversarial

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


def t_consistente_pos_neg_soma_100():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A")})
    # P_1=0.7, P_0=0.3 (soma=1, consistente)
    respostas = ["PROBABILIDADE FINAL: 70%", "PROBABILIDADE FINAL: 30%"]
    i = [0]
    def mock(**k):
        r = respostas[i[0]]; i[0] += 1
        return r
    adv = consulta_adversarial("x", "A", sim, llm_fn=mock)
    teste("P_1 = 0.7", adv["prob_positiva"] == 0.7)
    teste("P_0 = 0.3", adv["prob_negativa"] == 0.3)
    teste("debias ≈ 0.7", abs(adv["prob_debias"] - 0.7) < 0.01)
    teste("consistencia = 1.0", adv["consistencia"] == 1.0)


def t_anchor_bias_detectado():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A")})
    # P_1=0.8 e P_0=0.4 (soma=1.2, LLM infla ambos framings)
    respostas = ["PROBABILIDADE FINAL: 80%", "PROBABILIDADE FINAL: 40%"]
    i = [0]
    def mock(**k):
        r = respostas[i[0]]; i[0] += 1
        return r
    adv = consulta_adversarial("x", "A", sim, llm_fn=mock)
    # debias = (0.8 + (1-0.4)) / 2 = (0.8 + 0.6) / 2 = 0.7
    teste("debias corrige inflação", abs(adv["prob_debias"] - 0.7) < 0.01)
    # consistencia = 1 - |0.8 + 0.4 - 1| = 1 - 0.2 = 0.8
    teste("consistencia < 1 (anchor bias)", adv["consistencia"] < 1.0)


def t_um_sem_resposta():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A")})
    respostas = ["PROBABILIDADE FINAL: 60%", "sem numero"]
    i = [0]
    def mock(**k):
        r = respostas[i[0]]; i[0] += 1
        return r
    adv = consulta_adversarial("x", "A", sim, llm_fn=mock)
    # P_2 None → debias = P_1
    teste("fallback P_1", adv["prob_debias"] == 0.6)


def t_ambos_sem_resposta():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A")})
    def mock(**k): return "sem numero"
    adv = consulta_adversarial("x", "A", sim, llm_fn=mock)
    teste("ambos None → debias None", adv["prob_debias"] is None)


def t_panel_adversarial():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A"), "B": _MockPersona("B")})
    def mock(**k): return "PROBABILIDADE FINAL: 70%"  # Todos igual
    r = panel_adversarial("x", ["A","B"], sim, llm_fn=mock)
    teste("n_personas=2", r["n_personas"] == 2)
    # Todos retornam 70% em ambos framings. debias = (0.7 + 0.3)/2 = 0.5
    teste("todos mesma resposta = ambíguo → ~0.5",
           abs(r["prob_agregada"] - 0.5) < 0.05)


def main():
    print("=== test_adversarial_prompt ===")
    for fn in [t_consistente_pos_neg_soma_100, t_anchor_bias_detectado,
               t_um_sem_resposta, t_ambos_sem_resposta, t_panel_adversarial]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
