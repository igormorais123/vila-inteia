"""
Middleware de autenticação + rate limit (Onda 46).

Auth: header X-API-Token validado contra env VILA_API_TOKEN (se definido).
Se VILA_API_TOKEN vazio → auth desabilitada (dev mode).

Rate limit: token bucket por IP, janela deslizante 1 min.
"""

from __future__ import annotations

import os
import time
import threading
from collections import defaultdict, deque


VILA_API_TOKEN = os.getenv("VILA_API_TOKEN", "")
VILA_RATE_LIMIT_PER_MIN = int(os.getenv("VILA_RATE_LIMIT_PER_MIN", "120"))
VILA_AUTH_EXCLUDE_PATHS = {"/docs", "/openapi.json", "/redoc", "/api/v1/vila/health", "/metrics"}


class RateLimiter:
    """Janela deslizante por IP."""

    def __init__(self, limite_por_min: int = 120):
        self.limite = limite_por_min
        self.requests: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def permitir(self, ip: str) -> tuple[bool, int]:
        """Retorna (ok, n_restantes). Remove timestamps > 60s."""
        agora = time.time()
        with self._lock:
            fila = self.requests[ip]
            while fila and fila[0] < agora - 60:
                fila.popleft()
            if len(fila) >= self.limite:
                return False, 0
            fila.append(agora)
            return True, self.limite - len(fila)


RATE_LIMITER_GLOBAL = RateLimiter(VILA_RATE_LIMIT_PER_MIN)


async def middleware_auth_rate(request, call_next):
    """Middleware FastAPI aplicado em serve/live."""
    from fastapi.responses import JSONResponse

    path = request.url.path
    # Excluir static + docs + health
    if any(path.startswith(p) for p in VILA_AUTH_EXCLUDE_PATHS):
        return await call_next(request)
    if not path.startswith("/api/"):
        return await call_next(request)

    # Rate limit
    ip = request.client.host if request.client else "desconhecido"
    ok, restantes = RATE_LIMITER_GLOBAL.permitir(ip)
    if not ok:
        return JSONResponse(
            {"erro": "rate limit excedido", "limite_por_min": VILA_RATE_LIMIT_PER_MIN},
            status_code=429,
            headers={"Retry-After": "60"},
        )

    # Auth (só se token configurado)
    if VILA_API_TOKEN:
        token = request.headers.get("X-API-Token", "")
        if token != VILA_API_TOKEN:
            return JSONResponse(
                {"erro": "token inválido ou ausente"},
                status_code=401,
            )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(restantes)
    response.headers["X-RateLimit-Limit"] = str(VILA_RATE_LIMIT_PER_MIN)
    return response


def auth_ativa() -> bool:
    return bool(VILA_API_TOKEN)


def config_resumo() -> dict:
    return {
        "auth_ativa": auth_ativa(),
        "rate_limit_per_min": VILA_RATE_LIMIT_PER_MIN,
        "paths_excluidos": sorted(VILA_AUTH_EXCLUDE_PATHS),
    }
