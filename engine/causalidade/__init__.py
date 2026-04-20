"""
engine.causalidade — inferência causal à la Pearl (Onda 28).

Operações principais:
    - do(X=x): intervenção que força variável X a valor x
    - counterfactual: Y|do(X=x') se fosse x em vez de x'
    - intervention sweep: varre valores, mede efeito em Y
    - average treatment effect (ATE)

Uso na Vila:
    Cenário: "se Diabob não provocar no step N, o consenso muda?"
    — Substitui provocação por ação neutra (do), roda sim, compara estados.
"""

from engine.causalidade.pearl import (
    intervir,
    counterfactual,
    ate,
    intervention_sweep,
    VariavelCausal,
)

__all__ = [
    "intervir",
    "counterfactual",
    "ate",
    "intervention_sweep",
    "VariavelCausal",
]
