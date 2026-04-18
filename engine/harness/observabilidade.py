"""
engine/harness/observabilidade — Onda 2 do HARNESS_VILA.md (Gap #1).

TraceEvent estruturado + decorator @trace_fase + writer assíncrono para
Supabase (tabela vila_traces).

Modo shadow por padrão: se Supabase não estiver configurado ou a tabela
não existir, a decoração é no-op silencioso. Nunca altera o retorno da
função decorada. Nunca levanta exceção para o caller.

Habilitar em produção:
    export VILA_TRACE_ENABLED=1

Ver migrations/001_vila_traces.sql para schema da tabela.
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
import queue
import threading
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

logger = logging.getLogger("vila-inteia.harness.observabilidade")

# ---------------------------------------------------------------------
# Config

_ENABLED = os.getenv("VILA_TRACE_ENABLED", "0") == "1"
_QUEUE_MAX = int(os.getenv("VILA_TRACE_QUEUE_MAX", "2000"))
_BATCH_SIZE = int(os.getenv("VILA_TRACE_BATCH", "50"))
_FLUSH_INTERVAL_S = float(os.getenv("VILA_TRACE_FLUSH_S", "5.0"))


def habilitado() -> bool:
    """Retorna True se tracing está ativo."""
    return _ENABLED


# ---------------------------------------------------------------------
# Schema

@dataclass
class TraceEvent:
    """
    Evento de trace estruturado para uma fase cognitiva ou ação observável.

    Mapeia 1:1 com a tabela vila_traces. Pode ser serializado direto como JSON.
    """

    trace_id: str
    step: int
    agente_id: str
    fase: str                      # perceber|recuperar|planejar|executar|conversar|refletir|sintetizar|skill|protocolo
    inicio: str                    # ISO8601
    fim: str                       # ISO8601
    duracao_ms: int
    inputs_hash: str               # sha256 dos inputs (para correlação sem vazar dados)
    outputs_hash: str              # sha256 dos outputs
    causal_parent: Optional[str]   # trace_id do evento que causou este
    tokens_consumidos: int = 0
    custo_usd: float = 0.0
    ferramenta_chamada: Optional[str] = None
    resultado: str = "sucesso"     # sucesso|falha|aprovacao_humana|retry|vazio
    metadata: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------
# Writer assíncrono (não bloqueia o loop cognitivo)

_queue: "queue.Queue[TraceEvent]" = queue.Queue(maxsize=_QUEUE_MAX)
_stop = threading.Event()
_flush_thread: Optional[threading.Thread] = None
_current_parent = threading.local()   # trace_id ativo por thread (para causal chain)


def _supabase_insert_bulk(eventos: list[dict]) -> bool:
    """Insere lote em vila_traces. Retorna False se falhou (não levanta)."""
    try:
        from .. import supabase_db
        ok = True
        for ev in eventos:
            r = supabase_db.inserir("vila_traces", ev)
            if r is None:
                ok = False
        return ok
    except Exception as exc:
        logger.debug("trace insert falhou (shadow): %s", exc)
        return False


def _writer_loop() -> None:
    """Drena a fila em lotes e escreve no Supabase."""
    buffer: list[TraceEvent] = []
    last_flush = time.time()
    while not _stop.is_set():
        try:
            ev = _queue.get(timeout=1.0)
            buffer.append(ev)
        except queue.Empty:
            pass

        agora = time.time()
        precisa_flush = (
            len(buffer) >= _BATCH_SIZE
            or (buffer and agora - last_flush >= _FLUSH_INTERVAL_S)
        )
        if precisa_flush:
            dados = [e.as_dict() for e in buffer]
            _supabase_insert_bulk(dados)
            buffer.clear()
            last_flush = agora

    # flush final ao parar
    if buffer:
        _supabase_insert_bulk([e.as_dict() for e in buffer])


def _ensure_writer() -> None:
    global _flush_thread
    if _flush_thread is None or not _flush_thread.is_alive():
        _flush_thread = threading.Thread(
            target=_writer_loop, name="vila-trace-writer", daemon=True
        )
        _flush_thread.start()


def flush_traces(timeout_s: float = 10.0) -> None:
    """Força flush imediato. Usar em shutdown ou antes de snapshot."""
    if not _ENABLED:
        return
    deadline = time.time() + timeout_s
    while not _queue.empty() and time.time() < deadline:
        time.sleep(0.2)


# ---------------------------------------------------------------------
# Hash helpers (nunca levantam)

def _safe_hash(obj: Any) -> str:
    try:
        payload = json.dumps(obj, default=str, sort_keys=True, ensure_ascii=False)
    except Exception:
        payload = str(obj)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _extrair_agente_id(args: tuple, kwargs: dict) -> str:
    """Tenta identificar o agente nos args. Fallback: desconhecido."""
    for a in list(args) + list(kwargs.values()):
        for attr in ("agente_id", "id", "nome"):
            if hasattr(a, attr):
                v = getattr(a, attr)
                if isinstance(v, str) and v:
                    return v
    return "desconhecido"


def _extrair_step(args: tuple, kwargs: dict) -> int:
    for a in list(args) + list(kwargs.values()):
        if isinstance(a, int) and 0 <= a < 10_000_000:
            return a
        for attr in ("step", "step_atual"):
            if hasattr(a, attr):
                v = getattr(a, attr)
                if isinstance(v, int):
                    return v
    return kwargs.get("step", 0) if isinstance(kwargs.get("step"), int) else 0


# ---------------------------------------------------------------------
# Decorator

def trace_fase(
    fase: str,
    *,
    capturar_tokens: Optional[Callable[[Any], int]] = None,
    capturar_custo: Optional[Callable[[Any], float]] = None,
) -> Callable:
    """
    Decorator que emite TraceEvent ao redor de uma fase cognitiva.

    Uso mínimo::

        from engine.harness import trace_fase

        @trace_fase("sintetizar")
        def sintetizar(personas, topico, hora_atual, ...):
            ...

    Em shadow mode (VILA_TRACE_ENABLED!=1) vira passthrough, sem overhead
    perceptível. Em modo ativo, emite 1 evento por chamada com causal chain.

    Parâmetros:
        fase: nome da fase — convenção usa as 7 do Agent Loop + "skill"/"protocolo"/"tool"
        capturar_tokens: função opcional que lê o retorno e devolve nº de tokens
        capturar_custo: idem para custo em USD
    """
    def deco(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not _ENABLED:
                return func(*args, **kwargs)

            _ensure_writer()
            trace_id = uuid.uuid4().hex
            parent = getattr(_current_parent, "id", None)
            _current_parent.id = trace_id

            inicio = datetime.now(timezone.utc)
            resultado = "sucesso"
            saida = None
            try:
                saida = func(*args, **kwargs)
                return saida
            except Exception:
                resultado = "falha"
                raise
            finally:
                fim = datetime.now(timezone.utc)
                try:
                    tokens = capturar_tokens(saida) if capturar_tokens and saida else 0
                    custo = capturar_custo(saida) if capturar_custo and saida else 0.0
                    ev = TraceEvent(
                        trace_id=trace_id,
                        step=_extrair_step(args, kwargs),
                        agente_id=_extrair_agente_id(args, kwargs),
                        fase=fase,
                        inicio=inicio.isoformat(),
                        fim=fim.isoformat(),
                        duracao_ms=int((fim - inicio).total_seconds() * 1000),
                        inputs_hash=_safe_hash({"args_types": [type(a).__name__ for a in args], "kwargs_keys": list(kwargs.keys())}),
                        outputs_hash=_safe_hash(saida) if saida is not None else "vazio",
                        causal_parent=parent,
                        tokens_consumidos=tokens,
                        custo_usd=custo,
                        resultado=resultado,
                        metadata={},
                    )
                    try:
                        _queue.put_nowait(ev)
                    except queue.Full:
                        logger.warning("vila_traces queue cheia — evento descartado")
                except Exception as exc:
                    logger.debug("erro ao construir trace (shadow): %s", exc)
                finally:
                    # restaura parent para o anterior
                    _current_parent.id = parent
        return wrapper
    return deco
