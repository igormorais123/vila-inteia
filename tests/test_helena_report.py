"""Tests for engine.helena_report — Helena 8-block adapter."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.forecast_result import ForecastResult
from engine.helena_report import helena_report, render_markdown


def _make_result(*, n=100, brier=0.18, ci=(0.16, 0.20),
                 reliability=0.01, resolution=0.06, uncertainty=0.25,
                 cv_mean=0.18, cv_std=0.02) -> ForecastResult:
    return ForecastResult(
        n=n,
        base_acc=0.72,
        base_brier=brier,
        bootstrap_brier_ci=ci,
        selective={0.30: {"coverage": 0.85, "brier": 0.15}},
        conformal={"coverage": 0.80},
        murphy={
            "reliability": reliability,
            "resolution": resolution,
            "uncertainty": uncertainty,
            "brier": brier,
            "base_rate": 0.5,
        },
        time_series_cv={"mean_brier": cv_mean, "std_brier": cv_std, "n_folds": 5},
    )


def test_basic_keys_present():
    r = helena_report(_make_result(), dataset_name="dummy")
    expected = {"status", "achado", "evidencia", "mecanismo", "red_team",
                "cenarios", "recomendacao", "calibracao_confianca",
                "curiosidade_residual"}
    assert expected.issubset(r.keys())


def test_high_confidence_when_clean():
    r = helena_report(_make_result(n=120, ci=(0.17, 0.19), reliability=0.005))
    assert r["calibracao_confianca"]["label"] == "alta"


def test_low_confidence_small_n():
    r = helena_report(_make_result(n=10))
    assert r["calibracao_confianca"]["label"] == "baixa"
    assert "n=10" in r["calibracao_confianca"]["justificativa"]


def test_medium_confidence_wide_ci():
    r = helena_report(_make_result(n=60, ci=(0.10, 0.30)))
    assert r["calibracao_confianca"]["label"] == "média"


def test_red_team_flags_ci_overlap_baseline():
    r = helena_report(_make_result(brier=0.22, ci=(0.20, 0.27), uncertainty=0.25))
    flags = " ".join(r["red_team"])
    assert "baseline" in flags.lower()


def test_red_team_flags_bad_calibration():
    r = helena_report(_make_result(reliability=0.10))
    assert any("descalibrado" in x for x in r["red_team"])


def test_red_team_flags_low_resolution():
    r = helena_report(_make_result(resolution=0.005))
    assert any("Resolution" in x for x in r["red_team"])


def test_red_team_flags_unstable_cv():
    r = helena_report(_make_result(cv_mean=0.18, cv_std=0.15))
    assert any("instável" in x for x in r["red_team"])


def test_red_team_clean_when_all_good():
    r = helena_report(_make_result(brier=0.14, ci=(0.12, 0.16),
                                    reliability=0.005, resolution=0.08,
                                    cv_std=0.01, cv_mean=0.14))
    assert any("nenhuma" in x.lower() for x in r["red_team"])


def test_recommendation_recalibrate_when_reliability_high():
    r = helena_report(_make_result(reliability=0.10))
    assert "Recalibrar" in r["recomendacao"]


def test_recommendation_collect_more_when_n_tiny():
    r = helena_report(_make_result(n=8))
    assert "holdout maior" in r["recomendacao"]


def test_recommendation_promote_when_clean():
    r = helena_report(_make_result(brier=0.14, ci=(0.12, 0.16),
                                    reliability=0.005, resolution=0.08))
    assert "Promover" in r["recomendacao"]


def test_scenarios_have_three_levels():
    r = helena_report(_make_result())
    assert set(r["cenarios"].keys()) == {"otimista", "base", "pessimista"}
    assert r["cenarios"]["otimista"]["brier"] <= r["cenarios"]["base"]["brier"]
    assert r["cenarios"]["base"]["brier"] <= r["cenarios"]["pessimista"]["brier"]


def test_accepts_dict_input():
    fr = _make_result()
    r1 = helena_report(fr)
    r2 = helena_report(fr.as_dict())
    assert r1["achado"] == r2["achado"]
    assert r1["recomendacao"] == r2["recomendacao"]


def test_render_markdown_has_all_blocks():
    md = render_markdown(helena_report(_make_result(), dataset_name="X"))
    for header in ("## 1. Status", "## 2. Achado", "## 3. Mecanismo",
                   "## 4. Red Team", "## 5. Cenários", "## 6. Recomendação",
                   "## 7. Calibração", "## 8. Curiosidade"):
        assert header in md


def test_achado_detects_real_skill():
    r = helena_report(_make_result(brier=0.14, ci=(0.12, 0.16), uncertainty=0.25))
    assert "skill real" in r["achado"]


def test_achado_detects_uncertain_skill():
    r = helena_report(_make_result(brier=0.22, ci=(0.20, 0.27), uncertainty=0.25))
    assert "incerto" in r["achado"]


def test_achado_detects_no_skill():
    r = helena_report(_make_result(brier=0.27, ci=(0.25, 0.30), uncertainty=0.25))
    assert "Não bate" in r["achado"]


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
