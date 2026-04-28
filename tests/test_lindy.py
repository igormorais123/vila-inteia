"""Onda 256: testa engine/lindy.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.lindy import (
    lindy_probability, parse_year_from_context, lindy_for_event,
    KNOWN_LINDY_EVENTS,
)

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_lindy ===")

print("\n[1] lindy_probability — older = more likely to continue")
p_young = lindy_probability(1, 1)
p_old = lindy_probability(100, 1)
check(p_old > p_young, f"100yr ({p_old:.3f}) > 1yr ({p_young:.3f})")
check(p_young == 0.5, f"1yr horizon=1 → 0.5 (got {p_young})")
check(abs(p_old - 100/101) < 1e-9, f"100yr ≈ 0.990 (got {p_old:.3f})")

# Edge cases
check(lindy_probability(0, 1) == 0.5, "age=0 → 0.5 default")
check(lindy_probability(50, 0.5) == 50/50.5, "horizon=0.5")

print("\n[2] parse_year_from_context")
check(parse_year_from_context("Olympics realized in 1896") == 1896, "1896")
check(parse_year_from_context("modern era 2026") == 2026, "2026")
check(parse_year_from_context("WW2 ended 1945 then 1950") == 1945, "first match")
check(parse_year_from_context("no year here") is None, "None when missing")

print("\n[3] KNOWN_LINDY_EVENTS coverage")
check(len(KNOWN_LINDY_EVENTS) >= 15, f"≥ 15 events (got {len(KNOWN_LINDY_EVENTS)})")
check(all(1800 < y < 2030 for y in KNOWN_LINDY_EVENTS.values()),
      "all years sane")

print("\n[4] lindy_for_event")
# Olympics 1896 → 130 years → ~0.992
p = lindy_for_event("Winter Olympics Milan-Cortina 2026", current_year=2026)
check(p is not None and p > 0.98,
      f"Olympics very likely ({p})")

# MWC Barcelona 2006 → 20 years → ~0.952
p = lindy_for_event("MWC Barcelona 2026 mar", current_year=2026)
check(p is not None and 0.93 < p < 0.97, f"MWC ~0.95 ({p})")

# Unknown event
p = lindy_for_event("Some random new product launch")
check(p is None, f"unknown returns None (got {p})")

# Match in contexto not framing
p = lindy_for_event("event Q1 2026", contexto="annual wrestlemania since 1985",
                    current_year=2026)
check(p is not None, f"matches contexto ({p})")

print("\n[5] Lindy boost on real scheduled events")
# Compare Lindy vs hardcoded 0.92 for scheduled_event category
sys.path.insert(0, "/home/pedroafonso/vila-inteia")
from engine.post_cutoff_classifier import classify_and_predict
import csv

events = []
for fn in ["sports_specific_q1_2026.csv", "tech_releases_q1_2026.csv"]:
    fp = Path("/home/pedroafonso/vila-inteia/data/backtest") / fn
    with open(fp) as f:
        for r in csv.DictReader(f):
            try:
                events.append({
                    "framing": r.get("outcome_framing", ""),
                    "contexto": r.get("contexto", ""),
                    "real": int(r["outcome_real"]),
                })
            except (ValueError, KeyError):
                pass

# Apply Lindy where applicable
hits_base = hits_lindy = 0
brier_base = brier_lindy = 0.0
n_lindy = 0
for e in events:
    p_base, lbl = classify_and_predict(e["framing"], e["contexto"])
    p_lindy_val = lindy_for_event(e["framing"], e["contexto"])
    p_use = p_lindy_val if (p_lindy_val is not None and lbl == "scheduled_event") else p_base
    if p_lindy_val is not None and lbl == "scheduled_event":
        n_lindy += 1
    if (p_base >= 0.5) == bool(e["real"]):
        hits_base += 1
    if (p_use >= 0.5) == bool(e["real"]):
        hits_lindy += 1
    brier_base += (p_base - e["real"]) ** 2
    brier_lindy += (p_use - e["real"]) ** 2

n = len(events)
print(f"  n={n}, lindy applied={n_lindy}")
print(f"  Baseline: acc={hits_base/n:.1%} brier={brier_base/n:.3f}")
print(f"  Lindy:    acc={hits_lindy/n:.1%} brier={brier_lindy/n:.3f}")
check(n_lindy > 0, "Lindy applied to some events")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
