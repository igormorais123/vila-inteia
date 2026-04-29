"""Tests for engine.helena_quality_scorer — Helena 6-dim quality check."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.helena_quality_scorer import score_helena_report, render_scorecard
from engine.helena_report import helena_report
from engine.forecast_result import ForecastResult


def _make_result(**kw) -> ForecastResult:
    defaults = dict(
        n=100, base_acc=0.72, base_brier=0.18,
        bootstrap_brier_ci=(0.16, 0.20),
        selective={0.30: {"coverage": 0.85, "brier": 0.15}},
        conformal={"coverage": 0.80},
        murphy={"reliability": 0.01, "resolution": 0.06,
                "uncertainty": 0.25, "brier": 0.18, "base_rate": 0.5},
        time_series_cv={"mean_brier": 0.18, "std_brier": 0.02, "n_folds": 5},
    )
    defaults.update(kw)
    return ForecastResult(**defaults)


def test_clean_report_scores_high():
    r = helena_report(_make_result())
    s = score_helena_report(r)
    assert s["score"] >= 83.0  # at least 5/6
    assert s["passed"] >= 5
    assert s["total"] == 6


def test_perfect_report_scores_100():
    fr = _make_result(n=120, base_brier=0.14, bootstrap_brier_ci=(0.12, 0.16))
    fr_dict = fr.as_dict()
    fr_dict["murphy"] = {"reliability": 0.005, "resolution": 0.08,
                          "uncertainty": 0.25, "brier": 0.14, "base_rate": 0.5}
    r = helena_report(fr_dict)
    s = score_helena_report(r)
    assert s["score"] == 100.0


def test_small_n_fails_dados():
    r = helena_report(_make_result(n=10))
    s = score_helena_report(r)
    assert not s["breakdown"]["dados_antes_opiniao"]["passed"]


def test_missing_red_team_fails():
    r = helena_report(_make_result())
    r["red_team"] = []
    s = score_helena_report(r)
    assert not s["breakdown"]["red_team_explicito"]["passed"]


def test_no_action_verb_fails_acionabilidade():
    r = helena_report(_make_result())
    r["recomendacao"] = "tudo certo"
    s = score_helena_report(r)
    assert not s["breakdown"]["acionabilidade"]["passed"]


def test_weasel_words_fail_sem_muro():
    r = helena_report(_make_result())
    r["achado"] = "Talvez bata baseline, possivelmente"
    s = score_helena_report(r)
    assert not s["breakdown"]["protocolo_sem_muro"]["passed"]


def test_missing_calibration_fails():
    r = helena_report(_make_result())
    r["calibracao_confianca"] = {"label": "", "justificativa": ""}
    s = score_helena_report(r)
    assert not s["breakdown"]["calibracao_confianca"]["passed"]


def test_shallow_mechanism_fails_profundidade():
    r = helena_report(_make_result())
    r["mecanismo"] = "deu bom"
    s = score_helena_report(r)
    assert not s["breakdown"]["profundidade"]["passed"]


def test_render_scorecard_has_all_dims():
    s = score_helena_report(helena_report(_make_result()))
    md = render_scorecard(s)
    for dim in ("dados antes opiniao", "red team explicito",
                "calibracao confianca", "acionabilidade",
                "profundidade", "protocolo sem muro"):
        assert dim in md
    assert "Helena Quality Score" in md


def test_breakdown_keys():
    s = score_helena_report(helena_report(_make_result()))
    expected = {"dados_antes_opiniao", "red_team_explicito",
                "calibracao_confianca", "acionabilidade",
                "profundidade", "protocolo_sem_muro"}
    assert set(s["breakdown"].keys()) == expected


def test_score_range():
    s = score_helena_report(helena_report(_make_result(n=5)))
    assert 0 <= s["score"] <= 100


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
