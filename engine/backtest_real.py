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
# Onda 123: format CoT "PROBABILIDADE FINAL: N%"
_REGEX_FINAL = re.compile(
    r"PROBABILIDADE\s+FINAL\s*[:：]\s*(\d{1,3})\s*%",
    re.IGNORECASE,
)


def extrair_probabilidade(texto: str) -> float | None:
    """
    Extrai probabilidade (0-1) de texto livre.
    Prioridade:
      - "PROBABILIDADE FINAL: 70%" (Onda 123 CoT)
      - "70%" primeiro match
      - "0.6" ou "0,6"
      - ignora fora [0,1].
    """
    if not texto:
        return None
    t = texto.replace(",", ".")
    m = _REGEX_FINAL.search(t)
    if m:
        v = int(m.group(1)) / 100.0
        if 0 <= v <= 1:
            return v
    m = _REGEX_PCT.search(t)
    if m:
        v = int(m.group(1)) / 100.0
        if 0 <= v <= 1:
            return v
    m = _REGEX_DEC.search(t)
    if m:
        v = float("0." + m.group(1))
        if 0 <= v <= 1:
            return v
    return None


def _build_cot_prefix() -> str:
    """Onda 123: chain-of-thought instruction."""
    return (
        "\n\nPense passo-a-passo antes de responder:\n"
        "  1. Identifique os drivers principais (macro, micro, institucional).\n"
        "  2. Liste fatores a favor e contra o outcome.\n"
        "  3. Ajuste sua estimativa por base rates históricas similares.\n"
        "  4. Confirme: você está over-confident? Ancorar em 40-80% se incerto.\n\n"
        "Estrutura da resposta:\n"
        "RACIOCÍNIO: <2-3 frases curtas>\n"
        "PROBABILIDADE FINAL: <N%>"
    )


def _build_few_shot_block(
    exemplos: list[dict] | None,
    n_max: int = 3,
) -> str:
    """Onda 121: injeta exemplos past-event+outcome pra calibrar LLM."""
    if not exemplos:
        return ""
    linhas = ["\n\nExemplos passados com resultado real (calibre sua resposta):"]
    for e in exemplos[:n_max]:
        ctx = (e.get("contexto") or "")[:160]
        out = e.get("outcome_real")
        prior = e.get("probabilidade_prior", 0.5)
        verdict = "ACONTECEU" if out == 1 else "NÃO ACONTECEU"
        linhas.append(
            f"- \"{ctx}\" → prior humano {int(prior*100)}%, real: {verdict}."
        )
    linhas.append("\nAgora o evento atual:")
    return "\n".join(linhas)


def _agregar_ponderado(
    per_persona: list[dict],
    pesos_persona: dict[str, float] | None,
) -> float | None:
    """
    Onda 122: weighted mean por skill inverso Brier histórico.
    pesos_persona: {persona_id: weight}. Vazio = média aritmética simples.
    """
    validos = [(p["persona_id"], p["prob_extraida"]) for p in per_persona
                if p.get("prob_extraida") is not None]
    if not validos:
        return None
    if not pesos_persona:
        return sum(p for _, p in validos) / len(validos)
    soma_pesos = 0.0
    soma_prob = 0.0
    for pid, prob in validos:
        w = pesos_persona.get(pid, 1.0)
        soma_pesos += w
        soma_prob += w * prob
    if soma_pesos <= 0:
        return sum(p for _, p in validos) / len(validos)
    return soma_prob / soma_pesos


def pesos_desde_ranking_skill(ranking: list[dict]) -> dict[str, float]:
    """
    Onda 122: converte ranking persona_skill em pesos = 1/(Brier+0.01).
    Lower brier → higher weight. Missing brier → peso 1.0.
    """
    pesos = {}
    for r in ranking:
        pid = r.get("persona_id")
        b = r.get("brier_avg")
        if pid is None:
            continue
        if b is None or b < 0:
            pesos[pid] = 1.0
        else:
            pesos[pid] = 1.0 / (b + 0.01)
    return pesos


def consultar_panel(
    contexto: str,
    persona_ids: list[str],
    sim: Any,
    llm_fn=None,
    paralelo: bool = False,
    sleep_entre_personas_s: float = 0.0,
    few_shot_exemplos: list[dict] | None = None,
    pesos_persona: dict[str, float] | None = None,
    chain_of_thought: bool = True,
) -> dict:
    """
    Consulta panel estratégico sobre probabilidade de outcome=1.
    Retorna per-persona prob + agregado (média ou ponderada).

    paralelo=False (default) respeita rate limits TPM.
    few_shot_exemplos: Onda 121 — eventos passados injetados no prompt.
    pesos_persona: Onda 122 — {persona_id: weight}. Vazio = média simples.
    chain_of_thought: Onda 123 — pede raciocínio estruturado (default True).
    """
    from engine.panel_chat import panel_chat
    few_shot = _build_few_shot_block(few_shot_exemplos)
    if chain_of_thought:
        pergunta = (
            f"Analise o seguinte evento: \"{contexto}\"\n\n"
            f"Pergunta: qual a probabilidade (0% a 100%) do resultado "
            f"principal associado acontecer/ter acontecido?"
            + few_shot
            + _build_cot_prefix()
        )
        max_tok = 250
    else:
        pergunta = (
            f"Analise o seguinte evento: \"{contexto}\"\n\n"
            f"Pergunta: qual a probabilidade (0% a 100%) do resultado "
            f"principal associado acontecer/ter acontecido? "
            f"Responda em 1-2 frases citando APENAS um número em %."
            + few_shot
        )
        max_tok = 120
    resp = panel_chat(
        persona_ids=persona_ids,
        pergunta=pergunta, sim=sim, llm_fn=llm_fn,
        max_tokens=max_tok, temperatura=0.4,
        paralelo=paralelo,
    )
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
    agregado = _agregar_ponderado(per_persona, pesos_persona)
    n_validas = sum(1 for p in per_persona if p.get("prob_extraida") is not None)
    return {
        "prob_agregada": agregado,
        "n_respostas_validas": n_validas,
        "n_personas": len(persona_ids),
        "per_persona": per_persona,
        "pesos_aplicados": dict(pesos_persona) if pesos_persona else None,
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
    few_shot_k: int = 2,
    pesos_persona: dict[str, float] | None = None,
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
        # Onda 121: walk-forward few-shot = últimos k eventos anteriores
        exemplos = eventos_raw[max(0, i - few_shot_k):i] if few_shot_k > 0 else None
        panel = consultar_panel(ev["contexto"], persona_ids, sim, llm_fn=llm_fn,
                                 few_shot_exemplos=exemplos,
                                 pesos_persona=pesos_persona)
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
            "per_persona": panel["per_persona"],
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
