"""
Onda 103: auth token + rate limit simples.

Auth:
  VILA_API_KEYS env: CSV de tokens válidos. Vazio = auth disabled.
  Endpoints custosos verificam header X-API-Key.

Rate limit:
  Sliding window per-IP. VILA_RATE_LIMIT_RPM default 30 (por minuto).
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Optional

from fastapi import Request, HTTPException


def _keys_validas() -> set[str]:
    raw = os.getenv("VILA_API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


def auth_required(request: Request) -> None:
    """Raise 401 se header X-API-Key inválido. No-op se keys env vazio."""
    keys = _keys_validas()
    if not keys:
        return  # auth disabled
    key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
    if not key:
        raise HTTPException(401, "X-API-Key header required")
    if key not in keys:
        raise HTTPException(401, "X-API-Key invalid")


_HISTORY: dict[str, deque] = defaultdict(deque)
_LOCK = Lock()


def rate_limit(
    request: Request,
    rpm: Optional[int] = None,
) -> None:
    """Sliding window per-IP. Raise 429 se excedeu."""
    if rpm is None:
        rpm = int(os.getenv("VILA_RATE_LIMIT_RPM", "30"))
    if rpm <= 0:
        return
    ip = request.client.host if request.client else "unknown"
    agora = time.monotonic()
    limite = agora - 60.0
    with _LOCK:
        dq = _HISTORY[ip]
        while dq and dq[0] < limite:
            dq.popleft()
        if len(dq) >= rpm:
            raise HTTPException(
                429,
                f"rate limit {rpm}/min excedido (retry in {int(dq[0]+60-agora)+1}s)",
            )
        dq.append(agora)


def auth_e_rate(request: Request) -> None:
    """Combina auth + rate limit. Use via Depends()."""
    auth_required(request)
    rate_limit(request)
