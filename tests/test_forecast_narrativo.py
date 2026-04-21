"""Testes Onda 78: forecast-narrativo (Markov + LLM)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.forecast_narrativo import (
    gerar_forecast, _convs_llm_ricas, _top_n_estados,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


class _MockTrajetoria:
    def __init__(self, estados, mules):
        self.estados = list(estados)
        self.steps = list(range(len(estados)))
        self.mules_detectados = list(mules)
    def ultimo_estado(self):
        return self.estados[-1] if self.estados else "bootstrap"
    def distribuicao_historica(self):
        from collections import Counter
        c = Counter(self.estados)
        n = sum(c.values()) or 1
        return {k: v / n for k, v in c.items()}


class _MockRastreador:
    def __init__(self, traj):
        self.trajetoria = traj


def t_top_n_estados_ordena_desc():
    estados = ["a", "b", "c", "d"]
    dist = [0.1, 0.5, 0.2, 0.2]
    out = _top_n_estados(dist, estados, n=2)
    teste("top-1 = 'b'", out[0]["estado"] == "b")
    teste("top-1 prob = 0.5", abs(out[0]["prob"] - 0.5) < 1e-9)
    teste("top-2 size = 2", len(out) == 2)


def t_convs_llm_filtra_template():
    convs = [
        {"parceiro_nome": "X", "topico": "tema",
         "turnos": [("A", "oi"), ("B", "Como eu sempre digo: foo"),
                    ("A", "ok"), ("B", "sim")]},
        {"parceiro_nome": "Y", "topico": "real",
         "turnos": [("A", "Inversão sempre."),
                    ("B", "Concordo, e aplico aqui."),
                    ("A", "Bom raciocínio."),
                    ("B", "Voltemos amanhã.")]},
    ]
    out = _convs_llm_ricas(convs, max_conv=5)
    teste("filtra template, mantém rica", len(out) == 1 and out[0]["parceiro"] == "Y")


def t_forecast_basico_sem_llm():
    rast = _MockRastreador(_MockTrajetoria(
        estados=["bootstrap", "expansao", "expansao", "expansao"],
        mules=[],
    ))
    out = gerar_forecast(rastreador=rast, conversas_recentes=[],
                          horizonte=5, com_narrativa=False)
    teste("estado_atual = expansao", out["estado_atual"] == "expansao")
    teste("n_steps_observados = 4", out["n_steps_observados"] == 4)
    teste("horizonte = 5", out["horizonte"] == 5)
    teste("top_estados é list de 3", len(out["top_estados_horizonte"]) == 3)
    teste("entropia_inicial >= 0", out["entropia_inicial"] >= 0)
    teste("sem narrativa quando com_narrativa=False", "narrativa" not in out)
    teste("n_mules_recentes = 0", out["n_mules_recentes"] == 0)


def t_forecast_com_evidencias_e_mules():
    rast = _MockRastreador(_MockTrajetoria(
        estados=["bootstrap", "polarizacao", "polarizacao"],
        mules=[{"step": 5, "tipo": "anomalia"}],
    ))
    convs = [{"parceiro_nome": "Trump", "topico": "ego",
              "turnos": [("Ellison", "Oracle vence."),
                         ("Trump", "Meu Trump Tower é melhor."),
                         ("Ellison", "Modelos? você fala de modelos?"),
                         ("Trump", "Meu nome é o futuro.")]}]
    out = gerar_forecast(rastreador=rast, conversas_recentes=convs,
                          horizonte=10, com_narrativa=False)
    teste("evidencias_llm capturadas", len(out["evidencias_llm"]) == 1)
    teste("evidencia parceiro = Trump", out["evidencias_llm"][0]["parceiro"] == "Trump")
    teste("n_mules_recentes = 1", out["n_mules_recentes"] == 1)
    teste("mules_recentes len = 1", len(out["mules_recentes"]) == 1)


def t_forecast_narrativa_com_llm_mock():
    rast = _MockRastreador(_MockTrajetoria(
        estados=["expansao"], mules=[],
    ))
    chamadas = []
    def mock_llm(mensagens, modelo, max_tokens, temperatura, bypass_step_cap=False):
        chamadas.append({"prompt": mensagens[0]["content"][:100], "modelo": modelo,
                          "bypass": bypass_step_cap})
        return "  Vila tende a expansão estável; recomende Helena monitorar.  "

    out = gerar_forecast(rastreador=rast, conversas_recentes=[],
                          horizonte=5, com_narrativa=True, llm_fn=mock_llm)
    teste("narrativa presente", "narrativa" in out)
    teste("narrativa stripped", out.get("narrativa", "").startswith("Vila"))
    teste("LLM chamado uma vez", len(chamadas) == 1)
    teste("modelo = rapido", chamadas[0]["modelo"] == "rapido")
    teste("bypass_step_cap=True (não consome slot da sim)", chamadas[0]["bypass"] is True)


def t_forecast_llm_falha_devolve_sem_narrativa():
    rast = _MockRastreador(_MockTrajetoria(
        estados=["consenso_fragil"], mules=[],
    ))
    def llm_quebrado(*a, **k):
        raise RuntimeError("boom")

    out = gerar_forecast(rastreador=rast, conversas_recentes=[],
                          horizonte=3, com_narrativa=True, llm_fn=llm_quebrado)
    teste("LLM falha → narrativa ausente", "narrativa" not in out)
    teste("payload outras chaves OK", "estado_atual" in out and "top_estados_horizonte" in out)


def t_forecast_trajetoria_vazia_usa_bootstrap():
    rast = _MockRastreador(_MockTrajetoria(estados=[], mules=[]))
    out = gerar_forecast(rastreador=rast, conversas_recentes=[],
                          horizonte=3, com_narrativa=False)
    teste("vazio → estado_atual = bootstrap", out["estado_atual"] == "bootstrap")
    teste("vazio → n_steps = 0", out["n_steps_observados"] == 0)


def main():
    print("=== test_forecast_narrativo ===")
    for fn in [t_top_n_estados_ordena_desc, t_convs_llm_filtra_template,
               t_forecast_basico_sem_llm, t_forecast_com_evidencias_e_mules,
               t_forecast_narrativa_com_llm_mock,
               t_forecast_llm_falha_devolve_sem_narrativa,
               t_forecast_trajetoria_vazia_usa_bootstrap]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
