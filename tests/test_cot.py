"""Testes Onda 123: chain-of-thought reasoning."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.backtest_real import (
    extrair_probabilidade, _build_cot_prefix, consultar_panel,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_cot_prefix_format():
    cot = _build_cot_prefix()
    teste("cot tem passo-a-passo", "passo-a-passo" in cot.lower())
    teste("cot tem RACIOCÍNIO", "RACIOCÍNIO" in cot)
    teste("cot tem PROBABILIDADE FINAL", "PROBABILIDADE FINAL" in cot)


def t_extrair_prioriza_final():
    """Texto com % no raciocínio + FINAL ao final — deve pegar FINAL."""
    texto = (
        "RACIOCÍNIO: Base rate indica 30% histórico, mas drivers atuais elevam. "
        "PROBABILIDADE FINAL: 70%"
    )
    p = extrair_probabilidade(texto)
    teste(f"pegou FINAL 70% (got {p})", p == 0.70)


def t_extrair_final_com_dois_pontos_unicode():
    texto = "PROBABILIDADE FINAL：85%"
    p = extrair_probabilidade(texto)
    teste("unicode ：", p == 0.85)


def t_extrair_fallback_se_sem_final():
    texto = "Acho que 60% é razoável"
    p = extrair_probabilidade(texto)
    teste("sem FINAL: fallback primeiro %", p == 0.60)


def t_extrair_final_case_insensitive():
    texto = "probabilidade final: 55%"
    p = extrair_probabilidade(texto)
    teste("case insensitive", p == 0.55)


class _MockPersona:
    def __init__(self, nome): self.nome_exibicao = nome
    def gerar_prompt_sistema(self): return f"Você é {self.nome_exibicao}."


class _MockSim:
    def __init__(self, personas): self.personas = personas


def t_consultar_panel_cot_injetado():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"CL001": _MockPersona("Musk")})
    prompts = []
    def mock(**k):
        prompts.append(k["mensagens"][-1]["content"])
        return "RACIOCÍNIO: análise. PROBABILIDADE FINAL: 75%"
    r = consultar_panel("evento teste", ["CL001"], sim, llm_fn=mock,
                         chain_of_thought=True)
    teste("CoT no prompt", "passo-a-passo" in prompts[0])
    teste("extraiu FINAL=0.75", r["prob_agregada"] == 0.75)


def t_consultar_panel_sem_cot():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"CL002": _MockPersona("X")})
    prompts = []
    def mock(**k):
        prompts.append(k["mensagens"][-1]["content"])
        return "Probabilidade 60%"
    consultar_panel("x", ["CL002"], sim, llm_fn=mock, chain_of_thought=False)
    teste("sem CoT: prompt curto", "passo-a-passo" not in prompts[0])


def main():
    print("=== test_cot ===")
    for fn in [t_cot_prefix_format, t_extrair_prioriza_final,
               t_extrair_final_com_dois_pontos_unicode,
               t_extrair_fallback_se_sem_final,
               t_extrair_final_case_insensitive,
               t_consultar_panel_cot_injetado,
               t_consultar_panel_sem_cot]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
