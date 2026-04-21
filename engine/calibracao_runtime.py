"""
Onda 97: runtime Platt calibration.

Carrega coefs (a, b) de disk + aplica em qualquer prob raw.
Self-calibrating Vila: após backtest, coefs salvos; runtime aplica.

Path default: data/calibracao_platt.json
Schema Platt: {"a": float, "b": float, "n_amostras": int,
          "fitado_em": iso_timestamp, "fonte": str}

Onda 148: suporta isotonic mapping.
Schema Isotonic: {"tipo": "isotonic", "mapping": [[raw, cal], ...],
          "n_amostras": int, "fitado_em": iso_timestamp, "fonte": str}
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

_DEFAULT_PATH = Path(os.getenv("VILA_CALIB_PATH", "data/calibracao_platt.json"))
_CACHE: dict | None = None
_CACHE_MTIME: float = 0.0


def _clip(p: float, eps: float = 1e-12) -> float:
    return max(eps, min(1 - eps, p))


def salvar_coefs(
    a: float,
    b: float,
    n_amostras: int,
    fonte: str = "backtest",
    path: str | Path | None = None,
) -> Path:
    """Persiste coefs Platt em disk (JSON)."""
    p = Path(path) if path else _DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "a": float(a),
        "b": float(b),
        "n_amostras": int(n_amostras),
        "fitado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fonte": fonte,
    }
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    global _CACHE, _CACHE_MTIME
    _CACHE = payload
    _CACHE_MTIME = p.stat().st_mtime
    return p


def carregar_coefs(path: str | Path | None = None, use_cache: bool = True) -> dict | None:
    """Lê coefs do disk. Cache invalidado em mtime mudou."""
    p = Path(path) if path else _DEFAULT_PATH
    if not p.exists():
        return None
    global _CACHE, _CACHE_MTIME
    mtime = p.stat().st_mtime
    if use_cache and _CACHE is not None and mtime == _CACHE_MTIME:
        return _CACHE
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
        _CACHE = payload
        _CACHE_MTIME = mtime
        return payload
    except Exception as e:
        logger.debug(f"carregar_coefs falhou: {e}")
        return None


def calibracao_ativa(path: str | Path | None = None) -> bool:
    return carregar_coefs(path) is not None


def aplicar(
    prob_raw: float,
    path: str | Path | None = None,
) -> float:
    """
    Aplica calibração se coefs existem. Senão retorna prob original.
    Onda 148: Se tipo='isotonic', aplica mapping. Senão Platt default.
    """
    coefs = carregar_coefs(path)
    if not coefs:
        return prob_raw
    if coefs.get("tipo") == "isotonic":
        try:
            from engine.calibracao_stats import isotonic_aplicar
            mapping = [(float(m[0]), float(m[1])) for m in coefs.get("mapping", [])]
            return isotonic_aplicar(prob_raw, mapping)
        except Exception as e:
            logger.debug(f"isotonic aplicar falhou: {e}")
            return prob_raw
    # Default Platt
    a = coefs.get("a")
    b = coefs.get("b")
    if a is None or b is None:
        return prob_raw
    p = _clip(prob_raw)
    logit = math.log(p / (1 - p))
    z = a * logit + b
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def aplicar_varios(
    probs: Iterable[float],
    path: str | Path | None = None,
) -> list[float]:
    return [aplicar(p, path) for p in probs]


def salvar_isotonic(
    mapping: list[tuple[float, float]],
    n_amostras: int,
    fonte: str = "backtest",
    path: str | Path | None = None,
) -> Path:
    """
    Onda 148: persiste isotonic mapping em disk (JSON).
    Mapping: lista ordenada de (prob_raw, prob_calibrada).
    """
    p = Path(path) if path else _DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tipo": "isotonic",
        "mapping": [[float(x), float(y)] for x, y in mapping],
        "n_amostras": int(n_amostras),
        "fitado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fonte": fonte,
    }
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    global _CACHE, _CACHE_MTIME
    _CACHE = payload
    _CACHE_MTIME = p.stat().st_mtime
    return p


def status(path: str | Path | None = None) -> dict:
    """Retorna info legível pra endpoint /api/v1/vila/calibracao/status."""
    coefs = carregar_coefs(path)
    p = Path(path) if path else _DEFAULT_PATH
    if not coefs:
        return {"ativa": False, "path": str(p)}
    tipo = coefs.get("tipo", "platt")
    out = {
        "ativa": True,
        "tipo": tipo,
        "path": str(p),
        "n_amostras": coefs.get("n_amostras"),
        "fitado_em": coefs.get("fitado_em"),
        "fonte": coefs.get("fonte"),
    }
    if tipo == "isotonic":
        out["mapping_size"] = len(coefs.get("mapping", []))
    else:
        out["a"] = coefs.get("a")
        out["b"] = coefs.get("b")
    return out
