"""Testes Onda 79: counterfactual-narrativo (Pearl do-calc + LLM)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.counterfactual_narrativo import gerar_counterfactual, _top_n
import numpy as np

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


class _MockTraj:
    def __init__(self, estados):
        self.estados = list(estados)
        self.steps = list(range(len(estados)))
        self.mules_detectados = []
    def ultimo_estado(self):
        return self.estados[-1] if self.estados else "bootstrap"
    def distribuicao_historica(self):
        from collections import Counter
        c = Counter(self.estados); n = sum(c.values()) or 1
        return {k: v/n for k, v in c.items()}


class _MockRastreador:
    def __init__(self, traj):
        self.trajetoria = traj


def t_top_n_sorting():
    arr = np.array([0.05, 0.5, 0.2, 0.25])
    estados = ["a", "b", "c", "d"]
    out = _top_n(arr, estados, 3)
    teste("top1 = b", out[0]["estado"] == "b")
    teste("top2 = d", out[1]["estado"] == "d")
    teste("top3 = c", out[2]["estado"] == "c")


def t_basico_sem_narrativa():
    rast = _MockRastreador(_MockTraj(["bootstrap", "expansao"]))
    out = gerar_counterfactual(
        estado_alternativo="polarizacao",
        rastreador=rast, horizonte=5, com_narrativa=False,
    )
    teste("estado_factual_atual = expansao", out["estado_factual_atual"] == "expansao")
    teste("estado_alternativo = polarizacao", out["estado_alternativo"] == "polarizacao")
    teste("horizonte = 5", out["horizonte"] == 5)
    teste("top_factual len 3", len(out["top_estados_factual"]) == 3)
    teste("top_cf len 3", len(out["top_estados_counterfactual"]) == 3)
    teste("divergencia_tv >= 0", out["divergencia_tv"] >= 0)
    teste("divergencia_tv <= 1", out["divergencia_tv"] <= 1)
    teste("estados_ordem present", isinstance(out["estados_ordem"], list))
    teste("sem narrativa", "narrativa" not in out)


def t_estado_alternativo_invalido():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    erro = None
    try:
        gerar_counterfactual("estado_inexistente", rastreador=rast,
                              horizonte=5, com_narrativa=False)
    except ValueError as e:
        erro = str(e)
    teste("estado inválido levanta ValueError", erro is not None and "desconhecido" in erro)


def t_trajetoria_vazia_usa_bootstrap():
    rast = _MockRastreador(_MockTraj([]))
    out = gerar_counterfactual("expansao", rastreador=rast,
                                horizonte=3, com_narrativa=False)
    teste("vazio → factual = bootstrap", out["estado_factual_atual"] == "bootstrap")


def t_factual_igual_alternativo_div_baixa():
    """Se factual == alternativo, divergência deve ser 0."""
    rast = _MockRastreador(_MockTraj(["expansao"]))
    out = gerar_counterfactual("expansao", rastreador=rast,
                                horizonte=8, com_narrativa=False)
    teste("factual==alt → divergência = 0", out["divergencia_tv"] < 1e-9)


def t_factual_diferente_alt_div_positiva():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    out = gerar_counterfactual("polarizacao", rastreador=rast,
                                horizonte=3, com_narrativa=False)
    teste("estados diferentes → divergência > 0", out["divergencia_tv"] > 0)


def t_ate_polarizacao_vs_equilibrio_calculado():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    out = gerar_counterfactual("expansao", rastreador=rast,
                                horizonte=10, com_narrativa=False)
    teste("ATE field present", "ate_polarizacao_vs_equilibrio" in out)
    teste("ATE float", isinstance(out["ate_polarizacao_vs_equilibrio"], float))


def t_narrativa_com_llm_mock():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    chamadas = []
    def mock(mensagens, modelo, max_tokens, temperatura, bypass_step_cap=False):
        chamadas.append({"bypass": bypass_step_cap, "modelo": modelo})
        return "Forçar polarização aumenta risco de fragmentação. Helena deve mediar antes."
    out = gerar_counterfactual("polarizacao", rastreador=rast,
                                horizonte=5, com_narrativa=True, llm_fn=mock)
    teste("narrativa presente", "narrativa" in out)
    teste("LLM 1 chamada", len(chamadas) == 1)
    teste("bypass_step_cap=True", chamadas[0]["bypass"] is True)
    teste("modelo = rapido", chamadas[0]["modelo"] == "rapido")


def t_llm_falha_sem_narrativa():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    def quebrado(*a, **k): raise RuntimeError("boom")
    out = gerar_counterfactual("polarizacao", rastreador=rast,
                                horizonte=3, com_narrativa=True, llm_fn=quebrado)
    teste("LLM falha → sem narrativa", "narrativa" not in out)
    teste("payload outras chaves OK", "estado_factual_atual" in out)


def main():
    print("=== test_counterfactual_narrativo ===")
    for fn in [t_top_n_sorting, t_basico_sem_narrativa,
               t_estado_alternativo_invalido, t_trajetoria_vazia_usa_bootstrap,
               t_factual_igual_alternativo_div_baixa,
               t_factual_diferente_alt_div_positiva,
               t_ate_polarizacao_vs_equilibrio_calculado,
               t_narrativa_com_llm_mock, t_llm_falha_sem_narrativa]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
