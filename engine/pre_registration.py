"""Cryptographic pre-registration of forecasts.

Commit predictions BEFORE outcomes are known, sign with SHA256 over
(events_text, predictions_text, timestamp). Anyone can later verify the
committed file was not altered post-hoc by recomputing the hash and comparing.

Format:
    {
        "timestamp": "<ISO-8601 UTC>",
        "events_hash": "<sha256 of canonical events JSON>",
        "predictions": [{"id": "...", "p": 0.73}, ...],
        "commitment_hash": "<sha256 of events_text + predictions_text + timestamp>",
    }
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from engine._pred_utils import unpack_pred


def _canonical_events_text(events: list[dict[str, Any]]) -> str:
    """Stable JSON of events used for hashing.

    Only fields relevant for prediction are included so re-running with the
    same input yields the same digest. `outcome_real` is intentionally
    excluded — the commitment must be ground-truth-blind.
    """
    rows = []
    for e in events:
        rows.append({
            "id": e.get("evento_id") or e.get("id") or "",
            "framing": e.get("outcome_framing") or e.get("framing", ""),
            "contexto": e.get("contexto", ""),
        })
    return json.dumps(rows, ensure_ascii=False, sort_keys=True)


def _canonical_predictions_text(predictions: list[dict[str, Any]]) -> str:
    rows = [{"id": p["id"], "p": round(float(p["p"]), 6)} for p in predictions]
    return json.dumps(rows, ensure_ascii=False, sort_keys=True)


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def commit_predictions(
    events: list[dict[str, Any]],
    classify_fn: Callable[[str, str], Any],
    output_path: str | Path,
) -> str:
    """Compute predictions, sign with SHA256, write JSON, return commitment hash.

    Hash spans events_text + predictions_text + timestamp so any tamper
    (changing events, predictions, or backdating) breaks verification.
    """
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    predictions: list[dict[str, Any]] = []
    for i, e in enumerate(events):
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        p = unpack_pred(classify_fn(framing, contexto))
        eid = e.get("evento_id") or e.get("id") or f"row_{i}"
        predictions.append({"id": str(eid), "p": float(p)})

    events_text = _canonical_events_text(events)
    predictions_text = _canonical_predictions_text(predictions)
    events_hash = _sha256(events_text)
    commitment_hash = _sha256(events_text + predictions_text + timestamp)

    payload = {
        "timestamp": timestamp,
        "events_hash": events_hash,
        "predictions": predictions,
        "commitment_hash": commitment_hash,
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return commitment_hash


def verify_predictions(
    commitment_path: str | Path,
    ground_truth: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify commitment integrity and score against revealed outcomes.

    Returns:
        valid_hash:  True iff stored commitment_hash matches the recomputed
                     SHA256 over (canonical_events + canonical_predictions +
                     stored_timestamp). Hash uses the events bound at commit
                     time (re-derived from `ground_truth` rows by matching id).
        brier:       mean (p - y)^2 across matched ids
        acc:         fraction where (p >= 0.5) == bool(y)
        n_matched:   number of ids matched to ground_truth
        events_hash_match: True iff stored events_hash matches recomputed
    """
    payload = json.loads(Path(commitment_path).read_text())
    stored_hash = payload["commitment_hash"]
    stored_ts = payload["timestamp"]
    stored_events_hash = payload["events_hash"]
    predictions = payload["predictions"]

    # Re-derive canonical events from ground_truth (same id set, same fields).
    events_text = _canonical_events_text(ground_truth)
    predictions_text = _canonical_predictions_text(predictions)
    recomputed_hash = _sha256(events_text + predictions_text + stored_ts)
    recomputed_events_hash = _sha256(events_text)
    valid_hash = recomputed_hash == stored_hash
    events_hash_match = recomputed_events_hash == stored_events_hash

    # Score predictions against ground_truth by id.
    truth_by_id: dict[str, int] = {}
    for e in ground_truth:
        eid = str(e.get("evento_id") or e.get("id") or "")
        y = e.get("outcome_real")
        if y is None or eid == "":
            continue
        truth_by_id[eid] = int(y)

    n = 0
    brier_sum = 0.0
    hits = 0
    for pred in predictions:
        pid = str(pred["id"])
        if pid not in truth_by_id:
            continue
        y = truth_by_id[pid]
        p = float(pred["p"])
        n += 1
        brier_sum += (p - y) ** 2
        if (p >= 0.5) == bool(y):
            hits += 1

    return {
        "valid_hash": valid_hash,
        "events_hash_match": events_hash_match,
        "n_matched": n,
        "brier": brier_sum / n if n else 0.0,
        "acc": hits / n if n else 0.0,
    }
