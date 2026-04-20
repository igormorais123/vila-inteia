"""
Webhook notifier (Onda 48).

Envia notificações HTTP quando eventos críticos ocorrem:
    - Mule detectado (anomalia psico-história)
    - Urgência crítica recomendação (múltiplos Mules)
    - Auto-calibrador disparou
    - Desafio concluído

Compatível Slack/Discord incoming webhooks (formato {text: "..."} ou {content: "..."}).
Config via env VILA_WEBHOOK_URL (vazio = desabilitado).
"""

from __future__ import annotations

import os
import json
import time
import threading
from urllib.request import Request, urlopen
from urllib.error import URLError
from dataclasses import dataclass, field


VILA_WEBHOOK_URL = os.getenv("VILA_WEBHOOK_URL", "")
VILA_WEBHOOK_FORMATO = os.getenv("VILA_WEBHOOK_FORMATO", "slack")  # slack|discord|generic
VILA_NOTIFY_MULES = os.getenv("VILA_NOTIFY_MULES", "1") == "1"
VILA_NOTIFY_CRITICO = os.getenv("VILA_NOTIFY_CRITICO", "1") == "1"


@dataclass
class NotificacaoRegistro:
    tipo: str
    mensagem: str
    timestamp: float = field(default_factory=time.time)
    sucesso: bool = False
    http_code: int = 0


class Notifier:
    def __init__(self, webhook_url: str = "", formato: str = "slack"):
        self.webhook_url = webhook_url
        self.formato = formato
        self._historico: list[NotificacaoRegistro] = []
        self._lock = threading.Lock()
        self._taxas: dict[str, float] = {}   # último envio por tipo (anti-flood)
        self._min_intervalo_s = 30            # mesmo tipo: min 30s

    @property
    def ativo(self) -> bool:
        return bool(self.webhook_url)

    def _formatar_payload(self, mensagem: str) -> dict:
        if self.formato == "slack":
            return {"text": mensagem}
        if self.formato == "discord":
            return {"content": mensagem}
        return {"message": mensagem, "timestamp": time.time()}

    def enviar(self, tipo: str, mensagem: str, force: bool = False) -> NotificacaoRegistro:
        reg = NotificacaoRegistro(tipo=tipo, mensagem=mensagem)
        if not self.ativo:
            with self._lock:
                self._historico.append(reg)
            return reg

        # Anti-flood
        agora = time.time()
        if not force:
            with self._lock:
                ultima = self._taxas.get(tipo, 0)
                if agora - ultima < self._min_intervalo_s:
                    return reg
                self._taxas[tipo] = agora

        try:
            payload = self._formatar_payload(mensagem)
            req = Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=5) as resp:
                reg.sucesso = True
                reg.http_code = resp.status
        except URLError as e:
            reg.http_code = getattr(e, "code", 0)
        except Exception:
            pass

        with self._lock:
            self._historico.append(reg)
            self._historico = self._historico[-100:]   # podagem
        return reg

    def notificar_mule(self, mule: dict, step: int) -> NotificacaoRegistro:
        if not VILA_NOTIFY_MULES:
            return NotificacaoRegistro(tipo="mule", mensagem="", sucesso=False)
        z = mule.get("z_score", 0)
        desc = mule.get("descricao", "?")[:80]
        msg = f"🚨 Vila Mule @ step {step} (z={z:.2f}): {desc}"
        return self.enviar("mule", msg)

    def notificar_recomendacao_critica(self, estado: str, destino: str, n_mules: int) -> NotificacaoRegistro:
        if not VILA_NOTIFY_CRITICO:
            return NotificacaoRegistro(tipo="critico", mensagem="", sucesso=False)
        msg = f"⚠️ Vila URGÊNCIA CRÍTICA: estado={estado}, destino={destino}, mules={n_mules}"
        return self.enviar("critico", msg)

    def notificar_calibracao(self, step: int, ganho_pct: float) -> NotificacaoRegistro:
        msg = f"✓ Vila calibração @ step {step}: ganho perplexity {ganho_pct:.1f}%"
        return self.enviar("calibracao", msg)

    def stats(self) -> dict:
        with self._lock:
            from collections import Counter
            tipos = Counter(r.tipo for r in self._historico)
            sucesso = sum(1 for r in self._historico if r.sucesso)
            return {
                "ativo": self.ativo,
                "formato": self.formato,
                "total_enviadas": len(self._historico),
                "total_sucesso": sucesso,
                "por_tipo": dict(tipos),
                "webhook_url_configurada": bool(self.webhook_url),
            }


NOTIFIER_GLOBAL = Notifier(VILA_WEBHOOK_URL, VILA_WEBHOOK_FORMATO)
