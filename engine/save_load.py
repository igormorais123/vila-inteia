"""
Save/Load de Vilas — cada vila é um "jogo salvo" retomável.

Uma vila tem:
  - instância  (linha em vila_instancias)
  - estado     (snapshots em vila_snapshots — JSONB completo)

Fluxo:
    criar_vila(nome, pacote, qtd)          -> vila_id
    snapshot_vila(vila_id, simulacao)       -> snapshot_id   (auto ou manual)
    listar_vilas(status=None)               -> [{...}]
    pausar_vila(vila_id)
    retomar_vila(vila_id)                   -> SimulacaoVila
    restaurar_snapshot(snapshot_id)         -> SimulacaoVila

O estado serializado inclui:
    {
      "step": int,
      "hora_virtual": iso,
      "habitantes_ids": [...],
      "grafo_social": {...},
      "historico": [...],
      "economia_saldos": {agente_id: float},
      "constituicao_vigente": [artigo_id, ...],
      "desafios_ativos": [...],
      "workspace": {...},
      "estado_chateaubriand": {...}
    }
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from engine.supabase_db import inserir, buscar, atualizar

logger = logging.getLogger("vila-inteia.saveload")


# =========================================================
# Criar / listar / pausar / retomar
# =========================================================

def criar_vila(
    nome: str,
    pacote_base: str,
    qtd_habitantes: int = 100,
    objetivo: str = "",
    descricao: str = "",
    metadados: Optional[dict] = None,
    criada_por: str = "",
) -> Optional[dict]:
    """Cria nova instância de vila. Retorna registro completo."""
    registro = {
        "nome": nome,
        "descricao": descricao,
        "pacote_base": pacote_base,
        "qtd_habitantes": max(1, min(qtd_habitantes, 2000)),
        "objetivo": objetivo,
        "status": "ativa",
        "step_atual": 0,
        "hora_virtual": datetime.now(timezone.utc).isoformat(),
        "metadados": metadados or {},
        "criada_por": criada_por or "sistema",
    }
    resultado = inserir("vila_instancias", registro)
    if resultado:
        logger.info(f"Vila criada: {resultado['id']} ({nome})")
    return resultado


def listar_vilas(status: Optional[str] = None, limite: int = 50) -> list[dict]:
    """Lista vilas, opcionalmente filtradas por status."""
    params = f"order=atualizada_em.desc&limit={limite}"
    if status:
        params = f"status=eq.{status}&{params}"
    return buscar("vila_instancias", params)


def get_vila(vila_id: str) -> Optional[dict]:
    resultados = buscar("vila_instancias", f"id=eq.{vila_id}")
    return resultados[0] if resultados else None


def pausar_vila(vila_id: str) -> bool:
    """Pausa vila. Não apaga estado, só marca."""
    data = {
        "status": "pausada",
        "pausada_em": datetime.now(timezone.utc).isoformat(),
        "atualizada_em": datetime.now(timezone.utc).isoformat(),
    }
    return atualizar("vila_instancias", f"id=eq.{vila_id}", data) is not None


def retomar_vila(vila_id: str) -> bool:
    """Marca vila como ativa de novo."""
    data = {
        "status": "ativa",
        "pausada_em": None,
        "atualizada_em": datetime.now(timezone.utc).isoformat(),
    }
    return atualizar("vila_instancias", f"id=eq.{vila_id}", data) is not None


def arquivar_vila(vila_id: str) -> bool:
    """Move vila para arquivada (não aparece em listas padrão)."""
    data = {
        "status": "arquivada",
        "atualizada_em": datetime.now(timezone.utc).isoformat(),
    }
    return atualizar("vila_instancias", f"id=eq.{vila_id}", data) is not None


# =========================================================
# Snapshots
# =========================================================

def snapshot_vila(
    vila_id: str,
    simulacao,                # instância de SimulacaoVila
    tipo: str = "auto",
) -> Optional[dict]:
    """Tira snapshot completo da vila."""
    estado = _serializar_simulacao(simulacao)
    snap = {
        "vila_id": vila_id,
        "step": getattr(simulacao, "step", 0),
        "tipo": tipo,
        "estado": estado,
        "tamanho_bytes": len(json.dumps(estado, default=str)),
    }
    resultado = inserir("vila_snapshots", snap)

    # Atualizar step_atual e hora_virtual da vila
    if resultado:
        atualizar(
            "vila_instancias",
            f"id=eq.{vila_id}",
            {
                "step_atual": snap["step"],
                "hora_virtual": getattr(simulacao, "hora_atual", datetime.now(timezone.utc)).isoformat()
                                if hasattr(simulacao, "hora_atual") else None,
                "atualizada_em": datetime.now(timezone.utc).isoformat(),
            },
        )
    return resultado


def listar_snapshots(vila_id: str, limite: int = 20) -> list[dict]:
    return buscar("vila_snapshots",
                  f"vila_id=eq.{vila_id}&order=step.desc&limit={limite}")


def snapshot_mais_recente(vila_id: str) -> Optional[dict]:
    snaps = listar_snapshots(vila_id, limite=1)
    return snaps[0] if snaps else None


def restaurar_snapshot(snapshot_id: str):
    """
    Retorna o estado serializado do snapshot.
    O caller reconstrói SimulacaoVila a partir disso.
    """
    resultados = buscar("vila_snapshots", f"id=eq.{snapshot_id}")
    return resultados[0] if resultados else None


# =========================================================
# Serialização de SimulacaoVila
# =========================================================

def _serializar_simulacao(sim) -> dict:
    """
    Converte SimulacaoVila em dict JSON-friendly.

    Dá preferência a atributos, cai em getattr defensivo.
    """
    def _safe(x):
        try:
            json.dumps(x, default=str)
            return x
        except (TypeError, ValueError):
            return str(x)

    habitantes = []
    personas = getattr(sim, "personas", {}) or {}
    for pid, p in personas.items():
        habitantes.append({
            "id": pid,
            "nome": getattr(p, "nome_exibicao", ""),
            "categoria": getattr(p, "categoria", ""),
            "local_atual": getattr(getattr(p, "rascunho", None), "local_atual", ""),
            "saldo": getattr(p, "saldo", None),
            "humor": getattr(p, "humor", None),
        })

    return {
        "step": getattr(sim, "step", 0),
        "hora_virtual": getattr(sim, "hora_atual", datetime.now(timezone.utc)).isoformat()
                       if hasattr(sim, "hora_atual") else None,
        "nome": getattr(sim, "nome", ""),
        "habitantes": habitantes,
        "qtd_habitantes": len(habitantes),
        "stats": _safe(getattr(sim, "stats", {})),
        "conversas_recentes": _safe(getattr(sim, "conversas_recentes", [])[-50:]),
        "topicos_ativos": _safe(getattr(sim, "topicos_ativos", [])),
        "pausada": getattr(sim, "pausada", False),
    }
