"""
engine.backtest — testa poder preditivo da Vila contra datasets históricos.

Onda 5. Compara simulação a partir de t=T0 contra outcome real em t=T_real.
Métricas: Brier score, log-loss, AUC, accuracy.

Uso:
    from engine.backtest import rodar_backtest, Brier
    r = rodar_backtest(dataset="eleicao_municipal_sp_2024", n_sims=5)
    print(f"Brier: {r.brier:.3f}, log-loss: {r.log_loss:.3f}")
"""

from engine.backtest.dataset import carregar_dataset, DatasetBacktest, EventoHistorico
from engine.backtest.metricas import brier_score, log_loss, accuracy_binaria
from engine.backtest.runner import rodar_backtest, ResultadoBacktest

__all__ = [
    "carregar_dataset",
    "DatasetBacktest",
    "EventoHistorico",
    "brier_score",
    "log_loss",
    "accuracy_binaria",
    "rodar_backtest",
    "ResultadoBacktest",
]
