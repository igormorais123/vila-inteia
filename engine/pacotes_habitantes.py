"""
Pacotes de Habitantes — carrega agentes sintéticos para uma Vila.

Cada pacote é um JSON em data/pacotes/<id>.json.

API:
    listar_pacotes()             → lista de {id, nome, qtd, tipo}
    carregar_pacote(pacote_id)   → list[dict] de agentes
    amostrar(pacote_id, qtd)     → amostra aleatória
    combinar(configs)            → mistura múltiplos pacotes

Config típico para Vila nova:
    [
        {"pacote_id": "eleitores-df-2015", "qtd": 500, "seed": 42},
        {"pacote_id": "consultores-lendarios", "qtd": 20}
    ]
"""

from __future__ import annotations

import json
import logging
import os
import random
from pathlib import Path
from typing import Optional

from engine.supabase_db import buscar

logger = logging.getLogger("vila-inteia.pacotes")


PACOTES_DIR = Path(__file__).parent.parent / "data" / "pacotes"


# =========================================================
# Listagem
# =========================================================

def listar_pacotes() -> list[dict]:
    """
    Une metadados do Supabase com arquivos presentes em disco.
    """
    db = buscar("vila_pacotes_habitantes") or []
    arquivos = {p.stem: p for p in PACOTES_DIR.glob("*.json")}

    pacotes = []
    for reg in db:
        arq = arquivos.get(reg["id"])
        total = reg.get("total_agentes")
        if not total and arq:
            try:
                with arq.open(encoding="utf-8") as f:
                    total = len(json.load(f))
            except Exception:
                total = 0
        pacotes.append({
            "id": reg["id"],
            "nome": reg["nome"],
            "descricao": reg.get("descricao", ""),
            "tipo": reg.get("tipo", ""),
            "total_agentes": total,
            "disponivel_local": arq is not None,
        })
    # Pacotes no disco mas não registrados
    registrados = {p["id"] for p in pacotes}
    for stem, path in arquivos.items():
        if stem in registrados:
            continue
        try:
            with path.open(encoding="utf-8") as f:
                total = len(json.load(f))
        except Exception:
            total = 0
        pacotes.append({
            "id": stem,
            "nome": stem,
            "descricao": "(não registrado no Supabase)",
            "tipo": "",
            "total_agentes": total,
            "disponivel_local": True,
        })
    return pacotes


# =========================================================
# Carregamento
# =========================================================

def carregar_pacote(pacote_id: str) -> list[dict]:
    """Lê o JSON do pacote e retorna lista de agentes."""
    path = PACOTES_DIR / f"{pacote_id}.json"
    if not path.exists():
        # fallback: alguns bancos vivem em data/ direto
        fallback = PACOTES_DIR.parent / f"banco-{pacote_id}.json"
        if fallback.exists():
            path = fallback
        else:
            logger.warning(f"Pacote não encontrado: {pacote_id}")
            return []

    try:
        with path.open(encoding="utf-8") as f:
            agentes = json.load(f)
        if not isinstance(agentes, list):
            logger.error(f"Pacote {pacote_id} não é lista")
            return []
        return agentes
    except Exception as e:
        logger.error(f"Erro carregando {pacote_id}: {e}")
        return []


def amostrar(pacote_id: str, qtd: int, seed: Optional[int] = None) -> list[dict]:
    """Pega amostra aleatória do pacote."""
    todos = carregar_pacote(pacote_id)
    if not todos:
        return []
    n = min(qtd, len(todos))
    rng = random.Random(seed)
    return rng.sample(todos, n)


# =========================================================
# Combinação de múltiplos pacotes
# =========================================================

def combinar(configs: list[dict]) -> list[dict]:
    """
    Mistura pacotes seguindo configs.

    configs = [
        {"pacote_id": "eleitores-df-2015", "qtd": 500, "seed": 42},
        {"pacote_id": "consultores-lendarios", "qtd": 20}
    ]
    """
    resultado = []
    vistos = set()
    for c in configs:
        pid = c.get("pacote_id")
        qtd = c.get("qtd", 50)
        seed = c.get("seed")
        if not pid:
            continue
        amostra = amostrar(pid, qtd, seed)
        for a in amostra:
            aid = a.get("id") or f"{pid}:{len(resultado)}"
            if aid in vistos:
                continue
            vistos.add(aid)
            a.setdefault("pacote_origem", pid)
            a.setdefault("id", aid)
            resultado.append(a)
    return resultado


# =========================================================
# Validação de pacote
# =========================================================

CAMPOS_MINIMOS = {"id", "nome"}


def validar_pacote(pacote_id: str) -> dict:
    """Retorna diagnóstico do pacote: quantidade, campos, problemas."""
    agentes = carregar_pacote(pacote_id)
    if not agentes:
        return {"ok": False, "motivo": "pacote vazio ou inexistente"}

    faltando = []
    for i, a in enumerate(agentes[:100]):
        falta = CAMPOS_MINIMOS - set(a.keys())
        if falta:
            faltando.append({"idx": i, "faltando": list(falta)})

    return {
        "ok": len(faltando) == 0,
        "total": len(agentes),
        "amostra_problemas": faltando[:5],
        "campos_presentes": sorted(set().union(*(a.keys() for a in agentes[:10]))),
    }
