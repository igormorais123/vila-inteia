# -*- coding: utf-8 -*-
"""
Bridge entre Vila INTEIA e OSA (Optimal System Agent).

Integra capacidades do OSA onde agregam valor real:
- Signal Theory: classificar complexidade para rotear modelo
- Web Search: grounding de sínteses com notícias reais
- Vault Memory: persistência de insights entre sessões

O OSA roda na URL definida em OSA_URL e usa OmniRoute como provider.
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

OSA_URL = os.getenv("OSA_URL", "http://localhost:8089")
OSA_TIMEOUT = int(os.getenv("OSA_TIMEOUT", "30"))
OSA_HABILITADO = os.getenv("OSA_HABILITADO", "true").lower() == "true"


class OSABridge:
    """Interface entre Vila INTEIA e OSA."""

    def __init__(self, url: str = OSA_URL):
        self.url = url
        self.habilitado = OSA_HABILITADO
        self._online: Optional[bool] = None

    async def _check_online(self) -> bool:
        """Verifica se OSA está respondendo."""
        if self._online is not None:
            return self._online
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.url}/health")
                self._online = resp.status_code == 200
        except Exception:
            self._online = False
        return self._online

    # =========================================================================
    # Signal Theory — Classificar complexidade da conversa
    # =========================================================================

    async def classificar_complexidade(self, topico: str) -> float:
        """Retorna weight 0.0-1.0 via Signal Theory do OSA.

        Usado em conversar.py para decidir se usa modelo elite ou gratuito.
        - weight < 0.2: conversa trivial → BestFREE ou heurística
        - weight 0.2-0.6: conversa normal → osa-specialist
        - weight > 0.6: debate profundo → osa-elite
        """
        if not self.habilitado or not await self._check_online():
            return 0.3  # fallback: complexidade média

        try:
            async with httpx.AsyncClient(timeout=OSA_TIMEOUT) as client:
                resp = await client.post(
                    f"{self.url}/api/v1/classify",
                    json={"message": topico},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    signal = data.get("signal", {})
                    weight = signal.get("weight", 0.3)
                    logger.debug("[OSA] classify '%s' → weight=%.2f", topico[:50], weight)
                    return weight
        except Exception as e:
            logger.warning("[OSA] classify falhou: %s", e)

        return 0.3

    def modelo_por_complexidade(self, weight: float) -> str:
        """Retorna combo OmniRoute baseado no weight do Signal Theory."""
        if weight >= 0.6:
            return "osa-elite"
        elif weight >= 0.2:
            return "osa-specialist"
        return "BestFREE"

    # =========================================================================
    # Web Search — Grounding de sínteses com notícias
    # =========================================================================

    async def buscar_noticias(self, topico: str, max_resultados: int = 5) -> list[dict]:
        """Busca notícias recentes via OSA web_search.

        Usado em sintetizar.py para enriquecer sínteses com dados reais.
        Retorna lista de {titulo, snippet, fonte}.
        """
        if not self.habilitado or not await self._check_online():
            return []

        try:
            async with httpx.AsyncClient(timeout=OSA_TIMEOUT) as client:
                resp = await client.post(
                    f"{self.url}/api/v1/orchestrate",
                    json={
                        "input": f"Busque notícias recentes sobre: {topico}. "
                                 f"Retorne apenas os {max_resultados} resultados mais relevantes.",
                    },
                )
                if resp.status_code in (200, 202):
                    data = resp.json()
                    content = data.get("content") or data.get("response", "")
                    if content and content != "...":
                        return [{"tipo": "noticia", "conteudo": content, "fonte": "OSA web_search"}]
        except Exception as e:
            logger.warning("[OSA] buscar_noticias falhou: %s", e)

        return []

    # =========================================================================
    # Vault — Persistência de insights entre sessões
    # =========================================================================

    async def salvar_insights(self, persona_id: str, insights: list[dict]) -> bool:
        """Salva insights no Vault do OSA para próxima sessão.

        Usado em simulacao.py no checkpoint de persistência.
        """
        if not self.habilitado or not await self._check_online():
            return False

        try:
            for insight in insights[:10]:  # max 10 por persona
                async with httpx.AsyncClient(timeout=OSA_TIMEOUT) as client:
                    await client.post(
                        f"{self.url}/api/v1/orchestrate",
                        json={
                            "input": f"Lembre: o consultor {persona_id} concluiu: "
                                     f"{insight.get('descricao', '')}",
                        },
                    )
            logger.info("[OSA] %d insights salvos para %s", len(insights), persona_id)
            return True
        except Exception as e:
            logger.warning("[OSA] salvar_insights falhou: %s", e)
            return False

    async def carregar_insights(self, persona_id: str, topico: str = "") -> list[str]:
        """Carrega insights do Vault do OSA da sessão anterior.

        Usado em persona.__init__() para injetar memória prévia.
        """
        if not self.habilitado or not await self._check_online():
            return []

        try:
            async with httpx.AsyncClient(timeout=OSA_TIMEOUT) as client:
                resp = await client.post(
                    f"{self.url}/api/v1/orchestrate",
                    json={
                        "input": f"O que você lembra sobre o consultor {persona_id}? "
                                 f"Contexto: {topico}" if topico else
                                 f"O que você lembra sobre o consultor {persona_id}?",
                    },
                )
                if resp.status_code in (200, 202):
                    data = resp.json()
                    content = data.get("content") or data.get("response", "")
                    if content and content != "...":
                        return [content]
        except Exception as e:
            logger.warning("[OSA] carregar_insights falhou: %s", e)

        return []


# Singleton
osa = OSABridge()
