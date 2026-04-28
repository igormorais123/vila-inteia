"""
Onda 251: Data preview + inspector.

Tools pra inspecionar:
- Datasets (events count per file, outcomes distribution)
- Cache (size, recent prices)
- Strategies coverage (tested vs untested)
- Held-out separation Q1 vs Q2 2026

CLI: python engine/data_preview.py
"""

from __future__ import annotations

import glob
import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def preview_datasets() -> dict:
    """Lista todos datasets backtest com stats."""
    out = []
    for fp in sorted(glob.glob(str(REPO / "data" / "backtest" / "*.csv"))):
        name = Path(fp).stem
        try:
            from engine.backtest_real import carregar_dataset
            events = carregar_dataset(fp)
            outcomes = [e["outcome_real"] for e in events if "outcome_real" in e]
            yes_rate = sum(outcomes) / len(outcomes) if outcomes else 0
            out.append({
                "dataset": name,
                "n_events": len(events),
                "yes_rate": yes_rate,
                "yes_count": sum(outcomes),
                "no_count": len(outcomes) - sum(outcomes),
                "type": _classify_dataset(name),
            })
        except Exception as e:
            out.append({"dataset": name, "error": str(e)})
    return {"datasets": out, "n_total": sum(d.get("n_events", 0) for d in out)}


def _classify_dataset(name: str) -> str:
    """Classify by naming convention."""
    if name.startswith("post_cutoff_q1"):
        return "post_cutoff_q1"
    if name.startswith("post_cutoff_q2"):
        return "post_cutoff_q2_holdout"
    return "pre_cutoff_historical"


def preview_cache() -> dict:
    """Inspect market_cache.json."""
    cache_path = REPO / "data" / "market_cache.json"
    if not cache_path.exists():
        return {"exists": False}
    cache = json.loads(cache_path.read_text())
    syms = Counter()
    dates = Counter()
    for k in cache:
        if ":" not in k:
            continue
        sym, date = k.split(":", 1)
        syms[sym] += 1
        dates[date[:7]] += 1  # YYYY-MM
    return {
        "exists": True,
        "n_entries": len(cache),
        "n_symbols": len(syms),
        "top_symbols": syms.most_common(5),
        "month_distribution": dict(sorted(dates.items())),
    }


def preview_strategies() -> dict:
    """Lista strategies disponíveis."""
    strategies = {
        "factor_models": ["baseline", "momentum", "mean_reversion", "rsi", "ensemble"],
        "advanced_factors": ["hurst_regime", "vol_adj_momentum", "kelly_calibrated", "bayesian_multi"],
        "exotic_factors": ["bollinger", "ichimoku", "stochastic", "macd"],
        "post_cutoff": ["text_classifier"],
        "ensemble_methods": ["weighted", "simple_avg", "majority_vote"],
        "forecasting_real": ["s1_baseline", "s2_shrink_50", "s3_base_rate_30",
                             "s4_invert_tail", "s5_conservative", "s6_ensemble"],
    }
    return {
        "modules": strategies,
        "total": sum(len(v) for v in strategies.values()),
    }


def preview_holdout_split() -> dict:
    """Held-out split: Q1 train, Q2 holdout."""
    train = []
    holdout = []
    for fp in sorted(glob.glob(str(REPO / "data" / "backtest" / "post_cutoff*.csv"))):
        name = Path(fp).stem
        try:
            from engine.backtest_real import carregar_dataset
            events = carregar_dataset(fp)
            n = len(events)
            if "q2" in name or "holdout" in name:
                holdout.append({"file": name, "n": n})
            else:
                train.append({"file": name, "n": n})
        except Exception:
            pass
    return {
        "train_q1": {"files": train, "n_total": sum(t["n"] for t in train)},
        "holdout_q2": {"files": holdout, "n_total": sum(h["n"] for h in holdout)},
    }


def preview_all() -> dict:
    """Completo: datasets + cache + strategies + split."""
    return {
        "datasets": preview_datasets(),
        "cache": preview_cache(),
        "strategies": preview_strategies(),
        "holdout_split": preview_holdout_split(),
    }


if __name__ == "__main__":
    import json as j
    out = preview_all()
    print(j.dumps(out, indent=2, default=str))
