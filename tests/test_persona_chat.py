"""Testes Onda 86: persona chat."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.persona_chat import (
    chat_com_persona, resetar_historico, historico_persona_public,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


class _MockPersona:
    def __init__(self, nome="Steve Jobs"):
        self.nome_exibicao = nome
    def gerar_prompt_sistema(self):
        return f"Você é {self.nome_exibicao}, CEO Apple."


class _MockSim:
    def __init__(self, personas):
        self.personas = personas


def _reset():
    resetar_historico()


def t_persona_inexistente():
    _reset()
    sim = _MockSim({})
    out = chat_com_persona("CL999", "olá", sim)
    teste("persona inexistente: erro", out.get("erro") is not None)
    teste("resposta None", out["resposta"] is None)


def t_pergunta_vazia():
    _reset()
    sim = _MockSim({"CL001": _MockPersona()})
    out = chat_com_persona("CL001", "", sim)
    teste("pergunta vazia: erro 'vazia'", "vazia" in (out.get("erro") or ""))


def t_chat_basico_mock():
    _reset()
    sim = _MockSim({"CL001": _MockPersona("Elon Musk")})
    chamadas = []
    def mock(mensagens, modelo, max_tokens, temperatura, system_prompt="", bypass_step_cap=False):
        chamadas.append({"sys": system_prompt[:80], "bypass": bypass_step_cap, "n_msg": len(mensagens)})
        return "Mars or bust. Aim for impossible, settle for extraordinary."
    out = chat_com_persona("CL001", "pq Mars?", sim, llm_fn=mock)
    teste("resposta não vazia", bool(out["resposta"]))
    teste("bypass_step_cap=True", chamadas[0]["bypass"] is True)
    teste("system prompt inclui Elon Musk", "Elon Musk" in chamadas[0]["sys"])
    teste("n_turnos=1", out["n_turnos_historico"] == 1)


def t_historico_acumula():
    _reset()
    sim = _MockSim({"CL002": _MockPersona("Warren Buffett")})
    resps = ["Invista em valor.", "Long-term compounding.", "Circle of competence."]
    i = [0]
    def mock(mensagens, modelo, max_tokens, temperatura, system_prompt="", bypass_step_cap=False):
        r = resps[i[0]]; i[0] += 1
        return r
    for q in ["valor?", "prazo?", "risco?"]:
        chat_com_persona("CL002", q, sim, llm_fn=mock)
    h = historico_persona_public("CL002")
    teste("histórico 3 turnos", h["n_turnos"] == 3)
    teste("turno 0 pergunta = valor?", h["turnos"][0]["pergunta"] == "valor?")
    teste("turno 2 resposta = Circle...",
          h["turnos"][2]["resposta"].startswith("Circle"))


def t_reset_limpa():
    _reset()
    sim = _MockSim({"CL003": _MockPersona()})
    def mock(**k): return "ok"
    chat_com_persona("CL003", "oi", sim, llm_fn=mock)
    teste("pré-reset: 1 turno", historico_persona_public("CL003")["n_turnos"] == 1)
    resetar_historico("CL003")
    teste("pós-reset: 0 turnos", historico_persona_public("CL003")["n_turnos"] == 0)


def t_llm_falha_retorna_erro_gracioso():
    _reset()
    sim = _MockSim({"CL004": _MockPersona()})
    def quebrado(**k): raise RuntimeError("boom")
    out = chat_com_persona("CL004", "teste", sim, llm_fn=quebrado)
    teste("LLM erro: resposta None", out["resposta"] is None)
    teste("erro mencionado", "error" in (out["erro"] or "").lower())
    teste("histórico não corrompido",
          historico_persona_public("CL004")["n_turnos"] == 0)


def t_llm_vazio_trata():
    _reset()
    sim = _MockSim({"CL005": _MockPersona()})
    def mock(**k): return None
    out = chat_com_persona("CL005", "oi", sim, llm_fn=mock)
    teste("LLM vazio: resposta None", out["resposta"] is None)
    teste("erro 'quota/circuit'", "quota" in (out["erro"] or "").lower() or "circuit" in (out["erro"] or "").lower())


def t_historico_max_10():
    _reset()
    sim = _MockSim({"CL006": _MockPersona()})
    def mock(**k): return "ok"
    for i in range(15):
        chat_com_persona("CL006", f"q{i}", sim, llm_fn=mock)
    h = historico_persona_public("CL006")
    teste("histórico capped a 10", h["n_turnos"] == 10)
    teste("últimos 10 preservados, primeiro = q5",
          h["turnos"][0]["pergunta"] == "q5")


def main():
    print("=== test_persona_chat ===")
    for fn in [t_persona_inexistente, t_pergunta_vazia, t_chat_basico_mock,
               t_historico_acumula, t_reset_limpa,
               t_llm_falha_retorna_erro_gracioso, t_llm_vazio_trata,
               t_historico_max_10]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
