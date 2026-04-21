"""Testes Onda 120: comparison table."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.comparison_table import build_comparison, SIMULADORES, FEATURES_KEY

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_simuladores_presentes():
    for k in ["vila_inteia", "generative_agents", "oasis", "mirofish"]:
        teste(f"{k} presente", k in SIMULADORES)


def t_vila_tem_todas_features_true():
    v = SIMULADORES["vila_inteia"]
    # Essential Vila features should be True
    for f in ["markov_psicohistoria", "calibracao_online_platt",
              "pearl_do_calculus", "louvain_communities",
              "backtest_real_events", "persona_chat_direto_user",
              "dashboard_d3_forcegraph"]:
        teste(f"vila.{f} = True", v.get(f) is True)


def t_build_comparison():
    r = build_comparison()
    teste("simuladores presentes", "simuladores" in r)
    teste("features_ordem tem FEATURES_KEY", r["features_ordem"] == FEATURES_KEY)
    teste("n_exclusivas > 0", r["n_features_exclusivas"] > 0)


def t_exclusivas_vila():
    r = build_comparison()
    # Features únicas Vila confirma markov + Platt + Pearl + backtest
    ex = r["features_exclusivas_vila"]
    for must_have in ["markov_psicohistoria", "calibracao_online_platt",
                       "pearl_do_calculus", "backtest_real_events"]:
        teste(f"{must_have} exclusiva Vila", must_have in ex)


def t_n_agentes():
    v = SIMULADORES["vila_inteia"]
    o = SIMULADORES["oasis"]
    teste("Vila 144 personas", v["n_agentes_max"] == 144)
    teste("OASIS target 1M", o["n_agentes_max"] == 1_000_000)


def main():
    print("=== test_comparison_table ===")
    for fn in [t_simuladores_presentes, t_vila_tem_todas_features_true,
               t_build_comparison, t_exclusivas_vila, t_n_agentes]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
