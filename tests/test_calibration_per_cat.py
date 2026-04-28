"""Per-category Platt calibration: fit + predict + integration with classifier.

Targets the Q4 v4 over-confidence (REL=0.131): per-cat sigmoid post EB+stretch
shrinks miscalibrated categories without flattening accurate ones.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.calibration import (
    fit_platt_per_category,
    platt_predict_per_category,
)
from engine.post_cutoff_classifier import (
    classify_and_predict,
    PLATT_PER_CATEGORY,
)
from engine.validation_rigorous import murphy_decomposition


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
                    "outcome_framing": r.get("outcome_framing") or r.get("framing", ""),
                    "contexto": r.get("contexto", ""),
                    "outcome_real": int(r["outcome_real"]),
                })
            except (ValueError, KeyError):
                pass
    return out


print("=== test_calibration_per_cat ===")

# ---------------------------------------------------------------------------
print("\n[1] fit_platt_per_category — separate fit per label")
# Two synthetic categories with different miscalibration profiles.
# 'over' classifier returns 0.95 but only 60% are real=1 → should shrink.
# 'under' classifier returns 0.20 but 70% are real=1 → should expand.
def two_cat_clf(framing, contexto=""):
    if "over" in framing:
        return 0.95, "over"
    if "under" in framing:
        return 0.20, "under"
    return 0.50, "default"


events = (
    [{"outcome_framing": "over A", "outcome_real": 1, "contexto": ""}] * 6 +
    [{"outcome_framing": "over B", "outcome_real": 0, "contexto": ""}] * 4 +
    [{"outcome_framing": "under A", "outcome_real": 1, "contexto": ""}] * 7 +
    [{"outcome_framing": "under B", "outcome_real": 0, "contexto": ""}] * 3
)
params = fit_platt_per_category(
    events, two_cat_clf, max_iter=500, lr=0.1, min_n=3
)
check("over" in params, f"over cat fit (got {list(params.keys())})")
check("under" in params, f"under cat fit (got {list(params.keys())})")

p_over = platt_predict_per_category(0.95, "over", params)
p_under = platt_predict_per_category(0.20, "under", params)
print(f"  over 0.95 → {p_over:.3f}, under 0.20 → {p_under:.3f}")
check(p_over < 0.95, f"over shrunk ({p_over:.3f} < 0.95)")
check(p_under > 0.20, f"under expanded ({p_under:.3f} > 0.20)")

# ---------------------------------------------------------------------------
print("\n[2] platt_predict_per_category — fallback for unknown label")
unknown = platt_predict_per_category(0.7, "ghost_label", params)
# default (1.0, 0.0) → sigmoid(0.7) ≈ 0.668
check(0.66 < unknown < 0.68, f"unknown label sigmoid identity ({unknown:.3f})")

# Also explicit default param
custom = platt_predict_per_category(0.5, "ghost", {}, default=(2.0, -1.0))
# sigmoid(2*0.5 - 1) = sigmoid(0) = 0.5
check(abs(custom - 0.5) < 1e-9, f"custom default applied ({custom:.4f})")

# ---------------------------------------------------------------------------
print("\n[3] min_n threshold — degenerate fallback for tiny categories")
sparse_events = (
    [{"outcome_framing": "over A", "outcome_real": 1, "contexto": ""}] * 1 +
    [{"outcome_framing": "under A", "outcome_real": 1, "contexto": ""}] * 5 +
    [{"outcome_framing": "under B", "outcome_real": 0, "contexto": ""}] * 5
)
sparse_params = fit_platt_per_category(
    sparse_events, two_cat_clf, max_iter=500, lr=0.1, min_n=3
)
# 'over' has only 1 event → degenerate
check(sparse_params.get("over") == (1.0, 0.0),
      f"over below min_n → identity ({sparse_params.get('over')})")
# 'under' has 10 events → fitted
check(sparse_params.get("under") != (1.0, 0.0),
      f"under above min_n → fit ({sparse_params.get('under')})")

# ---------------------------------------------------------------------------
print("\n[4] classify_and_predict — apply_platt_per_cat flag wired correctly")
# With flag off, must equal pre-existing behavior
p_off, lbl_off = classify_and_predict("Israel attack Iran", apply_platt_per_cat=False)
p_on, lbl_on = classify_and_predict("Israel attack Iran", apply_platt_per_cat=True)
check(lbl_off == lbl_on == "war_conflict", f"label stable ({lbl_off}/{lbl_on})")
# war_conflict has non-degenerate Platt → output should differ when flag on
# (war_conflict (1.30, 0.30) shrinks high p slightly; EB+stretch already 1.0)
ab = PLATT_PER_CATEGORY["war_conflict"]
check(ab != (1.0, 0.0), f"war_conflict has non-trivial params ({ab})")
# A degenerate category should be a no-op
p_deg_off, lbl_deg_off = classify_and_predict(
    "Trump removed in coup", apply_platt_per_cat=False
)
p_deg_on, lbl_deg_on = classify_and_predict(
    "Trump removed in coup", apply_platt_per_cat=True
)
check(lbl_deg_off == lbl_deg_on == "regime_change",
      f"regime_change label ({lbl_deg_off}/{lbl_deg_on})")
check(PLATT_PER_CATEGORY["regime_change"] == (1.0, 0.0),
      f"regime_change degenerate ({PLATT_PER_CATEGORY['regime_change']})")
check(p_deg_off == p_deg_on,
      f"degenerate category is no-op ({p_deg_off:.4f} vs {p_deg_on:.4f})")

# ---------------------------------------------------------------------------
print("\n[5] Q4 v4 holdout: per-cat Platt drops REL")
q4 = load_csv(
    "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q4_2026_holdout_v4.csv"
)
preds_off, preds_on, reals = [], [], []
for e in q4:
    p_off, _ = classify_and_predict(
        e["outcome_framing"], e["contexto"], apply_platt_per_cat=False
    )
    p_on, _ = classify_and_predict(
        e["outcome_framing"], e["contexto"], apply_platt_per_cat=True
    )
    preds_off.append(p_off)
    preds_on.append(p_on)
    reals.append(e["outcome_real"])
m_off = murphy_decomposition(preds_off, reals, n_bins=10)
m_on = murphy_decomposition(preds_on, reals, n_bins=10)
print(f"  BEFORE: brier={m_off['brier']:.4f} REL={m_off['reliability']:.4f}")
print(f"  AFTER:  brier={m_on['brier']:.4f} REL={m_on['reliability']:.4f}")
check(m_off["n"] == 30, f"Q4 v4 n=30 (got {m_off['n']})")
check(m_on["reliability"] < m_off["reliability"],
      f"REL drops ({m_on['reliability']:.4f} < {m_off['reliability']:.4f})")
check(m_on["brier"] < m_off["brier"],
      f"brier drops ({m_on['brier']:.4f} < {m_off['brier']:.4f})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
