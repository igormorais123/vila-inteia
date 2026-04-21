"""Testes Onda 171: Full Karpathy autoresearch."""

from __future__ import annotations
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.autoresearch_karpathy import (
    proposal_llm_guided, loop_tournament,
    git_commit_experiment, atualizar_program_md,
)
from engine.autoresearch_accuracy import Experiment, _hash_config

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_proposal_llm_fallback_sem_llm_fn():
    """Sem llm_fn → fallback pra propor_variacao random."""
    config = {"usar_debate": False, "peso_vila": 0.7}
    historia = [Experiment(iteracao=0, config=config, config_hash=_hash_config(config),
                            parent_hash=None, proposal_delta={}, kept=True)]
    novo, delta = proposal_llm_guided(config, historia, llm_fn=None)
    teste("fallback produz proposal", len(delta) > 0)


def t_proposal_llm_parse_json_malformado():
    """LLM retorna texto não-JSON → fallback random."""
    config = {"usar_debate": False, "peso_vila": 0.7}
    historia = [Experiment(iteracao=0, config=config, config_hash=_hash_config(config),
                            parent_hash=None, proposal_delta={}, kept=True)]

    # Stub chamar_llm retornando texto não-JSON
    from engine import ia_client
    def fake_llm(**kw): return "bla bla nada de JSON aqui"
    orig = ia_client.chamar_llm
    ia_client.chamar_llm = fake_llm
    try:
        novo, delta = proposal_llm_guided(config, historia, llm_fn=lambda: None)
        teste("fallback random quando LLM malformed", len(delta) > 0)
    finally:
        ia_client.chamar_llm = orig


def t_proposal_llm_valid_json():
    """LLM retorna JSON válido → aplica proposta."""
    config = {"usar_debate": False, "peso_vila": 0.7}
    historia = [Experiment(iteracao=0, config=config, config_hash=_hash_config(config),
                            parent_hash=None, proposal_delta={}, kept=True)]
    from engine import ia_client
    def fake_llm(**kw):
        return '{"param": "peso_vila", "novo_valor": 0.85}'
    orig = ia_client.chamar_llm
    ia_client.chamar_llm = fake_llm
    try:
        novo, delta = proposal_llm_guided(config, historia, llm_fn=lambda: None)
        teste("aplica peso_vila=0.85", novo["peso_vila"] == 0.85)
        teste("delta tem param", "peso_vila" in delta)
    finally:
        ia_client.chamar_llm = orig


def t_atualizar_program_md():
    """Append run ao program.md sem reescrever existente."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Original\n")
        p = f.name
    resultado = {
        "baseline_brier": 0.15,
        "best_brier": 0.12,
        "n_iteracoes": 5,
        "n_kept": 2,
        "n_reverted": 3,
        "best_config": {"usar_debate": True, "peso_vila": 0.8},
    }
    atualizar_program_md(resultado, path=p)
    content = open(p).read()
    teste("original preserved", "# Original" in content)
    teste("adicionou Run section", "## Run" in content)
    teste("Best brier no content", "Best brier: 0.12" in content)
    os.unlink(p)


def t_tournament_retorna_campeao():
    """Tournament sem backtest real (stub rodar_experimento)."""
    from engine import autoresearch_accuracy
    call_count = [0]
    def fake_rodar(config, datasets, sim, persona_ids, llm_fn, max_eventos_por_dataset=3):
        call_count[0] += 1
        return (0.1 + call_count[0] * 0.01, 3)

    orig = autoresearch_accuracy.rodar_experimento
    autoresearch_accuracy.rodar_experimento = fake_rodar
    try:
        r = loop_tournament(
            baseline_config={"peso_vila": 0.7},
            datasets=["dummy.csv"], sim=None,
            persona_ids=["CL001"],
            n_seeds=2, max_iteracoes=2,
            verbose=False,
        )
        teste("tournament tem campeao_seed", "campeao_seed" in r)
        teste("tournament tem 2 seeds", len(r["todos_seeds"]) == 2)
    finally:
        autoresearch_accuracy.rodar_experimento = orig


def main():
    print("=== test_autoresearch_karpathy ===")
    for fn in [t_proposal_llm_fallback_sem_llm_fn,
               t_proposal_llm_parse_json_malformado,
               t_proposal_llm_valid_json,
               t_atualizar_program_md,
               t_tournament_retorna_campeao]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
