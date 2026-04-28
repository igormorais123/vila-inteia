"""External prediction-market API integration: Manifold (public, no auth)
+ stubs for Polymarket / Kalshi / Metaculus (require auth or OAuth)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "external_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MANIFOLD_BASE = "https://api.manifold.markets/v0"
HEADERS = {"User-Agent": "vila-inteia-forecast-bench/1.0"}


def _http_get(url: str, timeout: int = 15) -> Any:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _cache_key(label: str, query: str) -> Path:
    safe = re.sub(r"[^a-z0-9_-]", "_", query.lower())[:80]
    return CACHE_DIR / f"{label}_{safe}.json"


def search_manifold(query: str, limit: int = 5,
                    use_cache: bool = True) -> list[dict]:
    """Search Manifold by query text. Returns top markets matching."""
    cache = _cache_key("manifold", query)
    if use_cache and cache.exists():
        return json.loads(cache.read_text())

    qs = urllib.parse.urlencode({"term": query, "limit": limit})
    url = f"{MANIFOLD_BASE}/search-markets?{qs}"
    try:
        data = _http_get(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        return [{"error": str(e), "query": query}]

    cache.write_text(json.dumps(data, indent=2))
    return data


def fetch_manifold_market(market_id: str) -> dict:
    """Fetch single Manifold market by id or slug."""
    cache = _cache_key("manifold_id", market_id)
    if cache.exists():
        return json.loads(cache.read_text())
    try:
        data = _http_get(f"{MANIFOLD_BASE}/market/{market_id}")
        cache.write_text(json.dumps(data, indent=2))
        return data
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        return {"error": str(e)}


def _shorten_query(framing: str, max_words: int = 6) -> str:
    """Strip leading question words + trailing 'Q1/Q2 ...?'; return key noun phrase."""
    s = framing.strip().rstrip("?").strip()
    s = re.sub(r"^(será que|será|vai|will|does|is|are|did|did the|did a)\s+", "",
               s, flags=re.IGNORECASE)
    s = re.sub(r"\s+(Q[1-4]\s*\d{4}|em\s+\d{4}).*$", "", s, flags=re.IGNORECASE)
    words = s.split()
    return " ".join(words[:max_words])


def manifold_prob_for_event(framing: str) -> tuple[float | None, dict | None]:
    """Find best Manifold market matching framing, return its probability.
    Tries shortened query first (better matching), then full text."""
    queries = [_shorten_query(framing), framing]
    for q in queries:
        if not q:
            continue
        results = search_manifold(q, limit=5)
        if not results or "error" in results[0]:
            continue
        for m in results:
            if m.get("outcomeType") == "BINARY" and "probability" in m:
                return float(m["probability"]), m
    return None, None


def fetch_polymarket_event(query: str) -> dict:
    """Polymarket integration. Gamma-api blocked from many envs;
    requires OAuth via wallet for full data. Stub returns error.
    For production: integrate via official Polymarket SDK."""
    return {
        "error": "polymarket_requires_wallet_oauth",
        "query": query,
        "note": "Use https://github.com/Polymarket/polymarket-clob-client with WALLET_PK env",
    }


def fetch_kalshi_event(query: str) -> dict:
    """Kalshi integration. Requires login + OAuth."""
    return {
        "error": "kalshi_requires_login",
        "query": query,
        "note": "Set KALSHI_EMAIL + KALSHI_PASSWORD env, use kalshi-python SDK",
    }


def fetch_metaculus_question(query: str, token: str | None = None) -> dict:
    """Metaculus public API requires authenticated token."""
    if not token:
        import os
        token = os.environ.get("METACULUS_TOKEN")
    if not token:
        return {
            "error": "metaculus_requires_token",
            "query": query,
            "note": "Set METACULUS_TOKEN env from https://www.metaculus.com/aggregations/",
        }
    qs = urllib.parse.urlencode({"search": query, "limit": 5})
    url = f"https://www.metaculus.com/api2/questions/?{qs}"
    req = urllib.request.Request(url, headers={
        **HEADERS,
        "Authorization": f"Token {token}",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        return {"error": str(e)}


def compare_to_manifold(events: list, classify_fn, max_events: int = 10) -> dict:
    """Match events to Manifold markets, compare Vila vs Manifold brier."""
    matched = []
    for e in events[:max_events]:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        p_vila, _ = classify_fn(framing, contexto)
        p_manifold, market = manifold_prob_for_event(framing)
        if p_manifold is None:
            continue
        matched.append({
            "framing": framing[:80],
            "p_vila": p_vila,
            "p_manifold": p_manifold,
            "y": y,
            "market_url": market.get("url", ""),
        })

    n = len(matched)
    if not n:
        return {"n": 0, "error": "no_matches"}

    brier_vila = sum((m["p_vila"] - m["y"]) ** 2 for m in matched) / n
    brier_manifold = sum((m["p_manifold"] - m["y"]) ** 2 for m in matched) / n
    return {
        "n": n,
        "brier_vila": brier_vila,
        "brier_manifold": brier_manifold,
        "delta": brier_vila - brier_manifold,
        "vila_better": brier_vila < brier_manifold,
        "matched": matched,
    }
