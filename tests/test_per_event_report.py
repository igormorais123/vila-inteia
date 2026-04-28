"""Tests for engine/per_event_report.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.per_event_report import per_event_diagnostic, format_per_event_table
from engine.conformal import conformal_calibrate
from engine.post_cutoff_classifier import classify_and_predict

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


print("=== test_per_event_report ===")

events = [
    {"outcome_framing": "war attack Iran", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Olympics held", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "tech launches", "outcome_real": 0, "contexto": ""},
    {"outcome_framing": "Bitcoin > $200k", "outcome_real": 0, "contexto": ""},
    {"outcome_framing": "FOMC reunião realizada", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Apple lança iPad", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "election candidate wins", "outcome_real": 1, "contexto": ""},
    {"outcome_framing": "Brazil PEC reforma", "outcome_real": 0, "contexto": ""},
] * 2

print("\n[1] Basic shape and keys")
quants = conformal_calibrate(events, classify_and_predict, alpha=0.2)
rows = per_event_diagnostic(events, classify_and_predict, quants, tau=0.30)
check(len(rows) == len(events), f"len rows = len events ({len(rows)})")
required = {"framing", "p", "label", "conformal_lo", "conformal_hi",
            "conformal_set", "selective_decision"}
first = rows[0]
check(required.issubset(first.keys()), f"required keys present (got {set(first.keys())})")

print("\n[2] Probability + interval bounds")
for r in rows:
    if not (0.0 <= r["p"] <= 1.0):
        print(f"  bad p: {r}")
        break
    if r["conformal_lo"] > r["conformal_hi"]:
        print(f"  bad interval: {r}")
        break
    if r["conformal_lo"] > r["p"] or r["p"] > r["conformal_hi"]:
        # interval is symmetric clipped, p must lie within
        print(f"  p outside interval: {r}")
        break
else:
    check(True, "all p in [lo, hi] in [0,1]")
    check(True, "intervals well-formed")

print("\n[3] Selective decision semantics (tau)")
# tau=0.0 → no abstain
rows_t0 = per_event_diagnostic(events, classify_and_predict, quants, tau=0.0)
no_abstain = all(r["selective_decision"] is not None for r in rows_t0)
check(no_abstain, "tau=0.0 → no abstain")

# tau=0.49 → most abstain (only |p-0.5|>=0.49 commit)
rows_th = per_event_diagnostic(events, classify_and_predict, quants, tau=0.49)
abstains = sum(1 for r in rows_th if r["selective_decision"] is None)
check(abstains > 0, f"tau=0.49 → some abstain (got {abstains})")

# decision is in {0, 1, None}
all_valid = all(r["selective_decision"] in (0, 1, None) for r in rows)
check(all_valid, "decision in {0, 1, None}")

print("\n[4] 'real' field included when outcome_real present")
all_have_real = all("real" in r for r in rows)
check(all_have_real, "real present for labeled events")
# Mix with unlabeled event
mixed = events + [{"outcome_framing": "future event", "contexto": ""}]
rows_mix = per_event_diagnostic(mixed, classify_and_predict, quants, tau=0.30)
last = rows_mix[-1]
check("real" not in last, "real absent for unlabeled event")
check(len(rows_mix) == len(mixed), "still emits row for unlabeled")

print("\n[5] format_per_event_table renders")
out = format_per_event_table(rows)
check(isinstance(out, str) and "framing" in out, "header rendered")
check(out.count("\n") >= len(rows), f"≥ {len(rows)} lines")

empty_out = format_per_event_table([])
check("no events" in empty_out, "empty handled")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
