"""
engine/harness/protocolos — Onda 3 HARNESS_VILA.md (Gap #4).

Capability cards MCP-like. Cada card descreve uma integração externa
da Vila (OmniRoute, Mirante, Supabase, ...) em contrato versionado
legível por humanos e máquinas.

Formato: TOML em `cards/<nome>.toml` + parser simples.

Futuro (Onda 4): expor via JSON-RPC 2.0 para outros agentes da Colmeia
descobrirem e invocarem as capabilities da Vila uniformemente.
"""

from .registry import (
    CapabilityCard,
    listar_cards,
    obter_card,
    carregar_cards,
)

__all__ = ["CapabilityCard", "listar_cards", "obter_card", "carregar_cards"]
