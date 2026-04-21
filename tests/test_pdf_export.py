"""Testes Onda 105: PDF export."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.pdf_export import html_forecast, html_recomendacao, render_pdf

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_html_forecast_minimo():
    h = html_forecast({
        "estado_atual": "expansao", "horizonte": 10,
        "top_estados_horizonte": [{"estado": "equilibrio", "prob": 0.49}],
        "entropia_inicial": 0.0, "entropia_final": 2.11,
        "n_mules_recentes": 0, "evidencias_llm": [], "narrativa": "",
    })
    teste("html tem h1", "<h1" in h and "Vila INTEIA" in h)
    teste("html tem estado_atual", "expansao" in h)
    teste("html tem equilibrio", "equilibrio" in h)
    teste("html tem 49.0%", "49.0%" in h)


def t_html_forecast_com_calibracao():
    h = html_forecast({
        "estado_atual": "expansao", "horizonte": 10,
        "top_estados_horizonte": [],
        "entropia_inicial": 0, "entropia_final": 0,
        "calibracao": {"ativa": True, "a": -0.337, "b": 1.272, "n_amostras": 15},
    })
    teste("html menciona Platt ativa", "Calibração Platt ativa" in h)
    teste("html mostra n=15", "n=15" in h)


def t_html_recomendacao_minimo():
    h = html_recomendacao({
        "estado_atual": "expansao", "outcome_desejado": "equilibrio", "horizonte": 20,
        "melhor_intervencao": {"estado": "bootstrap", "prob_outcome": 0.503},
        "ranking": [{"estado": "bootstrap", "prob_outcome": 0.503,
                      "estado_mais_provavel": "equilibrio"}],
        "recomendacao_llm": "",
    })
    teste("rec HTML tem bootstrap", "bootstrap" in h)
    teste("rec HTML tem 50.3%", "50.3%" in h)


def t_render_pdf_retorna_bytes_ou_none():
    h = "<!DOCTYPE html><html><body><h1>Test</h1></body></html>"
    out = render_pdf(h)
    # Ou bytes (weasyprint OK) ou None (não instalado/erro)
    teste("PDF bytes ou None", out is None or isinstance(out, bytes))
    if isinstance(out, bytes):
        teste("PDF magic header", out[:4] == b"%PDF")


def main():
    print("=== test_pdf_export ===")
    for fn in [t_html_forecast_minimo, t_html_forecast_com_calibracao,
               t_html_recomendacao_minimo, t_render_pdf_retorna_bytes_ou_none]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
