"""Multi-tenant API key auth + rate limit for political prediction product.

In-memory client registry (loaded from data/clients.json) with per-client tier:
  - free:   30 req/min, 500/day, public endpoints only
  - pro:    300 req/min, 50000/day, all endpoints
  - enterprise: unlimited, custom contract

Production: replace _CLIENT_DB with Supabase vila_clients lookup.
"""
from __future__ import annotations

import json
import os
import time
import secrets
from collections import deque, defaultdict
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
CLIENTS_PATH = ROOT / "data" / "clients.json"

_TIER_LIMITS = {
    "free":       {"per_min": 30,    "per_day": 500},
    "pro":        {"per_min": 300,   "per_day": 50000},
    "enterprise": {"per_min": 100000, "per_day": 100000000},
}


class RateLimitExceeded(Exception):
    def __init__(self, scope: str, limit: int, retry_after: int):
        self.scope = scope
        self.limit = limit
        self.retry_after = retry_after
        super().__init__(f"rate limit {scope} exceeded ({limit})")


class ClientRegistry:
    """In-memory; thread-safe enough for single-process Render deploy."""

    def __init__(self):
        self._db: dict[str, dict] = {}
        self._req_log: dict[str, deque] = defaultdict(deque)
        self._reload()

    def _reload(self):
        if CLIENTS_PATH.exists():
            try:
                self._db = json.loads(CLIENTS_PATH.read_text())
            except Exception:
                self._db = {}
        else:
            self._db = {}

    def lookup(self, api_key: Optional[str]) -> Optional[dict]:
        if not api_key:
            return None
        return self._db.get(api_key)

    def issue(self, name: str, tier: str = "free", contact: str = "") -> str:
        key = "vila_pol_" + secrets.token_urlsafe(24)
        self._db[key] = {"name": name, "tier": tier, "contact": contact,
                         "created_at": time.time(), "active": True}
        CLIENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        CLIENTS_PATH.write_text(json.dumps(self._db, indent=2))
        return key

    def revoke(self, api_key: str):
        if api_key in self._db:
            self._db[api_key]["active"] = False
            CLIENTS_PATH.write_text(json.dumps(self._db, indent=2))

    def check_rate(self, api_key: str, tier: str):
        now = time.time()
        log = self._req_log[api_key]
        # purge entries older than 1 day
        cutoff_day = now - 86400
        while log and log[0] < cutoff_day:
            log.popleft()
        # count last minute
        cutoff_min = now - 60
        last_min = sum(1 for t in log if t >= cutoff_min)
        last_day = len(log)
        limits = _TIER_LIMITS.get(tier, _TIER_LIMITS["free"])
        if last_min >= limits["per_min"]:
            raise RateLimitExceeded("per_min", limits["per_min"], 60)
        if last_day >= limits["per_day"]:
            raise RateLimitExceeded("per_day", limits["per_day"], 86400)
        log.append(now)


_REGISTRY: Optional[ClientRegistry] = None


def get_registry() -> ClientRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ClientRegistry()
    return _REGISTRY


def authenticate(api_key: Optional[str], require_pro: bool = False) -> dict:
    """Return client dict, or `anonymous` for missing keys.
    Raises HTTPException 401 on invalid key, 402 on insufficient tier,
    429 on rate limit exceeded.
    """
    from fastapi import HTTPException
    reg = get_registry()
    if api_key is None:
        if require_pro:
            raise HTTPException(401, "API key required for this endpoint")
        return {"name": "anonymous", "tier": "free", "active": True}
    client = reg.lookup(api_key)
    if not client:
        raise HTTPException(401, "invalid API key")
    if not client.get("active", True):
        raise HTTPException(401, "API key revoked")
    if require_pro and client["tier"] == "free":
        raise HTTPException(402, f"endpoint requires pro tier (current: {client['tier']})")
    try:
        reg.check_rate(api_key, client["tier"])
    except RateLimitExceeded as e:
        raise HTTPException(429, str(e), headers={"Retry-After": str(e.retry_after)})
    return client
