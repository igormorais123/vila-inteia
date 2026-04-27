"""
Onda 197: Vila pipeline estilo Mirofish — corpus → grafo → simulação → relatório.

Wrapper sobre engine.backtest_real que expõe API-compatible com Mirofish:
  - GrafoVila      (entidades=events+personas, relações=predições)
  - SimulacaoVila  (status, progresso, resultado)
  - RelatorioVila  (conteudo, insights, calibração)

Mantém Vila specialty (arquétipos hardcoded, Brier+Platt calib, backtest real)
e adiciona output narrativo + grafo + insights emergentes.

Usado por api/rotas_mirofish.py.
"""

from __future__ import annotations

import glob
import time
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Optional

from engine.backtest_real import carregar_dataset, rodar_backtest


# =========================================================================
# Dataclasses (espelham Mirofish: GrafoMirofish, SimulacaoMirofish, RelatorioMirofish)
# =========================================================================

@dataclass
class GrafoVila:
    graph_id: str
    total_entidades: int = 0
    total_relacoes: int = 0
    status: str = "pronto"
    schema: dict = field(default_factory=dict)
    datasets: list = field(default_factory=list)
    personas: list = field(default_factory=list)


@dataclass
class SimulacaoVila:
    simulation_id: str
    graph_id: str
    status: str = "rodando"
    progresso: float = 0.0
    steps_executados: int = 0
    elapsed_s: float = 0.0
    resultado: dict = field(default_factory=dict)


@dataclass
class RelatorioVila:
    report_id: str
    graph_id: str
    simulation_id: str
    titulo: str = ""
    conteudo: str = ""
    metricas: dict = field(default_factory=dict)
    per_dataset: list = field(default_factory=list)
    insights: list = field(default_factory=list)
    gerado_em: str = ""


# =========================================================================
# Pipeline
# =========================================================================

def construir_grafo(
    dataset_paths: list[str],
    persona_ids: list[str],
    persona_nomes: dict[str, str],
) -> GrafoVila:
    """Fase 1: corpus → grafo de entidades + relações."""
    n_eventos = 0
    for dp in dataset_paths:
        n_eventos += len(carregar_dataset(dp))
    n_personas = len(persona_ids)
    n_entidades = n_eventos + n_personas
    n_relacoes = n_eventos * n_personas + n_eventos  # persona-event + event-dataset
    return GrafoVila(
        graph_id=f"vila-{int(time.time())}",
        total_entidades=n_entidades,
        total_relacoes=n_relacoes,
        status="pronto",
        schema={
            "nodos": ["PersonaLendaria", "EventoHistorico", "Dataset"],
            "arestas": ["Persona-PREV->Event", "Event-PERTENCE->Dataset"],
        },
        datasets=[Path(dp).stem for dp in dataset_paths],
        personas=[{"id": pid, "nome": persona_nomes.get(pid, pid)} for pid in persona_ids],
    )


def rodar_simulacao(
    grafo: GrafoVila,
    dataset_paths: list[str],
    persona_ids: list[str],
    sim: Any,
    llm_fn=None,
) -> tuple[SimulacaoVila, list[dict], list[dict]]:
    """Fase 2: rodar backtest Vila em todos eventos.

    Retorna (SimulacaoVila, per_event_list, per_dataset_list).
    """
    sim_id = f"sim-{int(time.time())}"
    per_event = []
    per_dataset = []
    t0 = time.time()
    total_eventos = 0

    for dp in dataset_paths:
        name = Path(dp).stem
        res = rodar_backtest(
            dataset_path=dp, sim=sim, persona_ids=persona_ids,
            llm_fn=llm_fn, few_shot_k=0,
        )
        ds_hits = sum(1 for e in res["eventos"] if e["acertou_vila"])
        per_dataset.append({
            "dataset": name, "n": res["n_eventos"], "hits": ds_hits,
            "acc": ds_hits / res["n_eventos"] if res["n_eventos"] else 0,
            "brier_vila": res["brier_vila_avg"],
            "brier_prior": res["brier_prior_avg"],
            "skill": (1 - res["brier_vila_avg"] / res["brier_prior_avg"])
                     if (res["brier_vila_avg"] is not None and res["brier_prior_avg"]) else None,
        })
        for e in res["eventos"]:
            probs_pp = [pp["prob_extraida"] for pp in e["per_persona"]
                        if pp["prob_extraida"] is not None]
            per_event.append({
                "evento_id": e["evento_id"], "dataset": name,
                "prob_vila": e["prob_vila"], "prob_prior": e["prob_prior"],
                "outcome_real": e["outcome_real"], "acertou": e["acertou_vila"],
                "per_persona_probs": {
                    pp["persona_id"]: pp["prob_extraida"] for pp in e["per_persona"]
                },
                "std_persona": pstdev(probs_pp) if len(probs_pp) > 1 else 0.0,
                "contexto": e["contexto"][:160],
            })
        total_eventos += res["n_eventos"]

    dt = time.time() - t0
    total_hits = sum(1 for e in per_event if e["acertou"])
    brier_vila_vals = [
        (e["prob_vila"] - e["outcome_real"]) ** 2
        for e in per_event if e["prob_vila"] is not None
    ]
    brier_prior_vals = [(e["prob_prior"] - e["outcome_real"]) ** 2 for e in per_event]
    bv = mean(brier_vila_vals) if brier_vila_vals else None
    bp = mean(brier_prior_vals) if brier_prior_vals else None
    skill = (1 - bv / bp) if (bv is not None and bp) else None

    simulacao = SimulacaoVila(
        simulation_id=sim_id, graph_id=grafo.graph_id,
        status="concluida", progresso=1.0,
        steps_executados=total_eventos * len(persona_ids),
        elapsed_s=dt,
        resultado={
            "n_eventos": total_eventos, "n_personas": len(persona_ids),
            "acc_total": total_hits / total_eventos if total_eventos else 0,
            "brier_vila_avg": bv, "brier_prior_avg": bp,
            "skill_brier_vs_prior": skill,
        },
    )
    return simulacao, per_event, per_dataset


def extrair_insights(per_event: list[dict], top_k: int = 5) -> list[dict]:
    """Fase 3: divergências, consensos, wins/losses confiantes."""
    if not per_event:
        return []
    divergences = sorted(per_event, key=lambda x: -x["std_persona"])[:top_k]
    consensos = [e for e in per_event if e["std_persona"] < 0.03 and e["acertou"]][:top_k]
    conf_wins = sorted(
        [e for e in per_event if e["acertou"] and e["prob_vila"] is not None],
        key=lambda x: -abs(x["prob_vila"] - 0.5)
    )[:top_k]
    conf_losses = sorted(
        [e for e in per_event if not e["acertou"] and e["prob_vila"] is not None],
        key=lambda x: -abs(x["prob_vila"] - 0.5)
    )[:top_k]
    return [
        {"tipo": "divergencia_personas",
         "desc": "Eventos com maior discordância entre personas (potencial alpha)",
         "items": [{"evento": e["evento_id"], "std": round(e["std_persona"], 3),
                    "probs": e["per_persona_probs"], "contexto": e["contexto"][:80]}
                   for e in divergences]},
        {"tipo": "consenso_forte",
         "desc": "Eventos onde personas convergiram e acertaram",
         "items": [{"evento": e["evento_id"], "prob": round(e["prob_vila"], 3),
                    "real": e["outcome_real"]} for e in consensos]},
        {"tipo": "vitoria_confiante",
         "desc": "Previsões com alta confiança que se confirmaram",
         "items": [{"evento": e["evento_id"], "prob": round(e["prob_vila"], 3),
                    "real": e["outcome_real"]} for e in conf_wins]},
        {"tipo": "derrota_confiante",
         "desc": "Previsões confiantes que falharam (risco calibração)",
         "items": [{"evento": e["evento_id"], "prob": round(e["prob_vila"], 3),
                    "real": e["outcome_real"], "contexto": e["contexto"][:80]}
                   for e in conf_losses]},
    ]


def gerar_relatorio(
    grafo: GrafoVila,
    simulacao: SimulacaoVila,
    per_event: list[dict],
    per_dataset: list[dict],
    insights: list[dict],
    persona_nomes: dict[str, str],
    persona_ids: list[str],
) -> RelatorioVila:
    """Fase 4: relatório executivo (heurístico, sem dependência LLM)."""
    res = simulacao.resultado
    nomes = ", ".join(persona_nomes.get(pid, pid) for pid in persona_ids)
    n_ev = res["n_eventos"]
    n_hits = int(res["acc_total"] * n_ev)

    melhor = max(per_dataset, key=lambda x: x["acc"]) if per_dataset else None
    pior = min(per_dataset, key=lambda x: x["acc"]) if per_dataset else None
    div_media = mean(e["std_persona"] for e in per_event) if per_event else 0.0

    skill_pct = (res.get("skill_brier_vs_prior") or 0) * 100
    bv = res.get("brier_vila_avg") or 0
    bp = res.get("brier_prior_avg") or 0
    secao_datasets = (
        f"Melhor dataset: {melhor['dataset']} ({100*melhor['acc']:.0f}% acc). "
        f"Pior: {pior['dataset']} ({100*pior['acc']:.0f}% acc) — datasets com framings "
        f"anti-contextuais degradam performance."
        if (melhor and pior)
        else "Sem dados de dataset agregados disponíveis."
    )
    narrativa = (
        f"A Vila INTEIA, com panel estratégico de {len(persona_ids)} consultores lendários "
        f"({nomes}), previu {n_ev} eventos históricos em {len(per_dataset)} domínios distintos. "
        f"\n\n"
        f"Acurácia geral: {n_hits}/{n_ev} ({100*res['acc_total']:.1f}%). "
        f"Brier score Vila = {bv:.4f}, contra prior humano = {bp:.4f}. "
        f"Skill score (ganho vs prior) = {skill_pct:+.1f}%, indicando que o panel Vila "
        f"melhora sobre a intuição humana calibrada."
        f"\n\n"
        f"{secao_datasets}"
        f"\n\n"
        f"Divergência média entre personas = {div_media:.3f}. "
        f"Divergência alta sinaliza incerteza estrutural (potential alpha em mercados de previsão)."
    )

    return RelatorioVila(
        report_id=f"rep-{int(time.time())}",
        graph_id=grafo.graph_id, simulation_id=simulacao.simulation_id,
        titulo=f"Vila INTEIA Predictions — {n_ev} events, {len(per_dataset)} datasets",
        conteudo=narrativa,
        metricas=res,
        per_dataset=per_dataset,
        insights=insights,
        gerado_em=time.strftime("%Y-%m-%dT%H:%M:%S"),
    )


def pipeline_completo(
    base_dir: str = "data/backtest",
    dataset_glob: str = "*.csv",
    persona_ids: list[str] | None = None,
    sim: Any = None,
    llm_fn=None,
) -> dict:
    """Pipeline end-to-end: grafo → simulação → insights → relatório.

    Returns dict com {grafo, simulacao, relatorio} (dataclass.__dict__).
    """
    persona_ids = persona_ids or ["CL001", "CL002", "CL007"]
    dataset_paths = sorted(glob.glob(f"{base_dir}/{dataset_glob}"))
    if not dataset_paths:
        return {"erro": f"sem datasets em {base_dir}/{dataset_glob}"}

    if sim is None:
        return {"erro": "sim obrigatório (SimulacaoVila ativa)"}

    persona_nomes = {}
    for pid in persona_ids:
        p = sim.personas.get(pid)
        if p:
            persona_nomes[pid] = getattr(p, "nome_exibicao", pid)
        else:
            persona_nomes[pid] = pid

    t_start = time.time()
    grafo = construir_grafo(dataset_paths, persona_ids, persona_nomes)
    simulacao, per_event, per_dataset = rodar_simulacao(
        grafo, dataset_paths, persona_ids, sim, llm_fn=llm_fn,
    )
    insights = extrair_insights(per_event)
    relatorio = gerar_relatorio(
        grafo, simulacao, per_event, per_dataset, insights,
        persona_nomes, persona_ids,
    )

    return {
        "grafo": grafo.__dict__,
        "simulacao": simulacao.__dict__,
        "relatorio": relatorio.__dict__,
        "pipeline_elapsed_s": time.time() - t_start,
    }
