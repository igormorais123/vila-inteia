"""Testes Onda 95: persona prediction skill analysis."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.persona_skill import analisar_skill_personas, categorizar_dataset

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _evt(y, per_persona):
    return {"outcome_real": y, "per_persona": per_persona}


def _p(pid, nome, prob):
    return {"persona_id": pid, "persona_nome": nome, "prob_extraida": prob}


def t_vazio():
    r = analisar_skill_personas([])
    teste("vazio: 0 personas", r["n_personas_ativas"] == 0)


def t_ignora_datasets_com_erro():
    ds = [{"erro": "boom", "eventos": []}]
    r = analisar_skill_personas(ds)
    teste("erro: 0 personas", r["n_personas_ativas"] == 0)


def t_agrega_eventos():
    ds = [{"eventos": [
        _evt(1, [_p("CL001", "Musk", 0.8)]),
        _evt(0, [_p("CL001", "Musk", 0.3)]),
    ]}]
    r = analisar_skill_personas(ds)
    teste("1 persona", r["n_personas_ativas"] == 1)
    musk = r["ranking"][0]
    teste("Musk n=2", musk["n_previsoes"] == 2)
    teste("Musk accuracy 100%", musk["accuracy"] == 1.0)
    # (0.8-1)² + (0.3-0)² = 0.04 + 0.09 = 0.13 / 2 = 0.065
    teste("Musk brier ~0.065", abs(musk["brier_avg"] - 0.065) < 0.01)


def t_prob_null_nao_conta_valida():
    ds = [{"eventos": [
        _evt(1, [_p("CL001", "Musk", None), _p("CL001", "Musk", 0.9)]),
    ]}]
    r = analisar_skill_personas(ds)
    musk = r["ranking"][0]
    teste("n_previsoes=2", musk["n_previsoes"] == 2)
    teste("n_validas=1", musk["n_validas"] == 1)


def t_ranking_por_brier():
    ds = [{"eventos": [
        _evt(1, [_p("CL001", "Musk", 0.9), _p("CL002", "Jobs", 0.4)]),
        _evt(1, [_p("CL001", "Musk", 0.95), _p("CL002", "Jobs", 0.5)]),
    ]}]
    r = analisar_skill_personas(ds)
    teste("top = Musk", r["ranking"][0]["persona_id"] == "CL001")
    teste("Musk brier < Jobs brier",
           r["ranking"][0]["brier_avg"] < r["ranking"][1]["brier_avg"])


def t_multi_datasets_agrega():
    ds = [
        {"eventos": [_evt(1, [_p("CL001", "Musk", 0.7)])]},
        {"eventos": [_evt(0, [_p("CL001", "Musk", 0.2)])]},
    ]
    r = analisar_skill_personas(ds)
    musk = r["ranking"][0]
    teste("Musk agregou 2 datasets", musk["n_previsoes"] == 2)


def t_categorizar_dataset():
    teste("impeachment → politica_br",
          categorizar_dataset("data/backtest/impeachment_dilma_2016.csv") == "politica_br")
    teste("crypto_bitcoin → crypto",
          categorizar_dataset("crypto_bitcoin_2024.csv") == "crypto")
    teste("twitter_musk → social_media",
          categorizar_dataset("twitter_musk_2022_2024") == "social_media")
    teste("apple_vpro → tech_launch",
          categorizar_dataset("lancamento_apple_vpro_2024") == "tech_launch")
    teste("desconhecido → geral",
          categorizar_dataset("foo_bar.csv") == "geral")


def t_ranking_por_categoria():
    ds = [
        {"dataset": "data/backtest/impeachment_dilma_2016.csv",
         "eventos": [_evt(1, [_p("CL001", "Musk", 0.9)])]},
        {"dataset": "data/backtest/crypto_bitcoin_2024.csv",
         "eventos": [_evt(1, [_p("CL001", "Musk", 0.5)])]},
    ]
    r = analisar_skill_personas(ds)
    teste("tem ranking_por_categoria",
          "ranking_por_categoria" in r)
    rpc = r["ranking_por_categoria"]
    teste("politica_br presente", "politica_br" in rpc)
    teste("crypto presente", "crypto" in rpc)
    # Musk melhor em política (brier 0.01) que crypto (brier 0.25)
    musk_pol = rpc["politica_br"][0]
    musk_cry = rpc["crypto"][0]
    teste("Musk brier política < crypto",
          musk_pol["brier_avg"] < musk_cry["brier_avg"])


def t_categorizar_geral_para_desconhecido():
    ds = [{"dataset": "random_dataset.csv",
           "eventos": [_evt(1, [_p("CL001", "Musk", 0.7)])]}]
    r = analisar_skill_personas(ds)
    teste("geral presente", "geral" in r["ranking_por_categoria"])


def main():
    print("=== test_persona_skill ===")
    for fn in [t_vazio, t_ignora_datasets_com_erro, t_agrega_eventos,
               t_prob_null_nao_conta_valida, t_ranking_por_brier,
               t_multi_datasets_agrega,
               t_categorizar_dataset, t_ranking_por_categoria,
               t_categorizar_geral_para_desconhecido]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
