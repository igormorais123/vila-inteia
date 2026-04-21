"""Testes Onda 175: meta-autoresearch."""

from __future__ import annotations
import sys, os, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.meta_autoresearch import (
    agregar_traces, salvar_learnings, carregar_learnings,
    biased_proposal, relatorio,
)
from engine.autoresearch_accuracy import Experiment, _hash_config

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_agregar_vazio():
    """Glob sem arquivos → agregado vazio."""
    r = agregar_traces("/tmp/nao_existe_xxx*.jsonl")
    teste("n_runs=0", r["n_runs"] == 0)
    teste("por_param vazio", len(r["por_param"]) == 0)


def t_agregar_parse_trace():
    """Trace sintético: 2 KEEP usar_debate, 1 REVERT prob_floor."""
    d = tempfile.mkdtemp()
    with open(f"{d}/trace_a.jsonl", "w") as f:
        f.write(json.dumps({
            "iteracao": 1, "config": {}, "config_hash": "a", "parent_hash": None,
            "proposal_delta": {"usar_debate": {"antes": False, "depois": True}},
            "metric": 0.10, "kept": True,
        }) + "\n")
        f.write(json.dumps({
            "iteracao": 2, "config": {}, "config_hash": "b", "parent_hash": "a",
            "proposal_delta": {"prob_floor": {"antes": 0.05, "depois": 0.10}},
            "metric": 0.15, "kept": False,
        }) + "\n")
    with open(f"{d}/trace_b.jsonl", "w") as f:
        f.write(json.dumps({
            "iteracao": 1, "config": {}, "config_hash": "c", "parent_hash": None,
            "proposal_delta": {"usar_debate": {"antes": False, "depois": True}},
            "metric": 0.08, "kept": True,
        }) + "\n")

    r = agregar_traces(f"{d}/trace_*.jsonl")
    teste(f"n_runs=2 (got {r['n_runs']})", r["n_runs"] == 2)
    teste(f"n_exp=3 (got {r['n_experiments']})", r["n_experiments"] == 3)
    pb = r["por_param"]
    teste("usar_debate 2 kept", pb["usar_debate"]["kept"] == 2)
    teste("usar_debate score > 0.5",
          pb["usar_debate"]["score"] > 0.5)
    teste("prob_floor 1 reverted", pb["prob_floor"]["reverted"] == 1)
    teste(f"global_best_brier=0.08", r["global_best_brier"] == 0.08)
    import shutil; shutil.rmtree(d)


def t_salvar_carregar_learnings():
    p = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    os.unlink(p)
    agregado = {"n_runs": 1, "por_param": {"x": {"kept": 1, "reverted": 0, "score": 0.667}}}
    salvar_learnings(agregado, path=p)
    loaded = carregar_learnings(p)
    teste("roundtrip", loaded["por_param"]["x"]["score"] == 0.667)
    os.unlink(p)


def t_biased_proposal_sem_learnings_fallback():
    config = {"usar_debate": False, "peso_vila": 0.7}
    historia = [Experiment(iteracao=0, config=config, config_hash=_hash_config(config),
                            parent_hash=None, proposal_delta={}, kept=True)]
    novo, delta = biased_proposal(config, historia, learnings={})
    teste("sem learnings produz proposta", len(delta) > 0)


def t_biased_proposal_prefere_param_alto_score():
    """Com learnings: param com score alto vem primeiro quando não explora."""
    config = {"usar_debate": False, "peso_vila": 0.7, "usar_peso_adaptativo": False}
    historia = [Experiment(iteracao=0, config=config, config_hash=_hash_config(config),
                            parent_hash=None, proposal_delta={}, kept=True)]
    learnings = {
        "por_param": {
            "usar_debate": {"kept": 5, "reverted": 0, "score": 0.857},
            "peso_vila": {"kept": 0, "reverted": 3, "score": 0.2},
        }
    }
    import random
    rng = random.Random(42)
    # Run 10 vezes sem explore — espera usar_debate dominar
    debates = 0
    pesos = 0
    for _ in range(10):
        novo, delta = biased_proposal(config, historia, rng=rng, learnings=learnings, explore_rate=0.0)
        if "usar_debate" in delta:
            debates += 1
        elif "peso_vila" in delta:
            pesos += 1
    teste(f"usar_debate dominante ({debates}/10)", debates >= 5)


def t_relatorio_formatacao():
    agregado = {
        "n_runs": 1, "n_experiments": 3,
        "global_best_brier": 0.10,
        "por_param": {
            "usar_debate": {"kept": 2, "reverted": 0, "score": 0.75},
            "prob_floor": {"kept": 0, "reverted": 1, "score": 0.333},
        }
    }
    r = relatorio(agregado)
    teste("contém 'usar_debate'", "usar_debate" in r)
    teste("contém score 0.75", "0.750" in r or "0.75" in r)


def main():
    print("=== test_meta_autoresearch ===")
    for fn in [t_agregar_vazio, t_agregar_parse_trace,
               t_salvar_carregar_learnings,
               t_biased_proposal_sem_learnings_fallback,
               t_biased_proposal_prefere_param_alto_score,
               t_relatorio_formatacao]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
