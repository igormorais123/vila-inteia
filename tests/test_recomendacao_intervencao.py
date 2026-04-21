"""Testes Onda 80: recomendacao-intervencao (multi-CF sweep)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.recomendacao_intervencao import gerar_recomendacao

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
    def distribuicao_historica(self): return {}


class _MockRastreador:
    def __init__(self, traj): self.trajetoria = traj


def t_basico_sem_llm():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    out = gerar_recomendacao(outcome_desejado="equilibrio", horizonte=15,
                              rastreador=rast, com_recomendacao_llm=False)
    teste("estado_atual = expansao", out["estado_atual"] == "expansao")
    teste("outcome = equilibrio", out["outcome_desejado"] == "equilibrio")
    teste("horizonte = 15", out["horizonte"] == 15)
    teste("ranking não vazio", len(out["ranking"]) > 0)
    teste("melhor_intervencao presente", out["melhor_intervencao"] is not None)
    teste("sem recomendacao_llm", "recomendacao_llm" not in out)


def t_ranking_ordenado_desc():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    out = gerar_recomendacao(outcome_desejado="equilibrio", horizonte=20,
                              rastreador=rast, com_recomendacao_llm=False)
    probs = [r["prob_outcome"] for r in out["ranking"]]
    teste("ranking ordenado desc", all(probs[i] >= probs[i+1] for i in range(len(probs)-1)))


def t_outcome_invalido():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    erro = None
    try:
        gerar_recomendacao(outcome_desejado="estado_zoado",
                            rastreador=rast, com_recomendacao_llm=False)
    except ValueError as e: erro = str(e)
    teste("outcome inválido → ValueError", erro is not None)


def t_trajetoria_vazia_usa_bootstrap():
    rast = _MockRastreador(_MockTraj([]))
    out = gerar_recomendacao(outcome_desejado="equilibrio",
                              rastreador=rast, com_recomendacao_llm=False)
    teste("vazio → bootstrap", out["estado_atual"] == "bootstrap")


def t_melhor_intervencao_eh_top1():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    out = gerar_recomendacao(outcome_desejado="equilibrio",
                              rastreador=rast, com_recomendacao_llm=False)
    teste("melhor == ranking[0]",
          out["melhor_intervencao"]["estado"] == out["ranking"][0]["estado"])


def t_ranking_cobre_todos_estados():
    """Sweep deve avaliar todos estados do grafo."""
    rast = _MockRastreador(_MockTraj(["expansao"]))
    out = gerar_recomendacao(outcome_desejado="equilibrio", horizonte=5,
                              rastreador=rast, com_recomendacao_llm=False)
    teste("ranking cobre todos estados", len(out["ranking"]) == len(out["estados_ordem"]))


def t_recomendacao_llm_mock():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    chamadas = []
    def mock(mensagens, modelo, max_tokens, temperatura, bypass_step_cap=False):
        chamadas.append({"bypass": bypass_step_cap})
        return "Recomenda: forçar equilibrio. Custo: baixo. Risco: 12%."
    out = gerar_recomendacao(outcome_desejado="equilibrio", horizonte=10,
                              rastreador=rast, com_recomendacao_llm=True, llm_fn=mock)
    teste("recomendacao_llm presente", "recomendacao_llm" in out)
    teste("LLM 1 chamada", len(chamadas) == 1)
    teste("bypass=True", chamadas[0]["bypass"] is True)


def t_llm_falha_sem_recomendacao():
    rast = _MockRastreador(_MockTraj(["expansao"]))
    def quebrado(*a, **k): raise RuntimeError("boom")
    out = gerar_recomendacao(outcome_desejado="equilibrio",
                              rastreador=rast, com_recomendacao_llm=True, llm_fn=quebrado)
    teste("LLM falha → sem recomendacao_llm", "recomendacao_llm" not in out)
    teste("ranking ainda OK", len(out["ranking"]) > 0)


def main():
    print("=== test_recomendacao_intervencao ===")
    for fn in [t_basico_sem_llm, t_ranking_ordenado_desc, t_outcome_invalido,
               t_trajetoria_vazia_usa_bootstrap, t_melhor_intervencao_eh_top1,
               t_ranking_cobre_todos_estados, t_recomendacao_llm_mock,
               t_llm_falha_sem_recomendacao]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
