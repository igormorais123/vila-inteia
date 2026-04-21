"""Testes Onda 131: LLM-as-judge."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.llm_judge import (
    avaliar_resposta, filtrar_panel_por_qualidade, _REGEX_SCORE,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_regex_score():
    m = _REGEX_SCORE.search("ANÁLISE: ok. QUALIDADE: 75/100")
    teste("extrai 75", m and m.group(1) == "75")
    m = _REGEX_SCORE.search("QUALIDADE: 60%")
    teste("percentage", m and m.group(1) == "60")
    m = _REGEX_SCORE.search("qualidade: 40")
    teste("case insensitive + no suffix", m and m.group(1) == "40")


def t_avaliar_resposta_sem_llm():
    r = avaliar_resposta("x", "y", 0.7, llm_fn=lambda **k: None)
    teste("LLM vazio → erro", r.get("erro") is not None)


def t_avaliar_resposta_score_alto():
    def mock(**k):
        return "ANÁLISE: bem justificado. QUALIDADE: 85/100"
    r = avaliar_resposta("x", "y", 0.7, llm_fn=mock)
    teste("score = 0.85", r["score"] == 0.85)
    teste("ok = True", r["ok"] is True)


def t_avaliar_resposta_score_baixo():
    def mock(**k):
        return "ANÁLISE: ruim. QUALIDADE: 30/100"
    r = avaliar_resposta("x", "y", 0.9, llm_fn=mock)
    teste("score = 0.30", r["score"] == 0.30)
    teste("ok = False", r["ok"] is False)


def t_avaliar_regex_falha():
    def mock(**k): return "sem score formatado"
    r = avaliar_resposta("x", "y", 0.7, llm_fn=mock)
    teste("regex falha → None", r["score"] is None)


def t_filtrar_panel_remove_low_quality():
    per_persona = [
        {"persona_id": "A", "prob_extraida": 0.8, "resposta": "bom raciocinio"},
        {"persona_id": "B", "prob_extraida": 0.2, "resposta": "mal raciocinio"},
        {"persona_id": "C", "prob_extraida": 0.6, "resposta": "medio"},
    ]
    i = [0]
    scores = ["85", "25", "60"]
    def mock(**k):
        s = scores[i[0]]; i[0] += 1
        return f"QUALIDADE: {s}/100"
    r = filtrar_panel_por_qualidade(per_persona, "contexto", llm_fn=mock, threshold=0.5)
    teste("annotated tem 3", len(r["per_persona_annotated"]) == 3)
    teste("filtrado tem 2 (B excluído)", len(r["per_persona_filtrado"]) == 2)
    teste("n_filtrados_out=1", r["n_filtrados_out"] == 1)
    # B tinha score 0.25 < 0.5
    filtrados_ids = [p["persona_id"] for p in r["per_persona_filtrado"]]
    teste("B fora do filtrado", "B" not in filtrados_ids)


def t_filtrar_panel_ignora_prob_none():
    per_persona = [
        {"persona_id": "A", "prob_extraida": None, "resposta": "x"},
    ]
    r = filtrar_panel_por_qualidade(per_persona, "x", llm_fn=lambda **k: "70/100",
                                      threshold=0.5)
    teste("prob None: annotated judge_score=None",
          r["per_persona_annotated"][0]["judge_score"] is None)


def main():
    print("=== test_llm_judge ===")
    for fn in [t_regex_score, t_avaliar_resposta_sem_llm,
               t_avaliar_resposta_score_alto, t_avaliar_resposta_score_baixo,
               t_avaliar_regex_falha, t_filtrar_panel_remove_low_quality,
               t_filtrar_panel_ignora_prob_none]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
