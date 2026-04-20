"""
Genetic algorithm para evoluir thresholds do classificador (Onda 57).

Alternativa a grid_search_thresholds (Onda 25). Vantagens:
    - Espaço contínuo (não grid discreto)
    - Escala bem para mais parâmetros
    - Encontra ótimos locais melhores em landscapes rugosos

Fitness combina entropia da distribuição (queremos diversidade) e
perplexity do rastreador + classificador (queremos ajuste aos dados).
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field, replace
from collections import Counter

from engine.psicohistoria.detector_estado_vila import MetricasStep, ESTADOS_CANONICOS
from engine.psicohistoria.tuner_classificador import (
    ThresholdsClassificador, classificar_com_thresholds, entropia_distribuicao,
)


@dataclass
class Individuo:
    thresholds: ThresholdsClassificador
    fitness: float = 0.0


@dataclass
class ResultadoGenetic:
    melhor: Individuo
    historico_fitness: list[float]
    geracoes: int
    populacao_final: list[Individuo]


def _aleatorizar(rng: random.Random) -> ThresholdsClassificador:
    return ThresholdsClassificador(
        bootstrap_step_max=rng.randint(5, 50),
        bootstrap_ativos_frac_max=rng.uniform(0.30, 0.80),
        recrutamento_ativos_frac_max=rng.uniform(0.20, 0.60),
        expansao_contribs_min=rng.randint(5, 100),
        expansao_ativos_frac_min=rng.uniform(0.40, 0.95),
        polarizacao_min=rng.uniform(0.30, 0.90),
        consenso_fragil_min=rng.uniform(0.05, 0.30),
        consenso_fragil_max=rng.uniform(0.30, 0.70),
        gini_crise_min=rng.uniform(0.50, 0.90),
    )


def _valido(t: ThresholdsClassificador) -> bool:
    return t.consenso_fragil_min < t.consenso_fragil_max


def fitness_individuo(t: ThresholdsClassificador, metricas: list[MetricasStep]) -> float:
    """Fitness = entropia (max) + diversidade cobertura (max)."""
    if not _valido(t) or not metricas:
        return 0.0
    estados = [classificar_com_thresholds(m, t) for m in metricas]
    ent = entropia_distribuicao(estados)
    cobertura = len(set(estados)) / len(ESTADOS_CANONICOS)
    # Penalidade se único estado domina (>90%)
    c = Counter(estados)
    max_frac = max(c.values()) / len(estados) if estados else 1.0
    penalidade = max(0, max_frac - 0.70) * 2   # domínio >70% reduz fitness
    return ent + 0.5 * cobertura - penalidade


def _crossover(a: ThresholdsClassificador, b: ThresholdsClassificador,
                rng: random.Random) -> ThresholdsClassificador:
    """Crossover uniforme: cada campo vem de a ou b com prob 0.5."""
    campos = [
        "bootstrap_step_max", "bootstrap_ativos_frac_max",
        "recrutamento_ativos_frac_max", "expansao_contribs_min",
        "expansao_ativos_frac_min", "polarizacao_min",
        "consenso_fragil_min", "consenso_fragil_max", "gini_crise_min",
    ]
    kwargs = {}
    for c in campos:
        kwargs[c] = getattr(a, c) if rng.random() < 0.5 else getattr(b, c)
    return ThresholdsClassificador(**kwargs)


def _mutar(t: ThresholdsClassificador, rng: random.Random,
            taxa: float = 0.15) -> ThresholdsClassificador:
    """Mutação gaussiana por campo com prob taxa."""
    novo = replace(t)
    if rng.random() < taxa:
        novo.bootstrap_step_max = max(1, int(novo.bootstrap_step_max + rng.gauss(0, 5)))
    if rng.random() < taxa:
        novo.bootstrap_ativos_frac_max = min(1.0, max(0.0, novo.bootstrap_ativos_frac_max + rng.gauss(0, 0.1)))
    if rng.random() < taxa:
        novo.recrutamento_ativos_frac_max = min(1.0, max(0.0, novo.recrutamento_ativos_frac_max + rng.gauss(0, 0.1)))
    if rng.random() < taxa:
        novo.expansao_contribs_min = max(1, int(novo.expansao_contribs_min + rng.gauss(0, 10)))
    if rng.random() < taxa:
        novo.expansao_ativos_frac_min = min(1.0, max(0.0, novo.expansao_ativos_frac_min + rng.gauss(0, 0.1)))
    if rng.random() < taxa:
        novo.polarizacao_min = min(1.0, max(0.0, novo.polarizacao_min + rng.gauss(0, 0.1)))
    if rng.random() < taxa:
        novo.consenso_fragil_min = min(1.0, max(0.0, novo.consenso_fragil_min + rng.gauss(0, 0.05)))
    if rng.random() < taxa:
        novo.consenso_fragil_max = min(1.0, max(0.0, novo.consenso_fragil_max + rng.gauss(0, 0.05)))
    if rng.random() < taxa:
        novo.gini_crise_min = min(1.0, max(0.0, novo.gini_crise_min + rng.gauss(0, 0.1)))
    return novo


def _torneio(pop: list[Individuo], rng: random.Random, k: int = 3) -> Individuo:
    """Seleção por torneio: k aleatórios, retorna melhor."""
    amostra = rng.sample(pop, min(k, len(pop)))
    return max(amostra, key=lambda i: i.fitness)


def evoluir(
    metricas: list[MetricasStep],
    pop_size: int = 30,
    geracoes: int = 50,
    taxa_mutacao: float = 0.15,
    elitismo: int = 2,
    seed: int = 42,
) -> ResultadoGenetic:
    """
    Loop principal do GA.
    elitismo: quantos melhores copiar direto para próxima geração.
    """
    rng = random.Random(seed)
    # População inicial
    pop = []
    while len(pop) < pop_size:
        t = _aleatorizar(rng)
        if _valido(t):
            pop.append(Individuo(thresholds=t,
                                   fitness=fitness_individuo(t, metricas)))
    pop.sort(key=lambda i: i.fitness, reverse=True)
    historico = [pop[0].fitness]

    for g in range(geracoes):
        # Elitismo: top-N direto
        nova_pop = pop[:elitismo]
        while len(nova_pop) < pop_size:
            pai1 = _torneio(pop, rng)
            pai2 = _torneio(pop, rng)
            filho_t = _crossover(pai1.thresholds, pai2.thresholds, rng)
            filho_t = _mutar(filho_t, rng, taxa=taxa_mutacao)
            if _valido(filho_t):
                nova_pop.append(Individuo(
                    thresholds=filho_t,
                    fitness=fitness_individuo(filho_t, metricas),
                ))
        nova_pop.sort(key=lambda i: i.fitness, reverse=True)
        pop = nova_pop
        historico.append(pop[0].fitness)

    return ResultadoGenetic(
        melhor=pop[0],
        historico_fitness=historico,
        geracoes=geracoes,
        populacao_final=pop,
    )
