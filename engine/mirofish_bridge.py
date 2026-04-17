"""
Bridge Mirofish — motor de simulação de rede social com grafos.

Mirofish (https://github.com/.../Mirofish-INTEIA) é o motor usado pela Vila
para rodar simulação de rede social. Faz:
  - Construção de grafo de conhecimento (entidades + relações)
  - Perfis de agentes (baseado em OASIS)
  - Simulação paralela de dinâmicas sociais
  - Relatório executivo com insights

Config via env:
    MIROFISH_API_URL   — http://host:5001  (endpoint Flask Mirofish)
    MIROFISH_TIMEOUT_S — 60 (default)

Endpoints consumidos:
    POST /api/graph/upload              — upload de corpus (docs da Vila)
    GET  /api/graph/project/<id>
    POST /api/simulation/run            — inicia simulação com habitantes
    GET  /api/simulation/status?id=...
    POST /api/report/generate
    GET  /api/report/<id>

Integração Vila ←→ Mirofish:
  - Habitantes Vila → perfis OASIS no Mirofish
  - Workspace Vila → corpus para grafo Mirofish
  - Resultado Mirofish → insight publicado na rede social Vila e/ou matéria no Mirante
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger("vila-inteia.mirofish")

MIROFISH_API_URL = os.getenv("MIROFISH_API_URL", "").rstrip("/")
MIROFISH_TIMEOUT_S = int(os.getenv("MIROFISH_TIMEOUT_S", "60"))


# =========================================================
# Dataclasses
# =========================================================

@dataclass
class GrafoMirofish:
    graph_id: str
    total_entidades: int = 0
    total_relacoes: int = 0
    status: str = "pronto"


@dataclass
class SimulacaoMirofish:
    simulation_id: str
    status: str = "rodando"   # rodando | concluida | erro
    graph_id: str = ""
    progresso: float = 0.0
    resultado: dict = field(default_factory=dict)


@dataclass
class RelatorioMirofish:
    report_id: str
    conteudo: str = ""
    insights: list = field(default_factory=list)
    gerado_em: str = ""


# =========================================================
# Cliente HTTP leve
# =========================================================

def _request(method: str, path: str, data: Optional[dict] = None,
             timeout: Optional[int] = None) -> Optional[dict]:
    if not MIROFISH_API_URL:
        logger.error("MIROFISH_API_URL não configurado")
        return None

    url = f"{MIROFISH_API_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "vila-inteia-bridge/1.0",
    }
    body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data else None
    req = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(req, timeout=timeout or MIROFISH_TIMEOUT_S) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else {}
    except HTTPError as e:
        corpo = e.read().decode("utf-8", errors="ignore")[:400]
        logger.error(f"Mirofish HTTP {e.code}: {corpo}")
        return None
    except URLError as e:
        logger.error(f"Mirofish URL error: {e.reason}")
        return None
    except Exception as e:
        logger.error(f"Mirofish bridge: {type(e).__name__}: {e}")
        return None


# =========================================================
# Grafo
# =========================================================

def upload_corpus(corpus: list[dict]) -> Optional[GrafoMirofish]:
    """
    Envia corpus (ex: matérias e debates da Vila) para Mirofish montar grafo.
    corpus = [{titulo, conteudo, autor, data}, ...]
    """
    resp = _request("POST", "/api/graph/upload", {"docs": corpus})
    if not resp:
        return None
    return GrafoMirofish(
        graph_id=resp.get("graph_id", ""),
        total_entidades=resp.get("total_entidades", 0),
        total_relacoes=resp.get("total_relacoes", 0),
        status=resp.get("status", "pronto"),
    )


def obter_grafo(graph_id: str) -> Optional[dict]:
    return _request("GET", f"/api/graph/project/{graph_id}")


# =========================================================
# Simulação
# =========================================================

def iniciar_simulacao(
    graph_id: str,
    habitantes: list[dict],
    cenario: str = "",
    steps: int = 20,
) -> Optional[SimulacaoMirofish]:
    """
    Dispara simulação Mirofish com habitantes da Vila como perfis OASIS.

    habitantes = [{id, nome, personalidade, categoria, ...}]
    cenario = descrição livre do cenário a simular (ex: "eleição municipal")
    """
    payload = {
        "graph_id": graph_id,
        "agents": habitantes,
        "scenario": cenario,
        "steps": steps,
    }
    resp = _request("POST", "/api/simulation/run", payload, timeout=90)
    if not resp:
        return None
    return SimulacaoMirofish(
        simulation_id=resp.get("simulation_id", ""),
        status=resp.get("status", "rodando"),
        graph_id=graph_id,
    )


def status_simulacao(simulation_id: str) -> Optional[SimulacaoMirofish]:
    resp = _request("GET", f"/api/simulation/status?id={simulation_id}")
    if not resp:
        return None
    return SimulacaoMirofish(
        simulation_id=simulation_id,
        status=resp.get("status", "rodando"),
        graph_id=resp.get("graph_id", ""),
        progresso=resp.get("progresso", 0.0),
        resultado=resp.get("resultado", {}),
    )


# =========================================================
# Relatório
# =========================================================

def gerar_relatorio(simulation_id: str) -> Optional[RelatorioMirofish]:
    resp = _request("POST", "/api/report/generate",
                    {"simulation_id": simulation_id}, timeout=120)
    if not resp:
        return None
    return RelatorioMirofish(
        report_id=resp.get("report_id", ""),
        conteudo=resp.get("conteudo", ""),
        insights=resp.get("insights", []),
        gerado_em=resp.get("gerado_em", ""),
    )


def obter_relatorio(report_id: str) -> Optional[RelatorioMirofish]:
    resp = _request("GET", f"/api/report/{report_id}")
    if not resp:
        return None
    return RelatorioMirofish(
        report_id=report_id,
        conteudo=resp.get("conteudo", ""),
        insights=resp.get("insights", []),
        gerado_em=resp.get("gerado_em", ""),
    )


# =========================================================
# Pipeline completo (helper para a Vila)
# =========================================================

def simular_rede_social(
    corpus: list[dict],
    habitantes: list[dict],
    cenario: str = "",
    steps: int = 20,
) -> dict:
    """
    Pipeline Vila → Mirofish → relatório de uma vez só.
    Síncrono. Para uso interativo use as chamadas individuais.
    """
    grafo = upload_corpus(corpus)
    if not grafo or not grafo.graph_id:
        return {"erro": "falha ao montar grafo"}

    sim = iniciar_simulacao(grafo.graph_id, habitantes, cenario, steps)
    if not sim or not sim.simulation_id:
        return {"erro": "falha ao iniciar simulação", "graph_id": grafo.graph_id}

    # NOTA: versão simples aguarda síncrono — em prod, poll assíncrono
    import time
    for _ in range(60):
        st = status_simulacao(sim.simulation_id)
        if st and st.status in ("concluida", "erro"):
            sim = st
            break
        time.sleep(5)

    if sim.status != "concluida":
        return {"erro": "simulação não concluiu", "simulation_id": sim.simulation_id}

    rel = gerar_relatorio(sim.simulation_id)
    return {
        "graph_id": grafo.graph_id,
        "simulation_id": sim.simulation_id,
        "report_id": rel.report_id if rel else "",
        "insights": rel.insights if rel else [],
        "conteudo": rel.conteudo if rel else "",
    }


def status_integracao() -> dict:
    return {
        "api_configurada": bool(MIROFISH_API_URL),
        "api_url": MIROFISH_API_URL or None,
        "timeout_s": MIROFISH_TIMEOUT_S,
    }
