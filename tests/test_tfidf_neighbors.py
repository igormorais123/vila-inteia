"""Test engine/tfidf_neighbors.py — TF-IDF cosine kNN forecaster."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.tfidf_neighbors import (
    build_tfidf_index,
    evaluate_tfidf,
    tfidf_predict,
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
                })
            except (ValueError, KeyError):
                pass
    return out


print("=== test_tfidf_neighbors ===")

print("\n[1] build_tfidf_index — synthetic toy corpus")
events = [
    {"outcome_framing": "Bitcoin atinge ATH", "contexto": "btc bull",
     "outcome_real": 0},
    {"outcome_framing": "BTC quebra resistência", "contexto": "bitcoin",
     "outcome_real": 0},
    {"outcome_framing": "Olympics realizada Q1", "contexto": "olimpíada",
     "outcome_real": 1},
    {"outcome_framing": "Davos summit held", "contexto": "WEF",
     "outcome_real": 1},
    {"outcome_framing": "Election won by candidate",
     "contexto": "presidential", "outcome_real": 1},
]
idx = build_tfidf_index(events)
check(idx["n_docs"] == 5, f"5 docs (got {idx['n_docs']})")
check(len(idx["doc_vectors"]) == 5, "doc_vectors len 5")
check(len(idx["doc_norms"]) == 5, "doc_norms len 5")
check(len(idx["doc_outcomes"]) == 5, "doc_outcomes len 5")
check(all(n > 0.0 for n in idx["doc_norms"]), "all doc_norms > 0")
check(isinstance(idx["tokens"], dict) and len(idx["tokens"]) > 5,
      f"idf dict non-trivial (n_tokens={len(idx['tokens'])})")
# IDF: rare token has higher IDF than common token.
# "olympics" appears in 1 doc, "btc" / "bitcoin" appear in 2.
# Use a token guaranteed unique, e.g. "wef" appears in 1 doc.
idf = idx["tokens"]
check("olympics" in idf, "olympics token indexed")
check("davos" in idf, "davos token indexed")
# Skip events without outcome_real.
events_with_none = events + [{"outcome_framing": "skip", "outcome_real": None}]
idx2 = build_tfidf_index(events_with_none)
check(idx2["n_docs"] == 5, f"None outcomes skipped (got {idx2['n_docs']})")

print("\n[2] tfidf_predict — exact match returns its outcome")
# Querying with the exact framing of a positive event should return ~1.
p = tfidf_predict("Olympics realizada Q1", "olimpíada", idx, k=1)
check(p == 1.0, f"exact pos match (got {p})")
p = tfidf_predict("Bitcoin atinge ATH", "btc bull", idx, k=1)
check(p == 0.0, f"exact neg match (got {p})")

print("\n[3] tfidf_predict — k>1 weighted average")
# Cluster: 2 BTC negatives + 3 positives. Querying BTC should be near 0.
p = tfidf_predict("BTC quebra resistência", "bitcoin", idx, k=5)
check(p < 0.5, f"BTC query leans negative (got {p:.3f})")
# Querying with a sports/event keyword should be near 1.
p = tfidf_predict("Davos summit held", "WEF", idx, k=5)
check(p > 0.5, f"event query leans positive (got {p:.3f})")

print("\n[4] Edge cases — empty index, zero-overlap, default fallback")
empty = build_tfidf_index([])
check(empty["n_docs"] == 0, "empty index n_docs=0")
p = tfidf_predict("anything", "", empty, k=5, default=0.42)
check(p == 0.42, f"empty index returns default (got {p})")
# Query with zero-overlap tokens (totally novel).
p = tfidf_predict("zzzqqqxxx unrelated_gibberish", "", idx, k=5, default=0.33)
check(p == 0.33, f"zero overlap returns default (got {p})")
# Empty query string returns default.
p = tfidf_predict("", "", idx, k=5, default=0.7)
check(p == 0.7, f"empty query returns default (got {p})")

print("\n[5] Bench on real Q1 TRAIN + holdout n=80")
train = load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q1_2026.csv")
train += load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q1_2026_v2.csv")
holdouts = []
for fn in (
    "post_cutoff_q2_2026_holdout",
    "post_cutoff_q2_2026_holdout_v2",
    "post_cutoff_q3_2026_holdout_v3",
    "post_cutoff_q4_2026_holdout_v4",
    "post_cutoff_q1_2027_holdout_v5",
):
    holdouts += load_csv(f"/home/pedroafonso/vila-inteia/data/backtest/{fn}.csv")
holdouts = holdouts[:80]
print(f"  TRAIN n={len(train)} HOLDOUT n={len(holdouts)}")
idx_train = build_tfidf_index(train)
check(idx_train["n_docs"] == len(train),
      f"train index built ({idx_train['n_docs']} docs)")
res = evaluate_tfidf(holdouts, idx_train, k=5)
print(f"  TF-IDF holdout: brier={res['brier']:.4f} acc={res['acc']:.1%} n={res['n']}")
check(res["n"] == len(holdouts), f"holdout n={res['n']}")
check(0.0 <= res["brier"] <= 1.0, f"brier in [0,1] (={res['brier']})")
check(0.0 <= res["acc"] <= 1.0, f"acc in [0,1] (={res['acc']})")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
