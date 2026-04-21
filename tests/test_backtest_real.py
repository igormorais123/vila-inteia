"""Testes Onda 92: backtest real event prediction."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.backtest_real import (
    carregar_dataset, extrair_probabilidade, brier,
    consultar_panel, rodar_backtest,
)
from engine.persona_chat import resetar_historico

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_carregar_impeachment():
    d = carregar_dataset("data/backtest/impeachment_dilma_2016.csv")
    teste("10 eventos carregados", len(d) == 10)
    teste("imp01 outcome=1", d[0]["outcome_real"] == 1)
    teste("imp01 prior=0.55", abs(d[0]["probabilidade_prior"] - 0.55) < 1e-9)


def t_extrair_percent():
    teste("70% → 0.7", abs(extrair_probabilidade("probabilidade 70%") - 0.70) < 1e-9)
    teste("0.85 → 0.85", abs(extrair_probabilidade("P=0.85 aqui") - 0.85) < 1e-9)
    teste("sem numero → None", extrair_probabilidade("sei lá") is None)
    teste("fora de range → None ou valido",
           extrair_probabilidade("150%") is None or extrair_probabilidade("150%") <= 1)
    teste("0,6 → 0.6", abs(extrair_probabilidade("0,6") - 0.6) < 1e-9)
    # Onda 139: quando múltiplos %, pegar último (conclusão) sem header FINAL
    teste("últ match: 30% → 70%",
          extrair_probabilidade("30% rejeição, mas 70% a favor") == 0.70)
    teste("anchor scale não interfere",
          extrair_probabilidade("0-10% impossível. Resposta: 85%") == 0.85)
    teste("FINAL ainda prevalece",
          extrair_probabilidade("30% 50% PROBABILIDADE FINAL: 75%") == 0.75)


def t_brier_math():
    teste("brier acertou certeza = 0", brier(1.0, 1) == 0.0)
    teste("brier errou certeza = 1", brier(0.0, 1) == 1.0)
    teste("brier 0.5 = 0.25", brier(0.5, 1) == 0.25)


class _MockPersona:
    def __init__(self, nome): self.nome_exibicao = nome
    def gerar_prompt_sistema(self): return f"Você é {self.nome_exibicao}."


class _MockSim:
    def __init__(self, personas): self.personas = personas


def t_consultar_panel_extrai_prob():
    resetar_historico()
    sim = _MockSim({
        "CL001": _MockPersona("Musk"),
        "CL002": _MockPersona("Jobs"),
    })
    def mock(mensagens, modelo, max_tokens, temperatura, system_prompt="", bypass_step_cap=False):
        if "Musk" in system_prompt: return "Probabilidade 75%."
        return "Avalio em 0.65 de chance."
    p = consultar_panel("evento teste", ["CL001","CL002"], sim, llm_fn=mock)
    teste("n_validas=2", p["n_respostas_validas"] == 2)
    teste("agregado ~0.70", abs(p["prob_agregada"] - 0.70) < 1e-2)
    teste("2 per_persona", len(p["per_persona"]) == 2)


def t_backtest_miniflow_mock():
    resetar_historico()
    # CSV temporário
    import tempfile
    csv = """evento_id,data,contexto,outcome_real,probabilidade_prior
e1,2026-04-01,"evento alpha",1,0.5
e2,2026-04-02,"evento beta",0,0.5
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv)
        tmppath = f.name
    sim = _MockSim({"CL001": _MockPersona("A"), "CL002": _MockPersona("B")})
    def mock(mensagens, modelo, max_tokens, temperatura, system_prompt="", bypass_step_cap=False):
        # Vila responde 80% sempre
        return "Probabilidade 80%."
    r = rodar_backtest(tmppath, sim, persona_ids=["CL001","CL002"], llm_fn=mock)
    os.unlink(tmppath)
    teste("n_eventos=2", r["n_eventos"] == 2)
    teste("n_respondidos=2", r["n_respondidos"] == 2)
    # Vila sempre 80%, e1 real=1 → acertou (0.8>0.5), e2 real=0 → errou
    teste("accuracy=0.5", r["accuracy_vila"] == 0.5)
    # Brier Vila: (0.8-1)²=0.04 + (0.8-0)²=0.64 → avg 0.34
    teste("brier vila ~0.34", abs(r["brier_vila_avg"] - 0.34) < 1e-2)


def main():
    print("=== test_backtest_real ===")
    for fn in [t_carregar_impeachment, t_extrair_percent, t_brier_math,
               t_consultar_panel_extrai_prob, t_backtest_miniflow_mock]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
