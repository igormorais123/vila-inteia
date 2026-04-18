"""
engine/harness — Camada de Harness da Vila INTEIA.

Aplicação do framework de Zhou et al. (2026, arXiv:2604.08224) sobre a
arquitetura existente. Ver HARNESS_VILA.md, HARNESS_VILA_VIVENCIAL.md e
HARNESS_VILA_FUNCIONAL.md na raiz do repo.

Módulos:
    observabilidade — TraceEvent + @trace_fase (Onda 2)
    orcamento       — Orçamento de contexto por fase (Onda 2, stub)
    skill_registry  — Discovery semântica de oficinas (Onda 3, futuro)
    protocolos/     — Capability cards MCP-like (Onda 3, futuro)
    policy_engine   — Constituição como policy runtime (Onda 4, futuro)
"""

from .observabilidade import (
    TraceEvent, trace_fase, trace_contexto, flush_traces, habilitado,
    acumular_usage,
)
from .orcamento import (
    Orcamento,
    ORCAMENTO_POR_FASE,
    obter_orcamento,
    estimar_tokens,
    caber_ou_resumir,
    registrar_consumo,
    relatorio_orcamentos,
)
from . import skill_registry
from .protocolos import CapabilityCard, listar_cards, obter_card

__all__ = [
    "TraceEvent", "trace_fase", "flush_traces", "habilitado",
    "Orcamento", "ORCAMENTO_POR_FASE", "obter_orcamento", "estimar_tokens",
    "caber_ou_resumir", "registrar_consumo", "relatorio_orcamentos",
]
