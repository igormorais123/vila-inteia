"""Per-event diagnostic: prob, conformal interval, selective decision."""

from __future__ import annotations

from typing import Callable

from engine._pred_utils import unpack_pred
from engine.conformal import conformal_interval, conformal_set
from engine.selective_forecast import selective_predict


def per_event_diagnostic(
    events: list,
    classify_fn: Callable,
    conformal_quants: dict[str, float],
    tau: float = 0.30,
) -> list[dict]:
    """One row per event: framing, p, label, conformal interval, selective decision.

    Includes 'real' iff event has outcome_real.
    """
    out: list[dict] = []
    for e in events:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        raw = classify_fn(framing, contexto)
        if isinstance(raw, tuple):
            p, label = raw[0], raw[1] if len(raw) > 1 else "default"
        else:
            p, label = unpack_pred(raw), "default"
        lo, hi = conformal_interval(p, label, conformal_quants)
        cset = conformal_set(p, label, conformal_quants)
        sel = selective_predict(p, tau=tau)
        row = {
            "framing": framing,
            "p": round(p, 4),
            "label": label,
            "conformal_lo": round(lo, 4),
            "conformal_hi": round(hi, 4),
            "conformal_set": sorted(cset),
            "selective_decision": sel,
        }
        if e.get("outcome_real") is not None:
            row["real"] = int(e["outcome_real"])
        out.append(row)
    return out


def format_per_event_table(rows: list[dict]) -> str:
    """Plain-text table for CLI output."""
    if not rows:
        return "(no events)"
    header = f"{'p':>6} {'lo':>6} {'hi':>6} {'set':>7} {'sel':>4} {'real':>4}  framing"
    lines = [header, "=" * 80]
    for r in rows:
        sel = "abst" if r["selective_decision"] is None else str(r["selective_decision"])
        real = str(r.get("real", "?"))
        cset = "{" + ",".join(str(x) for x in r["conformal_set"]) + "}"
        framing = (r["framing"] or "")[:40]
        lines.append(
            f"{r['p']:>6.3f} {r['conformal_lo']:>6.3f} {r['conformal_hi']:>6.3f} "
            f"{cset:>7} {sel:>4} {real:>4}  {framing}"
        )
    return "\n".join(lines)
