"""
Cache LRU para respostas LLM (Onda 60).

Reduz chamadas API deduplicando prompts idênticos/similares.
TTL default 1h. Capacity default 500 entries.

Uso:
    from engine.ia_cache import cache_get, cache_put
    chave = cache_chave(system, user, modelo)
    hit = cache_get(chave)
    if hit is not None:
        return hit
    resp = chamar_llm(...)
    cache_put(chave, resp)
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class CacheEntry:
    valor: str
    timestamp: float
    hits: int = 0


class LRUCache:
    def __init__(self, capacity: int = 500, ttl_segundos: int = 3600):
        self.capacity = capacity
        self.ttl = ttl_segundos
        self._dados: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, chave: str) -> str | None:
        with self._lock:
            e = self._dados.get(chave)
            if e is None:
                self._misses += 1
                return None
            # TTL
            if time.time() - e.timestamp > self.ttl:
                del self._dados[chave]
                self._misses += 1
                return None
            # Move to end (LRU)
            self._dados.move_to_end(chave)
            e.hits += 1
            self._hits += 1
            return e.valor

    def put(self, chave: str, valor: str) -> None:
        with self._lock:
            if chave in self._dados:
                self._dados.move_to_end(chave)
                self._dados[chave].valor = valor
                self._dados[chave].timestamp = time.time()
                return
            self._dados[chave] = CacheEntry(valor=valor, timestamp=time.time())
            if len(self._dados) > self.capacity:
                self._dados.popitem(last=False)  # remove oldest

    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "capacity": self.capacity,
                "size": len(self._dados),
                "ttl_segundos": self.ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0.0,
            }

    def limpar(self) -> int:
        with self._lock:
            n = len(self._dados)
            self._dados.clear()
            self._hits = 0
            self._misses = 0
            return n


def cache_chave(system_prompt: str, user_prompt: str, modelo: str = "rapido") -> str:
    """SHA-256 dos 3 campos concatenados."""
    raw = f"{modelo}||{system_prompt}||{user_prompt}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


# Singleton global
CACHE_GLOBAL = LRUCache(
    capacity=int(os.getenv("VILA_LLM_CACHE_SIZE", "500")),
    ttl_segundos=int(os.getenv("VILA_LLM_CACHE_TTL", "3600")),
)
