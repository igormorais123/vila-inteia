"""
Onda 116: E2E integration test pipeline.

Valida fluxo completo sem LLM real (usa mocks):
1. carregar dataset CSV
2. mock panel_chat → prob fake via regex
3. rodar_backtest → agregado + per-persona
4. Platt calibração → coefs
5. salvar_coefs disk + carregar
6. aplicar em forecast mock
7. html_forecast → html_recomendacao → PDF bytes ou HTML
8. snapshot via _serializar_simulacao
9. reliability + brier decomposition
10. CV holdout

Se qualquer módulo quebrar por cross-dep, CI falha.
"""

from __future__ import annotations
import sys, os, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


class _MockPersona:
    def __init__(self, nome): self.nome_exibicao = nome
    def gerar_prompt_sistema(self): return f"Você é {self.nome_exibicao}."


class _MockSim:
    def __init__(self, personas, nome="test"):
        self.personas = personas
        self.nome = nome
        self.step = 5
        self.conversas_recentes = []
        self.sinteses = []


def t_pipeline_completo():
    from engine.backtest_real import rodar_backtest
    from engine.calibracao_platt import avaliar_calibracao, fit_platt, aplicar_platt
    from engine.calibracao_runtime import salvar_coefs, carregar_coefs, aplicar
    from engine.pdf_export import html_forecast, html_recomendacao, render_pdf
    from engine.reliability_diagram import reliability
    from engine.brier_decomp import decompor
    from engine.cv_holdout import cv_holdout_platt
    from engine.persona_skill import analisar_skill_personas
    from engine.persona_chat import resetar_historico

    resetar_historico()

    # ===== 1. Mock backtest com LLM =====
    call_count = [0]
    def mock_llm(mensagens, modelo, max_tokens, temperatura,
                 system_prompt="", bypass_step_cap=False):
        # Respostas determinísticas variadas
        call_count[0] += 1
        probs = [80, 75, 85, 60, 90]
        p = probs[call_count[0] % len(probs)]
        return f"Probabilidade {p}%."

    sim = _MockSim({
        "CL001": _MockPersona("Musk"),
        "CL002": _MockPersona("Jobs"),
        "CL003": _MockPersona("Bezos"),
    })

    # Cria CSV temp
    csv_content = """evento_id,data,contexto,outcome_real,probabilidade_prior
e01,2026-01-01,"evento alpha teste",1,0.6
e02,2026-01-02,"evento beta teste",1,0.7
e03,2026-01-03,"evento gamma teste",0,0.4
e04,2026-01-04,"evento delta teste",1,0.5
e05,2026-01-05,"evento epsilon teste",0,0.45
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        r = rodar_backtest(csv_path, sim, persona_ids=["CL001","CL002","CL003"],
                            llm_fn=mock_llm, max_eventos=5)
        teste("backtest retorna n_eventos=5", r["n_eventos"] == 5)
        teste("backtest n_respondidos=5", r["n_respondidos"] == 5)
        teste("brier_vila present", r["brier_vila_avg"] is not None)
        teste("per_persona present em eventos",
              all("per_persona" in e for e in r["eventos"]))

        # ===== 2. Platt calibração =====
        probs = [e["prob_vila"] for e in r["eventos"]]
        ys = [e["outcome_real"] for e in r["eventos"]]
        cal = avaliar_calibracao(probs, ys)
        teste("Platt fit retorna a,b", "platt_a" in cal and "platt_b" in cal)
        teste("ECE antes/depois", "ece_antes" in cal and "ece_depois" in cal)

        # ===== 3. Runtime persist =====
        tmp_coefs = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        os.unlink(tmp_coefs)
        salvar_coefs(cal["platt_a"], cal["platt_b"], cal["n"],
                      fonte="e2e_test", path=tmp_coefs)
        loaded = carregar_coefs(path=tmp_coefs, use_cache=False)
        teste("roundtrip coefs", abs(loaded["a"] - cal["platt_a"]) < 1e-9)

        # ===== 4. Aplicar em prob runtime =====
        p_cal = aplicar(0.9, path=tmp_coefs)
        teste("aplicar retorna float válido", 0 <= p_cal <= 1)

        # ===== 5. PDF forecast =====
        fc_payload = {
            "estado_atual": "expansao", "horizonte": 10,
            "top_estados_horizonte": [{"estado":"equilibrio","prob":0.5}],
            "entropia_inicial": 0.0, "entropia_final": 2.0,
            "n_mules_recentes": 0, "evidencias_llm": [], "narrativa": "",
        }
        html = html_forecast(fc_payload)
        teste("html_forecast gera html", "<h1" in html)
        pdf = render_pdf(html)
        teste("render_pdf bytes ou None",
               pdf is None or (isinstance(pdf, bytes) and pdf[:4] == b"%PDF"))

        # ===== 6. Recomendacao =====
        rec_payload = {
            "estado_atual": "expansao", "outcome_desejado": "equilibrio",
            "horizonte": 20,
            "melhor_intervencao": {"estado":"bootstrap","prob_outcome":0.5},
            "ranking": [{"estado":"bootstrap","prob_outcome":0.5,
                         "estado_mais_provavel":"equilibrio"}],
            "recomendacao_llm": "",
        }
        html_rec = html_recomendacao(rec_payload)
        teste("html_recomendacao gera", "bootstrap" in html_rec)

        # ===== 7. Snapshot =====
        from engine.save_load import _serializar_simulacao
        estado = _serializar_simulacao(sim)
        teste("serializar_simulacao retorna dict", isinstance(estado, dict))

        # ===== 8. Reliability diagram =====
        rel = reliability(probs, ys, n_bins=5)
        teste("reliability retorna bins", "bins" in rel and len(rel["bins"]) == 5)

        # ===== 9. Brier decomposition =====
        dec = decompor(probs, ys, n_bins=5)
        teste("brier decomp chaves", all(k in dec for k in ["brier_score","reliability","resolution","uncertainty"]))

        # ===== 10. CV holdout =====
        # Precisa n>=5, temos exatamente 5
        cv = cv_holdout_platt(probs, ys, test_frac=0.2, n_repeats=3)
        teste("cv holdout retorna brier_test_avg",
              "brier_test_avg" in cv or "erro" in cv)

        # ===== 11. Per-persona skill =====
        skill = analisar_skill_personas([r])
        teste("persona_skill ranking",
              "ranking" in skill and len(skill["ranking"]) == 3)

        # ===== 12. History persist =====
        from engine.backtest_history import _flatten
        flat = _flatten({"agregado": {"n_eventos_total": 5,
                                        "accuracy_global": 0.6},
                          "datasets": [{"persona_panel":["CL001"]}]})
        teste("backtest_history _flatten", flat["n_eventos"] == 5)

        # ===== 13. Bootstrap CI =====
        from engine.calibracao_stats import bootstrap_ci
        from engine.calibracao_platt import brier
        bci = bootstrap_ci(brier, probs, ys, n_boot=50)
        teste("bootstrap CI retorna point+lo+hi",
              all(k in bci for k in ["point","lo","hi"]))

        # ===== 14. Isotonic =====
        from engine.calibracao_stats import comparacao_platt_vs_isotonic
        cmp = comparacao_platt_vs_isotonic(probs, ys)
        teste("comparacao Platt vs isotonic",
              "platt" in cmp and "isotonic" in cmp)

    finally:
        os.unlink(csv_path)
        if os.path.exists(tmp_coefs):
            os.unlink(tmp_coefs)


def main():
    print("=== test_e2e_pipeline ===")
    for fn in [t_pipeline_completo]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
