"""
Onda 156: per-persona Platt/isotonic calibration.

Cada persona tem viés calibração distinto. Musk é mais aggressive
bull (tende alto); Buffett conservador (tende baixo). Calibrador
global não captura. Per-persona: cada uma tem próprio (a, b) ou
mapping isotonic fitado no seu histórico pessoal.

Schema JSON (data/calibracao_por_persona.json):
{
  "CL001": {"tipo": "platt", "a": 0.9, "b": 0.2, "n": 15, ...},
  "CL007": {"tipo": "isotonic", "mapping": [[0.1, 0.05], ...], "n": 12, ...},
  ...
}

Runtime: persona_chat aplica prob_extraida → calibrado antes
agregação panel.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

_DEFAULT_PATH = Path(os.getenv(
    "VILA_CALIB_POR_PERSONA_PATH",
    "data/calibracao_por_persona.json",
))
_CACHE: dict | None = None
_CACHE_MTIME: float = 0.0


def _carregar(path: str | Path | None = None) -> dict:
    """Carrega mapping {persona_id: calibrator_dict}. {} se não existe."""
    p = Path(path) if path else _DEFAULT_PATH
    if not p.exists():
        return {}
    global _CACHE, _CACHE_MTIME
    mtime = p.stat().st_mtime
    if _CACHE is not None and mtime == _CACHE_MTIME:
        return _CACHE
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        _CACHE = data
        _CACHE_MTIME = mtime
        return data
    except Exception as e:
        logger.debug(f"_carregar per-persona falhou: {e}")
        return {}


def _salvar(data: dict, path: str | Path | None = None) -> Path:
    p = Path(path) if path else _DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    global _CACHE, _CACHE_MTIME
    _CACHE = data
    _CACHE_MTIME = p.stat().st_mtime
    return p


def aplicar_persona(
    persona_id: str,
    prob_raw: float,
    path: str | Path | None = None,
) -> float:
    """Aplica calibrador da persona se existe. Senão retorna raw."""
    data = _carregar(path)
    coefs = data.get(persona_id)
    if not coefs:
        return prob_raw

    tipo = coefs.get("tipo", "platt")
    if tipo == "isotonic":
        try:
            from engine.calibracao_stats import isotonic_aplicar
            mapping = [(float(m[0]), float(m[1])) for m in coefs.get("mapping", [])]
            return isotonic_aplicar(prob_raw, mapping)
        except Exception as e:
            logger.debug(f"iso aplicar persona {persona_id} falhou: {e}")
            return prob_raw

    # Platt
    a = coefs.get("a")
    b = coefs.get("b")
    if a is None or b is None:
        return prob_raw
    import math
    eps = 1e-12
    p = max(eps, min(1 - eps, prob_raw))
    logit = math.log(p / (1 - p))
    z = a * logit + b
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def fitar_persona(
    persona_id: str,
    probs: Iterable[float],
    y: Iterable[int],
    fonte: str = "backtest",
    path: str | Path | None = None,
) -> dict:
    """
    Fita melhor calibrador (Platt vs isotonic) pra persona + salva no
    calibracao_por_persona.json sem sobrescrever outras personas.
    """
    from engine.calibracao_auto import fit_melhor_calibrador

    r = fit_melhor_calibrador(probs, y)
    if r["vencedor"] == "nenhum":
        return {"persona_id": persona_id, "salvo": False, **r}

    data = _carregar(path)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if r["vencedor"] == "platt":
        data[persona_id] = {
            "tipo": "platt",
            "a": r["platt"]["a"],
            "b": r["platt"]["b"],
            "n_amostras": r["n_amostras"],
            "fitado_em": timestamp,
            "fonte": f"{fonte}_platt",
        }
    else:
        data[persona_id] = {
            "tipo": "isotonic",
            "mapping": [[float(x), float(y_)] for x, y_ in r["isotonic"]["mapping"]],
            "n_amostras": r["n_amostras"],
            "fitado_em": timestamp,
            "fonte": f"{fonte}_isotonic",
        }

    _salvar(data, path)
    return {
        "persona_id": persona_id,
        "salvo": True,
        "tipo": data[persona_id]["tipo"],
        "n_amostras": r["n_amostras"],
        "brier_raw": r["brier_raw"],
        "brier_melhor": min(r["platt"]["brier"], r["isotonic"]["brier"]),
    }


def fitar_todas_personas(
    datasets: list[dict],
    min_amostras: int = 5,
    path: str | Path | None = None,
) -> dict:
    """
    Extrai per_persona de datasets backtest, fita cada persona com ≥min_amostras.
    Returns resumo {persona_id: fit_result}.
    """
    from collections import defaultdict
    por_persona: dict[str, list] = defaultdict(list)

    for ds in datasets:
        if "erro" in ds:
            continue
        for ev in ds.get("eventos", []):
            y = ev.get("outcome_real")
            if y is None:
                continue
            for p in ev.get("per_persona", []):
                pid = p.get("persona_id")
                prob = p.get("prob_extraida")
                if pid and prob is not None:
                    por_persona[pid].append((float(prob), int(y)))

    resumo = {}
    for pid, pares in por_persona.items():
        if len(pares) < min_amostras:
            resumo[pid] = {"salvo": False, "motivo": f"n<{min_amostras}", "n": len(pares)}
            continue
        probs = [p for p, _ in pares]
        ys = [y for _, y in pares]
        resumo[pid] = fitar_persona(
            pid, probs, ys,
            fonte=f"fitar_todas_{len(pares)}ev",
            path=path,
        )
    return resumo


def status(path: str | Path | None = None) -> dict:
    """Retorna status legível."""
    data = _carregar(path)
    return {
        "n_personas_calibradas": len(data),
        "personas": {
            pid: {
                "tipo": c.get("tipo"),
                "n_amostras": c.get("n_amostras"),
                "fitado_em": c.get("fitado_em"),
            }
            for pid, c in data.items()
        },
    }
