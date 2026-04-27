"""
Onda 166: bootstrap pareado para critério de aceitação do gate.

Operacionaliza o reparo P1.4 da auditoria Helena (campanha N=100):

Substitui "aceitar se brier_gate <= brier_tune * 1.35" (tolerância arbitrária)
por bootstrap pareado de 10.000 iterações sobre delta = brier_gate - brier_tune.

Critério oficial:
- IC 95% superior do delta < 0.05 absoluto
- p-valor unilateral (H0: gate degrada significativamente) < 0.10
- Ambos exigidos. Falha de qualquer um = gate REPROVADO = campanha aborta.

Por que pareado: cada evento contribui com seu próprio brier no tune e no gate
(quando aplicável). Em N=100 isso não é diretamente possível porque os splits
são disjuntos, então usamos *unpaired* mas com replicação por bootstrap. Para
o critério oficial, o pareamento é entre as configurações (tune_baseline vs
gate_avaliacao), não entre eventos.

Uso:
    from engine.bootstrap_gate import avaliar_gate
    r = avaliar_gate(briers_tune, briers_gate, n_iter=10000, seed=42)
    if r['aceito']:
        # liberar holdout
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence


@dataclass
class ResultadoGate:
    aceito: bool
    razao: str
    brier_tune: float
    brier_gate: float
    delta_observado: float
    ic_95_inferior: float
    ic_95_superior: float
    p_valor_unilateral: float
    n_iter: int
    n_tune: int
    n_gate: int

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def _media(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _bootstrap_delta(
    briers_tune: list[float],
    briers_gate: list[float],
    n_iter: int,
    rng: random.Random,
) -> list[float]:
    """Reamostragem bootstrap independente em cada split.

    Para cada iteração: amostra com reposição n_tune do tune e n_gate do gate,
    computa delta = mean(gate) - mean(tune). Retorna distribuição empírica.
    """
    deltas: list[float] = []
    n_t = len(briers_tune)
    n_g = len(briers_gate)
    for _ in range(n_iter):
        sample_t = [briers_tune[rng.randrange(n_t)] for _ in range(n_t)]
        sample_g = [briers_gate[rng.randrange(n_g)] for _ in range(n_g)]
        deltas.append(_media(sample_g) - _media(sample_t))
    return deltas


def _percentile(xs: list[float], p: float) -> float:
    """Percentil p (0..1) sobre lista ordenada (linear interpolation)."""
    if not xs:
        return 0.0
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (k - f) * (s[c] - s[f])


def avaliar_gate(
    briers_tune: Sequence[float],
    briers_gate: Sequence[float],
    n_iter: int = 10_000,
    seed: int = 42,
    delta_max_aceitavel: float = 0.05,
    p_valor_max: float = 0.10,
) -> ResultadoGate:
    """Avalia se gate pode ser aceito segundo critério Helena P1.4.

    Args:
        briers_tune: brier por evento no split tune (com config vencedora aplicada).
        briers_gate: brier por evento no split gate (com mesma config).
        n_iter: iterações bootstrap. Default 10k (recomendação Helena).
        seed: para reprodutibilidade.
        delta_max_aceitavel: limite superior do IC 95% para aceite.
        p_valor_max: significância máxima da hipótese "gate degrada".

    Returns:
        ResultadoGate com decisão e estatísticas.
    """
    briers_tune = list(briers_tune)
    briers_gate = list(briers_gate)
    if not briers_tune or not briers_gate:
        return ResultadoGate(
            aceito=False, razao="briers vazios",
            brier_tune=0.0, brier_gate=0.0,
            delta_observado=0.0, ic_95_inferior=0.0, ic_95_superior=0.0,
            p_valor_unilateral=1.0, n_iter=0,
            n_tune=len(briers_tune), n_gate=len(briers_gate),
        )

    rng = random.Random(seed)
    brier_t = _media(briers_tune)
    brier_g = _media(briers_gate)
    delta_obs = brier_g - brier_t

    deltas = _bootstrap_delta(briers_tune, briers_gate, n_iter, rng)
    ic_low = _percentile(deltas, 0.025)
    ic_high = _percentile(deltas, 0.975)

    # P-valor unilateral: P(delta > delta_max_aceitavel) sob H0
    # H0: gate degrada significativamente (delta > delta_max_aceitavel).
    # Rejeitamos H0 se a fração da distribuição BS acima de delta_max_aceitavel
    # for pequena.
    n_acima = sum(1 for d in deltas if d > delta_max_aceitavel)
    p_valor = n_acima / len(deltas) if deltas else 1.0

    # Critérios:
    cond_ic = ic_high < delta_max_aceitavel
    cond_pvalor = p_valor < p_valor_max
    aceito = cond_ic and cond_pvalor

    if aceito:
        razao = (f"aceito: IC95% superior {ic_high:.4f} < {delta_max_aceitavel} "
                 f"E p-valor {p_valor:.4f} < {p_valor_max}")
    else:
        falhas = []
        if not cond_ic:
            falhas.append(f"IC95% superior {ic_high:.4f} >= {delta_max_aceitavel}")
        if not cond_pvalor:
            falhas.append(f"p-valor {p_valor:.4f} >= {p_valor_max}")
        razao = "REPROVADO: " + " E ".join(falhas)

    return ResultadoGate(
        aceito=aceito, razao=razao,
        brier_tune=brier_t, brier_gate=brier_g,
        delta_observado=delta_obs,
        ic_95_inferior=ic_low, ic_95_superior=ic_high,
        p_valor_unilateral=p_valor,
        n_iter=n_iter, n_tune=len(briers_tune), n_gate=len(briers_gate),
    )


def skill_score(brier_modelo: float, brier_referencia: float) -> float:
    """Skill score = 1 - (brier_modelo / brier_referencia).

    Helena P2.5: métrica primária da campanha. >0 significa que o modelo
    bate o baseline; <0 significa que perde para chute aleatório informado.
    """
    if brier_referencia <= 0:
        return 0.0
    return 1.0 - (brier_modelo / brier_referencia)


def skill_score_ic(
    briers_modelo: Sequence[float],
    briers_referencia: Sequence[float],
    n_iter: int = 10_000,
    seed: int = 42,
) -> dict:
    """Bootstrap IC 95% para skill score.

    Helena exige IC 95% que NÃO cruze zero para o claim ser defensável.
    """
    briers_modelo = list(briers_modelo)
    briers_referencia = list(briers_referencia)
    if not briers_modelo or not briers_referencia:
        return {"erro": "briers vazios"}

    rng = random.Random(seed)
    n_m = len(briers_modelo)
    n_r = len(briers_referencia)

    scores: list[float] = []
    for _ in range(n_iter):
        sm = [briers_modelo[rng.randrange(n_m)] for _ in range(n_m)]
        sr = [briers_referencia[rng.randrange(n_r)] for _ in range(n_r)]
        scores.append(skill_score(_media(sm), _media(sr)))

    pontual = skill_score(_media(briers_modelo), _media(briers_referencia))
    return {
        "skill_score_pontual": pontual,
        "ic_95_inferior": _percentile(scores, 0.025),
        "ic_95_superior": _percentile(scores, 0.975),
        "exclui_zero": (_percentile(scores, 0.025) > 0) or (_percentile(scores, 0.975) < 0),
        "n_iter": n_iter,
        "n_modelo": n_m,
        "n_referencia": n_r,
    }
