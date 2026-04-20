"""
Mechanism design: alocação de recursos escassos, leilões, transferências VCG.

Referências:
    Vickrey (1961); Clarke (1971); Groves (1973).
    Nisan, Roughgarden, Tardos, Vazirani (2007), Algorithmic Game Theory.

Uso na Vila:
    - Alocação de slots em oficinas lotadas
    - Distribuição de cargos (relator, moderador)
    - Leilão interno de direito de publicar matéria no Mirante
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Lance:
    bidder_id: str
    valor: float                     # INTEIA Coins que está disposto a pagar


@dataclass
class Alocacao:
    vencedor_id: str
    preco_pago: float
    segundos_colocados: list[str]   # p/ auditoria


def vickrey_2nd_price(lances: list[Lance]) -> Alocacao | None:
    """
    Leilão Vickrey (2nd-price sealed-bid): maior lance vence, paga valor do 2º.

    Strategy-proof: lance ótimo é valor verdadeiro.
    """
    if not lances:
        return None
    ordenados = sorted(lances, key=lambda l: l.valor, reverse=True)
    vencedor = ordenados[0]
    preco = ordenados[1].valor if len(ordenados) > 1 else 0.0
    return Alocacao(
        vencedor_id=vencedor.bidder_id,
        preco_pago=preco,
        segundos_colocados=[l.bidder_id for l in ordenados[1:]],
    )


@dataclass
class AlocacaoVCG:
    alocacao: dict[str, list[str]]         # item_id -> lista de bidders
    pagamentos: dict[str, float]           # bidder_id -> preço VCG
    welfare_total: float


def vcg_alocacao(
    valuations: dict[str, dict[str, float]],
    capacidade: dict[str, int],
) -> AlocacaoVCG:
    """
    VCG multi-item (unit-demand por item, slots independentes).

    Versão simples: cada item é alocado independentemente via 2nd price.
    Para itens com capacidade > 1: top-k bidders ganham, pagam (k+1)-ésimo preço.
    Strategy-proof por item.

    valuations[bidder][item] = valor do bidder para o item
    capacidade[item] = slots
    """
    alocacao: dict[str, list[str]] = {}
    pagamentos: dict[str, float] = {b: 0.0 for b in valuations}
    welfare = 0.0
    for item, k in capacidade.items():
        lances = [(b, v.get(item, 0.0)) for b, v in valuations.items()]
        lances.sort(key=lambda x: x[1], reverse=True)
        vencedores = [b for b, _ in lances[:k] if _ > 0]
        alocacao[item] = vencedores
        preco_corte = lances[k][1] if len(lances) > k else 0.0
        for b in vencedores:
            pagamentos[b] += preco_corte
            welfare += valuations[b].get(item, 0.0)
    return AlocacaoVCG(alocacao=alocacao, pagamentos=pagamentos, welfare_total=welfare)


def leilao_publicacao_mirante(
    candidatos: list[Lance],
    slots_disponiveis: int = 1,
) -> list[Alocacao]:
    """
    N habitantes licitam direito de publicar no Mirante, K slots disponíveis.
    Usa multi-item Vickrey: top-K ganham, todos pagam (K+1)-ésimo preço.
    """
    if slots_disponiveis <= 0 or not candidatos:
        return []
    ordenados = sorted(candidatos, key=lambda l: l.valor, reverse=True)
    vencedores = ordenados[:slots_disponiveis]
    preco = ordenados[slots_disponiveis].valor if len(ordenados) > slots_disponiveis else 0.0
    resultado: list[Alocacao] = []
    for v in vencedores:
        resultado.append(Alocacao(
            vencedor_id=v.bidder_id,
            preco_pago=preco,
            segundos_colocados=[l.bidder_id for l in ordenados if l.bidder_id != v.bidder_id],
        ))
    return resultado
