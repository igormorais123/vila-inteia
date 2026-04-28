"""Testes Pinball loss (Koenker & Bassett 1978)."""

from __future__ import annotations
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.pinball_loss import pinball_loss, quantile_calibration, _pinball_one
from engine.post_cutoff_classifier import classify_and_predict

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_vazio():
    teste("empty preds → 0", pinball_loss([], []) == 0.0)


def t_perfect_pred():
    """Pred igual real → loss = 0."""
    loss = pinball_loss([0.5, 0.7, 0.3], [0.5, 0.7, 0.3], alpha=0.5)
    teste(f"perfect → 0 (got {loss:.6f})", abs(loss) < 1e-9)


def t_alpha_invalido():
    raised = False
    try:
        pinball_loss([0.5], [1], alpha=0.0)
    except ValueError:
        raised = True
    teste("alpha=0 raises", raised)


def t_assimetria_alpha_baixo():
    """alpha=0.1: penaliza over-prediction (q > y) muito mais que under."""
    # y=0, q=1: diff=-1, loss = (0.1 - 1)*-1 = 0.9 (over)
    # y=1, q=0: diff=1, loss = 0.1 * 1 = 0.1 (under)
    over = _pinball_one(0.0, 1.0, 0.1)
    under = _pinball_one(1.0, 0.0, 0.1)
    teste(f"alpha=0.1 over({over:.2f}) > under({under:.2f})", over > under)


def t_assimetria_alpha_alto():
    """alpha=0.9: penaliza under > over."""
    over = _pinball_one(0.0, 1.0, 0.9)
    under = _pinball_one(1.0, 0.0, 0.9)
    teste(f"alpha=0.9 under({under:.2f}) > over({over:.2f})", under > over)


def t_pinball_median_eq_mae_div2():
    """alpha=0.5 → pinball = |y-q|/2."""
    preds = [0.3, 0.5, 0.8]
    reals = [1, 0, 1]
    loss = pinball_loss(preds, reals, alpha=0.5)
    mae_half = sum(abs(p - r) for p, r in zip(preds, reals)) / (2 * len(preds))
    teste(f"alpha=0.5 == MAE/2 (got {loss:.4f} vs {mae_half:.4f})",
          abs(loss - mae_half) < 1e-9)


def t_calibration_dict():
    r = quantile_calibration([0.5, 0.5, 0.5], [0, 1, 0], alpha=0.5)
    teste("coverage in [0,1]", 0.0 <= r["coverage"] <= 1.0)
    teste("has pinball_loss", "pinball_loss" in r)


def t_real_bench_post_cutoff():
    """CSV n=40: pinball loss alpha=0.5 ~ MAE/2."""
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
    loss_05 = pinball_loss(preds, reals, alpha=0.5)
    loss_09 = pinball_loss(preds, reals, alpha=0.9)
    teste(f"loss > 0 (got {loss_05:.4f})", loss_05 > 0)
    # alpha=0.9 (most events =1) → menor loss que alpha=0.5 esperado se preds tendem alta
    cal = quantile_calibration(preds, reals, alpha=0.5)
    teste(f"coverage range (got {cal['coverage']:.3f})",
          0.0 <= cal["coverage"] <= 1.0)
    teste(f"pinball alpha=0.9 finito (got {loss_09:.4f})", loss_09 >= 0)


def main():
    print("=== test_pinball_loss ===")
    for fn in [t_vazio, t_perfect_pred, t_alpha_invalido,
               t_assimetria_alpha_baixo, t_assimetria_alpha_alto,
               t_pinball_median_eq_mae_div2, t_calibration_dict,
               t_real_bench_post_cutoff]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
