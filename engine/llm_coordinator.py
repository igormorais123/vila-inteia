"""LLM as forecasting strategy coordinator.

Vila has many forecasting tools (keyword classifier, EB priors, Lindy, conformal,
TF-IDF, AdaHedge, etc). For each event, the LLM decides which subset to apply
and how to weight them, then returns a structured strategy plan that the
deterministic engine executes.

This adds a meta-layer: the LLM is no longer a peer forecaster but a router
that picks formulas. Stateless per call. Cached.

Strategy plan format (JSON returned by LLM):
{
  "use_vila": true,
  "use_lindy": false,
  "use_llm_direct": true,
  "use_market_implied": false,
  "use_tfidf": false,
  "weights": {"vila": 0.3, "llm": 0.7},
  "rationale": "scheduled event, recurring → Lindy + Vila; else LLM"
}
"""

from __future__ import annotations

import json
import re

from engine.lindy import lindy_for_event
from engine.llm_forecaster import _claude_cli_predict, llm_predict
from engine.log_pool import log_pool
from engine.post_cutoff_classifier import classify_and_predict


COORDINATOR_PROMPT = """You are a forecasting strategy coordinator. Given an event, choose which tools from a deterministic forecaster's toolbox to apply, and how to weight them.

Available tools:
- vila: deterministic keyword classifier with empirical-Bayes priors (works well for politics_br, scheduled events, war_conflict)
- lindy: duration prior for recurring scheduled events (Olympics, FOMC, WWDC, etc) — high if event has long history
- llm_direct: direct LLM forecast (your own world knowledge, best for tail-risk and out-of-distribution)
- market_implied: use the dataset author's a-priori probability as crowd-sourced prior
- tfidf: kNN over training corpus (only useful if many similar past events)

Output ONLY a JSON object with these exact keys (no prefix, no markdown fence):
{{
  "weights": {{"vila": 0.0-1.0, "lindy": 0.0-1.0, "llm_direct": 0.0-1.0, "market_implied": 0.0-1.0, "tfidf": 0.0-1.0}},
  "rationale": "<one short sentence>"
}}

Weights must sum to ~1.0 across non-zero entries. Set any tool to 0.0 if not relevant.

Event: {framing}
Context: {contexto}

JSON ="""


_PLAN_CACHE: dict[str, dict] = {}


def _parse_plan(text: str) -> dict | None:
    if not text:
        return None
    match = re.search(r'\{[^{}]*"weights"[^{}]*\{[^{}]*\}[^{}]*\}', text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def llm_pick_strategy(framing: str, contexto: str = "") -> dict:
    """Ask LLM to pick forecasting strategy weights for this event."""
    key = (framing + "|" + contexto[:200])[:400]
    if key in _PLAN_CACHE:
        return _PLAN_CACHE[key]

    prompt = COORDINATOR_PROMPT.format(framing=framing, contexto=contexto[:500])
    text = _claude_cli_predict(prompt, timeout=90)
    plan = _parse_plan(text or "")
    if plan is None:
        plan = {
            "weights": {"vila": 0.3, "llm_direct": 0.7},
            "rationale": "fallback: 70/30 LLM-Vila",
        }
    _PLAN_CACHE[key] = plan
    return plan


def coordinated_predict(framing: str, contexto: str = "",
                        prior_field: float | None = None) -> tuple[float, dict]:
    """LLM-coordinated prediction.

    1. LLM picks which tools to apply with which weights.
    2. Vila executes each tool, gets prob.
    3. log-pool combines with LLM weights.
    """
    plan = llm_pick_strategy(framing, contexto)
    weights = plan.get("weights", {})

    probs = {}
    if weights.get("vila", 0) > 0:
        p, _ = classify_and_predict(framing, contexto)
        probs["vila"] = p
    if weights.get("lindy", 0) > 0:
        p = lindy_for_event(framing, contexto)
        if p is not None:
            probs["lindy"] = p
    if weights.get("llm_direct", 0) > 0:
        p = llm_predict(framing, contexto)
        if p is not None:
            probs["llm_direct"] = p
    if weights.get("market_implied", 0) > 0 and prior_field is not None:
        try:
            probs["market_implied"] = max(0.05, min(0.95, float(prior_field)))
        except (TypeError, ValueError):
            pass

    active_weights = {k: weights.get(k, 0) for k in probs}
    total = sum(active_weights.values())
    if total <= 0 or not probs:
        p_vila, _ = classify_and_predict(framing, contexto)
        return p_vila, plan

    p_pool = log_pool(probs, active_weights)
    return p_pool, plan


def evaluate_coordinator(events: list, max_events: int = 60) -> dict:
    """Bench coordinator vs Vila standalone."""
    n = 0
    h_coord = h_vila = 0
    b_coord = b_vila = 0.0
    plans_used = []

    for e in events[:max_events]:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        prior = e.get("probabilidade_prior")
        p_coord, plan = coordinated_predict(framing, contexto, prior)
        p_vila, _ = classify_and_predict(framing, contexto)
        n += 1
        if (p_coord >= 0.5) == bool(y): h_coord += 1
        if (p_vila >= 0.5) == bool(y): h_vila += 1
        b_coord += (p_coord - y) ** 2
        b_vila += (p_vila - y) ** 2
        plans_used.append(plan)

    if n == 0:
        return {"n": 0}

    # Aggregate plan usage
    tool_usage = {}
    for plan in plans_used:
        for tool, w in plan.get("weights", {}).items():
            if w > 0:
                tool_usage[tool] = tool_usage.get(tool, 0) + 1

    return {
        "n": n,
        "vila": {"acc": h_vila / n, "brier": b_vila / n},
        "coordinator": {"acc": h_coord / n, "brier": b_coord / n},
        "tool_usage": tool_usage,
    }
