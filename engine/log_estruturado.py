"""
Logging estruturado JSON (Onda 55).

Emite logs como JSON de 1 linha por registro — ingestão fácil em:
    - Loki / Grafana
    - Elasticsearch / OpenSearch
    - jq / DuckDB (análise offline)

Sem dependência externa. Integra com stdlib logging via handler customizado.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import os
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Formatter que emite JSON 1-linha."""

    CAMPOS_PADRAO = {
        "asctime", "created", "exc_info", "exc_text", "filename", "funcName",
        "levelname", "levelno", "lineno", "message", "module", "msecs",
        "name", "pathname", "process", "processName", "relativeCreated",
        "stack_info", "thread", "threadName", "args", "msg",
    }

    def __init__(self, extra_defaults: dict | None = None):
        super().__init__()
        self.extra_defaults = extra_defaults or {}

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": record.created,
            "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
                      + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)

        # Campos extras (passados via extra={})
        for k, v in record.__dict__.items():
            if k in self.CAMPOS_PADRAO or k.startswith("_"):
                continue
            try:
                json.dumps(v)   # garante serializável
                data[k] = v
            except (TypeError, ValueError):
                data[k] = repr(v)

        for k, v in self.extra_defaults.items():
            data.setdefault(k, v)

        return json.dumps(data, ensure_ascii=False)


def configurar(level: str = "INFO",
               extra_defaults: dict | None = None,
               stream=None) -> logging.Logger:
    """
    Configura root logger com StructuredFormatter. Retorna root.

    Uso:
        logger = configurar(level="DEBUG", extra_defaults={"service": "vila"})
        logger.info("step completado", extra={"step": 42, "estado": "expansao"})
    """
    stream = stream or sys.stdout
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredFormatter(extra_defaults or {}))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    return root


def configurar_arquivo(arquivo: str, level: str = "INFO",
                        extra_defaults: dict | None = None) -> logging.Logger:
    """Versão que escreve em arquivo JSONL."""
    os.makedirs(os.path.dirname(os.path.abspath(arquivo)) or ".", exist_ok=True)
    handler = logging.FileHandler(arquivo, encoding="utf-8")
    handler.setFormatter(StructuredFormatter(extra_defaults or {}))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    return root


def log_evento(logger: logging.Logger, tipo: str, **campos) -> None:
    """Helper: logger.info com tipo + campos."""
    logger.info(f"evento:{tipo}", extra={"tipo": tipo, **campos})
