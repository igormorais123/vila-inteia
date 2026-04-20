"""
engine.opinion_dynamics — modelagem analítica de crenças e polarização.

Módulos:
    degroot            — consensus linear (DeGroot 1974)
    bounded_confidence — Deffuant-Weisbuch, Hegselmann-Krause
    cascatas           — Bikhchandani-Hirshleifer-Welch info cascade
    bayesiano          — Bayesian belief update
    social_impact      — Nowak-Latane social impact theory
"""

from engine.opinion_dynamics.degroot import degroot_step, degroot_convergencia
from engine.opinion_dynamics.bounded_confidence import deffuant_step, hk_step
from engine.opinion_dynamics.cascatas import bikhchandani
from engine.opinion_dynamics.bayesiano import atualizar_crenca_bayes
from engine.opinion_dynamics.social_impact import impacto_social

__all__ = [
    "degroot_step",
    "degroot_convergencia",
    "deffuant_step",
    "hk_step",
    "bikhchandani",
    "atualizar_crenca_bayes",
    "impacto_social",
]
