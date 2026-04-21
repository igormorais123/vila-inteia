"""Testes Onda 121: few-shot examples em backtest."""

from __future__ import annotations
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.backtest_real import _build_few_shot_block, consultar_panel, rodar_backtest

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_build_vazio():
    teste("None → vazio", _build_few_shot_block(None) == "")
    teste("[] → vazio", _build_few_shot_block([]) == "")


def t_build_format():
    exs = [
        {"contexto": "evento A", "outcome_real": 1, "probabilidade_prior": 0.6},
        {"contexto": "evento B", "outcome_real": 0, "probabilidade_prior": 0.4},
    ]
    out = _build_few_shot_block(exs)
    teste("contém 'ACONTECEU'", "ACONTECEU" in out)
    teste("contém 'NÃO ACONTECEU'", "NÃO ACONTECEU" in out)
    teste("contém prior 60%", "60%" in out)
    teste("contém contexto A", "evento A" in out)


def t_build_cap_n_max():
    exs = [{"contexto": f"evt_x{i}", "outcome_real": 1, "probabilidade_prior": 0.5}
            for i in range(10)]
    out = _build_few_shot_block(exs, n_max=3)
    # Conta token único evt_x que só aparece nos exemplos
    teste("só 3 de 10", out.count("evt_x") == 3)


class _MockPersona:
    def __init__(self, nome): self.nome_exibicao = nome
    def gerar_prompt_sistema(self): return f"Você é {self.nome_exibicao}."


class _MockSim:
    def __init__(self, personas): self.personas = personas


def t_consultar_panel_injeta_exemplos():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"CL001": _MockPersona("Musk")})
    prompts = []
    def mock(mensagens, modelo, max_tokens, temperatura, system_prompt="", bypass_step_cap=False):
        prompts.append(mensagens[0]["content"])
        return "Probabilidade 75%."
    exs = [{"contexto": "passado", "outcome_real": 1, "probabilidade_prior": 0.5}]
    consultar_panel("evento atual", ["CL001"], sim, llm_fn=mock, few_shot_exemplos=exs)
    teste("prompt injeta few-shot", "passado" in prompts[0] and "ACONTECEU" in prompts[0])


def t_rodar_backtest_walk_forward():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    csv = """evento_id,data,contexto,outcome_real,probabilidade_prior
e1,2026-01-01,"alpha",1,0.6
e2,2026-01-02,"beta",1,0.5
e3,2026-01-03,"gamma",0,0.4
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv); p = f.name
    try:
        sim = _MockSim({"CL001": _MockPersona("X")})
        prompts = []
        def mock(mensagens, modelo, max_tokens, temperatura, system_prompt="", bypass_step_cap=False):
            prompts.append(mensagens[-1]["content"])
            return "Probabilidade 70%."
        r = rodar_backtest(p, sim, persona_ids=["CL001"], llm_fn=mock, few_shot_k=2)
        teste("3 eventos", r["n_eventos"] == 3)
        teste("e1: sem exemplos", "Exemplos passados" not in prompts[0])
        teste("e2: 1 exemplo",
              "Exemplos passados" in prompts[1] and "alpha" in prompts[1])
        teste("e3: 2 exemplos (últimos)",
              "Exemplos passados" in prompts[2] and "alpha" in prompts[2] and "beta" in prompts[2])
    finally:
        os.unlink(p)


def t_few_shot_k_zero_disable():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    csv = """evento_id,data,contexto,outcome_real,probabilidade_prior
e1,2026-01-01,"x",1,0.5
e2,2026-01-02,"y",1,0.5
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv); p = f.name
    try:
        sim = _MockSim({"CL001": _MockPersona("X")})
        prompts = []
        def mock(**k):
            prompts.append(k["mensagens"][-1]["content"])
            return "Probabilidade 50%."
        rodar_backtest(p, sim, persona_ids=["CL001"], llm_fn=mock, few_shot_k=0)
        teste("k=0 desabilita",
              all("Exemplos passados" not in pr for pr in prompts))
    finally:
        os.unlink(p)


def main():
    print("=== test_few_shot ===")
    for fn in [t_build_vazio, t_build_format, t_build_cap_n_max,
               t_consultar_panel_injeta_exemplos, t_rodar_backtest_walk_forward,
               t_few_shot_k_zero_disable]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
