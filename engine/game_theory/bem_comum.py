"""
Bens públicos e tragédia dos comuns.

Referências:
    Hardin (1968), The Tragedy of the Commons.
    Ostrom (1990), Governing the Commons. 8 princípios de design.
    Ledyard (1995), Public goods experiments.

Uso na Vila:
    - Orçamento compartilhado (INTEIA Coins pool)
    - Contribuição ao desafio coletivo
    - Biblioteca Infinita (recurso compartilhado)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResultadoBemComum:
    contribuicoes: dict[str, float]
    total_pool: float
    retorno_per_capita: float
    payoffs_individuais: dict[str, float]
    eficiencia: float               # 0 (full free-ride) a 1 (full cooperation)


def public_goods_game(
    dotacoes: dict[str, float],
    contribuicoes: dict[str, float],
    mpcr: float = 0.5,
) -> ResultadoBemComum:
    """
    Public goods game linear.
    mpcr = marginal per capita return (0 < mpcr < 1, n * mpcr > 1 p/ cooperação ser eficiente)

    Cada agente recebe:
        payoff_i = (dotacao_i - contribuicao_i) + mpcr * total_pool
    """
    n = len(contribuicoes)
    if n == 0:
        return ResultadoBemComum({}, 0, 0, {}, 0)
    total = sum(contribuicoes.values())
    retorno = mpcr * total
    payoffs = {}
    for aid, contrib in contribuicoes.items():
        dot = dotacoes.get(aid, 0)
        payoffs[aid] = (dot - contrib) + retorno
    max_possivel = sum(dotacoes.values()) * mpcr * n
    eficiencia = total / sum(dotacoes.values()) if dotacoes else 0
    return ResultadoBemComum(
        contribuicoes=contribuicoes,
        total_pool=total,
        retorno_per_capita=retorno,
        payoffs_individuais=payoffs,
        eficiencia=eficiencia,
    )


def ostrom_principios() -> list[str]:
    """
    Os 8 princípios de design da Elinor Ostrom para governar comuns.
    Useful para constituir artigos constitucionais sobre recurso compartilhado.
    """
    return [
        "1. Limites claros: quem é membro, qual é o recurso",
        "2. Regras adaptadas às condições locais",
        "3. Arenas de decisão coletiva participativas",
        "4. Monitoramento eficaz por membros ou responsáveis a eles",
        "5. Sanções graduais para quem viola regras",
        "6. Mecanismos baratos de resolução de conflitos",
        "7. Direito de auto-organização reconhecido por autoridade externa",
        "8. Governança em múltiplos níveis (nested enterprises)",
    ]


def tragedia_dos_comuns(
    usuarios: int,
    recurso_capacidade: float,
    consumo_por_usuario: float,
) -> float:
    """
    Modela esgotamento: retorna fração do recurso restante após consumo.
    Negativo = esgotamento (tragédia configurada).
    """
    total = usuarios * consumo_por_usuario
    return max(0.0, 1 - total / recurso_capacidade) if recurso_capacidade > 0 else 0
