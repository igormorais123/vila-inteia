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
    parser.add_argument("--rotate-models", action="store_true",
                        help="Onda 191: rotate Groq models per iter (evita TPD burn)")
    parser.add_argument("--timeout", type=int, default=30,
                        help="LLM timeout segundos (default 30s)")
    args = parser.parse_args()

    _load_env()
    if args.no_groq:
        os.environ["GROQ_API_KEY"] = ""
    os.environ["VILA_LLM_TIMEOUT_S"] = str(args.timeout)
    os.environ["PYTHONUNBUFFERED"] = "1"

    from engine.persona import Persona
    from engine.persona_chat import resetar_historico
    from engine.autoresearch_accuracy import loop_autoresearch

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

    model_pool = None
    if args.rotate_models:
        from engine.autoresearch_accuracy import MODEL_POOL_DEFAULT
        model_pool = MODEL_POOL_DEFAULT
        print(f"[autoresearch] rotating models: {model_pool}")

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
        model_pool=model_pool,
    )

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
