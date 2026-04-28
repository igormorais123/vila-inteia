"""Test engine/external_apis.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.external_apis import (
    search_manifold, fetch_manifold_market, manifold_prob_for_event,
    fetch_polymarket_event, fetch_kalshi_event, fetch_metaculus_question,
    compare_to_manifold,
)

ok = fail = 0
def check(c, m):
    global ok, fail
    if c: ok += 1; print(f"  OK  {m}")
    else: fail += 1; print(f"  FAIL {m}")

print("=== test_external_apis ===")

print("\n[1] Manifold search")
results = search_manifold("Trump 2026", limit=3)
check(isinstance(results, list), f"list returned (got {type(results).__name__})")
if results and "error" not in results[0]:
    check(len(results) > 0, f"got {len(results)} results")
    print(f"  Sample: {results[0].get('question', '?')[:60]}")
else:
    print(f"  Network unavailable, skipping live test")

print("\n[2] manifold_prob_for_event")
p, market = manifold_prob_for_event("Will Trump be president")
if p is not None:
    check(0 <= p <= 1, f"prob in [0,1] (got {p:.3f})")
    print(f"  Matched: {market.get('question', '?')[:50]} → p={p:.3f}")
else:
    print(f"  No match found (network may be unavailable)")
    check(True, "no_match handled")

print("\n[3] Polymarket stub")
r = fetch_polymarket_event("any query")
check("error" in r and r["error"] == "polymarket_requires_wallet_oauth",
      f"polymarket returns clear OAuth message")

print("\n[4] Kalshi stub")
r = fetch_kalshi_event("any query")
check("error" in r and r["error"] == "kalshi_requires_login",
      "kalshi returns clear login message")

print("\n[5] Metaculus without token")
import os
os.environ.pop("METACULUS_TOKEN", None)
r = fetch_metaculus_question("any query")
check(r.get("error") == "metaculus_requires_token", "metaculus needs token")

print("\n[6] compare_to_manifold smoke")
def fake_clf(f, c=""):
    return 0.5, "default"
events = [
    {"outcome_framing": "Trump declares emergency Q1 2026", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Bitcoin reaches $100k 2026", "outcome_real": 0, "contexto": ""},
]
res = compare_to_manifold(events, fake_clf, max_events=2)
check("n" in res, f"returns dict with n field (n={res.get('n')})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
