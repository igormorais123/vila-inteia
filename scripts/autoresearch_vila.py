"""
Onda 159: CLI AutoResearch Vila.

Uso:
  python scripts/autoresearch_vila.py [--iter N] [--seed S]
                                       [--trace <path>] [--datasets ds1,ds2,...]

Ponteiro pra docs/AUTORESEARCH_PROGRAM.md como research directions.

Pattern Karpathy: baseline → propose → test → keep/revert → loop.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _load_env():
    envp = Path.home() / ".vila_env"
    if not envp.exists():
        return
    for line in envp.read_text().splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iter", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--trace", default="data/autoresearch_trace.jsonl")
    parser.add_argument("--datasets", default="impeachment_dilma_2016,eleicao_presidencial_br_2022")
    parser.add_argument("--max-eventos", type=int, default=3)
    parser.add_argument("--personas", default="CL001,CL002,CL007")
    parser.add_argument("--max-sem-melhoria", type=int, default=5)
    parser.add_argument("--no-groq", action="store_true", help="desabilita Groq (força fallback)")
    parser.add_argument("--tournament", type=int, default=0,
                        help="run N seeds tournament (0 = single)")
    parser.add_argument("--llm-guided", action="store_true",
                        help="usa LLM pra propor variações (Karpathy style)")
    parser.add_argument("--update-program", action="store_true",
                        help="append resultados ao docs/AUTORESEARCH_PROGRAM.md")
    parser.add_argument("--git-commit", action="store_true",
                        help="commit git per iter keep")
    args = parser.parse_args()

    _load_env()
    if args.no_groq:
        os.environ["GROQ_API_KEY"] = ""
    os.environ.setdefault("VILA_LLM_TIMEOUT_S", "15")
    os.environ["PYTHONUNBUFFERED"] = "1"

    from engine.persona import Persona
    from engine.persona_chat import resetar_historico
    from engine.autoresearch_accuracy import loop_autoresearch
    from engine.autoresearch_karpathy import (
        loop_tournament, atualizar_program_md, git_commit_experiment,
    )
    if args.llm_guided:
        # Monkey patch propor_variacao global pra usar LLM-guided
        from engine import autoresearch_accuracy as _aa
        from engine.autoresearch_karpathy import proposal_llm_guided
        _orig_propor = _aa.propor_variacao
        def _wrapped(cfg, hist, rng=None):
            return proposal_llm_guided(cfg, hist, llm_fn=lambda: None)
        _aa.propor_variacao = _wrapped

    banco_path = Path(__file__).resolve().parent.parent / "data" / "banco-consultores-lendarios.json"
    banco = json.load(open(banco_path))
    persona_ids = [p.strip() for p in args.personas.split(",")]
    ids_set = set(persona_ids)

    class _Sim:
        def __init__(self):
            self.personas = {}
            for p in banco:
                if p["id"] in ids_set:
                    self.personas[p["id"]] = Persona(p)

    sim = _Sim()
    resetar_historico()

    dataset_paths = [
        str(Path(__file__).resolve().parent.parent / "data" / "backtest" / f"{d.strip()}.csv")
        for d in args.datasets.split(",")
    ]

    # Baseline = full stack Onda 153+
    baseline = {
        "sleep_entre_eventos_s": 2.0,
        "few_shot_k": 2,
        "chain_of_thought": True,
        "usar_debate": False,
        "usar_bayesian_blend": True,
        "peso_vila": 0.7,
        "aplicar_platt": True,
        "usar_peso_adaptativo": True,
        "usar_blend_ensemble": True,
        "prob_floor": 0.05,
        "prob_ceiling": 0.95,
        "recency_decay": 0.9,
        "temp_por_persona": False,
    }

    print(f"[autoresearch] datasets: {args.datasets}")
    print(f"[autoresearch] personas: {persona_ids}")
    print(f"[autoresearch] max_iter: {args.iter}, seed: {args.seed}")
    print(f"[autoresearch] baseline: {json.dumps(baseline)}")
    print()

    if args.tournament > 0:
        # Tournament mode
        resultado = loop_tournament(
            baseline_config=baseline,
            datasets=dataset_paths,
            sim=sim,
            persona_ids=persona_ids,
            n_seeds=args.tournament,
            max_iteracoes=args.iter,
            max_sem_melhoria=args.max_sem_melhoria,
            max_eventos_por_dataset=args.max_eventos,
            trace_dir=str(Path(args.trace).parent / "tournament"),
            verbose=True,
        )
        # Tournament returns different schema; compat
        resultado = {
            "n_iteracoes": args.iter * args.tournament,
            "baseline_brier": None,
            "best_brier": resultado.get("campeao_brier"),
            "best_config": resultado.get("campeao_config", {}),
            "best_iteracao": resultado.get("campeao_seed"),
            "n_kept": None,
            "n_reverted": None,
            "tournament": resultado,
        }
    else:
        resultado = loop_autoresearch(
            baseline_config=baseline,
            datasets=dataset_paths,
            sim=sim,
            persona_ids=persona_ids,
            max_iteracoes=args.iter,
            max_sem_melhoria=args.max_sem_melhoria,
            seed=args.seed,
            trace_path=args.trace,
            max_eventos_por_dataset=args.max_eventos,
        )

    if args.update_program:
        try:
            atualizar_program_md(resultado)
            print("[autoresearch] docs/AUTORESEARCH_PROGRAM.md atualizado")
        except Exception as e:
            print(f"[autoresearch] update_program falhou: {e}")

    if args.git_commit and resultado.get("best_brier") is not None:
        from engine.autoresearch_accuracy import Experiment, _hash_config
        exp = Experiment(
            iteracao=resultado.get("best_iteracao", 0),
            config=resultado.get("best_config", {}),
            config_hash=_hash_config(resultado.get("best_config", {})),
            parent_hash=None,
            proposal_delta={},
            metric=resultado.get("best_brier"),
            kept=True,
        )
        sha = git_commit_experiment(exp)
        if sha:
            print(f"[autoresearch] git commit {sha}")

    print("\n=== AutoResearch Resumo ===")
    print(f"N iterações: {resultado['n_iteracoes']}")
    bb = resultado['baseline_brier'] or 0
    bt = resultado['best_brier'] or 0
    print(f"Baseline brier: {bb:.4f}")
    print(f"Best brier: {bt:.4f}")
    print(f"Best iteração: {resultado['best_iteracao']}")
    print(f"Kept: {resultado['n_kept']}, Reverted: {resultado['n_reverted']}")
    if resultado['baseline_brier'] and resultado['best_brier']:
        delta_pct = (resultado['best_brier'] - resultado['baseline_brier']) / resultado['baseline_brier'] * 100
        print(f"Delta: {delta_pct:+.1f}%")
    print(f"\nBest config:")
    for k, v in resultado['best_config'].items():
        print(f"  {k}: {v}")
    print(f"\nTrace: {args.trace}")


if __name__ == "__main__":
    main()
