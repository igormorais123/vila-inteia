"""TF-IDF + cosine k-NN forecaster (stdlib only).

Build a TF-IDF index from training events (framing + contexto) and
predict for a query event by averaging the outcomes of its k nearest
neighbors weighted by cosine similarity.

No sklearn, no sentence-transformers. Pure stdlib (collections, math, re).

Index returned by `build_tfidf_index`:
    {
        "tokens": {token: idf_value, ...},
        "doc_vectors": [ {token: tfidf, ...}, ... ],
        "doc_norms":   [ float, ...],
        "doc_outcomes":[ 0/1, ...],
        "n_docs": int,
    }
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable


_TOKEN_RE = re.compile(r"[a-z0-9]+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Lowercase + alphanumeric split. Drops punctuation, accents kept-out."""
    if not text:
        return []
    return _TOKEN_RE.findall(text.lower())


def _tf(tokens: Iterable[str]) -> dict[str, float]:
    """Raw term frequency counts."""
    return dict(Counter(tokens))


def _vec_norm(vec: dict[str, float]) -> float:
    return math.sqrt(sum(v * v for v in vec.values()))


def _cosine(qv: dict[str, float], qn: float,
            dv: dict[str, float], dn: float) -> float:
    if qn == 0.0 or dn == 0.0:
        return 0.0
    # iterate over the shorter vector
    if len(qv) > len(dv):
        qv, dv = dv, qv
    dot = 0.0
    for tok, w in qv.items():
        dvw = dv.get(tok)
        if dvw is not None:
            dot += w * dvw
    return dot / (qn * dn)


def _event_text(event: dict) -> str:
    framing = event.get("outcome_framing") or event.get("framing", "") or ""
    contexto = event.get("contexto", "") or ""
    return f"{framing} {contexto}"


def build_tfidf_index(events: list) -> dict:
    """Build TF-IDF index from events (only those with outcome_real).

    Skips events without outcome_real to keep parity with kNN labels.
    """
    docs_tokens: list[list[str]] = []
    outcomes: list[int] = []
    for e in events:
        y = e.get("outcome_real")
        if y is None:
            continue
        toks = _tokenize(_event_text(e))
        docs_tokens.append(toks)
        outcomes.append(int(y))

    n_docs = len(docs_tokens)

    # Document frequency.
    df: Counter = Counter()
    for toks in docs_tokens:
        for tok in set(toks):
            df[tok] += 1

    # IDF (smoothed): log((1 + N) / (1 + df)) + 1.
    idf: dict[str, float] = {}
    for tok, df_t in df.items():
        idf[tok] = math.log((1.0 + n_docs) / (1.0 + df_t)) + 1.0

    # TF-IDF doc vectors + norms.
    doc_vectors: list[dict[str, float]] = []
    doc_norms: list[float] = []
    for toks in docs_tokens:
        tf = _tf(toks)
        vec = {tok: tf_v * idf.get(tok, 0.0) for tok, tf_v in tf.items()}
        doc_vectors.append(vec)
        doc_norms.append(_vec_norm(vec))

    return {
        "tokens": idf,
        "doc_vectors": doc_vectors,
        "doc_norms": doc_norms,
        "doc_outcomes": outcomes,
        "n_docs": n_docs,
    }


def _vectorize_query(framing: str, contexto: str,
                     idf: dict[str, float]) -> tuple[dict[str, float], float]:
    toks = _tokenize(f"{framing} {contexto}")
    tf = _tf(toks)
    vec = {tok: tf_v * idf.get(tok, 0.0)
           for tok, tf_v in tf.items() if tok in idf}
    return vec, _vec_norm(vec)


def tfidf_predict(framing: str, contexto: str, index: dict,
                  k: int = 5, default: float = 0.5) -> float:
    """Cosine top-k weighted-average of neighbor outcomes.

    Returns `default` when index is empty or query has zero overlap with
    any indexed token.
    """
    n_docs = index.get("n_docs", 0)
    if n_docs == 0:
        return default

    qv, qn = _vectorize_query(framing, contexto, index["tokens"])
    if qn == 0.0:
        return default

    doc_vectors = index["doc_vectors"]
    doc_norms = index["doc_norms"]
    outcomes = index["doc_outcomes"]

    sims: list[tuple[float, int]] = []
    for i in range(n_docs):
        s = _cosine(qv, qn, doc_vectors[i], doc_norms[i])
        if s > 0.0:
            sims.append((s, outcomes[i]))

    if not sims:
        return default

    sims.sort(key=lambda x: -x[0])
    top = sims[:max(1, k)]
    weight_sum = sum(s for s, _ in top)
    if weight_sum <= 0.0:
        return default
    return sum(s * y for s, y in top) / weight_sum


def evaluate_tfidf(events: list, index: dict, k: int = 5) -> dict:
    """Compute brier and acc for tfidf_predict over events."""
    n = 0
    hits = 0
    brier_sum = 0.0
    for e in events:
        y = e.get("outcome_real")
        if y is None:
            continue
        framing = e.get("outcome_framing") or e.get("framing", "") or ""
        contexto = e.get("contexto", "") or ""
        p = tfidf_predict(framing, contexto, index, k=k)
        n += 1
        if (p >= 0.5) == bool(y):
            hits += 1
        brier_sum += (p - y) ** 2
    if n == 0:
        return {"n": 0, "brier": 0.0, "acc": 0.0, "hits": 0}
    return {
        "n": n,
        "hits": hits,
        "acc": hits / n,
        "brier": brier_sum / n,
    }
