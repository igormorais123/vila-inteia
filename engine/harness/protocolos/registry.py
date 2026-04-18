"""
Registry de capability cards. Lê arquivos `.toml` em `cards/` e devolve
estruturas padronizadas. Nunca levanta exceção para o caller — cards
malformados são silenciosamente ignorados com warning.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Python 3.11+ traz tomllib na stdlib
try:
    import tomllib  # type: ignore
except ImportError:  # 3.10
    import tomli as tomllib  # type: ignore

logger = logging.getLogger("vila-inteia.harness.protocolos")

_DIR_CARDS = Path(__file__).resolve().parent / "cards"


@dataclass
class CapabilityCard:
    id: str
    version: str
    descricao: str
    args: dict = field(default_factory=dict)
    permission: dict = field(default_factory=dict)
    lifecycle: dict = field(default_factory=dict)
    output: dict = field(default_factory=dict)
    path_arquivo: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "version": self.version,
            "descricao": self.descricao,
            "args": self.args,
            "permission": self.permission,
            "lifecycle": self.lifecycle,
            "output": self.output,
            "path": self.path_arquivo,
        }


_cache: dict[str, CapabilityCard] = {}
_loaded = False


def _parse_card(path: Path) -> Optional[CapabilityCard]:
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except Exception as exc:
        logger.warning("card malformado %s: %s", path, exc)
        return None

    cap = data.get("capability") or {}
    if not cap.get("id"):
        return None
    return CapabilityCard(
        id=str(cap.get("id")),
        version=str(cap.get("version") or "0.0.0"),
        descricao=str(cap.get("descricao") or ""),
        args=data.get("args", {}),
        permission=data.get("permission", {}),
        lifecycle=data.get("lifecycle", {}),
        output=data.get("output", {}),
        path_arquivo=str(path.relative_to(path.parents[3]) if len(path.parents) >= 4 else path.name),
    )


def carregar_cards(force: bool = False) -> dict[str, CapabilityCard]:
    global _loaded, _cache
    if _loaded and not force:
        return _cache
    _cache = {}
    if _DIR_CARDS.is_dir():
        for p in sorted(_DIR_CARDS.glob("*.toml")):
            c = _parse_card(p)
            if c:
                _cache[c.id] = c
    _loaded = True
    return _cache


def listar_cards() -> list[dict]:
    return [c.as_dict() for c in carregar_cards().values()]


def obter_card(cap_id: str) -> Optional[dict]:
    c = carregar_cards().get(cap_id)
    return c.as_dict() if c else None
