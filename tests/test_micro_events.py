"""Onda 233: testa engine/micro_events.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.micro_events import (
    BASE_RATES, MicroEvent,
    gerar_dataset_stock_prices, gerar_dataset_cripto_prices,
    avaliar_predictor_honesto, gerar_500_micro_events_q1_2026,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_micro_events ===")

print("\n[1] BASE_RATES tem categorias esperadas")
expected_cats = ["stock_price_up", "crypto_price_up", "sports_favorite_wins",
                 "election_incumbent_wins", "geopolitical_escalation_extreme",
                 "tech_release_on_time", "default"]
for cat in expected_cats:
    check(cat in BASE_RATES, f"{cat} in BASE_RATES")

# Markets ~50/50
check(BASE_RATES["stock_price_up"] == 0.50, "stock_price_up = 0.50")
check(BASE_RATES["crypto_price_up"] == 0.50, "crypto_price_up = 0.50")

print("\n[2] MicroEvent.predict() = base rate da categoria")
ev = MicroEvent(event_id="test", category="stock_price_up", framing="X up?", date="2026-01-15")
check(ev.predict() == 0.50, "stock predict = 0.50")

ev2 = MicroEvent(event_id="test2", category="sports_favorite_wins", framing="?", date="2026-02-01")
check(ev2.predict() == 0.65, "sports favorite = 0.65")

ev_unknown = MicroEvent(event_id="x", category="unknown_cat", framing="?", date="2026-01-01")
check(ev_unknown.predict() == 0.50, "unknown cat = default 0.50")

print("\n[3] gerar_dataset_stock_prices gera N tickers × dates")
events = gerar_dataset_stock_prices(["AAPL", "MSFT"], ["2026-01-15", "2026-02-15"])
check(len(events) == 4, f"2 tickers × 2 dates = 4 events (got {len(events)})")
check(events[0].category == "stock_price_up", "first event is stock_price_up")

print("\n[4] gerar_dataset_cripto_prices")
crypto_events = gerar_dataset_cripto_prices(["BTC", "ETH"], ["2026-01-15"])
check(len(crypto_events) == 2, "2 coins × 1 date = 2 events")
check(crypto_events[0].category == "crypto_price_up", "crypto category")

print("\n[5] avaliar_predictor_honesto com mix resolved/unresolved")
ev1 = MicroEvent(event_id="a", category="stock_price_up", framing="?", date="2026-01-15", real_outcome=1)
ev2 = MicroEvent(event_id="b", category="stock_price_up", framing="?", date="2026-01-15", real_outcome=0)
ev3 = MicroEvent(event_id="c", category="stock_price_up", framing="?", date="2026-01-15")  # unresolved
res = avaliar_predictor_honesto([ev1, ev2, ev3])
check(res["n"] == 3 and res["n_resolved"] == 2, "3 total, 2 resolved")
# stock_price_up = 0.50 → cls=1 (>= 0.5). ev1=1 hit, ev2=0 miss
check(res["hits"] == 1, f"1 hit (got {res['hits']})")
check(abs(res["brier"] - 0.25) < 0.01, f"brier = 0.25 (got {res['brier']:.3f})")

print("\n[6] avaliar com nenhum resolved")
res_empty = avaliar_predictor_honesto([
    MicroEvent(event_id="x", category="stock_price_up", framing="?", date="2026-01-01"),
])
check(res_empty["n_resolved"] == 0, "0 resolved")

print("\n[7] gerar_500_micro_events_q1_2026")
events_500 = gerar_500_micro_events_q1_2026()
check(len(events_500) >= 400, f"~500 events (got {len(events_500)})")

# Categorias presentes
cats_present = {e.category for e in events_500}
check("stock_price_up" in cats_present, "stocks gerados")
check("crypto_price_up" in cats_present, "criptos gerados")
check("sports_favorite_wins" in cats_present, "sports gerados")
check("election_incumbent_wins" in cats_present or "poll_lead_holds" in cats_present, "elections gerados")

# Todos têm real_outcome=None (não resolved)
check(all(e.real_outcome is None for e in events_500), "todos unresolved (precisam ground truth)")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
