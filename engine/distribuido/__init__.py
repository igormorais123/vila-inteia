"""
engine.distribuido — escala horizontal via Ray + vLLM (Onda 9, esqueleto).

Arquitetura planejada:
    - Ray Actors para cada persona (1 actor por habitante)
    - Coordinator central gerencia step barrier
    - Hot tier (5 %): agentes LLM-backed, rotacional
    - Cold tier (95 %): agentes puramente heurísticos (FluxoMemoria + regras)
    - Endpoint vLLM local (self-hosted Llama 3.3 70B 4-bit)

Esta versão inicial é esqueleto. Implementação completa requer cluster Ray.
"""

from engine.distribuido.tiers import classificar_tier, TierClassifier, HOT, COLD
from engine.distribuido.ray_actors import PersonaActor, coordinator_step
from engine.distribuido.vllm_client import VLLMClient

__all__ = [
    "classificar_tier",
    "TierClassifier",
    "HOT",
    "COLD",
    "PersonaActor",
    "coordinator_step",
    "VLLMClient",
]
