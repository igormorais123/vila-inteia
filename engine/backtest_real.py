"""
Onda 92: backtest de previsão em eventos históricos REAIS.

Datasets em data/backtest/*.csv:
  evento_id, data, contexto, outcome_real (0/1), probabilidade_prior

Pra cada evento, consulta panel de personas estratégicas, extrai
probabilidade estimada de outcome=1, compara com real. Métricas:
Brier score, accuracy, calibração.
"""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


PANEL_ESTRATEGICO_DEFAULT = ["CL001", "CL002", "CL007", "CL022"]
# CL001 Musk, CL002 Jobs, CL007 Buffett, CL022 Gates (checar JSON real)


def carregar_dataset(path: str | Path) -> list[dict]:
    """Lê CSV de backtest. Retorna lista de eventos dict."""
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append({
                "evento_id": row["evento_id"],
                "data": row["data"],
                "contexto": row["contexto"],
                "outcome_real": int(row["outcome_real"]),
                "probabilidade_prior": float(row["probabilidade_prior"]),
            })
    return out


_REGEX_PCT = re.compile(r"(\d{1,3})\s*%")
_REGEX_DEC = re.compile(r"\b0\.(\d{1,4})\b")


def extrair_probabilidade(texto: str) -> float | None:
    """
    Extrai probabilidade (0-1) de texto livre.
    Tenta:
      - "70%" → 0.70
      - "0.6" ou "0,6" → 0.6
      - ignora se nenhum match ou fora [0,1].
    """
    if not texto:
        return None
    t = texto.replace(",", ".")
    # %
    m = _REGEX_PCT.search(t)
    if m:
        v = int(m.group(1)) / 100.0
        if 0 <= v <= 1:
            return v
    # 0.xxx
    m = _REGEX_DEC.search(t)
    if m:
        v = float("0." + m.group(1))
        if 0 <= v <= 1:
            return v
    return None


def consultar_panel(
    contexto: str,
    persona_ids: list[str],
    sim: Any,
    llm_fn=None,
) -> dict:
    """
    Consulta panel estratégico sobre probabilidade de outcome=1.
    Retorna per-persona prob + agregado (média).
    """
    from engine.panel_chat import panel_chat
    pergunta = (
        f"Analise o seguinte evento: \"{contexto}\"\n\n"
        f"Pergunta: qual a probabilidade (0% a 100%) do resultado "
        f"principal associado acontecer/ter acontecido? "
        f"Responda em 1-2 frases citando APENAS um número em %."
    )
    resp = panel_chat(
        persona_ids=persona_ids,
        pergunta=pergunta, sim=sim, llm_fn=llm_fn,
        max_tokens=120, temperatura=0.4,
    )
    probs = []
    per_persona = []
    for r in resp.get("respostas", []):
        texto = r.get("resposta") or ""
        p = extrair_probabilidade(texto)
        per_persona.append({
            "persona_id": r.get("persona_id"),
            "persona_nome": r.get("persona_nome"),
            "resposta": texto,
            "prob_extraida": p,
            "erro": r.get("erro"),
        })
        if p is not None:
            probs.append(p)
    agregado = sum(probs) / len(probs) if probs else None
    return {
        "prob_agregada": agregado,
        "n_respostas_validas": len(probs),
        "n_personas": len(persona_ids),
        "per_persona": per_persona,
    }


def brier(p: float, y: int) -> float:
    return (p - y) ** 2


def rodar_backtest(
    dataset_path: str | Path,
    sim: Any,
    persona_ids: list[str] | None = None,
    llm_fn=None,
    max_eventos: int | None = None,
    sleep_entre_eventos_s: float = 0.0,
) -> dict:
    """
    Roda backtest completo em 1 dataset.

    Returns dict:
        dataset, n_eventos, n_respondidos,
        accuracy, brier_vila, brier_prior,
        skill_brier_vs_prior (>0 = Vila ganha),
        eventos: [{evento_id, contexto, outcome_real, prob_prior,
                    prob_vila, acertou, per_persona}, ...]
    """
    persona_ids = persona_ids or PANEL_ESTRATEGICO_DEFAULT
    eventos_raw = carregar_dataset(dataset_path)
    if max_eventos:
        eventos_raw = eventos_raw[:max_eventos]

    resultados = []
    briers_vila = []
    briers_prior = []
    acertos = 0

    import time as _time
    for i, ev in enumerate(eventos_raw):
        if i > 0 and sleep_entre_eventos_s > 0:
            _time.sleep(sleep_entre_eventos_s)
        panel = consultar_panel(ev["contexto"], persona_ids, sim, llm_fn=llm_fn)
        p_vila = panel["prob_agregada"]
        p_prior = ev["probabilidade_prior"]
        y = ev["outcome_real"]
        acertou = (p_vila is not None) and ((p_vila >= 0.5) == (y == 1))
        if acertou:
            acertos += 1
        if p_vila is not None:
            briers_vila.append(brier(p_vila, y))
        briers_prior.append(brier(p_prior, y))
        resultados.append({
            "evento_id": ev["evento_id"],
            "data": ev["data"],
            "contexto": ev["contexto"][:200],
            "outcome_real": y,
            "prob_prior": p_prior,
            "prob_vila": p_vila,
            "acertou_vila": acertou,
            "n_respostas_validas": panel["n_respostas_validas"],
        })

    n_resp = sum(1 for r in resultados if r["prob_vila"] is not None)
    brier_vila_avg = sum(briers_vila) / len(briers_vila) if briers_vila else None
    brier_prior_avg = sum(briers_prior) / len(briers_prior) if briers_prior else None
    skill = None
    if brier_vila_avg is not None and brier_prior_avg and brier_prior_avg > 0:
        skill = 1 - brier_vila_avg / brier_prior_avg

    return {
        "dataset": str(dataset_path),
        "n_eventos": len(eventos_raw),
        "n_respondidos": n_resp,
        "accuracy_vila": acertos / len(eventos_raw) if eventos_raw else 0,
        "brier_vila_avg": brier_vila_avg,
        "brier_prior_avg": brier_prior_avg,
        "skill_brier_vs_prior": skill,
        "persona_panel": persona_ids,
        "eventos": resultados,
    }


def rodar_backtest_todos(
    base_dir: str | Path = "data/backtest",
    sim: Any = None,
    persona_ids: list[str] | None = None,
    llm_fn=None,
    max_eventos_por_ds: int | None = None,
    sleep_entre_eventos_s: float = 0.0,
    sleep_entre_datasets_s: float = 0.0,
) -> dict:
    import time as _time
    base = Path(base_dir)
    if not base.exists():
        return {"erro": f"dir {base} não existe", "datasets": []}

    datasets = sorted(base.glob("*.csv"))
    resumos = []
    for j, ds in enumerate(datasets):
        if j > 0 and sleep_entre_datasets_s > 0:
            _time.sleep(sleep_entre_datasets_s)
        try:
            r = rodar_backtest(ds, sim, persona_ids, llm_fn, max_eventos_por_ds,
                                sleep_entre_eventos_s=sleep_entre_eventos_s)
            resumos.append(r)
        except Exception as e:
            resumos.append({"dataset": str(ds), "erro": str(e)})

    # Agregado
    total_eventos = sum(r.get("n_eventos", 0) for r in resumos if "erro" not in r)
    total_acertos = sum(
        r["accuracy_vila"] * r["n_eventos"]
        for r in resumos if "erro" not in r and r.get("accuracy_vila") is not None
    )
    briers_vila = [
        r["brier_vila_avg"] for r in resumos
        if "erro" not in r and r.get("brier_vila_avg") is not None
    ]
    briers_prior = [
        r["brier_prior_avg"] for r in resumos
        if "erro" not in r and r.get("brier_prior_avg") is not None
    ]

    agregado = {
        "n_datasets": len(datasets),
        "n_eventos_total": total_eventos,
        "accuracy_global": total_acertos / total_eventos if total_eventos else 0,
        "brier_vila_macro_avg": sum(briers_vila) / len(briers_vila) if briers_vila else None,
        "brier_prior_macro_avg": sum(briers_prior) / len(briers_prior) if briers_prior else None,
    }
    if agregado["brier_vila_macro_avg"] is not None and agregado["brier_prior_macro_avg"]:
        agregado["skill_brier_vs_prior_macro"] = 1 - agregado["brier_vila_macro_avg"] / agregado["brier_prior_macro_avg"]

    return {"agregado": agregado, "datasets": resumos}
