"""Tests for engine/pre_registration.py — hash-signed prediction commits.

5 sections:
  [1] commit returns 64-char SHA256 hex
  [2] verify round-trip: valid_hash=True, events_hash_match=True
  [3] tamper detection: edited predictions → valid_hash=False
  [4] timestamp tamper: backdated timestamp → valid_hash=False
  [5] holdout bench on post_cutoff_q3_2026_holdout_v3.csv (n=30)
"""
from __future__ import annotations

import csv
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.post_cutoff_classifier import classify_and_predict
from engine.pre_registration import commit_predictions, verify_predictions

ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {msg}")
    else:
        fail += 1
        print(f"  FAIL {msg}")


print("=== test_pre_registration ===")


def fake_clf(framing, contexto=""):
    if "war" in framing.lower():
        return 0.85, "war_conflict"
    if "price" in framing.lower():
        return 0.40, "price_threshold"
    return 0.50, "default"


events = [
    {"evento_id": "e1", "outcome_framing": "war event", "contexto": "", "outcome_real": 1},
    {"evento_id": "e2", "outcome_framing": "price btc", "contexto": "", "outcome_real": 0},
    {"evento_id": "e3", "outcome_framing": "neutral question", "contexto": "", "outcome_real": 1},
]


def with_tmp(suffix=".json"):
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    f.close()
    return f.name


print("\n[1] commit returns 64-char SHA256 hex")
path = with_tmp()
try:
    h = commit_predictions(events, fake_clf, path)
    check(isinstance(h, str), "returns str")
    check(len(h) == 64, f"length 64 (got {len(h)})")
    check(all(c in "0123456789abcdef" for c in h), "lowercase hex")
    payload = json.loads(Path(path).read_text())
    check(payload["commitment_hash"] == h, "file commitment_hash matches return")
    check("timestamp" in payload and "events_hash" in payload,
          "timestamp + events_hash present")
    check(len(payload["predictions"]) == 3, f"3 predictions (got {len(payload['predictions'])})")
finally:
    os.unlink(path)

print("\n[2] verify round-trip: hash valid, brier/acc computed")
path = with_tmp()
try:
    h = commit_predictions(events, fake_clf, path)
    res = verify_predictions(path, events)
    check(res["valid_hash"] is True, f"valid_hash=True (got {res['valid_hash']})")
    check(res["events_hash_match"] is True,
          f"events_hash_match=True (got {res['events_hash_match']})")
    check(res["n_matched"] == 3, f"n_matched=3 (got {res['n_matched']})")
    check(0.0 <= res["brier"] <= 1.0, f"brier in [0,1] (got {res['brier']:.4f})")
    check(0.0 <= res["acc"] <= 1.0, f"acc in [0,1] (got {res['acc']:.3f})")
finally:
    os.unlink(path)

print("\n[3] tamper detection: edited predictions → valid_hash=False")
path = with_tmp()
try:
    commit_predictions(events, fake_clf, path)
    payload = json.loads(Path(path).read_text())
    payload["predictions"][0]["p"] = 0.01  # tamper
    Path(path).write_text(json.dumps(payload))
    res = verify_predictions(path, events)
    check(res["valid_hash"] is False, f"tampered → valid_hash=False (got {res['valid_hash']})")
finally:
    os.unlink(path)

print("\n[4] timestamp tamper: backdated → valid_hash=False")
path = with_tmp()
try:
    commit_predictions(events, fake_clf, path)
    payload = json.loads(Path(path).read_text())
    payload["timestamp"] = "1970-01-01T00:00:00+00:00"
    Path(path).write_text(json.dumps(payload))
    res = verify_predictions(path, events)
    check(res["valid_hash"] is False,
          f"backdated → valid_hash=False (got {res['valid_hash']})")
finally:
    os.unlink(path)

print("\n[5] holdout bench: post_cutoff_q3_2026_holdout_v3.csv (n=30)")


def load_csv(fp):
    out = []
    with open(fp) as f:
        for r in csv.DictReader(f):
            try:
                out.append({
                    "evento_id": r.get("evento_id", ""),
                    "outcome_framing": r.get("outcome_framing") or r.get("framing", ""),
                    "contexto": r.get("contexto", ""),
                    "outcome_real": int(r["outcome_real"]),
                })
            except (ValueError, KeyError):
                pass
    return out


q3 = load_csv("/home/pedroafonso/vila-inteia/data/backtest/post_cutoff_q3_2026_holdout_v3.csv")
path = with_tmp()
try:
    h = commit_predictions(q3, classify_and_predict, path)
    res = verify_predictions(path, q3)
    print(f"  n={res['n_matched']}  brier={res['brier']:.4f}  acc={res['acc']:.3f}")
    print(f"  hash={h}")
    check(res["n_matched"] == 30, f"n_matched=30 (got {res['n_matched']})")
    check(res["valid_hash"] is True, "round-trip valid_hash=True")
    check(res["events_hash_match"] is True, "events_hash_match=True")
    check(res["acc"] >= 0.5, f"acc ≥ 0.5 (got {res['acc']:.3f})")
finally:
    os.unlink(path)

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
