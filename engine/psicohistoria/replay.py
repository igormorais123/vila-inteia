"""
Replay + export da trajetória psico-histórica (Onda 20).

Permite salvar trajetória completa de uma simulação em JSON, carregar depois
pra análise post-mortem, comparar múltiplas runs.

Uso:
    from engine.psicohistoria.replay import exportar_run, carregar_run, comparar_runs
    exportar_run("/tmp/vila-run-001.json", vila_id="sim_a")
    traj_a = carregar_run("/tmp/vila-run-001.json")
    diff = comparar_runs(traj_a, traj_b)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time
from collections import Counter


@dataclass
class ExportRun:
    vila_id: str
    timestamp_export: float
    n_steps: int
    estados: list[str]
    steps: list[int]
    metricas: list[dict]
    mules: list[dict]
    meta: dict


def exportar_run(
    arquivo: str | Path,
    vila_id: str = "default",
    meta: dict | None = None,
) -> int:
    """Salva trajetória atual do RASTREADOR_GLOBAL em JSON. Retorna bytes escritos."""
    from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
    traj = RASTREADOR_GLOBAL.trajetoria
    export = ExportRun(
        vila_id=vila_id,
        timestamp_export=time.time(),
        n_steps=len(traj.estados),
        estados=list(traj.estados),
        steps=list(traj.steps),
        metricas=[
            {
                "step": m.step,
                "n_conversas": m.n_conversas,
                "n_reflexoes": m.n_reflexoes,
                "n_agentes_ativos": m.n_agentes_ativos,
                "n_agentes_latentes": m.n_agentes_latentes,
                "total_agentes": m.total_agentes,
                "polarizacao_media": m.polarizacao_media,
                "gini_economia": m.gini_economia,
                "propostas_constituintes_ativas": m.propostas_constituintes_ativas,
                "contribuicoes_ao_desafio": m.contribuicoes_ao_desafio,
            }
            for m in traj.metricas_por_step
        ],
        mules=list(traj.mules_detectados),
        meta=meta or {},
    )
    path = Path(arquivo)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(export), ensure_ascii=False, indent=2)
    path.write_text(payload, encoding="utf-8")
    return len(payload.encode("utf-8"))


def carregar_run(arquivo: str | Path) -> ExportRun:
    """Carrega ExportRun de JSON."""
    path = Path(arquivo)
    if not path.exists():
        raise FileNotFoundError(f"run não existe: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return ExportRun(**data)


@dataclass
class ComparacaoRuns:
    run_a: str
    run_b: str
    n_steps_a: int
    n_steps_b: int
    distribuicao_a: dict[str, float]
    distribuicao_b: dict[str, float]
    kl_divergence: float
    total_variation: float
    ambos_convergem_mesmo: bool


def _kl(p: dict[str, float], q: dict[str, float]) -> float:
    import math
    eps = 1e-12
    keys = set(p) | set(q)
    total = 0.0
    for k in keys:
        pk = max(p.get(k, 0), eps)
        qk = max(q.get(k, 0), eps)
        total += pk * math.log(pk / qk)
    return total


def _distribuicao(estados: list[str]) -> dict[str, float]:
    if not estados:
        return {}
    c = Counter(estados)
    n = len(estados)
    return {k: v / n for k, v in c.items()}


def comparar_runs(run_a: ExportRun, run_b: ExportRun) -> ComparacaoRuns:
    """
    Compara 2 runs: KL divergence entre distribuições de estado + TV distance.
    Converge mesmo se último estado de ambos é igual.
    """
    dist_a = _distribuicao(run_a.estados)
    dist_b = _distribuicao(run_b.estados)
    kl = _kl(dist_a, dist_b)
    tv = 0.5 * sum(abs(dist_a.get(k, 0) - dist_b.get(k, 0))
                    for k in set(dist_a) | set(dist_b))
    ult_a = run_a.estados[-1] if run_a.estados else None
    ult_b = run_b.estados[-1] if run_b.estados else None
    return ComparacaoRuns(
        run_a=run_a.vila_id,
        run_b=run_b.vila_id,
        n_steps_a=len(run_a.estados),
        n_steps_b=len(run_b.estados),
        distribuicao_a=dist_a,
        distribuicao_b=dist_b,
        kl_divergence=kl,
        total_variation=tv,
        ambos_convergem_mesmo=ult_a == ult_b,
    )


def replay_no_rastreador(run: ExportRun) -> int:
    """
    Carrega run no RASTREADOR_GLOBAL (substitui estado atual).
    Restaura estados raw do export sem re-classificar.
    Útil para análise post-mortem usando endpoints ao vivo.
    """
    from engine.psicohistoria.detector_estado_vila import (
        RASTREADOR_GLOBAL, MetricasStep,
    )
    traj = RASTREADOR_GLOBAL.trajetoria
    traj.estados.clear()
    traj.steps.clear()
    traj.metricas_por_step.clear()
    traj.mules_detectados.clear()
    # Reconstrói preservando estados raw do export (não re-classifica)
    for estado, step_num, m_dict in zip(run.estados, run.steps, run.metricas):
        traj.estados.append(estado)
        traj.steps.append(step_num)
        traj.metricas_por_step.append(MetricasStep(**m_dict))
    for mule in run.mules:
        traj.mules_detectados.append(mule)
    return len(run.estados)


def resumo_run(run: ExportRun) -> dict:
    """Métricas agregadas da run (útil para display)."""
    dist = _distribuicao(run.estados)
    return {
        "vila_id": run.vila_id,
        "n_steps": run.n_steps,
        "distribuicao": dist,
        "estado_inicial": run.estados[0] if run.estados else None,
        "estado_final": run.estados[-1] if run.estados else None,
        "n_mules": len(run.mules),
    }
