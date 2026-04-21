"""
Onda 175: meta-autoresearch — loop aprende de traces anteriores.

Karpathy pattern evolves: cada run deixa trace, meta-autoresearch
agrega todos traces, identifica params com histórico positivo,
BIASA proposal sampler pra preferir esses params em novos runs.

Pipeline:
  1. scan data/autoresearch_trace*.jsonl
  2. aggregate por param: count KEEP vs REVERT
  3. compute score = (kept + 1) / (kept + reverted + 2)   Laplace-smoothed
  4. return scores dict
  5. biased_proposal usa scores como weights pra amostragem

Exemplo scores:
  usar_debate: 0.75 (3 kept, 0 revert) → proposta frequente
  prob_floor: 0.30 (0 kept, 2 revert) → proposta rara
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def agregar_traces(trace_glob: str = "data/autoresearch_trace*.jsonl") -> dict:
    """
    Lê todos os traces JSONL matching glob, retorna agregado.

    Returns:
        {
          "n_runs": N,
          "n_experiments": M,
          "por_param": {
            param_name: {"kept": k, "reverted": r, "score": s,
                         "valores_kept": [...], "valores_reverted": [...]},
            ...
          },
          "global_best_brier": min brier across all traces,
        }
    """
    from glob import glob
    por_param: dict[str, dict] = defaultdict(
        lambda: {"kept": 0, "reverted": 0, "valores_kept": [], "valores_reverted": []}
    )
    n_runs = 0
    n_experiments = 0
    global_best = None

    paths = glob(trace_glob)
    for path in paths:
        n_runs += 1
        try:
            for line in Path(path).read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                n_experiments += 1
                metric = d.get("metric")
                if metric is not None:
                    if global_best is None or metric < global_best:
                        global_best = metric
                # Count delta param mudança
                delta = d.get("proposal_delta", {}) or {}
                kept = d.get("kept", False)
                for param, change in delta.items():
                    bucket = por_param[param]
                    novo_v = change.get("depois") if isinstance(change, dict) else None
                    if kept:
                        bucket["kept"] += 1
                        if novo_v is not None:
                            bucket["valores_kept"].append(novo_v)
                    else:
                        bucket["reverted"] += 1
                        if novo_v is not None:
                            bucket["valores_reverted"].append(novo_v)
        except Exception as e:
            logger.debug(f"agregar_traces {path} falhou: {e}")

    # Laplace-smoothed score
    for param, b in por_param.items():
        k = b["kept"]
        r = b["reverted"]
        b["score"] = (k + 1) / (k + r + 2)
        b["n_total"] = k + r

    return {
        "n_runs": n_runs,
        "n_experiments": n_experiments,
        "por_param": dict(por_param),
        "global_best_brier": global_best,
    }


def salvar_learnings(
    agregado: dict,
    path: str | Path = "data/autoresearch_learnings.json",
) -> Path:
    """Persiste agregado pra próximo run consultar."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(agregado, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def carregar_learnings(
    path: str | Path = "data/autoresearch_learnings.json",
) -> dict:
    """Carrega learnings se existe, {} senão."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def biased_proposal(
    config_atual: dict,
    historia: list,
    rng=None,
    learnings: dict | None = None,
    explore_rate: float = 0.2,
):
    """
    Proposta meta-aware: com prob (1-explore_rate), escolhe param com
    maior score do learnings. Com prob explore_rate, amostra random
    (preserva exploração).

    Fallback pra propor_variacao original se learnings vazio.
    """
    import random as _rand
    from engine.autoresearch_accuracy import (
        propor_variacao, PROPOSAL_SPACE, _hash_config,
    )
    import copy

    rng = rng or _rand.Random()
    if not learnings or not learnings.get("por_param"):
        return propor_variacao(config_atual, historia, rng)

    # Explore: random proposal
    if rng.random() < explore_rate:
        return propor_variacao(config_atual, historia, rng)

    # Exploit: rank params por score desc
    scores = learnings.get("por_param", {})
    params_ranked = sorted(
        PROPOSAL_SPACE,
        key=lambda p: scores.get(p["param"], {}).get("score", 0.5),
        reverse=True,
    )
    seen_hashes = {e.config_hash for e in historia}

    for proposal in params_ranked:
        param = proposal["param"]
        novo = copy.deepcopy(config_atual)
        antes = novo.get(param)
        if proposal["tipo"] == "flag":
            novo[param] = not bool(novo.get(param, False))
        elif proposal["tipo"] == "range":
            lo, hi, step = proposal["min"], proposal["max"], proposal["step"]
            valores = [round(lo + i * step, 4) for i in range(int((hi - lo) / step) + 1)]
            candidatos = [v for v in valores if v != antes]
            if not candidatos:
                continue
            novo[param] = rng.choice(candidatos)
        elif proposal["tipo"] == "choice":
            candidatos = [v for v in proposal["valores"] if v != antes]
            if not candidatos:
                continue
            novo[param] = rng.choice(candidatos)
        else:
            continue
        novo_hash = _hash_config(novo)
        if novo_hash not in seen_hashes:
            return novo, {param: {"antes": antes, "depois": novo[param]}}
    # fallback random
    return propor_variacao(config_atual, historia, rng)


def relatorio(agregado: dict) -> str:
    """Formata agregado como tabela legível."""
    linhas = [
        f"=== Meta-AutoResearch Learnings ===",
        f"Runs: {agregado.get('n_runs')}",
        f"Experiments: {agregado.get('n_experiments')}",
        f"Global best brier: {agregado.get('global_best_brier')}",
        "",
        f"{'param':<30s} {'kept':>5s} {'rev':>5s} {'score':>6s}",
        "-" * 50,
    ]
    por_param = agregado.get("por_param", {})
    rows = sorted(por_param.items(), key=lambda kv: kv[1]["score"], reverse=True)
    for param, b in rows:
        linhas.append(
            f"{param:<30s} {b['kept']:>5d} {b['reverted']:>5d} {b['score']:>6.3f}"
        )
    return "\n".join(linhas)
