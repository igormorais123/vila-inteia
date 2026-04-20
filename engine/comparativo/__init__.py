"""
engine.comparativo — framework A/B de simulações paralelas (Onda 29).

Permite rodar múltiplas Vilas com parâmetros distintos, comparar estatisticamente:
    - Trajetória de estados
    - Convergência de crenças
    - Métricas econômicas
    - Divergência KL/TV

Útil para responder: "se eu mudar X, acontece Y de fato?"
"""

from engine.comparativo.runner import (
    ConfigSimComparativa,
    ResultadoComparativo,
    rodar_comparativo,
)
from engine.comparativo.metricas import (
    comparar_trajetorias,
    diferenca_convergencia,
)

__all__ = [
    "ConfigSimComparativa",
    "ResultadoComparativo",
    "rodar_comparativo",
    "comparar_trajetorias",
    "diferenca_convergencia",
]
