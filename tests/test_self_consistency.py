"""Testes Onda 128: self-consistency multi-sample."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.self_consistency import (
    sample_multipla, consultar_panel_self_consistency,
)

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


def t_sample_multipla_3_amostras():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A")})
    probs_mock = [70, 75, 65]
    i = [0]
    def mock(**k):
        p = probs_mock[i[0] % len(probs_mock)]; i[0] += 1
        return f"PROBABILIDADE FINAL: {p}%"
    r = sample_multipla("A", "x", sim, mock, n_samples=3)
    teste("3 samples retornados", r["n_samples"] == 3)
    teste("mediana = 0.70", r["prob_mediana"] == 0.70)
    teste("3 validas", r["n_validas"] == 3)


def t_sample_multipla_temperaturas_diversas():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A")})
    temps = []
    def mock(**k):
        temps.append(k["temperatura"])
        return "PROBABILIDADE FINAL: 50%"
    sample_multipla("A", "x", sim, mock, n_samples=3)
    teste("3 temperaturas distintas", len(set(temps)) == 3)


def t_sample_multipla_mediana_ignora_none():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A")})
    respostas = ["PROBABILIDADE FINAL: 80%", "sem numero", "PROBABILIDADE FINAL: 60%"]
    i = [0]
    def mock(**k):
        r = respostas[i[0]]; i[0] += 1
        return r
    r = sample_multipla("A", "x", sim, mock, n_samples=3)
    teste("n_validas=2", r["n_validas"] == 2)
    # mediana de [0.8, 0.6] = 0.7
    teste("mediana = 0.70", r["prob_mediana"] == 0.70)


def t_panel_self_consistency_smoke():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({
        "A": _MockPersona("A"),
        "B": _MockPersona("B"),
    })
    def mock(**k): return "PROBABILIDADE FINAL: 70%"
    r = consultar_panel_self_consistency(
        "evento x", ["A","B"], sim, llm_fn=mock,
        n_samples_por_persona=2, chain_of_thought=False,
    )
    teste("2 personas", r["n_personas"] == 2)
    teste("prob ~0.7", abs(r["prob_agregada"] - 0.7) < 0.01)
    teste("per_persona tem self_consistency",
          all("self_consistency" in p for p in r["per_persona"]))


def t_panel_self_consistency_com_pesos():
    from engine.persona_chat import resetar_historico
    resetar_historico()
    sim = _MockSim({"A": _MockPersona("A"), "B": _MockPersona("B")})
    i = [0]
    def mock(**k):
        # A sempre 90%, B sempre 10%
        persona_is_A = "Você é A" in k["system_prompt"]
        return "PROBABILIDADE FINAL: 90%" if persona_is_A else "PROBABILIDADE FINAL: 10%"
    r = consultar_panel_self_consistency(
        "x", ["A","B"], sim, llm_fn=mock,
        n_samples_por_persona=2,
        pesos_persona={"A": 10.0, "B": 1.0},
        chain_of_thought=False,
    )
    # Weighted: 10*0.9 + 1*0.1 = 9.1 / 11 ≈ 0.827
    teste(f"weighted ~0.83 (got {r['prob_agregada']:.3f})",
           abs(r["prob_agregada"] - 0.827) < 0.01)


def main():
    print("=== test_self_consistency ===")
    for fn in [t_sample_multipla_3_amostras,
               t_sample_multipla_temperaturas_diversas,
               t_sample_multipla_mediana_ignora_none,
               t_panel_self_consistency_smoke,
               t_panel_self_consistency_com_pesos]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
