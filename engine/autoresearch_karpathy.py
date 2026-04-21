"""
Onda 171: Full Karpathy-style autoresearch.

Completa Onda 159 com features Karpathy faltantes:
- LLM-guided proposals: agent analisa trace + propõe próxima variação
- Tournament mode: N seeds paralelos, best-of-N
- Git-commit integration: cada iter keep = git commit real (opcional)
- program.md live update: autoresearch escreve findings no markdown

Pattern Karpathy (2026-03):
  1. Single target file + single metric
  2. Agent edits, evaluates, commits if melhor
  3. Exploration trace visível via git log
  4. Hundreds of experiments per overnight
"""

from __future__ import annotations

import json
import logging
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def proposal_llm_guided(
    config_atual: dict,
    historia: list,  # list[Experiment]
    llm_fn=None,
) -> tuple[dict, dict]:
    """
    LLM-guided proposal: analisa trace, propõe próxima variação.

    Fallback pra random proposal se LLM indisponível.
    """
    from engine.autoresearch_accuracy import propor_variacao
    if not llm_fn:
        return propor_variacao(config_atual, historia)

    # Build trace summary pra LLM
    kept_moves = [e for e in historia if getattr(e, "kept", False)]
    reverted = [e for e in historia if not getattr(e, "kept", False)]

    trace_summary = []
    for e in historia[-10:]:  # últimos 10
        delta = getattr(e, "proposal_delta", {})
        m = getattr(e, "metric", None)
        kept = "KEEP" if getattr(e, "kept", False) else "REVERT"
        param = next(iter(delta.keys()), "baseline") if delta else "baseline"
        d = delta.get(param, {}) if delta else {}
        m_str = f"{m:.4f}" if m is not None else "None"
        trace_summary.append(
            f"iter {e.iteracao}: {param} {d.get('antes')}→{d.get('depois')} "
            f"brier={m_str} [{kept}]"
        )

    mensagens = [
        {"role": "system", "content": (
            "Você é um research scientist otimizando accuracy de predição (brier_blend lower=better). "
            "Analise o trace + proponha UMA mudança incremental ao config. "
            "Formato resposta: JSON {\"param\": nome, \"novo_valor\": valor}."
        )},
        {"role": "user", "content": (
            f"Config atual:\n{json.dumps(config_atual, indent=2)}\n\n"
            f"Trace histórico últimos 10:\n" + "\n".join(trace_summary) + "\n\n"
            f"Params exploráveis: usar_debate, usar_peso_adaptativo, usar_blend_ensemble, "
            f"chain_of_thought, aplicar_platt, usar_self_consistency, temp_por_persona, "
            f"aplicar_calib_por_persona, peso_vila (0.5-0.9), prob_floor (0.0-0.15), "
            f"prob_ceiling (0.85-1.0), recency_decay (0.7-1.0), few_shot_k (0-3). "
            f"Responda APENAS JSON da mudança."
        )},
    ]

    try:
        from engine.ia_client import chamar_llm
        resp = chamar_llm(
            mensagens=mensagens, modelo="rapido",
            max_tokens=100, temperatura=0.5,
            bypass_step_cap=True,
        )
        if not resp:
            return propor_variacao(config_atual, historia)
        # Parse JSON {"param": ..., "novo_valor": ...}
        import re
        match = re.search(r'\{[^}]*"param"[^}]*\}', resp)
        if not match:
            return propor_variacao(config_atual, historia)
        proposal = json.loads(match.group(0))
        param = proposal.get("param")
        novo_valor = proposal.get("novo_valor")
        if param is None or novo_valor is None:
            return propor_variacao(config_atual, historia)
        import copy
        novo = copy.deepcopy(config_atual)
        antes = novo.get(param)
        if antes == novo_valor:
            return propor_variacao(config_atual, historia)
        novo[param] = novo_valor
        return novo, {param: {"antes": antes, "depois": novo_valor}}
    except Exception as e:
        logger.debug(f"LLM proposal falhou: {e}")
        return propor_variacao(config_atual, historia)


def loop_tournament(
    baseline_config: dict,
    datasets: list[str],
    sim,
    persona_ids: list[str],
    llm_fn=None,
    n_seeds: int = 3,
    max_iteracoes: int = 10,
    trace_dir: str = "data/autoresearch_tournament",
    verbose: bool = True,
    **kwargs,
) -> dict:
    """
    Tournament mode: N seeds paralelos, melhor resultado vence.

    Seeds usam mesmo baseline + diferentes RNGs. Karpathy pattern:
    multiple agents racing, best wins.

    SEQUENCIAL por simplicidade (thread-safety concerns com LLM env).
    Paralelo verdadeiro requer isolation de GROQ_MODEL_RAPIDO.
    """
    from engine.autoresearch_accuracy import loop_autoresearch
    trace_dir_p = Path(trace_dir)
    trace_dir_p.mkdir(parents=True, exist_ok=True)

    resultados = []
    for seed in range(n_seeds):
        trace_path = trace_dir_p / f"seed_{seed}.jsonl"
        if verbose:
            print(f"\n=== Tournament seed {seed}/{n_seeds - 1} ===")
        r = loop_autoresearch(
            baseline_config=baseline_config,
            datasets=datasets, sim=sim,
            persona_ids=persona_ids, llm_fn=llm_fn,
            max_iteracoes=max_iteracoes,
            seed=seed,
            trace_path=str(trace_path),
            verbose=verbose,
            **kwargs,
        )
        resultados.append({"seed": seed, "resultado": r})

    # Vencedor: menor best_brier
    validos = [r for r in resultados if r["resultado"].get("best_brier") is not None]
    if not validos:
        return {"erro": "todos seeds falharam", "n_seeds": n_seeds}
    campeao = min(validos, key=lambda x: x["resultado"]["best_brier"])

    return {
        "n_seeds": n_seeds,
        "campeao_seed": campeao["seed"],
        "campeao_brier": campeao["resultado"]["best_brier"],
        "campeao_config": campeao["resultado"]["best_config"],
        "todos_seeds": [
            {
                "seed": r["seed"],
                "best_brier": r["resultado"].get("best_brier"),
                "baseline_brier": r["resultado"].get("baseline_brier"),
                "n_iter": r["resultado"].get("n_iteracoes"),
            }
            for r in resultados
        ],
    }


def git_commit_experiment(
    exp,  # Experiment
    repo_root: str | Path = ".",
    tag_prefix: str = "autoresearch",
) -> str | None:
    """
    Onda 171: git commit de uma iteração keep (Karpathy-style).
    Stages calibracao_platt.json se mudou, commit c/ config hash + brier.

    Returns commit SHA ou None se falhou.
    """
    p = Path(repo_root)
    try:
        subprocess.run(
            ["git", "-C", str(p), "add", "-u"],
            capture_output=True, check=True, timeout=10,
        )
        brier_str = f"{exp.metric:.4f}" if exp.metric is not None else "?"
        msg = (
            f"autoresearch iter {exp.iteracao}: brier={brier_str}\n\n"
            f"Config hash: {exp.config_hash}\n"
            f"Delta: {json.dumps(exp.proposal_delta)}"
        )
        r = subprocess.run(
            ["git", "-C", str(p), "commit", "-m", msg, "--allow-empty"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            return None
        sha = subprocess.run(
            ["git", "-C", str(p), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        return sha[:12]
    except Exception as e:
        logger.debug(f"git_commit_experiment falhou: {e}")
        return None


def atualizar_program_md(
    resultado: dict,
    path: str | Path = "docs/AUTORESEARCH_PROGRAM.md",
) -> None:
    """
    Append findings ao program.md pra agent revisitar em próxima rodada.
    Karpathy pattern: research directions evoluem com trace.
    """
    p = Path(path)
    if not p.exists():
        return
    import time
    timestamp = time.strftime("%Y-%m-%d %H:%M")
    best_brier = resultado.get("best_brier")
    baseline = resultado.get("baseline_brier")
    best_config = resultado.get("best_config", {})
    delta = ""
    if best_brier is not None and baseline is not None and baseline > 0:
        pct = (best_brier - baseline) / baseline * 100
        delta = f" ({pct:+.1f}%)"

    linhas = [
        f"\n\n## Run {timestamp}\n",
        f"- Baseline brier: {baseline}\n",
        f"- Best brier: {best_brier}{delta}\n",
        f"- Iter: {resultado.get('n_iteracoes')}, kept: {resultado.get('n_kept')}, "
        f"reverted: {resultado.get('n_reverted')}\n",
        f"- Best config params não-default: "
        f"{json.dumps({k: v for k, v in best_config.items() if v not in (None, False, 0, 1.0)})}\n",
    ]
    with open(p, "a", encoding="utf-8") as f:
        f.writelines(linhas)
