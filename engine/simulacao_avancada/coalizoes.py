"""
Cooperative game theory: Shapley, core, Banzhaf.

Referências:
    Shapley (1953), A Value for n-Person Games.
    Gillies (1959), core.
    Banzhaf (1965), power indices.

Uso na Vila:
    - Distribuição justa de pontos em desafio coletivo
    - Alocação de crédito entre contribuintes
"""

from __future__ import annotations

from itertools import permutations


def shapley_value(
    jogadores: list[str],
    funcao_valor: callable,
) -> dict[str, float]:
    """
    Valor de Shapley: fair distribution de payoff conjunto.

    funcao_valor(coalizao) -> valor gerado por aquela coalizão
    (coalizao é frozenset de ids)

    Complexidade O(n!) — só para n pequeno (<=10).
    Para Vila com 144 habitantes em desafios de 3-5 agentes, ok.
    """
    n = len(jogadores)
    if n == 0:
        return {}
    shap = {j: 0.0 for j in jogadores}
    total_perms = 0
    for perm in permutations(jogadores):
        total_perms += 1
        coalizao_anterior: frozenset = frozenset()
        for j in perm:
            coalizao_com = coalizao_anterior | {j}
            marginal = funcao_valor(coalizao_com) - funcao_valor(coalizao_anterior)
            shap[j] += marginal
            coalizao_anterior = coalizao_com
    for j in shap:
        shap[j] /= total_perms
    return shap


def core_membership(
    jogadores: list[str],
    alocacao: dict[str, float],
    funcao_valor: callable,
) -> bool:
    """
    Alocação está no core se nenhuma sub-coalizão tem incentivo a desviar.

    Para cada coalizão S: soma das alocações em S >= v(S)
    E soma total == v(N)
    """
    from itertools import combinations
    total = sum(alocacao[j] for j in jogadores)
    valor_total = funcao_valor(frozenset(jogadores))
    if abs(total - valor_total) > 1e-6:
        return False
    n = len(jogadores)
    for tam in range(1, n):
        for coal in combinations(jogadores, tam):
            soma = sum(alocacao[j] for j in coal)
            if soma < funcao_valor(frozenset(coal)) - 1e-6:
                return False
    return True


def banzhaf_power(jogadores: list[str], funcao_valor: callable) -> dict[str, float]:
    """
    Índice de poder de Banzhaf (para jogos de votação binários).
    Cada jogador é "pivotal" quando sua saída muda o valor da coalizão.
    Normalizado (soma 1).
    """
    from itertools import combinations
    n = len(jogadores)
    if n == 0:
        return {}
    swings = {j: 0 for j in jogadores}
    outros_de = {j: [k for k in jogadores if k != j] for j in jogadores}
    for j in jogadores:
        for tam in range(n):
            for coal_sem_j in combinations(outros_de[j], tam):
                v_sem = funcao_valor(frozenset(coal_sem_j))
                v_com = funcao_valor(frozenset(coal_sem_j) | {j})
                if v_com > v_sem:
                    swings[j] += 1
    total = sum(swings.values())
    if total == 0:
        return {j: 0.0 for j in jogadores}
    return {j: swings[j] / total for j in jogadores}
