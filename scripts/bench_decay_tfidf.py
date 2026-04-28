"""Bench: time-decay impact on Vila brier + TF-IDF vs Vila on n=80 holdout."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.post_cutoff_classifier import classify_and_predict
from engine.tfidf_neighbors import build_tfidf_index, evaluate_tfidf


TRAIN = [
    "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q1_2026.csv",
    "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q1_2026_v2.csv",
]
HOLDOUT = [
    "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout.csv",
    "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q2_2026_holdout_v2.csv",
    "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q3_2026_holdout_v3.csv",
    "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q4_2026_holdout_v4.csv",
    "/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q1_2027_holdout_v5.csv",
]


def load(fp):
    out = []
    with open(fp) as f:
        for r in csv.DictReader(f):
            try:
                out.append({
                    "outcome_framing": r.get("outcome_framing")
                        or r.get("framing", ""),
                    "contexto": r.get("contexto", ""),
                    "data": r.get("data", ""),
                    "outcome_real": int(r["outcome_real"]),
                })
            except (ValueError, KeyError):
                pass
    return out


def vila_brier(events, *, decay=False, half_life=180, ref="2026-04-28"):
    n = hits = 0
    bs = 0.0
    for e in events:
        y = e["outcome_real"]
        ed = e.get("data") or None
        p, _ = classify_and_predict(
            e["outcome_framing"], e["contexto"],
            apply_time_decay=decay,
            event_date=ed,
            reference_date=ref,
            half_life=half_life,
        )
        n += 1
        if (p >= 0.5) == bool(y):
            hits += 1
        bs += (p - y) ** 2
    return {"n": n, "brier": bs / n, "acc": hits / n}


def main():
    train = []
    for fp in TRAIN:
        train += load(fp)
    holdout = []
    for fp in HOLDOUT:
        holdout += load(fp)
    holdout = holdout[:80]
    print(f"TRAIN n={len(train)}  HOLDOUT n={len(holdout)}")

    print("\n[A] Time-decay impact on Vila brier (holdout n=80, ref=2026-04-28)")
    base = vila_brier(holdout, decay=False)
    print(f"  Vila no-decay  : brier={base['brier']:.4f}  acc={base['acc']:.1%}")
    for hl in (90, 180, 365, 720):
        r = vila_brier(holdout, decay=True, half_life=hl)
        delta = r["brier"] - base["brier"]
        print(f"  Vila decay h={hl:<4}: brier={r['brier']:.4f} "
              f"acc={r['acc']:.1%}  delta={delta:+.4f}")

    print("\n[B] TF-IDF vs Vila brier on holdout n=80")
    idx = build_tfidf_index(train)
    tfidf_res = evaluate_tfidf(holdout, idx, k=5)
    print(f"  TF-IDF k=5 : brier={tfidf_res['brier']:.4f} "
          f"acc={tfidf_res['acc']:.1%}")
    print(f"  Vila       : brier={base['brier']:.4f} "
          f"acc={base['acc']:.1%}")
    delta = tfidf_res["brier"] - base["brier"]
    print(f"  delta TF-IDF - Vila = {delta:+.4f}  "
          f"({'TF-IDF worse' if delta > 0 else 'TF-IDF better'})")

    print("\n[C] Time-decay also applied to TF-IDF? (k=5, decay-on-output)")
    # Apply same decay on the TF-IDF predictions for completeness.
    from engine.time_decay import apply_time_decay, event_age_days
    n = hits = 0
    bs = 0.0
    for e in holdout:
        y = e["outcome_real"]
        from engine.tfidf_neighbors import tfidf_predict
        p = tfidf_predict(e["outcome_framing"], e["contexto"], idx, k=5)
        if e.get("data"):
            age = event_age_days(e["data"], reference_date="2026-04-28")
            p = apply_time_decay(p, age, prior=0.5, half_life=180)
        n += 1
        if (p >= 0.5) == bool(y):
            hits += 1
        bs += (p - y) ** 2
    print(f"  TF-IDF + decay(h=180): brier={bs/n:.4f}  acc={hits/n:.1%}")


if __name__ == "__main__":
    main()
