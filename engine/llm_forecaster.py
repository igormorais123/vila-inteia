"""LLM-based forecaster (opt-in). Three providers:
1. claude_cli — subprocess `claude -p` using Claude Code's OAuth (no API key)
2. ia_client — engine/ia_client.py (OmniRoute or Anthropic via env keys)
3. fallback — None (caller decides default, e.g. 0.5)

NOTE: Using an LLM during scoring relaxes constraint 10.4 (no-LLM-at-scoring).
This module is OPT-IN via apply_llm=True flag. Deterministic Vila pipeline
(no LLM) remains the default and the canonical honest forecaster."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable

_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "llm_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_DISK_CACHE_FILE = _CACHE_DIR / "llm_predict.json"


def _load_disk_cache() -> dict[str, float]:
    if _DISK_CACHE_FILE.exists():
        try:
            return json.loads(_DISK_CACHE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_disk_cache(cache: dict[str, float]) -> None:
    tmp = _DISK_CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache))
    tmp.replace(_DISK_CACHE_FILE)

LLM_PROMPT_TEMPLATE = """You are a forecasting expert. Given an event question, output ONLY a single floating-point probability between 0.05 and 0.95 representing P(yes outcome).

Rules:
- No prefix, no explanation, no units. Output ONLY the number.
- Use base rates from history. Be calibrated, not overconfident.
- For routine recurring events (FOMC, Olympics): output ~0.95.
- For tail-risk events (war escalation, asset crashes): output ~0.10-0.30.
- For coin-flip events (election toss-up, market threshold): output 0.50.

Event: {framing}
Context: {contexto}

P(yes) ="""

LLM_PROMPT_HYBRID_TEMPLATE = """You are a forecasting expert. Given an event question and an analyst's pre-computed category prior, output ONLY a single floating-point probability between 0.05 and 0.95.

Analyst pre-classification (use as anchor, deviate only with strong reason):
- Category: {label}
- Empirical-Bayes prior: {prior:.3f}

Rules:
- Anchor on the EB prior; deviate only if event has strong specific signal.
- Output ONLY the number, no prefix or units.
- Be calibrated, not overconfident.

Event: {framing}
Context: {contexto}

P(yes) ="""


_CACHE: dict[str, float] = _load_disk_cache()


def _parse_prob(text: str) -> float | None:
    if not text:
        return None
    match = re.search(r"\b(0?\.\d+|0|1\.0|1)\b", text)
    if not match:
        return None
    try:
        p = float(match.group(1))
    except ValueError:
        return None
    return max(0.05, min(0.95, p))


def _claude_cli_predict(prompt: str, timeout: int = 60) -> str | None:
    """Subprocess `claude -p PROMPT`. Uses Claude Code OAuth keychain."""
    if not shutil.which("claude"):
        return None
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except (subprocess.TimeoutExpired, OSError):
        return None


def llm_predict(framing: str, contexto: str = "",
                provider: str = "auto",
                model: str = "rapido", use_cache: bool = True,
                vila_hint: tuple[str, float] | None = None) -> float | None:
    """Query LLM for forecast probability. None on failure.

    provider: 'auto' (claude_cli → ia_client fallback) | 'claude_cli' | 'ia_client'
    vila_hint: optional (category_label, eb_prior) — enables hybrid prompt
               that anchors LLM on Vila's pre-classification.
    """
    cache_suffix = ""
    if vila_hint is not None:
        cache_suffix = f"|{vila_hint[0]}|{vila_hint[1]:.3f}"
    key = (framing + "|" + contexto[:200] + cache_suffix)[:400]
    if use_cache and key in _CACHE:
        return _CACHE[key]

    if vila_hint is not None:
        prompt = LLM_PROMPT_HYBRID_TEMPLATE.format(
            framing=framing, contexto=contexto[:500],
            label=vila_hint[0], prior=vila_hint[1],
        )
    else:
        prompt = LLM_PROMPT_TEMPLATE.format(framing=framing, contexto=contexto[:500])

    if provider in ("auto", "claude_cli"):
        text = _claude_cli_predict(prompt)
        p = _parse_prob(text or "")
        if p is not None:
            _CACHE[key] = p
            _save_disk_cache(_CACHE)
            return p
        if provider == "claude_cli":
            return None

    if provider in ("auto", "ia_client"):
        try:
            from engine.ia_client import chamar_llm_conversa
        except ImportError:
            return None
        response = chamar_llm_conversa(
            system_prompt="You output only a probability number.",
            user_prompt=prompt,
            modelo=model,
            max_tokens=20,
        )
        p = _parse_prob(response or "")
        if p is not None:
            _CACHE[key] = p
            _save_disk_cache(_CACHE)
            return p
    return None


def evaluate_llm_forecaster(events: list, model: str = "rapido",
                            max_events: int = 50) -> dict:
    """Bench LLM forecaster on events; falls back when LLM unavailable."""
    n = hits = 0
    brier = 0.0
    n_llm = 0
    for e in events[:max_events]:
        framing = e.get("outcome_framing") or e.get("framing", "")
        contexto = e.get("contexto", "")
        y = e.get("outcome_real")
        if y is None:
            continue
        p = llm_predict(framing, contexto, model=model)
        if p is None:
            p = 0.5
        else:
            n_llm += 1
        n += 1
        if (p >= 0.5) == bool(y):
            hits += 1
        brier += (p - y) ** 2
    return {
        "n": n, "n_llm_resolved": n_llm,
        "hits": hits,
        "acc": hits / n if n else 0,
        "brier": brier / n if n else 0,
        "llm_available": n_llm > 0,
    }
