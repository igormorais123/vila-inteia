"""
api/rotas_vivos — Endpoints dos agentes vivos da INTEIA na Vila.

Helena Strategos (cientista-chefe) e Efesto Tekhton (CTO) estão vivos:
heartbeats executam auditoria real, publicam coluna diária no Mirante,
e podem ser consultados em tempo real.

Rotas:
    GET  /api/v1/vivos/status
    POST /api/v1/vivos/heartbeat/{agente}
    GET  /api/v1/vivos/{agente}/ultimos
    POST /api/v1/vivos/publicar-coluna-hoje
    GET  /api/v1/vivos/coluna/historico
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger("vila-inteia.api.vivos")

router = APIRouter(prefix="/api/v1/vivos", tags=["Agentes Vivos"])


@router.get("/status")
def status_vivos() -> dict:
    """Status do scheduler e dos agentes vivos."""
    from engine.agentes_vivos import scheduler, HELENA, EFESTO
    ult_helena = HELENA.ultimos_relatorios(limit=1)
    ult_efesto = EFESTO.ultimos_relatorios(limit=1)
    return {
        "scheduler": scheduler.status(),
        "ultimo_helena": ult_helena[0] if ult_helena else None,
        "ultimo_efesto": ult_efesto[0] if ult_efesto else None,
    }


@router.post("/heartbeat/{agente}")
def disparar_heartbeat(agente: str, step: int = 0) -> dict:
    """Dispara manualmente um heartbeat de um agente."""
    from engine.agentes_vivos import HELENA, EFESTO
    mapa = {"helena": HELENA, "helena_strategos": HELENA,
            "efesto": EFESTO, "efesto_tekhton": EFESTO}
    a = mapa.get(agente.lower())
    if not a:
        raise HTTPException(status_code=404, detail=f"Agente '{agente}' desconhecido. Opções: helena, efesto.")
    hb = a.executar_heartbeat(step=step or 1, sim=None)
    return hb.as_dict()


@router.get("/{agente}/ultimos")
def ultimos_heartbeats(
    agente: str,
    limit: int = Query(5, ge=1, le=50),
) -> dict:
    """Últimos relatórios de heartbeat de um agente."""
    from engine.agentes_vivos import HELENA, EFESTO
    mapa = {"helena": HELENA, "helena_strategos": HELENA,
            "efesto": EFESTO, "efesto_tekhton": EFESTO}
    a = mapa.get(agente.lower())
    if not a:
        raise HTTPException(status_code=404, detail=f"Agente '{agente}' desconhecido")
    return {"agente": a.id, "relatorios": a.ultimos_relatorios(limit=limit)}


@router.post("/publicar-coluna-hoje")
def publicar_coluna(
    forcar: bool = Query(False, description="republica mesmo se já existe matéria hoje"),
    autor: Optional[str] = Query(None, description="helena | efesto (override)"),
) -> dict:
    """Publica a coluna diária da Vila no Mirante News."""
    from engine.coluna_vila import publicar_coluna_hoje
    r = publicar_coluna_hoje(forcar=forcar, forcar_autor=autor)
    return r


@router.get("/coluna/previa")
def previa_coluna(autor: Optional[str] = None) -> dict:
    """Mostra como ficaria a coluna de hoje sem publicar (dry-run)."""
    from engine.coluna_vila import compor_coluna_hoje
    mdx = compor_coluna_hoje(forcar_autor=autor)
    return mdx


@router.get("/coluna/historico")
def historico_coluna(limit: int = Query(30, ge=1, le=365)) -> dict:
    """Histórico das colunas publicadas (persistido em vila_coluna_publicacoes)."""
    try:
        from engine import supabase_db
        rows = supabase_db.buscar("vila_coluna_publicacoes", f"order=publicado_em.desc&limit={limit}") or []
        return {"total": len(rows), "colunas": rows}
    except Exception as exc:
        logger.warning("historico coluna falhou: %s", exc)
        return {"total": 0, "colunas": [], "erro": str(exc)}
