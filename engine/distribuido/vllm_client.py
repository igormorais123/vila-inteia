"""
Cliente vLLM local (OpenAI-compatible API).

Permite roteamento de chamadas LLM para endpoint self-hosted
(Llama 3.3 70B 4-bit em GPU), reduzindo custo marginal a zero.

Config via env:
    VLLM_URL    — base URL do servidor vLLM (ex: http://localhost:8000/v1)
    VLLM_MODEL  — modelo a usar (ex: meta-llama/Llama-3.3-70B-Instruct)
"""

from __future__ import annotations

import os
import json
from urllib.request import Request, urlopen
from urllib.error import URLError


class VLLMClient:
    def __init__(self,
                 url: str | None = None,
                 modelo: str | None = None,
                 timeout: int = 60):
        self.url = (url or os.getenv("VLLM_URL", "")).rstrip("/")
        self.modelo = modelo or os.getenv("VLLM_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
        self.timeout = timeout

    @property
    def disponivel(self) -> bool:
        return bool(self.url)

    def completar(self, mensagens: list[dict], max_tokens: int = 500, temperatura: float = 0.7) -> str | None:
        """
        Chamada OpenAI-compatible: /chat/completions.
        Retorna texto ou None em falha.
        """
        if not self.disponivel:
            return None
        payload = {
            "model": self.modelo,
            "messages": mensagens,
            "max_tokens": max_tokens,
            "temperature": temperatura,
        }
        req = Request(
            f"{self.url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except (URLError, KeyError, json.JSONDecodeError):
            return None
