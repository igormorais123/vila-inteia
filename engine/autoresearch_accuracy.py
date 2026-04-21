"""
Onda 159: AutoResearch Vila — Karpathy-style accuracy optimization loop.

Inspirado em Karpathy/autoresearch (2026-03): AI agent runs experiments,
keeps changes that improve metric, reverts ones that don't. Single metric,
single target file, git history records exploration trace.

Para Vila: target config é o kwargs dict de rodar_backtest_acc.
Metric = brier_blend_final_avg agregado sobre N datasets (lower better).

Loop:
  1. baseline config + metric
  2. propose variação (toggle flag, tweak param)
  3. run backtest → brier
  4. keep if brier melhor, revert se pior
  5. save trace, repeat até stop criteria (max_iter, no-improvement, budget)

Cached: results por config_hash pra não repetir runs (quota-aware).
Research directions em docs/AUTORESEARCH_PROGRAM.md (markdown humana-editável).
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

logger = logging.getLogger(__name__)


# Space de variações: cada entry é (param_name, tipo, valores/range).
# Agent samples daqui pra propor nova config.
PROPOSAL_SPACE: list[dict[str, Any]] = [
    # Flags binárias
    {"param": "usar_debate", "tipo": "flag"},
    {"param": "usar_peso_adaptativo", "tipo": "flag"},
    {"param": "usar_blend_ensemble", "tipo": "flag"},
    {"param": "chain_of_thought", "tipo": "flag"},
    {"param": "aplicar_platt", "tipo": "flag"},
    {"param": "usar_self_consistency", "tipo": "flag"},
    {"param": "temp_por_persona", "tipo": "flag"},
    {"param": "aplicar_calib_por_persona", "tipo": "flag"},
    # Contínuos
    {"param": "peso_vila", "tipo": "range", "min": 0.5, "max": 0.9, "step": 0.05},
    {"param": "prob_floor", "tipo": "range", "min": 0.0, "max": 0.15, "step": 0.025},
    {"param": "prob_ceiling", "tipo": "range", "min": 0.85, "max": 1.0, "step": 0.025},
    {"param": "recency_decay", "tipo": "range", "min": 0.7, "max": 1.0, "step": 0.05},
    # Discretos
    {"param": "few_shot_k", "tipo": "choice", "valores": [0, 1, 2, 3]},
    {"param": "n_samples_sc", "tipo": "choice", "valores": [2, 3, 5]},
]


@dataclass
class Experiment:
    """Um run do loop autoresearch."""
    iteracao: int
    config: dict[str, Any]
    config_hash: str
    parent_hash: str | None
    proposal_delta: dict[str, Any]  # o que mudou vs parent
    metric: float | None = None  # brier_blend (lower better)
    n_eventos: int = 0
    kept: bool = False
    timestamp: str = ""
    erro: str | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def _hash_config(config: dict) -> str:
    """SHA1 de config ordenada pra cache lookup."""
    s = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def propor_variacao(
    config_atual: dict[str, Any],
    historia: list[Experiment],
    rng: random.Random | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Amostra uma variação do PROPOSAL_SPACE evitando repetir hashes já vistos.
    Returns (new_config, delta).
    """
    rng = rng or random.Random()
    seen_hashes = {e.config_hash for e in historia}

    for _ in range(50):
        proposal = rng.choice(PROPOSAL_SPACE)
        novo = copy.deepcopy(config_atual)
        param = proposal["param"]
        antes = novo.get(param)

        if proposal["tipo"] == "flag":
            novo[param] = not bool(novo.get(param, False))
        elif proposal["tipo"] == "range":
            lo, hi, step = proposal["min"], proposal["max"], proposal["step"]
            valores = [round(lo + i * step, 4) for i in range(int((hi - lo) / step) + 1)]
            escolha = rng.choice([v for v in valores if v != antes])
            novo[param] = escolha
        elif proposal["tipo"] == "choice":
            valores = [v for v in proposal["valores"] if v != antes]
            if not valores:
                continue
            novo[param] = rng.choice(valores)
        else:
            continue

        novo_hash = _hash_config(novo)
        if novo_hash not in seen_hashes:
            return novo, {param: {"antes": antes, "depois": novo[param]}}

    # fallback: retorna config atual se 50 tentativas falharam
    return config_atual, {}


def rodar_experimento(
    config: dict[str, Any],
    datasets: list[str],
    sim: Any,
    persona_ids: list[str],
    llm_fn=None,
    max_eventos_por_dataset: int = 3,
) -> tuple[float | None, int]:
    """
    Executa rodar_backtest_acc em N datasets com config dada.
    Retorna (brier_blend_avg_ponderado, n_eventos_total).
    """
    from engine.backtest_acc import rodar_backtest_acc

    briers = []
    n_eventos_total = 0
    for ds_path in datasets:
        try:
            r = rodar_backtest_acc(
                dataset_path=ds_path,
                sim=sim,
                persona_ids=persona_ids,
                llm_fn=llm_fn,
                max_eventos=max_eventos_por_dataset,
                **{k: v for k, v in config.items() if k != "max_eventos"},
            )
            b = r.get("brier_blend_final_avg") or r.get("brier_vila_calibrada_avg")
            n = r.get("n_eventos", 0)
            if b is not None and n > 0:
                briers.append((b, n))
                n_eventos_total += n
        except Exception as e:
            logger.debug(f"rodar_experimento {ds_path} falhou: {e}")

    if not briers:
        return None, 0
    w_total = sum(n for _, n in briers)
    brier_avg = sum(b * n for b, n in briers) / w_total if w_total else None
    return brier_avg, n_eventos_total


def loop_autoresearch(
    baseline_config: dict[str, Any],
    datasets: list[str],
    sim: Any,
    persona_ids: list[str],
    llm_fn=None,
    max_iteracoes: int = 10,
    max_sem_melhoria: int = 5,
    seed: int | None = None,
    trace_path: str | Path = "data/autoresearch_trace.jsonl",
    max_eventos_por_dataset: int = 3,
    verbose: bool = True,
) -> dict:
    """
    Loop Karpathy-style: propõe variações, roda, keep/revert.

    Stop:
      - max_iteracoes atingido
      - max_sem_melhoria consecutivos
    """
    rng = random.Random(seed)
    trace_path = Path(trace_path)
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    # Baseline
    if verbose:
        print(f"[autoresearch] rodando baseline...")
    b_base, n_base = rodar_experimento(
        baseline_config, datasets, sim, persona_ids, llm_fn,
        max_eventos_por_dataset=max_eventos_por_dataset,
    )
    base_hash = _hash_config(baseline_config)
    base_exp = Experiment(
        iteracao=0,
        config=baseline_config,
        config_hash=base_hash,
        parent_hash=None,
        proposal_delta={},
        metric=b_base,
        n_eventos=n_base,
        kept=True,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    historia: list[Experiment] = [base_exp]
    best = base_exp
    sem_melhoria = 0

    with open(trace_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(base_exp.to_dict(), default=str) + "\n")

    if verbose:
        print(f"[autoresearch] baseline brier={b_base} n={n_base}")

    for i in range(1, max_iteracoes + 1):
        novo_config, delta = propor_variacao(best.config, historia, rng)
        if not delta:
            if verbose:
                print(f"[autoresearch] iter {i}: espaço esgotado, parando")
            break
        novo_hash = _hash_config(novo_config)
        if verbose:
            k = list(delta.keys())[0]
            d = delta[k]
            print(f"[autoresearch] iter {i}: propor {k}={d['antes']} → {d['depois']}")

        b_novo, n_novo = rodar_experimento(
            novo_config, datasets, sim, persona_ids, llm_fn,
            max_eventos_por_dataset=max_eventos_por_dataset,
        )
        kept = b_novo is not None and (best.metric is None or b_novo < best.metric)
        exp = Experiment(
            iteracao=i,
            config=novo_config,
            config_hash=novo_hash,
            parent_hash=best.config_hash,
            proposal_delta=delta,
            metric=b_novo,
            n_eventos=n_novo,
            kept=kept,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        historia.append(exp)

        with open(trace_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(exp.to_dict(), default=str) + "\n")

        if kept:
            delta_brier = (best.metric or 0) - (b_novo or 0)
            if verbose:
                print(f"[autoresearch] iter {i}: KEEP brier {best.metric:.4f}→{b_novo:.4f} (Δ-{delta_brier:.4f})")
            best = exp
            sem_melhoria = 0
        else:
            if verbose:
                b_str = f"{b_novo:.4f}" if b_novo else "None"
                print(f"[autoresearch] iter {i}: REVERT brier={b_str} (best={best.metric:.4f})")
            sem_melhoria += 1
            if sem_melhoria >= max_sem_melhoria:
                if verbose:
                    print(f"[autoresearch] {sem_melhoria} iter sem melhoria, parando")
                break

    return {
        "n_iteracoes": len(historia) - 1,
        "baseline_brier": b_base,
        "best_brier": best.metric,
        "best_config": best.config,
        "best_hash": best.config_hash,
        "best_iteracao": best.iteracao,
        "historia": [e.to_dict() for e in historia],
        "n_kept": sum(1 for e in historia if e.kept),
        "n_reverted": sum(1 for e in historia if not e.kept),
    }
