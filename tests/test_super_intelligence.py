"""Testes Onda 81: super-intelligence (meta forecast + recomendacao + LLM)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.super_intelligence import gerar_super_intelligence

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


class _MockTraj:
    def __init__(self, estados):
        self.estados = list(estados); self.steps = list(range(len(estados)))
        self.mules_detectados = []
    def ultimo_estado(self): return self.estados[-1] if self.estados else "bootstrap"
    def distribuicao_historica(self):
        from collections import Counter
        c = Counter(self.estados); n = sum(c.values()) or 1
        return {k: v/n for k, v in c.items()}


class _MockRastreador:
    def __init__(self, traj): self.trajetoria = traj


def t_basico_sem_llm():
    rast = _MockRastreador(_MockTraj(["expansao", "expansao"]))
    out = gerar_super_intelligence(
        horizonte=5, outcome_desejado="equilibrio",
        rastreador=rast, conversas_recentes=[], com_sintese_llm=False,
    )
    teste("forecast presente", "forecast" in out)
    teste("recomendacao presente", "recomendacao" in out)
    teste("horizonte = 5", out["horizonte"] == 5)
    teste("outcome = equilibrio", out["outcome_desejado"] == "equilibrio")
    teste("sem briefing", "briefing_executivo" not in out)


def t_forecast_e_recomendacao_alinhados():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    out = gerar_super_intelligence(
        horizonte=10, outcome_desejado="equilibrio",
        rastreador=rast, conversas_recentes=[], com_sintese_llm=False,
    )
    teste("ambos usam mesmo estado_atual",
          out["forecast"]["estado_atual"] == out["recomendacao"]["estado_atual"])
    teste("ambos usam horizonte=10",
          out["forecast"]["horizonte"] == 10 and out["recomendacao"]["horizonte"] == 10)


def t_outcome_invalido_propaga_erro():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    erro = None
    try:
        gerar_super_intelligence(outcome_desejado="estado_zoado",
                                  rastreador=rast, com_sintese_llm=False)
    except ValueError as e: erro = str(e)
    teste("outcome inválido → ValueError", erro is not None)


def t_briefing_llm_mock():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    chamadas = []
    def mock(mensagens, modelo, max_tokens, temperatura, bypass_step_cap=False):
        chamadas.append({"prompt_size": len(mensagens[0]["content"]),
                          "bypass": bypass_step_cap})
        return "Diagnóstico: Vila estável. Risco: polarização. Ação: manter Helena vigilante. KPI: P(equilibrio)>50%."

    out = gerar_super_intelligence(
        horizonte=5, outcome_desejado="equilibrio",
        rastreador=rast, conversas_recentes=[], com_sintese_llm=True, llm_fn=mock,
    )
    teste("briefing presente", "briefing_executivo" in out)
    teste("briefing 1 LLM call (sub-funções não chamam LLM)", len(chamadas) == 1)
    teste("bypass_step_cap=True", chamadas[0]["bypass"] is True)


def t_llm_falha_sem_briefing():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    def quebrado(*a, **k): raise RuntimeError("boom")
    out = gerar_super_intelligence(
        horizonte=3, outcome_desejado="equilibrio",
        rastreador=rast, conversas_recentes=[], com_sintese_llm=True, llm_fn=quebrado,
    )
    teste("LLM falha → sem briefing", "briefing_executivo" not in out)
    teste("payload core OK", "forecast" in out and "recomendacao" in out)


def main():
    print("=== test_super_intelligence ===")
    for fn in [t_basico_sem_llm, t_forecast_e_recomendacao_alinhados,
               t_outcome_invalido_propaga_erro, t_briefing_llm_mock,
               t_llm_falha_sem_briefing]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
