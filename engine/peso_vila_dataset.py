"""
Onda 160: dataset-specific peso_vila override.

Empiricamente (Onda 154): Vila bate humano em política/política-BR
(skill +0.67 impeachment, +0.29 pres_2022), mas PERDE em crypto
(skill -1.18 em btc_2024). Prior humano já calibrado em domínios
"objetivos" (ETF approved, halving happens) — Vila adiciona ruído.

Solução: peso_vila condicional ao dataset. Crypto low (confia prior),
political alto (confia Vila).

Schema data/peso_vila_por_dataset.json:
{
  "impeachment_dilma_2016": 0.8,
  "crypto_bitcoin_2024": 0.4,
  "eleicao_presidencial_br_2022": 0.7,
  ...
}
Default: 0.7 (valor global onda 125).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_PATH = Path(os.getenv(
    "VILA_PESO_POR_DATASET_PATH",
    "data/peso_vila_por_dataset.json",
))
_DEFAULT_PESO = 0.7


def _normalize_key(dataset_name_or_path: str) -> str:
    """Extract stem (without .csv) from path or name."""
    name = dataset_name_or_path or ""
    name = name.replace("\\", "/").split("/")[-1]
    return name.replace(".csv", "").replace(".json", "")


def obter_peso_vila(
    dataset_name_or_path: str,
    default: float = _DEFAULT_PESO,
    path: str | Path | None = None,
) -> float:
    """
    Retorna peso_vila override pro dataset, ou default se não existe.
    """
    p = Path(path) if path else _DEFAULT_PATH
    if not p.exists():
        return default
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        key = _normalize_key(dataset_name_or_path)
        val = data.get(key)
        if val is None or not isinstance(val, (int, float)):
            return default
        return max(0.0, min(1.0, float(val)))
    except Exception as e:
        logger.debug(f"obter_peso_vila falhou: {e}")
        return default


def salvar_peso(
    dataset_name_or_path: str,
    peso: float,
    path: str | Path | None = None,
) -> Path:
    """Grava/atualiza override pra um dataset."""
    p = Path(path) if path else _DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    key = _normalize_key(dataset_name_or_path)
    data[key] = max(0.0, min(1.0, float(peso)))
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def listar_overrides(path: str | Path | None = None) -> dict:
    p = Path(path) if path else _DEFAULT_PATH
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
