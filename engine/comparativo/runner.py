"""
Runner de simulações comparativas A/B.

Versão simplificada: recebe ExportRun de 2 runs existentes, compara.
Versão completa (futura): roda 2 SimulacaoVila em paralelo com configs distintas.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.comparativo.metricas import comparar_trajetorias
from engine.psicohistoria.replay import ExportRun, resumo_run


@dataclass
class ConfigSimComparativa:
    """Config de uma variante da Vila para rodar em comparativo."""
    nome: str
    topico: str = "tema genérico"
    epsilon_crenca: float = 0.45       # Deffuant
    mu_crenca: float = 0.25
    intervalo_recalibracao: int = 50
    seed: int = 42


@dataclass
class ResultadoComparativo:
    config_a: dict
    config_b: dict
    resumo_a: dict
    resumo_b: dict
    metricas_comparativas: dict
    conclusoes: list[str] = field(default_factory=list)


def rodar_comparativo(
    run_a: ExportRun,
    run_b: ExportRun,
    config_a: ConfigSimComparativa | None = None,
    config_b: ConfigSimComparativa | None = None,
) -> ResultadoComparativo:
    """
    Compara 2 runs exportadas. Gera resumo + métricas + conclusões automáticas.
    """
    resumo_a = resumo_run(run_a)
    resumo_b = resumo_run(run_b)
    metricas = comparar_trajetorias(run_a.estados, run_b.estados)

    conclusoes = []
    if metricas["kl_divergence"] < 0.01:
        conclusoes.append("Runs estatisticamente idênticas (KL ~ 0)")
    elif metricas["kl_divergence"] < 0.5:
        conclusoes.append("Runs similares: KL baixo, mesmas dinâmicas dominantes")
    else:
        conclusoes.append(f"Runs divergem substancialmente: KL={metricas['kl_divergence']:.3f}")

    if resumo_a["estado_final"] == resumo_b["estado_final"]:
        conclusoes.append(f"Ambas convergem ao mesmo estado final: {resumo_a['estado_final']}")
    else:
        conclusoes.append(
            f"Estados finais divergem: A={resumo_a['estado_final']} vs B={resumo_b['estado_final']}"
        )

    if metricas["overlap_pct"] < 50:
        conclusoes.append("Baixa sobreposição de estados visitados — dinâmicas distintas")

    return ResultadoComparativo(
        config_a=config_a.__dict__ if config_a else {"nome": "A"},
        config_b=config_b.__dict__ if config_b else {"nome": "B"},
        resumo_a=resumo_a,
        resumo_b=resumo_b,
        metricas_comparativas=metricas,
        conclusoes=conclusoes,
    )
