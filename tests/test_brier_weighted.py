"""Testes Weighted Brier score com importance weights."""

from __future__ import annotations
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.brier_weighted import brier_weighted, auto_weight_by_uncertainty
from engine.post_cutoff_classifier import classify_and_predict

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_vazio():
    teste("empty → 0", brier_weighted([], [], []) == 0.0)


def t_unit_weights_eq_brier():
    """Pesos iguais → mesmo Brier não-ponderado."""
    preds = [0.6, 0.4, 0.7, 0.3]
    reals = [1, 0, 1, 0]
    weights = [1.0] * 4
    bw = brier_weighted(preds, reals, weights)
    bs = sum((p - r) ** 2 for p, r in zip(preds, reals)) / len(preds)
    teste(f"unit weights == Brier (got {bw:.4f} vs {bs:.4f})",
          abs(bw - bs) < 1e-9)


def t_peso_alto_amplifica():
    """Peso alto em evento errado → WBS sobe."""
    preds = [0.9, 0.5, 0.5]
    reals = [0, 1, 0]  # primeiro errado (0.81)
    bw_unif = brier_weighted(preds, reals, [1, 1, 1])
    bw_focused = brier_weighted(preds, reals, [10, 1, 1])
    teste(f"peso alto no errado: WBS sobe ({bw_unif:.3f} → {bw_focused:.3f})",
          bw_focused > bw_unif)


def t_peso_zero_ignora():
    """Peso zero ignora evento."""
    preds = [0.9, 0.5]
    reals = [0, 1]
    bw = brier_weighted(preds, reals, [0, 1])
    bs_only_2 = (0.5 - 1) ** 2  # apenas evento 2
    teste(f"peso 0 ignora (got {bw:.4f})", abs(bw - bs_only_2) < 1e-9)


def t_auto_weight_entropy_pico_05():
    """entropy max em p=0.5."""
    ws = auto_weight_by_uncertainty([0.5, 0.1, 0.9], weight_fn="entropy")
    teste("entropy 0.5 > 0.1", ws[0] > ws[1])
    teste("entropy 0.5 > 0.9", ws[0] > ws[2])


def t_auto_weight_variance():
    ws = auto_weight_by_uncertainty([0.5, 0.1], weight_fn="variance")
    teste(f"variance 0.5 ({ws[0]:.3f}) > variance 0.1 ({ws[1]:.3f})",
          ws[0] > ws[1])


def t_auto_weight_distance():
    ws = auto_weight_by_uncertainty([0.5, 0.0, 1.0], weight_fn="distance")
    teste("distance 0.5 = 1.0", abs(ws[0] - 1.0) < 1e-6)
    teste("distance 0.0 = 0.0", abs(ws[1]) < 1e-6)


def t_auto_weight_unknown():
    raised = False
    try:
        auto_weight_by_uncertainty([0.5], weight_fn="bogus")
    except ValueError:
        raised = True
    teste("unknown weight_fn raises", raised)


def t_real_bench_post_cutoff():
    """CSV n=40: WBS com auto_weight (entropy)."""
    csv_path = "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv"
    if not os.path.exists(csv_path):
        teste("CSV exists", False, csv_path)
        return
    preds, reals = [], []
    with open(csv_path) as f:
        r = csv.DictReader(f)
        for row in r:
            p, _ = classify_and_predict(row.get("outcome_framing", ""), row.get("contexto", ""))
            preds.append(p)
            reals.append(int(row["outcome_real"]))
    n = len(reals)
    teste(f"n=40 (got {n})", n == 40)
    ws_ent = auto_weight_by_uncertainty(preds, weight_fn="entropy")
    ws_var = auto_weight_by_uncertainty(preds, weight_fn="variance")
    teste(f"entropy weights size {len(ws_ent)}", len(ws_ent) == n)
    bw_ent = brier_weighted(preds, reals, ws_ent)
    bw_var = brier_weighted(preds, reals, ws_var)
    bs = sum((p - r) ** 2 for p, r in zip(preds, reals)) / n
    teste(f"WBS-entropy {bw_ent:.4f} >= 0", bw_ent >= 0)
    teste(f"WBS-variance {bw_var:.4f} >= 0", bw_var >= 0)
    teste(f"unweighted brier {bs:.4f}", bs >= 0)


def main():
    print("=== test_brier_weighted ===")
    for fn in [t_vazio, t_unit_weights_eq_brier, t_peso_alto_amplifica,
               t_peso_zero_ignora, t_auto_weight_entropy_pico_05,
               t_auto_weight_variance, t_auto_weight_distance,
               t_auto_weight_unknown, t_real_bench_post_cutoff]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
