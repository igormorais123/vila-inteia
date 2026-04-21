"""Testes Onda 126: backtest accuracy full-stack ensemble."""

from __future__ import annotations
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.backtest_acc import rodar_backtest_acc

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


def _csv(content):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(content)
    return f.name


CSV = """evento_id,data,contexto,outcome_real,probabilidade_prior
e1,2026-01-01,"alpha",1,0.6
e2,2026-01-02,"beta",1,0.7
e3,2026-01-03,"gamma",0,0.3
e4,2026-01-04,"delta",1,0.5
e5,2026-01-05,"epsilon",0,0.4
"""


def t_rodar_backtest_acc_smoke():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    path = _csv(CSV)
    try:
        sim = _MockSim({"A": _MockPersona("A"), "B": _MockPersona("B")})
        def mock(**k): return "RACIOCÍNIO: x. PROBABILIDADE FINAL: 70%"
        r = rodar_backtest_acc(
            path, sim, persona_ids=["A","B"], llm_fn=mock,
            usar_debate=False,  # sem debate pra menos calls
            aplicar_platt=False,  # evita runtime coefs
        )
        teste("n_eventos=5", r["n_eventos"] == 5)
        teste("accuracy_vila present", r["accuracy_vila_calibrada"] is not None)
        teste("brier_vila present", r["brier_vila_calibrada_avg"] is not None)
        teste("config registrada", r["configuracao"]["chain_of_thought"] is True)
    finally:
        os.unlink(path)


def t_bayesian_blend_puxa_pra_base_rate():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    path = _csv(CSV)
    try:
        sim = _MockSim({"A": _MockPersona("A")})
        def mock(**k): return "PROBABILIDADE FINAL: 90%"
        r = rodar_backtest_acc(
            path, sim, persona_ids=["A"], llm_fn=mock,
            usar_debate=False, aplicar_platt=False,
            usar_bayesian_blend=True, peso_vila=0.5,
        )
        # Evento 5 (último): base_rate = (1+1+0+1)/4 = 0.75 + Laplace = 5/6 ≈ 0.833
        # Vila diz 0.9, blend ~0.83-0.88 (puxa pra base rate)
        ultimo = r["eventos"][-1]
        teste(f"blend < vila_raw (got {ultimo['prob_blend_final']:.3f} vs {ultimo['prob_vila_raw']:.3f})",
              ultimo["prob_blend_final"] < ultimo["prob_vila_raw"])
    finally:
        os.unlink(path)


def t_disable_todas_features():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    path = _csv(CSV)
    try:
        sim = _MockSim({"A": _MockPersona("A")})
        def mock(**k): return "PROBABILIDADE FINAL: 50%"
        r = rodar_backtest_acc(
            path, sim, persona_ids=["A"], llm_fn=mock,
            few_shot_k=0, chain_of_thought=False, usar_debate=False,
            usar_bayesian_blend=False, aplicar_platt=False,
        )
        teste("todas features off: config coerente",
               r["configuracao"]["chain_of_thought"] is False and
               r["configuracao"]["usar_debate"] is False)
        teste("blend == raw quando bayesian off",
               all(e["prob_blend_final"] == e["prob_vila_calibrada"]
                    for e in r["eventos"] if e["prob_vila_calibrada"]))
    finally:
        os.unlink(path)


def main():
    print("=== test_backtest_acc ===")
    for fn in [t_rodar_backtest_acc_smoke,
               t_bayesian_blend_puxa_pra_base_rate,
               t_disable_todas_features]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
