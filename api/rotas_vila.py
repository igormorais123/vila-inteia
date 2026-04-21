"""
API REST da Vila INTEIA.

Endpoints para controlar e observar a simulação.
Pode ser integrado ao backend principal ou rodar standalone.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel

try:
    from ..engine.auth_middleware import auth_e_rate, rate_limit
except (ImportError, ValueError):
    from engine.auth_middleware import auth_e_rate, rate_limit

try:
    from ..engine.simulacao import SimulacaoVila
    from ..config import config
except (ImportError, ValueError):
    from engine.simulacao import SimulacaoVila
    from config import config


# ============================================================
# ESTADO GLOBAL DA SIMULAÇÃO
# ============================================================

import threading

simulacao: Optional[SimulacaoVila] = None
_sim_lock = threading.Lock()


def obter_simulacao() -> SimulacaoVila:
    """Retorna a simulação ativa ou cria uma nova.

    Onda 73: env VILA_MAX_AGENTES limita N personas (default 140 = todos).
    Pra rodar sim com LLM real menos lenta, usar 20-40.
    """
    global simulacao
    if simulacao is None:
        with _sim_lock:
            if simulacao is None:
                import os as _os
                max_ag = int(_os.getenv("VILA_MAX_AGENTES", "140"))
                simulacao = SimulacaoVila(nome="vila_inteia_default")
                simulacao.inicializar(max_agentes=max_ag)
    return simulacao


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(prefix="/api/v1/vila", tags=["Vila INTEIA"])


# --- Modelos de Request ---

class IniciarRequest(BaseModel):
    nome: str = "vila_inteia"
    max_agentes: int = 140


class StepRequest(BaseModel):
    n_steps: int = 1


class TopicoRequest(BaseModel):
    topico: str
    importancia: int = 8


# ============================================================
# ENDPOINTS DE CONTROLE
# ============================================================

@router.post("/iniciar")
async def iniciar_simulacao(req: IniciarRequest):
    """Inicializa uma nova simulação."""
    global simulacao
    simulacao = SimulacaoVila(nome=req.nome)
    simulacao.inicializar(max_agentes=req.max_agentes)
    return {
        "status": "ok",
        "mensagem": f"Simulação '{req.nome}' iniciada com {len(simulacao.personas)} agentes",
        "agentes": len(simulacao.personas),
    }


@router.post("/step")
async def executar_steps(req: StepRequest):
    """Executa N steps da simulação."""
    sim = obter_simulacao()
    resumos = sim.executar(n_steps=req.n_steps)
    return {
        "status": "ok",
        "steps_executados": len(resumos),
        "step_atual": sim.step,
        "hora_atual": sim.hora_atual.strftime("%Y-%m-%d %H:%M"),
        "resumos": resumos[-5:],  # últimos 5
    }


@router.post("/pausar")
async def pausar():
    """Pausa a simulação."""
    sim = obter_simulacao()
    sim.pausar()
    return {"status": "pausada"}


@router.post("/retomar")
async def retomar():
    """Retoma a simulação."""
    sim = obter_simulacao()
    sim.retomar()
    return {"status": "retomada"}


@router.post("/parar")
async def parar():
    """Para e salva a simulação."""
    sim = obter_simulacao()
    sim.parar()
    return {"status": "parada", "step_final": sim.step}


# ============================================================
# ENDPOINTS DE OBSERVAÇÃO
# ============================================================

@router.get("/estado")
async def estado_mundo():
    """Retorna o estado completo do mundo."""
    sim = obter_simulacao()
    return sim.estado_mundo()


@router.get("/mapa")
async def mapa_calor():
    """Retorna mapa de calor de ocupação dos locais."""
    sim = obter_simulacao()
    return {
        "step": sim.step,
        "hora": sim.hora_atual.strftime("%H:%M"),
        "mapa": sim.mapa_calor(),
    }


@router.get("/agentes")
async def listar_agentes(
    local: Optional[str] = None,
    categoria: Optional[str] = None,
    tier: Optional[str] = None,
):
    """Lista agentes com filtros opcionais."""
    sim = obter_simulacao()
    agentes = []

    for persona in sim.personas.values():
        if local and persona.rascunho.local_atual != local:
            continue
        if categoria and persona.categoria != categoria:
            continue
        if tier and persona.tier != tier:
            continue
        agentes.append(persona.resumo())

    return {
        "total": len(agentes),
        "agentes": agentes,
    }


@router.get("/agente/{agente_id}")
async def detalhe_agente(agente_id: str):
    """Retorna detalhes completos de um agente."""
    sim = obter_simulacao()
    detalhe = sim.consultar_agente(agente_id)
    if not detalhe:
        raise HTTPException(404, f"Agente {agente_id} não encontrado")
    return detalhe


@router.get("/conversas")
async def conversas_recentes(limite: int = Query(10, ge=1, le=50)):
    """Lista conversas recentes."""
    sim = obter_simulacao()
    return {
        "total": len(sim.conversas_recentes),
        "conversas": sim.conversas_recentes[-limite:],
    }


@router.get("/conversas/llm-only")
async def conversas_llm_only(limite: int = Query(20, ge=1, le=100)):
    """
    Lista conversas com 4+ turnos (heurística simples = 2-3 turnos).
    Conversas LLM têm 4-5 turnos com conteúdo rico, heurísticas template
    têm 3 turnos curtos com 'Como eu sempre digo: ...'.
    """
    sim = obter_simulacao()
    convs = sim.conversas_recentes[-limite * 3:]   # filtra mais ampla
    llm_convs = []
    PADROES_HEURISTICA = (
        "Como eu sempre digo",
        "Boa conversa. Devemos continuar",
        "Essa é uma perspectiva válida. Mas considere também",
        "Conte-me mais sobre sua visão",
    )
    for c in convs:
        turnos = c.get("turnos", [])
        if len(turnos) >= 4:
            tem_template = any(
                isinstance(t, (list, tuple)) and len(t) >= 2
                and any(p in str(t[1]) for p in PADROES_HEURISTICA)
                for t in turnos
            )
            if not tem_template:
                llm_convs.append({
                    "parceiro_nome": c.get("parceiro_nome"),
                    "tema": c.get("topico"),
                    "tipo_relacao": c.get("tipo_relacao"),
                    "local": c.get("local_id"),
                    "n_turnos": len(turnos),
                    "turnos": turnos,
                })
        if len(llm_convs) >= limite:
            break
    return {
        "total_filtradas": len(llm_convs),
        "conversas_llm": llm_convs,
    }


@router.get("/conversas/dialogo/{indice}")
async def conversa_dialogo(indice: int):
    """Retorna conversa N como diálogo formatado markdown."""
    sim = obter_simulacao()
    if indice >= len(sim.conversas_recentes) or indice < 0:
        return {"erro": "índice fora do range"}
    c = sim.conversas_recentes[indice]
    linhas = [
        f"# Conversa #{indice}",
        "",
        f"**{c.get('turnos', [['?',''], '?'])[0][0] if c.get('turnos') else '?'}** ↔ **{c.get('parceiro_nome', '?')}**",
        f"",
        f"- Tema: {c.get('topico', '')}",
        f"- Relação: {c.get('tipo_relacao', '')}",
        f"- Local: {c.get('local_id', '')}",
        "",
        "## Turnos",
        "",
    ]
    for t in c.get("turnos", []):
        if isinstance(t, list) and len(t) >= 2:
            linhas.append(f"**{t[0]}**: {t[1]}")
            linhas.append("")
    return {
        "markdown": "\n".join(linhas),
        "raw": c,
    }


@router.get("/sinteses")
async def listar_sinteses():
    """Lista sínteses de inteligência coletiva."""
    sim = obter_simulacao()
    return {
        "total": len(sim.sinteses),
        "sinteses": sim.sinteses[-20:],
    }


@router.get("/forecast-narrativo.pdf")
async def forecast_narrativo_pdf(
    horizonte: int = Query(10, ge=1, le=100),
    com_narrativa: bool = Query(True),
):
    """Onda 105: forecast como PDF download."""
    from fastapi.responses import Response
    from engine.forecast_narrativo import gerar_forecast
    from engine.pdf_export import html_forecast, render_pdf
    sim = obter_simulacao()
    payload = gerar_forecast(
        conversas_recentes=getattr(sim, "conversas_recentes", []),
        horizonte=horizonte, com_narrativa=com_narrativa,
    )
    html = html_forecast(payload)
    pdf = render_pdf(html)
    if pdf is None:
        return Response(content=html, media_type="text/html",
                        headers={"X-Weasyprint-Status": "unavailable"})
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="vila_forecast.pdf"'})


@router.get("/recomendacao-intervencao.pdf")
async def recomendacao_pdf(
    outcome_desejado: str = Query("equilibrio"),
    horizonte: int = Query(20, ge=1, le=100),
    com_recomendacao_llm: bool = Query(True),
):
    """Onda 105: recomendação como PDF download."""
    from fastapi.responses import Response
    from engine.recomendacao_intervencao import gerar_recomendacao
    from engine.pdf_export import html_recomendacao, render_pdf
    try:
        payload = gerar_recomendacao(
            outcome_desejado=outcome_desejado, horizonte=horizonte,
            com_recomendacao_llm=com_recomendacao_llm,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    html = html_recomendacao(payload)
    pdf = render_pdf(html)
    if pdf is None:
        return Response(content=html, media_type="text/html")
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="vila_recomendacao.pdf"'})


@router.get("/forecast-narrativo")
async def forecast_narrativo(
    horizonte: int = Query(10, ge=1, le=100),
    com_narrativa: bool = Query(True),
):
    """
    Onda 78: forecast Markov + evidências LLM + narrativa PT-BR opcional.
    Combina trajetória psico-histórica observada com projeção e síntese narrativa.
    """
    from engine.forecast_narrativo import gerar_forecast
    sim = obter_simulacao()
    return gerar_forecast(
        conversas_recentes=getattr(sim, "conversas_recentes", []),
        horizonte=horizonte,
        com_narrativa=com_narrativa,
    )


class PersonaChatRequest(BaseModel):
    persona_id: str
    pergunta: str
    max_tokens: int = 350
    temperatura: float = 0.75


@router.post("/persona-chat")
async def persona_chat(req: PersonaChatRequest, _=Depends(rate_limit)):
    """
    Onda 86: chat direto com persona lendária (Musk, Buffett, Sun Tzu, etc).
    LLM responde usando system prompt arquétipo profundo.
    Mantém histórico in-memory (últimos 10 turnos por persona).
    """
    from engine.persona_chat import chat_com_persona
    sim = obter_simulacao()
    return chat_com_persona(
        persona_id=req.persona_id,
        pergunta=req.pergunta,
        sim=sim,
        max_tokens=req.max_tokens,
        temperatura=req.temperatura,
    )


class PanelChatRequest(BaseModel):
    persona_ids: list[str]
    pergunta: str
    max_tokens: int = 280
    temperatura: float = 0.75
    paralelo: bool = True


@router.post("/panel-chat")
async def panel_chat_endpoint(req: PanelChatRequest, _=Depends(rate_limit)):
    """
    Onda 89: múltiplas personas respondem mesma pergunta em paralelo.
    Ex: Musk + Buffett + Sun Tzu sobre 'como escalar startup?' → 3 respostas
    lado-a-lado.
    """
    from engine.panel_chat import panel_chat as panel_fn
    sim = obter_simulacao()
    return panel_fn(
        persona_ids=req.persona_ids, pergunta=req.pergunta, sim=sim,
        max_tokens=req.max_tokens, temperatura=req.temperatura,
        paralelo=req.paralelo,
    )


@router.get("/persona-chat/historico/{persona_id}")
async def persona_chat_historico(persona_id: str):
    """Onda 86: retorna histórico de chat com uma persona."""
    from engine.persona_chat import historico_persona_public
    return historico_persona_public(persona_id)


@router.delete("/persona-chat/historico/{persona_id}")
async def persona_chat_reset(persona_id: str):
    """Onda 86: reseta histórico de chat com uma persona."""
    from engine.persona_chat import resetar_historico
    resetar_historico(persona_id)
    return {"ok": True, "persona_id": persona_id}


@router.get("/comunidades-personas")
async def comunidades_personas(resolution: float = Query(1.0, ge=0.1, le=5.0)):
    """
    Onda 84: detecção de comunidades Louvain sobre grafo de conversas.
    Identifica TRIBOS emergentes na Vila.
    """
    from engine.comunidades_personas import detectar_comunidades
    sim = obter_simulacao()
    return detectar_comunidades(
        conversas=getattr(sim, "conversas_recentes", []),
        resolution=resolution,
    )


@router.get("/influencia-personas")
async def influencia_personas(top_n: int = Query(20, ge=1, le=144)):
    """
    Onda 83: ranking de influência baseado em grafo de conversas.
    Centrality scores (degree, betweenness, eigenvector, pagerank).
    Identifica os Primeiros Motores da Vila.
    """
    from engine.influencia_personas import ranking_influencia
    sim = obter_simulacao()
    return ranking_influencia(
        conversas=getattr(sim, "conversas_recentes", []),
        top_n=top_n,
    )


@router.get("/predictive-power")
async def predictive_power(janela: int = Query(100, ge=2, le=10000)):
    """
    Onda 82: Brier + log-loss + skill scores comparando Markov Vila vs
    baselines (random, naive-last-state). Skill > 0 = Vila supera baseline.
    """
    from engine.predictive_power import avaliar_predictive_power
    from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
    estados = list(RASTREADOR_GLOBAL.trajetoria.estados[-janela:])
    return avaliar_predictive_power(estados_observados=estados)


@router.get("/snapshot")
async def snapshot_download():
    """
    Onda 90: exporta state completo da sim como JSON download.
    Use browser: href retorna Content-Disposition pra file dl.
    """
    from fastapi.responses import JSONResponse
    from engine.save_load import _serializar_simulacao
    import time
    sim = obter_simulacao()
    try:
        estado = _serializar_simulacao(sim)
    except Exception as e:
        raise HTTPException(500, f"serializar falhou: {e}")
    step_atual = getattr(sim, "step", 0)
    payload = {
        "vila_id": getattr(sim, "nome", "default"),
        "step": step_atual,
        "exportado_em": int(time.time()),
        "schema_version": 1,
        "estado": estado,
    }
    filename = f"vila_snapshot_step{step_atual}.json"
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/snapshot/ping")
async def snapshot_ping():
    """Health check: retorna step atual e tamanho estimado do snapshot."""
    from engine.save_load import _serializar_simulacao
    import json as _json
    sim = obter_simulacao()
    try:
        estado = _serializar_simulacao(sim)
        size = len(_json.dumps(estado, default=str))
    except Exception as e:
        return {"ok": False, "erro": str(e)}
    return {
        "ok": True,
        "step": getattr(sim, "step", 0),
        "tamanho_bytes_estimado": size,
        "n_personas": len(getattr(sim, "personas", {})),
        "n_conversas_buffer": len(getattr(sim, "conversas_recentes", [])),
    }


class BacktestRequest(BaseModel):
    dataset: Optional[str] = None
    max_eventos: int = 3
    personas: list[str] = ["CL001", "CL002", "CL007"]
    sleep_entre_eventos_s: float = 4.0


_ULTIMO_BACKTEST: dict = {}


@router.post("/backtest/rodar")
async def backtest_rodar(req: BacktestRequest, _=Depends(auth_e_rate)):
    """
    Onda 99: roda backtest via REST (sync, pode demorar ~1-5min).
    Se dataset fornecido: só esse. Senão: todos 5 datasets.
    Salva em _ULTIMO_BACKTEST + /backtest/ultimo.
    """
    from engine.backtest_real import rodar_backtest, rodar_backtest_todos
    from pathlib import Path as _P

    class _Sim:
        def __init__(self, ids):
            import json as _j
            from engine.persona import Persona
            banco = _j.load(open("data/banco-consultores-lendarios.json"))
            self.personas = {}
            for p in banco:
                if p["id"] in ids:
                    self.personas[p["id"]] = Persona(p)
    sim = _Sim(req.personas)

    if req.dataset:
        path = _P("data/backtest") / f"{req.dataset}.csv"
        if not path.exists():
            raise HTTPException(404, f"dataset {req.dataset} não existe")
        r = rodar_backtest(path, sim, persona_ids=req.personas,
                            max_eventos=req.max_eventos,
                            sleep_entre_eventos_s=req.sleep_entre_eventos_s)
        saida = {"agregado": None, "datasets": [r]}
    else:
        saida = rodar_backtest_todos(
            base_dir="data/backtest", sim=sim, persona_ids=req.personas,
            max_eventos_por_ds=req.max_eventos,
            sleep_entre_eventos_s=req.sleep_entre_eventos_s,
            sleep_entre_datasets_s=6.0,
        )

    # Calibração Platt
    try:
        from engine.calibracao_platt import avaliar_calibracao
        from engine.calibracao_runtime import salvar_coefs
        probs, ys = [], []
        for ds in saida.get("datasets", []):
            for e in ds.get("eventos", []):
                if e.get("prob_vila") is not None:
                    probs.append(e["prob_vila"]); ys.append(e["outcome_real"])
        if len(probs) >= 5:
            cal = avaliar_calibracao(probs, ys)
            saida["calibracao_platt"] = {k: v for k, v in cal.items() if k != "probs_calibradas"}
            salvar_coefs(cal["platt_a"], cal["platt_b"], cal["n"], fonte="backtest_endpoint")
    except Exception as e:
        saida["calibracao_erro"] = str(e)

    import time as _t
    saida["completado_em"] = int(_t.time())
    global _ULTIMO_BACKTEST
    _ULTIMO_BACKTEST = saida

    # Onda 106: persist history
    try:
        from engine.backtest_history import salvar as _salvar_bt
        saida["persistencia"] = _salvar_bt(saida)
    except Exception as e:
        saida["persistencia_erro"] = str(e)

    return saida


@router.get("/backtest/historico")
async def backtest_historico(limite: int = Query(20, ge=1, le=100)):
    """Onda 106: histórico de backtests passados (Supabase ou local)."""
    from engine.backtest_history import historico
    return {"registros": historico(limite=limite)}


@router.get("/backtest/ultimo")
async def backtest_ultimo():
    """Onda 99: retorna último resultado cached."""
    if not _ULTIMO_BACKTEST:
        return {"vazio": True, "msg": "Nenhum backtest rodado ainda. POST /backtest/rodar"}
    return _ULTIMO_BACKTEST


@router.get("/backtest/reliability")
async def backtest_reliability(n_bins: int = Query(10, ge=2, le=30)):
    """Onda 101: reliability diagram do último backtest."""
    from engine.reliability_diagram import reliability
    if not _ULTIMO_BACKTEST:
        return {"vazio": True}
    probs, ys = [], []
    for ds in _ULTIMO_BACKTEST.get("datasets", []):
        for e in ds.get("eventos", []):
            if e.get("prob_vila") is not None:
                probs.append(e["prob_vila"])
                ys.append(e["outcome_real"])
    return reliability(probs, ys, n_bins=n_bins)


@router.get("/backtest/bootstrap-ci")
async def backtest_bootstrap_ci(n_boot: int = Query(1000, ge=100, le=10000)):
    """Onda 100: bootstrap 95% CI para Brier + accuracy do último backtest."""
    from engine.calibracao_stats import bootstrap_ci
    from engine.calibracao_platt import brier
    if not _ULTIMO_BACKTEST:
        return {"vazio": True}
    probs, ys = [], []
    for ds in _ULTIMO_BACKTEST.get("datasets", []):
        for e in ds.get("eventos", []):
            if e.get("prob_vila") is not None:
                probs.append(e["prob_vila"]); ys.append(e["outcome_real"])

    def _acc(p, y):
        return sum(int((pi >= 0.5) == (yi == 1)) for pi, yi in zip(p, y)) / max(len(p), 1)

    return {
        "n": len(probs),
        "brier_ci": bootstrap_ci(brier, probs, ys, n_boot=n_boot),
        "accuracy_ci": bootstrap_ci(_acc, probs, ys, n_boot=n_boot),
    }


@router.get("/backtest/brier-decomp")
async def backtest_brier_decomp(n_bins: int = Query(10, ge=2, le=30)):
    """Onda 102: Murphy BS = Reliability − Resolution + Uncertainty decomposition."""
    from engine.brier_decomp import decompor
    if not _ULTIMO_BACKTEST:
        return {"vazio": True}
    probs, ys = [], []
    for ds in _ULTIMO_BACKTEST.get("datasets", []):
        for e in ds.get("eventos", []):
            if e.get("prob_vila") is not None:
                probs.append(e["prob_vila"]); ys.append(e["outcome_real"])
    return decompor(probs, ys, n_bins=n_bins)


@router.get("/backtest/cv-holdout")
async def backtest_cv_holdout(
    test_frac: float = Query(0.2, ge=0.1, le=0.5),
    n_repeats: int = Query(10, ge=1, le=50),
):
    """Onda 114: repeated hold-out CV pra Platt. Train/test split.
    Retorna brier_train/test avg + overfit_gap."""
    from engine.cv_holdout import cv_holdout_platt
    if not _ULTIMO_BACKTEST:
        return {"vazio": True}
    probs, ys = [], []
    for ds in _ULTIMO_BACKTEST.get("datasets", []):
        for e in ds.get("eventos", []):
            if e.get("prob_vila") is not None:
                probs.append(e["prob_vila"]); ys.append(e["outcome_real"])
    return cv_holdout_platt(probs, ys, test_frac=test_frac, n_repeats=n_repeats)


@router.get("/backtest/platt-vs-isotonic")
async def backtest_platt_vs_isotonic():
    """Onda 100: compara Platt vs isotonic no último backtest."""
    from engine.calibracao_stats import comparacao_platt_vs_isotonic
    if not _ULTIMO_BACKTEST:
        return {"vazio": True}
    probs, ys = [], []
    for ds in _ULTIMO_BACKTEST.get("datasets", []):
        for e in ds.get("eventos", []):
            if e.get("prob_vila") is not None:
                probs.append(e["prob_vila"]); ys.append(e["outcome_real"])
    return comparacao_platt_vs_isotonic(probs, ys)


@router.get("/backtest/datasets")
async def backtest_datasets():
    """Onda 99: lista datasets disponíveis + count eventos."""
    from pathlib import Path as _P
    import csv
    base = _P("data/backtest")
    out = []
    for p in sorted(base.glob("*.csv")):
        try:
            with open(p) as f:
                n = sum(1 for _ in csv.reader(f)) - 1
            out.append({"nome": p.stem, "n_eventos": n, "path": str(p)})
        except Exception:
            pass
    return {"datasets": out, "total": len(out)}


@router.get("/calibracao/status")
async def calibracao_status():
    """Onda 97: status da calibração Platt runtime."""
    from engine.calibracao_runtime import status
    return status()


class CalibracaoAplicarRequest(BaseModel):
    probs: list[float]


@router.post("/calibracao/aplicar")
async def calibracao_aplicar(req: CalibracaoAplicarRequest):
    """Onda 97: aplica Platt em lista de probs. Útil pra UI testar."""
    from engine.calibracao_runtime import aplicar_varios, calibracao_ativa
    ativa = calibracao_ativa()
    return {
        "ativa": ativa,
        "probs_raw": req.probs,
        "probs_calibradas": aplicar_varios(req.probs) if ativa else req.probs,
    }


@router.get("/godseye-stream")
async def godseye_stream():
    """
    Onda 87: SSE stream pra God's Eye dashboard.
    Emite eventos:
      - step: quando simulação avança um step
      - conversa: quando nova conversa é criada
      - mule: quando anomalia psico-histórica detectada
      - keepalive: a cada ~10s
    """
    from fastapi.responses import StreamingResponse
    import asyncio, json as _json

    async def gen():
        sim = obter_simulacao()
        ultimo_step = -1
        ultimo_n_conv = -1
        ultimo_n_mules = 0
        try:
            from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL
        except Exception:
            RASTREADOR_GLOBAL = None
        tick = 0
        for _ in range(2400):   # ~20min cap
            try:
                if sim.step != ultimo_step:
                    ultimo_step = sim.step
                    yield f"event: step\ndata: {_json.dumps({'step': sim.step})}\n\n"

                n_conv = len(getattr(sim, 'conversas_recentes', []))
                if n_conv != ultimo_n_conv:
                    ultimo_n_conv = n_conv
                    yield f"event: conversa\ndata: {_json.dumps({'total': n_conv})}\n\n"

                if RASTREADOR_GLOBAL is not None:
                    mules = RASTREADOR_GLOBAL.trajetoria.mules_detectados
                    if len(mules) > ultimo_n_mules:
                        for m in mules[ultimo_n_mules:]:
                            yield f"event: mule\ndata: {_json.dumps(m)}\n\n"
                        ultimo_n_mules = len(mules)

                tick += 1
                if tick % 20 == 0:
                    yield f"event: keepalive\ndata: {_json.dumps({'tick': tick})}\n\n"

                await asyncio.sleep(0.5)
            except Exception as e:
                yield f"event: error\ndata: {_json.dumps({'msg': str(e)})}\n\n"
                await asyncio.sleep(2)
    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/super-intelligence")
async def super_intelligence(
    horizonte: int = Query(10, ge=1, le=100),
    outcome_desejado: str = Query("equilibrio"),
    com_sintese_llm: bool = Query(True),
):
    """
    Onda 81: meta-endpoint que combina forecast + recomendacao + briefing LLM.
    Single round-trip pra dashboard executivo Helena/Efesto.
    """
    from engine.super_intelligence import gerar_super_intelligence
    sim = obter_simulacao()
    try:
        return gerar_super_intelligence(
            horizonte=horizonte,
            outcome_desejado=outcome_desejado,
            conversas_recentes=getattr(sim, "conversas_recentes", []),
            com_sintese_llm=com_sintese_llm,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/recomendacao-intervencao")
async def recomendacao_intervencao(
    outcome_desejado: str = Query("equilibrio"),
    horizonte: int = Query(20, ge=1, le=100),
    com_recomendacao_llm: bool = Query(True),
):
    """
    Onda 80: sweep multi-counterfactual + LLM recomenda melhor ação.
    Para cada estado psico-histórico, mede prob de atingir outcome em N steps.
    """
    from engine.recomendacao_intervencao import gerar_recomendacao
    try:
        return gerar_recomendacao(
            outcome_desejado=outcome_desejado,
            horizonte=horizonte,
            com_recomendacao_llm=com_recomendacao_llm,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/counterfactual-narrativo")
async def counterfactual_narrativo(
    estado_alternativo: str = Query(..., description="Estado psico-histórico hipotético"),
    horizonte: int = Query(10, ge=1, le=100),
    com_narrativa: bool = Query(True),
):
    """
    Onda 79: Pearl do-calculus counterfactual + ATE + narrativa LLM PT-BR.
    'E se, no step atual, o estado fosse `estado_alternativo` em vez do observado?'
    """
    from engine.counterfactual_narrativo import gerar_counterfactual
    try:
        return gerar_counterfactual(
            estado_alternativo=estado_alternativo,
            horizonte=horizonte,
            com_narrativa=com_narrativa,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/locais")
async def listar_locais():
    """Lista todos os locais do campus."""
    from ..engine.campus import LOCAIS
    return {
        "total": len(LOCAIS),
        "locais": [
            {
                "id": l.id,
                "nome": l.nome,
                "tipo": l.tipo,
                "descricao": l.descricao,
                "capacidade": l.capacidade,
                "nivel_formalidade": l.nivel_formalidade,
                "nivel_energia": l.nivel_energia,
                "posicao_x": l.posicao_x,
                "posicao_y": l.posicao_y,
                "conexoes": l.conexoes,
            }
            for l in LOCAIS.values()
        ],
    }


@router.get("/stats")
async def estatisticas():
    """Retorna estatísticas da simulação."""
    sim = obter_simulacao()
    return {
        "step": sim.step,
        "hora": sim.hora_atual.strftime("%Y-%m-%d %H:%M"),
        **sim.stats,
        "agentes_por_local": sim.mapa_calor(),
        "topicos_ativos": config.topicos_ativos,
    }


# ============================================================
# ENDPOINTS DE INTERAÇÃO
# ============================================================

@router.post("/topico")
async def injetar_topico(req: TopicoRequest):
    """Injeta um tópico para os agentes discutirem."""
    sim = obter_simulacao()
    sim.injetar_topico(req.topico, req.importancia)
    return {
        "status": "ok",
        "mensagem": f"Tópico '{req.topico}' injetado no campus",
        "topicos_ativos": config.topicos_ativos,
    }


@router.post("/sintetizar/{topico}")
async def forcar_sintese(topico: str):
    """Força síntese de inteligência coletiva sobre um tópico."""
    from ..engine.cognitivo.sintetizar import sintetizar

    sim = obter_simulacao()
    resultado = sintetizar(sim.personas, topico, sim.hora_atual, min_perspectivas=2)

    if not resultado:
        raise HTTPException(
            404,
            f"Sem perspectivas suficientes sobre '{topico}'. "
            "Execute mais steps ou injete o tópico primeiro."
        )

    sim.sinteses.append(resultado)
    return resultado


@router.post("/salvar")
async def salvar():
    """Salva o estado atual da simulação (desafio + incentivos + personas)."""
    sim = obter_simulacao()
    sim.salvar()
    return {"status": "salvo", "diretorio": sim.dir_dados}


@router.post("/carregar")
async def carregar():
    """Carrega estado salvo (desafio + incentivos + meta)."""
    sim = obter_simulacao()
    ok = sim.carregar()
    if not ok:
        return {"status": "sem_dados", "mensagem": "Nenhum estado salvo encontrado"}
    return {
        "status": "carregado",
        "step": sim.step,
        "desafio": sim.desafio.nome if sim.desafio.ativo else None,
        "agentes": len(sim.personas),
    }


# ============================================================
# ENDPOINTS DE INTELIGÊNCIA (Previsibilidade + Autoresearch)
# ============================================================

@router.get("/previsibilidade")
async def previsibilidade():
    """Retorna tendências e previsões da vila."""
    sim = obter_simulacao()
    tendencias = sim.motor_previsibilidade.analisar_tendencias()
    return {
        "tendencias": [t.to_dict() for t in tendencias],
        "briefing": sim.motor_previsibilidade.gerar_briefing_helena(),
        "total_steps_analisados": len(sim.motor_previsibilidade.palavras_por_step),
    }


@router.get("/previsibilidade/saturacao/{topico}")
async def saturacao_topico(topico: str):
    """Retorna nível de saturação de um tópico."""
    sim = obter_simulacao()
    return {
        "topico": topico,
        "saturacao": sim.motor_previsibilidade.prever_saturacao(topico),
        "engajamento_previsto": sim.motor_previsibilidade.prever_engajamento(topico),
    }


@router.get("/autoresearch")
async def autoresearch_status():
    """Retorna estado do motor de autoresearch."""
    sim = obter_simulacao()
    return sim.motor_autoresearch.to_dict()


@router.post("/autoresearch/executar")
async def executar_autoresearch(req: TopicoRequest):
    """Força execução de autoresearch sobre um tema."""
    sim = obter_simulacao()
    pesquisa = sim.motor_autoresearch.executar_pesquisa(
        req.topico, sim.personas, sim.step,
    )
    if not pesquisa:
        raise HTTPException(400, "Pesquisa falhou (poucos respondentes)")
    return pesquisa.to_dict()


@router.get("/live")
async def estado_live():
    """Estado completo da vila em tempo real."""
    sim = obter_simulacao()
    return {
        "step": sim.step,
        "hora_simulacao": sim.hora_atual.strftime("%Y-%m-%d %H:%M"),
        "agentes_ativos": sum(1 for p in sim.personas.values() if p.ativo),
        "stats": sim.stats,
        "topicos_ativos": config.topicos_ativos,
        "conversas_recentes": sim.conversas_recentes[-10:],
        "sinteses_recentes": sim.sinteses[-5:],
        "previsibilidade": sim.motor_previsibilidade.to_dict(),
        "autoresearch": sim.motor_autoresearch.to_dict(),
        "rede_social": {
            "total_posts": sim.rede_social.total_posts,
            "total_comentarios": sim.rede_social.total_comentarios,
            "total_reacoes": sim.rede_social.total_reacoes,
        },
    }


@router.get("/relatorio")
async def relatorio_executivo():
    """Relatório executivo consolidado — CONCLUSÕES, não dados brutos."""
    from engine.relatorio import gerar_relatorio
    sim = obter_simulacao()
    rel = gerar_relatorio(sim)
    return rel.to_dict()


@router.get("/relatorio/markdown")
async def relatorio_markdown():
    """Relatório em Markdown para leitura humana."""
    from engine.relatorio import gerar_relatorio
    from fastapi.responses import PlainTextResponse
    sim = obter_simulacao()
    rel = gerar_relatorio(sim)
    return PlainTextResponse(rel.to_markdown(), media_type="text/markdown")


# ============================================================
# ENDPOINTS DE DESAFIO COLETIVO
# ============================================================

class DesafioRequest(BaseModel):
    tema: str = ""
    descricao: str = ""
    documento: str = ""  # Conteúdo de arquivo anexado (texto)
    steps_por_fase: int = 100
    # Compat: aceita desafio_id antigo como alias de tema
    desafio_id: str = ""


class ContribuicaoRequest(BaseModel):
    agente_id: str
    conteudo: str
    tipo: str = "proposta"


class VotoRequest(BaseModel):
    agente_id: str
    entrega_id: str
    favor: bool = True


class PythonRequest(BaseModel):
    agente_id: str
    codigo: str


@router.get("/desafios")
async def listar_desafios_disponiveis():
    """Retorna instruções — o tema é definido pelo usuário."""
    from engine.desafio import listar_desafios
    return {"desafios": listar_desafios()}


@router.post("/desafio/iniciar")
async def iniciar_desafio(req: DesafioRequest):
    """Inicia um desafio coletivo a partir do tema do usuário."""
    sim = obter_simulacao()
    tema = req.tema or req.desafio_id  # compat
    if not tema:
        raise HTTPException(400, "Informe o tema do desafio")
    return sim.iniciar_desafio(
        desafio_id=tema,
        descricao=req.descricao,
        documento=req.documento,
        steps_por_fase=req.steps_por_fase,
    )


@router.get("/desafio")
async def estado_desafio():
    """Retorna estado atual do desafio."""
    sim = obter_simulacao()
    if not sim.desafio.ativo and sim.desafio.status != "concluido":
        return {"status": "inativo", "catalogo": "/api/v1/vila/desafios"}
    return sim.desafio.to_dict()


@router.post("/desafio/contribuir")
async def contribuir_desafio(req: ContribuicaoRequest):
    """Registra contribuição ao desafio."""
    sim = obter_simulacao()
    return sim.contribuir_desafio(req.agente_id, req.conteudo, req.tipo)


@router.post("/desafio/votar")
async def votar_desafio(req: VotoRequest):
    """Registra voto em uma entrega."""
    sim = obter_simulacao()
    return sim.votar_desafio(req.agente_id, req.entrega_id, req.favor)


# ============================================================
# ENDPOINTS DE FERRAMENTAS
# ============================================================

@router.post("/ferramentas/python")
async def executar_python_sandbox(req: PythonRequest):
    """Executa Python no sandbox de um agente."""
    sim = obter_simulacao()
    persona = sim.personas.get(req.agente_id)
    if not persona:
        raise HTTPException(404, f"Agente {req.agente_id} não encontrado")

    local = persona.rascunho.local_atual
    saldo = sim.incentivos.saldo(req.agente_id)

    resultado = sim.toolkit.executar_python(
        req.agente_id, req.codigo, local, saldo, sim.step
    )

    # Cobrar recurso e recompensar se sucesso
    from engine.ferramentas_agente import custo_uso_local
    custo = custo_uso_local(local)
    if resultado.sucesso:
        sim.incentivos.cobrar_recurso(req.agente_id, custo, "Python sandbox", sim.step)
        sim.incentivos.recompensar(req.agente_id, "codigo_executado", sim.step)

    return resultado.to_dict()


@router.get("/ferramentas/recursos/{local_id}")
async def recursos_local(local_id: str):
    """Retorna recursos disponíveis em um local."""
    from engine.ferramentas_agente import RECURSOS_POR_LOCAL
    recurso = RECURSOS_POR_LOCAL.get(local_id)
    if not recurso:
        return {"ferramentas": [], "custo": 0}
    return recurso


# ============================================================
# ENDPOINTS DE ECONOMIA / INCENTIVOS
# ============================================================

@router.get("/economia")
async def economia():
    """Retorna estado da economia da vila."""
    sim = obter_simulacao()
    return sim.incentivos.to_dict()


@router.get("/economia/carteira/{agente_id}")
async def carteira_agente(agente_id: str):
    """Retorna carteira de um agente."""
    sim = obter_simulacao()
    return sim.incentivos.obter_carteira(agente_id).to_dict()


@router.get("/economia/ranking")
async def ranking_economia(top: int = Query(20, ge=1, le=100)):
    """Ranking de agentes por reputação."""
    sim = obter_simulacao()
    return {"ranking": sim.incentivos.top_agentes(top)}


# ============================================================
# ENDPOINTS DE OFICINAS E WORKSPACE
# ============================================================

@router.get("/oficinas")
async def listar_oficinas():
    """Lista todas as oficinas (ferramentas reais por local)."""
    from engine.oficinas import todas_oficinas
    return {"oficinas": todas_oficinas()}


@router.get("/oficinas/{local_id}")
async def detalhe_oficina(local_id: str):
    """Detalhe de uma oficina: ferramentas, artefatos produzidos."""
    from engine.oficinas import oficina_do_local
    oficina = oficina_do_local(local_id)
    if not oficina:
        return {"erro": f"Sem oficina no local '{local_id}'"}
    return oficina.to_dict()


@router.get("/workspace")
async def workspace_listar():
    """Lista artefatos produzidos no workspace do desafio ativo."""
    sim = obter_simulacao()
    desafio_id = sim.desafio.id if sim.desafio.ativo else ""
    if not desafio_id:
        return {"total_arquivos": 0, "arquivos": []}
    return sim.workspace.to_dict(desafio_id)


@router.get("/workspace/{desafio_id}")
async def workspace_desafio(desafio_id: str):
    """Lista artefatos de um desafio específico."""
    sim = obter_simulacao()
    return sim.workspace.to_dict(desafio_id)


@router.get("/workspace/{desafio_id}/avaliar")
async def workspace_avaliar(desafio_id: str):
    """Helena avalia as entregas do workspace."""
    from engine.helena_ceo import avaliar_workspace
    sim = obter_simulacao()
    return avaliar_workspace(sim.workspace, desafio_id)


@router.get("/workspace/{desafio_id}/compilar")
async def workspace_compilar(desafio_id: str):
    """Compila todas as entregas em documento único."""
    from fastapi.responses import PlainTextResponse
    sim = obter_simulacao()
    compilado = sim.workspace.compilar(desafio_id)
    return PlainTextResponse(compilado, media_type="text/markdown")


@router.get("/workspace/{desafio_id}/arquivo/{nome_arquivo:path}")
async def workspace_ler_arquivo(desafio_id: str, nome_arquivo: str):
    """Lê conteúdo de um artefato."""
    sim = obter_simulacao()
    conteudo = sim.workspace.ler(desafio_id, nome_arquivo)
    if not conteudo:
        raise HTTPException(404, f"Arquivo '{nome_arquivo}' não encontrado")
    return {"arquivo": nome_arquivo, "conteudo": conteudo}


# ============================================================
# PUBLICAÇÃO MIRANTE NEWS
# ============================================================

class PublicarMiranteRequest(BaseModel):
    titulo: str
    corpo: str
    categoria: str = "Pesquisa IA"
    tags: list[str] = []
    agente_id: str = ""
    agente_nome: str = "Vila INTEIA"
    auto_push: bool = False


@router.post("/mirante/publicar")
async def publicar_mirante(req: PublicarMiranteRequest):
    """Publica artigo no Mirante News (mirantenews.com.br)."""
    from engine.publicar_mirante import ArtigoMirante, publicar_no_mirante

    artigo = ArtigoMirante(
        titulo=req.titulo,
        corpo=req.corpo,
        categoria=req.categoria,
        tags=req.tags or ["vila-inteia"],
        autor_id=req.agente_id,
        autor_nome=req.agente_nome,
    )
    resultado = publicar_no_mirante(artigo, auto_push=req.auto_push)
    return resultado


@router.post("/mirante/publicar-do-workspace")
async def publicar_workspace_mirante(
    titulo: str = Query(...),
    agente_id: str = Query(...),
    auto_push: bool = Query(False),
):
    """Compila artefatos de um agente no workspace e publica no Mirante."""
    from engine.publicar_mirante import criar_artigo_de_workspace, publicar_no_mirante

    sim = obter_simulacao()
    desafio_id = sim.desafio.id if sim.desafio.ativo else ""
    if not desafio_id:
        raise HTTPException(400, "Nenhum desafio ativo")

    persona = sim.personas.get(agente_id)
    if not persona:
        raise HTTPException(404, f"Agente {agente_id} não encontrado")

    artigo = criar_artigo_de_workspace(
        workspace=sim.workspace,
        desafio_id=desafio_id,
        agente_id=agente_id,
        agente_nome=persona.nome_exibicao,
        agente_categoria=persona.categoria,
        titulo=titulo,
        desafio_nome=sim.desafio.nome,
        fase_nome=sim.desafio.fase_atual.nome if sim.desafio.fase_atual else "",
    )

    if not artigo:
        raise HTTPException(404, "Nenhum artefato do agente no workspace")

    return publicar_no_mirante(artigo, auto_push=auto_push)


# ============================================================
# PROXY — Chat e Persistência (resolve CORS do jogo.html)
# ============================================================

import httpx

_BACKEND_PRINCIPAL = "https://api.inteia.com.br"
_proxy_client = None


def _get_proxy_client():
    global _proxy_client
    if _proxy_client is None:
        _proxy_client = httpx.AsyncClient(timeout=60.0)
    return _proxy_client


@router.post("/chat")
async def proxy_chat(body: dict):
    """Proxy para OmniRoute/chat — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.post(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/chat",
            json=body,
            timeout=60.0,
        )
        return resp.json()
    except Exception as e:
        raise HTTPException(502, f"Proxy chat falhou: {e}")


@router.post("/mensagens/salvar")
async def proxy_mensagens_salvar(body: dict):
    """Proxy para salvar mensagens — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.post(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/mensagens/salvar",
            json=body,
            timeout=15.0,
        )
        return resp.json()
    except Exception:
        return {"status": "salvo_local"}


@router.get("/mensagens/carregar/{tipo}")
async def proxy_mensagens_carregar(tipo: str, sessao_id: str = "", limit: int = 200):
    """Proxy para carregar mensagens — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.get(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/mensagens/carregar/{tipo}",
            params={"sessao_id": sessao_id, "limit": limit},
            timeout=15.0,
        )
        return resp.json()
    except Exception:
        return []


@router.post("/estado/salvar")
async def proxy_estado_salvar(body: dict):
    """Proxy para salvar estado — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.post(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/estado/salvar",
            json=body,
            timeout=15.0,
        )
        return resp.json()
    except Exception:
        return {"status": "salvo_local"}


@router.get("/estado/carregar/{tipo}")
async def proxy_estado_carregar(tipo: str, sessao_id: str = ""):
    """Proxy para carregar estado — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.get(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/estado/carregar/{tipo}",
            params={"sessao_id": sessao_id},
            timeout=15.0,
        )
        return resp.json()
    except Exception:
        return {}


@router.get("/constituicao/artigos")
async def proxy_constituicao():
    """Proxy para constituição — resolve CORS."""
    client = _get_proxy_client()
    try:
        resp = await client.get(
            f"{_BACKEND_PRINCIPAL}/api/v1/vila-inteia/constituicao/artigos",
            timeout=15.0,
        )
        return resp.json()
    except Exception:
        return []
