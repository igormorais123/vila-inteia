"""
Base comum dos agentes vivos. Dá acesso real a:
    - arquivos do repositório (leitura)
    - endpoints do harness (via cliente local, sem HTTP overhead quando
      possível)
    - Supabase (escrita dos heartbeats)
    - pasta data/agentes_vivos/<nome>/ para relatórios persistentes
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("vila-inteia.agentes_vivos")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "agentes_vivos"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Heartbeat:
    """Registro de um pulso de um agente vivo."""
    heartbeat_id: str
    agente: str
    step: int
    executado_em: str
    duracao_ms: int
    acoes: list[str] = field(default_factory=list)
    resultado: str = "ok"                       # ok | alerta | falha
    alertas: list[str] = field(default_factory=list)
    relatorio_path: str = ""
    metricas: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "heartbeat_id": self.heartbeat_id,
            "agente": self.agente,
            "step": self.step,
            "executado_em": self.executado_em,
            "duracao_ms": self.duracao_ms,
            "acoes": self.acoes,
            "resultado": self.resultado,
            "alertas": self.alertas,
            "relatorio_path": self.relatorio_path,
            "metricas": self.metricas,
        }


class AgenteVivo:
    """
    Agente vivo da INTEIA presente na Vila.

    Tem identidade, ciclo (acões), e sabe persistir traço de cada pulso.
    """

    id: str = "agente_vivo_base"
    nome: str = "Agente"
    papel: str = "?"
    intervalo_steps: int = 100

    def __init__(self):
        self.pasta_relatorios = DATA_DIR / self.id
        self.pasta_relatorios.mkdir(parents=True, exist_ok=True)

    # -------------- acesso a recursos --------------

    def ler_arquivo(self, rel_path: str, max_bytes: int = 20000) -> Optional[str]:
        """Leitura segura de arquivo do repositório (read-only, com limite)."""
        p = (REPO_ROOT / rel_path).resolve()
        try:
            if not str(p).startswith(str(REPO_ROOT)):
                return None  # impede traversal fora do repo
            if not p.is_file():
                return None
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(max_bytes)
        except Exception as exc:
            logger.debug("ler_arquivo falhou %s: %s", rel_path, exc)
            return None

    def listar(self, rel_dir: str, padrao: str = "*") -> list[str]:
        p = (REPO_ROOT / rel_dir).resolve()
        if not str(p).startswith(str(REPO_ROOT)) or not p.is_dir():
            return []
        return [str(x.relative_to(REPO_ROOT)) for x in p.glob(padrao) if x.is_file()]

    def obter_harness_local(self) -> dict:
        """Snapshot do estado do harness sem HTTP — importa direto."""
        try:
            from engine.harness import (
                habilitado, relatorio_orcamentos, skill_registry, listar_cards
            )
            from engine import supabase_db
            tot = 0
            try:
                r = supabase_db.buscar("vila_traces", "select=trace_id&limit=1")
                if r is not None:
                    r_all = supabase_db.buscar("vila_traces", "select=trace_id")
                    tot = len(r_all) if r_all else 0
            except Exception:
                pass
            return {
                "tracing_habilitado": habilitado(),
                "supabase_conectado": bool(supabase_db.status_conexao().get("conectado")),
                "total_traces": tot,
                "num_skills": len(skill_registry.listar(1)),
                "num_capabilities": len(listar_cards()),
                "fases_orcamento": list(relatorio_orcamentos().keys()),
            }
        except Exception as exc:
            return {"erro": str(exc)}

    def obter_ficha_fundador(self) -> dict:
        try:
            from engine.memoria.fundador import carregar_ficha
            return carregar_ficha().as_dict()
        except Exception:
            return {}

    # -------------- ciclo --------------

    def acoes(self, step: int, sim: Any = None) -> tuple[dict, list[str], list[str]]:
        """
        Sobrescrever na subclasse.

        Retorna: (metricas_dict, acoes_executadas_list, alertas_list)
        """
        return {}, [], []

    def executar_heartbeat(self, step: int, sim: Any = None) -> Heartbeat:
        inicio = time.perf_counter_ns()
        inicio_iso = datetime.now(timezone.utc).isoformat()
        heartbeat_id = uuid.uuid4().hex
        acoes = []
        alertas = []
        metricas = {}
        resultado = "ok"

        try:
            metricas, acoes, alertas = self.acoes(step, sim)
            if alertas:
                resultado = "alerta"
        except Exception as exc:
            resultado = "falha"
            alertas.append(f"exception:{exc}")
            logger.warning("heartbeat %s falhou: %s", self.id, exc)

        duracao_ms = max(1, (time.perf_counter_ns() - inicio) // 1_000_000)

        # persiste relatório local
        relatorio_path = self.pasta_relatorios / f"{heartbeat_id}.json"
        payload = {
            "heartbeat_id": heartbeat_id,
            "agente": self.id,
            "step": step,
            "inicio": inicio_iso,
            "duracao_ms": duracao_ms,
            "resultado": resultado,
            "acoes": acoes,
            "alertas": alertas,
            "metricas": metricas,
        }
        try:
            with open(relatorio_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.debug("erro gravando relatorio %s: %s", relatorio_path, exc)

        # grava em Supabase (tabela vila_heartbeat)
        try:
            from engine import supabase_db
            supabase_db.inserir("vila_heartbeat", {
                "heartbeat_id": heartbeat_id,
                "agente": self.id,
                "step": step,
                "executado_em": inicio_iso,
                "duracao_ms": duracao_ms,
                "resultado": resultado,
                "acoes": acoes,
                "alertas": alertas,
                "metricas": metricas,
            })
        except Exception as exc:
            logger.debug("erro gravando vila_heartbeat: %s", exc)

        return Heartbeat(
            heartbeat_id=heartbeat_id,
            agente=self.id,
            step=step,
            executado_em=inicio_iso,
            duracao_ms=duracao_ms,
            acoes=acoes,
            resultado=resultado,
            alertas=alertas,
            relatorio_path=str(relatorio_path.relative_to(REPO_ROOT)),
            metricas=metricas,
        )

    def ultimos_relatorios(self, limit: int = 5) -> list[dict]:
        arqs = sorted(self.pasta_relatorios.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        out = []
        for p in arqs[:limit]:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    out.append(json.load(f))
            except Exception:
                pass
        return out
