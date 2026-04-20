"""
Tuner de thresholds do classificador heurístico (Onda 25).

Problema: sim real só visita 2 dos 8 estados (expansao, equilibrio). Thresholds
default (contrib≥20 AND ativos>70%) são satisfeitos demais.

Solução: grid search sobre thresholds minimizando métrica de "concentração"
(queremos distribuição mais balanceada de estados observados).

Métrica: entropia de Shannon normalizada. Alta entropia = estados diversos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
import math

from engine.psicohistoria.detector_estado_vila import (
    MetricasStep, ESTADOS_CANONICOS,
)


@dataclass
class ThresholdsClassificador:
    bootstrap_step_max: int = 20
    bootstrap_ativos_frac_max: float = 0.60
    recrutamento_ativos_frac_max: float = 0.40
    expansao_contribs_min: int = 20
    expansao_ativos_frac_min: float = 0.70
    polarizacao_min: float = 0.60
    consenso_fragil_min: float = 0.15
    consenso_fragil_max: float = 0.40
    gini_crise_min: float = 0.75


def classificar_com_thresholds(m: MetricasStep, t: ThresholdsClassificador) -> str:
    if m.total_agentes == 0:
        return "bootstrap"
    frac = m.n_agentes_ativos / m.total_agentes
    if m.propostas_constituintes_ativas >= 1:
        return "renovacao_constituinte"
    if m.gini_economia > t.gini_crise_min:
        return "crise_economica"
    if m.polarizacao_media > t.polarizacao_min:
        return "polarizacao"
    if m.step < t.bootstrap_step_max and frac < t.bootstrap_ativos_frac_max:
        return "bootstrap"
    if frac < t.recrutamento_ativos_frac_max:
        return "recrutamento"
    if m.contribuicoes_ao_desafio >= t.expansao_contribs_min and frac > t.expansao_ativos_frac_min:
        return "expansao"
    if t.consenso_fragil_min <= m.polarizacao_media <= t.consenso_fragil_max:
        return "consenso_fragil"
    return "equilibrio"


def entropia_distribuicao(estados: list[str]) -> float:
    """Entropia Shannon normalizada (0=concentrado, 1=uniforme 8 estados)."""
    if not estados:
        return 0.0
    c = Counter(estados)
    n = len(estados)
    probs = [v / n for v in c.values()]
    h = -sum(p * math.log2(max(p, 1e-12)) for p in probs)
    h_max = math.log2(len(ESTADOS_CANONICOS))
    return h / h_max


@dataclass
class ResultadoTuning:
    thresholds_default: ThresholdsClassificador
    thresholds_otimos: ThresholdsClassificador
    entropia_default: float
    entropia_otima: float
    distribuicao_default: dict[str, float]
    distribuicao_otima: dict[str, float]
    n_testados: int


def grid_search_thresholds(
    metricas: list[MetricasStep],
    n_grid: int = 4,
) -> ResultadoTuning:
    """
    Varre grid de thresholds, escolhe o que maximiza entropia.

    Varia:
      expansao_contribs_min: [10, 20, 40, 80]
      expansao_ativos_frac_min: [0.50, 0.65, 0.80, 0.90]
      consenso_fragil_min: [0.05, 0.10, 0.15, 0.20]
      consenso_fragil_max: [0.30, 0.40, 0.50, 0.60]
    """
    default = ThresholdsClassificador()
    estados_default = [classificar_com_thresholds(m, default) for m in metricas]
    c_def = Counter(estados_default)
    n = max(1, len(metricas))
    dist_default = {e: c_def[e] / n for e in ESTADOS_CANONICOS if e in c_def}
    entr_default = entropia_distribuicao(estados_default)

    melhor_entr = entr_default
    melhor_t = default
    n_test = 0

    contribs_opts = [10, 20, 40, 80]
    ativos_opts = [0.50, 0.65, 0.80, 0.90]
    cf_min_opts = [0.05, 0.10, 0.15, 0.20]
    cf_max_opts = [0.30, 0.40, 0.50, 0.60]

    for co in contribs_opts[:n_grid]:
        for ao in ativos_opts[:n_grid]:
            for cmi in cf_min_opts[:n_grid]:
                for cma in cf_max_opts[:n_grid]:
                    if cmi >= cma:
                        continue
                    t = ThresholdsClassificador(
                        expansao_contribs_min=co,
                        expansao_ativos_frac_min=ao,
                        consenso_fragil_min=cmi,
                        consenso_fragil_max=cma,
                    )
                    estados = [classificar_com_thresholds(m, t) for m in metricas]
                    ent = entropia_distribuicao(estados)
                    n_test += 1
                    if ent > melhor_entr:
                        melhor_entr = ent
                        melhor_t = t

    estados_otimos = [classificar_com_thresholds(m, melhor_t) for m in metricas]
    c_otim = Counter(estados_otimos)
    dist_otima = {e: c_otim[e] / n for e in ESTADOS_CANONICOS if e in c_otim}

    return ResultadoTuning(
        thresholds_default=default,
        thresholds_otimos=melhor_t,
        entropia_default=entr_default,
        entropia_otima=melhor_entr,
        distribuicao_default=dist_default,
        distribuicao_otima=dist_otima,
        n_testados=n_test,
    )
