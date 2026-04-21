"""Testes Onda 159: AutoResearch Vila."""

from __future__ import annotations
import sys, os, tempfile, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.autoresearch_accuracy import (
    _hash_config, propor_variacao, Experiment, PROPOSAL_SPACE,
    carregar_trace, encontrar_best,
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


def t_carregar_trace_vazio():
    import tempfile
    p = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name
    os.unlink(p)
    r = carregar_trace(p)
    teste("trace inexistente → lista vazia", r == [])


def t_carregar_trace_parse_jsonl():
    import tempfile, json as _j
    p = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name
    with open(p, "w") as f:
        f.write(_j.dumps({
            "iteracao": 1, "config": {"a": 1}, "config_hash": "hash1",
            "parent_hash": None, "proposal_delta": {},
            "metric": 0.20, "n_eventos": 3, "kept": True,
        }) + "\n")
        f.write(_j.dumps({
            "iteracao": 2, "config": {"a": 2}, "config_hash": "hash2",
            "parent_hash": "hash1", "proposal_delta": {},
            "metric": 0.15, "n_eventos": 3, "kept": True,
        }) + "\n")
        f.write("malformed\n")
    r = carregar_trace(p)
    teste("trace 2 valid (malformed skipped)", len(r) == 2)
    teste("iter 1 parsed", r[0].iteracao == 1)
    os.unlink(p)


def t_encontrar_best():
    h = [
        Experiment(iteracao=0, config={}, config_hash="a", parent_hash=None,
                   proposal_delta={}, metric=0.20, kept=True),
        Experiment(iteracao=1, config={}, config_hash="b", parent_hash="a",
                   proposal_delta={}, metric=0.15, kept=True),
        Experiment(iteracao=2, config={}, config_hash="c", parent_hash="b",
                   proposal_delta={}, metric=0.30, kept=False),
    ]
    best = encontrar_best(h)
    teste("best iter=1 brier=0.15", best.iteracao == 1 and best.metric == 0.15)


def t_encontrar_best_ignora_none():
    h = [
        Experiment(iteracao=0, config={}, config_hash="a", parent_hash=None,
                   proposal_delta={}, metric=None, erro="LLM"),
        Experiment(iteracao=1, config={}, config_hash="b", parent_hash=None,
                   proposal_delta={}, metric=0.25, kept=True),
    ]
    best = encontrar_best(h)
    teste("ignora metric=None", best.metric == 0.25)


def t_encontrar_best_vazio():
    teste("lista vazia → None", encontrar_best([]) is None)


def main():
    print("=== test_autoresearch_accuracy ===")
    for fn in [t_hash_deterministico,
               t_hash_diferente_para_valores_diferentes,
               t_propor_flag_toggle,
               t_propor_evita_duplicados,
               t_proposal_space_nao_vazio,
               t_experiment_to_dict,
               t_carregar_trace_vazio,
               t_carregar_trace_parse_jsonl,
               t_encontrar_best,
               t_encontrar_best_ignora_none,
               t_encontrar_best_vazio]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
