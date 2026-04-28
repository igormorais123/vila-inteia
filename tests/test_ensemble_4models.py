"""Test engine/ensemble_4models.py — 4-model AdaHedge ensemble."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.ensemble_4models import (
    BASE_RATE,
    MODELS,
    evaluate_ensemble_4,
    model_base_rate,
    model_lindy,
    model_market_implied,
    model_vila,
)


ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {msg}")
    else:
        fail += 1
        print(f"  FAIL {msg}")


def load_csv(fp):
    out = []
    with open(fp) as f:
        for r in csv.DictReader(f):
            try:
                out.append({
                    "outcome_framing": r.get("outcome_framing")
                        or r.get("framing", ""),
                    "contexto": r.get("contexto", ""),
                    "outcome_real": int(r["outcome_real"]),
                    "probabilidade_prior": float(r["probabilidade_prior"])
                        if r.get("probabilidade_prior") not in (None, "") else None,
                })
            except (ValueError, KeyError):
                pass
    return out


print("=== test_ensemble_4models ===")

print("\n[1] Individual model contracts")
p = model_vila("Bitcoin atingirá $110k+ Q1 2026?", "BTC bear market")
check(0.0 <= p <= 1.0, f"vila in [0,1] (={p:.3f})")
p = model_base_rate("foo", "bar")
check(p == BASE_RATE, f"base_rate == 0.68 (={p})")
p = model_lindy("Davos WEF 2026", "Davos summit jan 2026")
check(p is not None and 0.0 < p < 1.0,
      f"lindy hits known event (={p:.4f})")
p = model_lindy("random no-match event", "irrelevant ctx")
check(p == BASE_RATE,
      f"lindy fallback=base_rate when None (={p})")
p = model_market_implied("foo", "bar", prior_field=0.42)
check(p == 0.42, f"market_implied passes prior (={p})")
p = model_market_implied("foo", "bar", prior_field=None)
check(p == BASE_RATE, f"market_implied None fallback (={p})")
p = model_market_implied("foo", "bar", prior_field=1.5)
check(p == 1.0, f"market_implied clipped to [0,1] (={p})")

print("\n[2] MODELS dict has 5 entries")
check(len(MODELS) == 5, f"5 models (got {len(MODELS)})")
check(set(MODELS.keys()) == {"vila", "base_rate", "lindy", "market", "tfidf"},
      "model names match")

print("\n[3] evaluate_ensemble_4 — synthetic")
synth = [
    {"outcome_framing": "Bitcoin $200k", "contexto": "btc",
     "outcome_real": 0, "probabilidade_prior": 0.10},
    {"outcome_framing": "Davos WEF 2026 realizado", "contexto": "summit",
     "outcome_real": 1, "probabilidade_prior": 0.95},
    {"outcome_framing": "Olympics 2026 held",
     "contexto": "winter olympics 2026",
     "outcome_real": 1, "probabilidade_prior": 0.92},
    {"outcome_framing": "MWC Mobile World Congress 2026 realizado",
     "contexto": "mwc barcelona",
     "outcome_real": 1, "probabilidade_prior": 0.95},
] * 3
res = evaluate_ensemble_4(synth)
print(f"  n={res['n']} brier={res['brier']:.4f} acc={res['acc']:.1%}")
print(f"  per-model brier: {res['per_model_brier']}")
print(f"  best={res['best_model']} regret={res['regret']:+.4f}")
check(res["n"] == 12, f"n=12 (got {res['n']})")
check(0.0 <= res["brier"] <= 1.0, "ensemble brier in valid range")
check(set(res["per_model_brier"].keys()) == set(MODELS),
      "all 4 models in per_model_brier")
check(abs(sum(res["final_weights"].values()) - 1.0) < 1e-6,
      "final weights sum to 1")

print("\n[4] Online property — weights NOT uniform after many events")
agg_res = evaluate_ensemble_4(synth * 5)
ws = agg_res["final_weights"]
print(f"  weights={ws}")
max_w = max(ws.values())
min_w = min(ws.values())
check(max_w - min_w > 0.01,
      f"weights diverged from uniform (spread={max_w - min_w:.3f})")

print("\n[5] Bench Q1 train + 5 holdouts (n~150)")
train_files = ["post_cutoff_q1_2026", "post_cutoff_q1_2026_v2"]
holdout_files = [
    "post_cutoff_q2_2026_holdout",
    "post_cutoff_q2_2026_holdout_v2",
    "post_cutoff_q3_2026_holdout_v3",
    "post_cutoff_q4_2026_holdout_v4",
    "post_cutoff_q1_2027_holdout_v5",
]
events = []
for fn in train_files + holdout_files:
    events += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")

print(f"  loaded {len(events)} events ({sum(1 for e in events if e['outcome_real'] == 1)} pos)")
res = evaluate_ensemble_4(events)
print(f"  n={res['n']} ensemble_brier={res['brier']:.4f} acc={res['acc']:.1%}")
print(f"  per-model brier:")
for name, b in sorted(res["per_model_brier"].items(), key=lambda x: x[1]):
    print(f"    {name:<11} brier={b:.4f}  acc={res['per_model_acc'][name]:.1%}")
print(f"  best_model={res['best_model']}  best_brier={res['best_model_brier']:.4f}")
print(f"  regret = {res['brier']:.4f} - {res['best_model_brier']:.4f}"
      f" = {res['regret']:+.4f}")
print(f"  final_weights:")
for n_, w_ in sorted(res["final_weights"].items(), key=lambda x: -x[1]):
    print(f"    {n_:<11} w={w_:.4f}")
print(f"  final_eta={res['final_eta']:.3f}")

check(res["n"] >= 140, f">=140 events (got {res['n']})")
check(res["brier"] <= max(res["per_model_brier"].values()) + 0.01,
      "ensemble brier ≤ worst individual")
check(set(res["final_weights"]) == set(MODELS), "all 4 models weighted")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
