"""
Onda 106: persist backtest runs em Supabase (opcional) + local JSONL fallback.

Tabela vila_backtests schema:
  id uuid PK, criado_em timestamptz, personas jsonb, n_eventos int,
  accuracy_global float, brier_vila float, brier_prior float, skill float,
  platt_a float, platt_b float, raw_payload jsonb

Local fallback: data/backtest_history.jsonl
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_LOCAL_LOG = Path("data/backtest_history.jsonl")


def _flatten(saida: dict) -> dict:
    """Extrai top-level metrics do payload de rodar_backtest_todos."""
    ag = saida.get("agregado", {}) or {}
    cal = saida.get("calibracao_platt", {}) or {}
    personas = []
    for ds in saida.get("datasets", []):
        personas = ds.get("persona_panel") or personas
        if personas: break
    return {
        "id": str(uuid.uuid4()),
        "criado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "personas": personas,
        "n_eventos": ag.get("n_eventos_total", 0),
        "n_datasets": ag.get("n_datasets", 0),
        "accuracy_global": ag.get("accuracy_global"),
        "brier_vila": ag.get("brier_vila_macro_avg"),
        "brier_prior": ag.get("brier_prior_macro_avg"),
        "skill": ag.get("skill_brier_vs_prior_macro"),
        "platt_a": cal.get("platt_a"),
        "platt_b": cal.get("platt_b"),
    }


def _supabase_disponivel() -> bool:
    try:
        from engine.supabase_db import SUPABASE_URL, SUPABASE_KEY
        return bool(SUPABASE_URL and SUPABASE_KEY)
    except Exception:
        return False


def salvar(saida: dict) -> dict:
    """Persiste backtest em Supabase se disponível + sempre em JSONL local."""
    record = _flatten(saida)
    record["raw_payload"] = saida  # só pra supabase; strip antes local

    # Supabase
    supabase_id = None
    if _supabase_disponivel():
        try:
            from engine.supabase_db import inserir
            resp = inserir("vila_backtests", record)
            if resp and isinstance(resp, list) and resp:
                supabase_id = resp[0].get("id")
        except Exception as e:
            logger.debug(f"supabase insert falhou: {e}")

    # Local JSONL (sem raw_payload pra não inflar)
    local_record = {k: v for k, v in record.items() if k != "raw_payload"}
    local_record["supabase_id"] = supabase_id
    _LOCAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOCAL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(local_record, default=str) + "\n")

    return {
        "salvo_em_supabase": supabase_id is not None,
        "salvo_em_local": True,
        "id": record["id"],
        "supabase_id": supabase_id,
    }


def historico(limite: int = 20) -> list[dict]:
    """Lê últimos N registros do log local (ou Supabase se configurado)."""
    if _supabase_disponivel():
        try:
            from engine.supabase_db import buscar
            # ORDER BY criado_em desc
            r = buscar("vila_backtests", f"order=criado_em.desc&limit={limite}")
            if r:
                return r
        except Exception as e:
            logger.debug(f"supabase query falhou: {e}")

    if not _LOCAL_LOG.exists():
        return []
    out = []
    with open(_LOCAL_LOG, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha: continue
            try:
                out.append(json.loads(linha))
            except json.JSONDecodeError:
                pass
    out.reverse()
    return out[:limite]
