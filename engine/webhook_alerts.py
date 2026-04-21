"""
Onda 117: webhook alerts (Discord/Slack/generic).

Envia POST a webhook URL quando evento crítico:
- Mule detectado (anomalia psico-histórica)
- Circuit breaker abre (LLM provider falhou)
- Brier skill score < threshold após backtest
- Sim step parado (uptime check degrade)

Config via env:
  VILA_WEBHOOK_URL: webhook HTTP (Discord/Slack/custom)
  VILA_WEBHOOK_FORMAT: "discord" | "slack" | "generic" (default: generic)
  VILA_WEBHOOK_TIMEOUT_S: 5

Sem deps externas. Usa urllib.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Any

logger = logging.getLogger(__name__)

_RATE_LIMIT_S = 60  # Min between same-type alerts
_LAST_SENT: dict[str, float] = {}


def _dedupe(tipo: str) -> bool:
    """True se enviar (não estava dentro janela rate limit)."""
    agora = time.monotonic()
    ultimo = _LAST_SENT.get(tipo, 0)
    if agora - ultimo < _RATE_LIMIT_S:
        return False
    _LAST_SENT[tipo] = agora
    return True


def _format_discord(titulo: str, msg: str, cor: int = 0xd69e2e) -> dict:
    return {
        "username": "Vila INTEIA",
        "embeds": [{
            "title": titulo,
            "description": msg,
            "color": cor,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }],
    }


def _format_slack(titulo: str, msg: str, cor: str = "warning") -> dict:
    return {
        "text": titulo,
        "attachments": [{
            "color": cor,
            "text": msg,
            "ts": int(time.time()),
        }],
    }


def _format_generic(titulo: str, msg: str, **kwargs) -> dict:
    return {
        "titulo": titulo, "mensagem": msg,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **kwargs,
    }


def enviar_alerta(
    tipo: str,
    titulo: str,
    msg: str,
    nivel: str = "warn",
    extra: dict | None = None,
    webhook_url: str | None = None,
) -> dict:
    """
    Envia alerta ao webhook. tipo: identificador para dedup (ex: "mule", "circuit").
    nivel: "info" | "warn" | "critical".
    Retorna dict com ok/sent/dedup/erro.
    """
    if not _dedupe(tipo):
        return {"ok": True, "dedup": True, "sent": False}

    url = webhook_url or os.getenv("VILA_WEBHOOK_URL", "")
    if not url:
        return {"ok": True, "sent": False, "motivo": "VILA_WEBHOOK_URL vazio"}

    fmt = os.getenv("VILA_WEBHOOK_FORMAT", "generic").lower()
    cores_d = {"info": 0x3b82f6, "warn": 0xeab308, "critical": 0xef4444}
    cores_s = {"info": "good", "warn": "warning", "critical": "danger"}

    if fmt == "discord":
        payload = _format_discord(titulo, msg, cor=cores_d.get(nivel, 0xd69e2e))
    elif fmt == "slack":
        payload = _format_slack(titulo, msg, cor=cores_s.get(nivel, "warning"))
    else:
        payload = _format_generic(titulo, msg, nivel=nivel, **(extra or {}))

    try:
        timeout = float(os.getenv("VILA_WEBHOOK_TIMEOUT_S", "5"))
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"ok": True, "sent": True, "status": resp.status}
    except urllib.error.HTTPError as e:
        logger.debug(f"webhook HTTP {e.code}: {e.reason}")
        return {"ok": False, "sent": False, "erro": f"HTTP {e.code}"}
    except urllib.error.URLError as e:
        logger.debug(f"webhook URL error: {e}")
        return {"ok": False, "sent": False, "erro": str(e.reason)[:80]}
    except Exception as e:
        logger.debug(f"webhook excep: {e}")
        return {"ok": False, "sent": False, "erro": str(e)[:80]}


def alerta_mule(mule: dict) -> dict:
    """Alert tipo 'mule' — anomalia psico-histórica."""
    return enviar_alerta(
        tipo="mule",
        titulo="🚨 Mule detectado (Vila INTEIA)",
        msg=f"Anomalia psico-histórica no step {mule.get('step', '?')}: "
            f"{mule.get('tipo', 'anomalia')}",
        nivel="warn",
        extra={"mule": mule},
    )


def alerta_circuit_aberto(provider: str, falhas: int) -> dict:
    return enviar_alerta(
        tipo="circuit",
        titulo="🔌 Circuit breaker aberto",
        msg=f"Provider {provider} falhou {falhas}x. Sim degrada pra heurístico.",
        nivel="warn",
    )


def alerta_skill_negativo(skill: float, limite: float = 0.0) -> dict:
    return enviar_alerta(
        tipo="skill_neg",
        titulo="📉 Skill score abaixo do limite",
        msg=f"Brier skill vs prior = {skill:.3f} < {limite}. "
            f"Vila pior que baseline humano.",
        nivel="critical",
        extra={"skill": skill, "limite": limite},
    )


def alerta_sim_parada(step: int, ultima_atividade_s: float) -> dict:
    return enviar_alerta(
        tipo="sim_parada",
        titulo="⏸ Sim potencialmente parada",
        msg=f"Step estagnado em {step} por {ultima_atividade_s:.0f}s. Verificar.",
        nivel="warn",
    )


def resetar_dedup():
    """Test helper."""
    _LAST_SENT.clear()
