"""Testes Onda 159: AutoResearch Vila."""

from __future__ import annotations
import sys, os, tempfile, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.autoresearch_accuracy import (
    _hash_config, propor_variacao, Experiment, PROPOSAL_SPACE,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_hash_deterministico():
    c1 = {"a": 1, "b": 2}
    c2 = {"b": 2, "a": 1}
    teste("hash deterministico ordem keys", _hash_config(c1) == _hash_config(c2))


def t_hash_diferente_para_valores_diferentes():
    c1 = {"a": 1}
    c2 = {"a": 2}
    teste("hash diferente valores", _hash_config(c1) != _hash_config(c2))


def t_propor_flag_toggle():
    rng = random.Random(1)
    config = {"usar_debate": False, "peso_vila": 0.7}
    historia = []
    # seed 1 garantia flag será escolhida
    for _ in range(20):
        novo, delta = propor_variacao(config, historia, rng)
        if delta:
            param = list(delta.keys())[0]
            teste(f"proposta mudou {param}", novo[param] != config.get(param))
            return
    teste("ao menos 1 proposta em 20 tent", False)


def t_propor_evita_duplicados():
    rng = random.Random(2)
    config = {"usar_debate": False, "peso_vila": 0.7, "usar_peso_adaptativo": False}
    historia = []
    hashes = set()
    for _ in range(5):
        novo, delta = propor_variacao(config, historia, rng)
        if not delta:
            break
        h = _hash_config(novo)
        teste(f"hash novo {h} inédito", h not in hashes)
        hashes.add(h)
        historia.append(Experiment(
            iteracao=len(historia), config=novo, config_hash=h,
            parent_hash=None, proposal_delta=delta,
        ))


def t_proposal_space_nao_vazio():
    teste("PROPOSAL_SPACE tem entries", len(PROPOSAL_SPACE) >= 10)
    tipos = {p["tipo"] for p in PROPOSAL_SPACE}
    teste("tem flags", "flag" in tipos)
    teste("tem ranges", "range" in tipos)
    teste("tem choices", "choice" in tipos)


def t_experiment_to_dict():
    e = Experiment(
        iteracao=1, config={"a": 1}, config_hash="abc123",
        parent_hash=None, proposal_delta={}, metric=0.15, kept=True,
    )
    d = e.to_dict()
    teste("to_dict tem metric", d["metric"] == 0.15)
    teste("to_dict tem kept", d["kept"] is True)


def main():
    print("=== test_autoresearch_accuracy ===")
    for fn in [t_hash_deterministico,
               t_hash_diferente_para_valores_diferentes,
               t_propor_flag_toggle,
               t_propor_evita_duplicados,
               t_proposal_space_nao_vazio,
               t_experiment_to_dict]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
