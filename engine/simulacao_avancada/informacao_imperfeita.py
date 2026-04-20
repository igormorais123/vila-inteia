"""
Signaling games, cheap talk, reputation models.

Referências:
    Spence (1973), Job Market Signaling.
    Crawford & Sobel (1982), cheap talk.
    Kreps et al (1982), reputation in repeated games.

Uso na Vila:
    - Habitantes podem sinalizar competência (custoso) ou apenas falar (cheap talk)
    - Reputação acumulada afeta credibilidade de sinais futuros
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Sinal:
    tipo_real: str             # "alto" | "baixo" — conhecimento privado
    sinal_enviado: str         # tipo que tenta se passar
    custo: float               # custo de enviar sinal (Spence)


def separating_equilibrium(
    custo_alto_para_alto: float,
    custo_alto_para_baixo: float,
    payoff_parecer_alto: float,
) -> bool:
    """
    Equilíbrio separador Spence: apenas tipos altos enviam sinal.
    Condição: baixos preferem não sinalizar mesmo que pareçam altos.

    Retorna True se equilíbrio separador existe.
    """
    lucro_baixo_sinalizar = payoff_parecer_alto - custo_alto_para_baixo
    lucro_baixo_nao_sinalizar = 0.0
    return lucro_baixo_sinalizar < lucro_baixo_nao_sinalizar


def cheap_talk_credivel(
    interesse_emissor_alinha_receptor: bool,
) -> bool:
    """
    Cheap talk (palavra sem custo) só é crível se interesses se alinham (Crawford-Sobel).
    """
    return interesse_emissor_alinha_receptor


def reputacao_update(
    reputacao_prior: float,
    acao: str,
    acao_esperada: str,
    peso_observacao: float = 0.3,
) -> float:
    """
    Atualização simples de reputação: exponential moving average de congruência.
    acao == acao_esperada: reputação sobe; senão desce.
    """
    alinhado = 1.0 if acao == acao_esperada else 0.0
    return (1 - peso_observacao) * reputacao_prior + peso_observacao * alinhado
