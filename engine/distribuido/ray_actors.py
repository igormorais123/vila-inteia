"""
Ray Actors para paralelização de personas (esqueleto).

Import de `ray` é guard — funciona sem ray instalado (modo fallback síncrono).
"""

from __future__ import annotations

from typing import Any

try:
    import ray
    RAY_OK = True
except ImportError:
    ray = None
    RAY_OK = False


if RAY_OK:
    @ray.remote
    class PersonaActor:
        """
        Actor isolado. Cada instância roda ciclo cognitivo de 1 persona
        independentemente, permitindo paralelização em cluster.
        """
        def __init__(self, persona_id: str, tier: str = "cold"):
            self.persona_id = persona_id
            self.tier = tier

        def step(self, estado_mundo: dict) -> dict:
            # Aqui caberia integração com engine.cognitivo pipeline real.
            # Versão inicial: retorna ação dummy para validar infra.
            return {
                "persona_id": self.persona_id,
                "tier": self.tier,
                "acao": "aguardar",
                "status": "skeleton_only",
            }

        def set_tier(self, tier: str) -> None:
            self.tier = tier
else:
    class PersonaActor:
        """Stub síncrono quando ray não está disponível."""
        def __init__(self, persona_id: str, tier: str = "cold"):
            self.persona_id = persona_id
            self.tier = tier
        def step(self, estado_mundo: dict) -> dict:
            return {
                "persona_id": self.persona_id,
                "tier": self.tier,
                "acao": "aguardar",
                "status": "sync_fallback",
            }
        def set_tier(self, tier: str) -> None:
            self.tier = tier


def coordinator_step(actors: list, estado_mundo: dict) -> list[dict]:
    """
    Executa 1 step em todos os actors em paralelo (se Ray) ou serial (fallback).
    """
    if RAY_OK:
        futures = [a.step.remote(estado_mundo) for a in actors]
        return ray.get(futures)
    else:
        return [a.step(estado_mundo) for a in actors]
