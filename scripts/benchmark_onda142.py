"""
Onda 142: heuristic benchmark pra features 134-141.

Roda backtest_acc em 10 datasets com mock LLM determinístico. Compara
Brier baseline (prior humano) vs config Vila em diferentes stacks:

- stack_minimal: só panel + few-shot
- stack_cot: + chain-of-thought + anchor_scale (Onda 138)
- stack_framing: + outcome_framing (Onda 135/136)
- stack_full: + bayesian blend + peso_adaptativo (Onda 137)

Sem quota LLM. Mock retorna prob enviesada pelo contexto via
keyword heuristic. Útil pra validar wiring sem burn tokens.

Uso: python scripts/benchmark_onda142.py [--dataset <nome>]
"""

from __future__ import annotations

import glob
import json
import os
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.backtest_acc import rodar_backtest_acc


_KEYWORDS_POS = [
    "aprovada", "aprovado", "confirmad", "vitória", "vitoria",
    "supera", "atinge", "viralizar", "viral", "eleito",
]
_KEYWORDS_NEG = [
    "rejeição", "rejeicao", "bloqueada", "bloqueado", "adiado",
    "fracasso", "cancelado", "queixa", "devolução", "devolucao",
    "fraco", "fraca",
]


def _heuristica_prob(contexto: str) -> float:
    """Mock heuristic: conta keywords pos/neg + modula around 0.5."""
    t = (contexto or "").lower()
    pos = sum(1 for kw in _KEYWORDS_POS if kw in t)
    neg = sum(1 for kw in _KEYWORDS_NEG if kw in t)
    score = pos - neg
    # sigmoid-like clamp
    p = 0.5 + 0.10 * score
    return max(0.10, min(0.90, p))


class _MockSim:
    personas: dict = {f"CL{str(i).zfill(3)}": object() for i in range(1, 40)}


def _extract_contexto(pergunta: str) -> str:
    # pergunta tipo: 'Analise o evento: "XYZ"\n\n...'
    m = re.search(r'"([^"]+)"', pergunta)
    return m.group(1) if m else ""


def llm_fn_mock(**kw):
    mensagens = kw.get("mensagens") or []
    pergunta = mensagens[-1].get("content", "") if mensagens else ""
    ctx = _extract_contexto(pergunta)
    p = _heuristica_prob(ctx)
    return f"RACIOCÍNIO: heurística keyword. PROBABILIDADE FINAL: {int(p * 100)}%"


STACKS = {
    "minimal": dict(
        chain_of_thought=False,
        usar_debate=False,
        usar_bayesian_blend=False,
        aplicar_platt=False,
    ),
    "cot": dict(
        chain_of_thought=True,
        usar_debate=False,
        usar_bayesian_blend=False,
        aplicar_platt=False,
    ),
    "cot_blend": dict(
        chain_of_thought=True,
        usar_debate=False,
        usar_bayesian_blend=True,
        aplicar_platt=False,
    ),
    "full_adaptive": dict(
        chain_of_thought=True,
        usar_debate=False,
        usar_bayesian_blend=True,
        usar_peso_adaptativo=True,
        aplicar_platt=False,
    ),
    "full_hedge": dict(
        chain_of_thought=True,
        usar_debate=False,
        usar_bayesian_blend=True,
        usar_peso_adaptativo=True,
        aplicar_platt=False,
        prob_floor=0.05,
        prob_ceiling=0.95,
    ),
}


def rodar_um_dataset(path: str) -> dict:
    resultados = {}
    for stack_nome, kwargs in STACKS.items():
        r = rodar_backtest_acc(
            dataset_path=path,
            sim=_MockSim(),
            persona_ids=["CL001", "CL002", "CL007"],
            llm_fn=llm_fn_mock,
            **kwargs,
        )
        resultados[stack_nome] = {
            "brier_vila": r.get("brier_vila_calibrada_avg"),
            "brier_blend": r.get("brier_blend_final_avg"),
            "brier_prior": r.get("brier_prior_avg"),
            "accuracy": r.get("accuracy_blend_final") or r.get("accuracy_vila_calibrada"),
        }
    return resultados


def main():
    dataset_filter = None
    if len(sys.argv) > 1 and sys.argv[1] == "--dataset":
        dataset_filter = sys.argv[2]

    pattern = "data/backtest/*.csv"
    all_paths = sorted(glob.glob(pattern))
    if dataset_filter:
        all_paths = [p for p in all_paths if dataset_filter in p]

    print(f"=== Onda 142: benchmark heuristic mock ({len(all_paths)} datasets) ===\n")

    agg = {s: {"brier_vila": [], "brier_blend": [], "brier_prior": [], "accuracy": []}
           for s in STACKS}

    for path in all_paths:
        nome = Path(path).stem
        print(f"## {nome}")
        r = rodar_um_dataset(path)
        for stack, m in r.items():
            print(f"  {stack:16s} brier_vila={m['brier_vila']:.3f}  "
                  f"brier_blend={m['brier_blend']:.3f}  "
                  f"acc={m['accuracy']:.2f}")
            for k, v in m.items():
                if v is not None:
                    agg[stack][k].append(v)
        print()

    print("\n=== Agregado (média sobre datasets) ===")
    baseline = None
    for stack in STACKS:
        vs = agg[stack]["brier_vila"]
        bs = agg[stack]["brier_blend"]
        ps = agg[stack]["brier_prior"]
        acs = agg[stack]["accuracy"]
        brier_blend_avg = sum(bs) / len(bs)
        delta = ""
        if baseline is None:
            baseline = brier_blend_avg
        else:
            pct = (brier_blend_avg - baseline) / baseline * 100
            delta = f"  ({pct:+.1f}% vs minimal)"
        print(
            f"  {stack:16s} "
            f"brier_vila={sum(vs)/len(vs):.3f} ({len(vs)} ds)  "
            f"brier_blend={brier_blend_avg:.3f}{delta}  "
            f"brier_prior={sum(ps)/len(ps):.3f}  "
            f"acc={sum(acs)/len(acs):.2f}"
        )


if __name__ == "__main__":
    main()
