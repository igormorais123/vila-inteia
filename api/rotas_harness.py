"""
api/rotas_harness — Endpoints da camada de Harness (Onda 2).

Expõe dados da tabela vila_traces para o frontend da Torre do Observatório
e relatórios operacionais. Ver HARNESS_VILA_FUNCIONAL.md §1.1 (Torre do
Observatório) e §2 (Produtos de Inteligência).

Rotas:
    GET  /api/v1/harness/saude             — status do harness + tracing
    GET  /api/v1/harness/traces            — lista paginada de traces
    GET  /api/v1/harness/traces/{trace_id} — trace + causal chain
    GET  /api/v1/harness/traces/agente/{agente_id} — traces de um agente
    GET  /api/v1/harness/metricas          — agregações (top-N agentes por custo/fase)
    POST /api/v1/harness/flush             — força flush da fila (admin)
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger("vila-inteia.api.harness")

router = APIRouter(prefix="/api/v1/harness", tags=["Harness"])


# ---------------------------------------------------------------------
# Helper: consulta vila_traces via supabase_db

def _buscar_traces(params: str = "") -> list[dict]:
    try:
        from engine import supabase_db
        return supabase_db.buscar("vila_traces", params) or []
    except Exception as exc:
        logger.warning("Falha ao consultar vila_traces: %s", exc)
        return []


# ---------------------------------------------------------------------
# Endpoints

@router.get("/saude")
def saude() -> dict:
    """Status do harness: tracing ativo, fila, tabela disponível."""
    from engine.harness import habilitado

    try:
        from engine import supabase_db
        supabase_ok = supabase_db.status_conexao().get("conectado", False)
    except Exception:
        supabase_ok = False

    total = 0
    if supabase_ok:
        r = _buscar_traces("select=trace_id&limit=1")
        total_r = _buscar_traces("select=trace_id")
        total = len(total_r) if total_r else 0

    return {
        "tracing_habilitado": habilitado(),
        "env_var": "VILA_TRACE_ENABLED",
        "supabase_conectado": supabase_ok,
        "total_traces": total,
        "tabela": "vila_traces",
        "onda": 2,
        "ref": "HARNESS_VILA.md §3.1",
    }


@router.get("/traces")
def listar_traces(
    limit: int = Query(100, ge=1, le=1000),
    fase: Optional[str] = Query(None, description="perceber|recuperar|planejar|executar|conversar|refletir|sintetizar|skill|protocolo|tool"),
    resultado: Optional[str] = Query(None, description="sucesso|falha|aprovacao_humana|retry|vazio"),
    step_min: Optional[int] = None,
    step_max: Optional[int] = None,
) -> dict:
    """Lista traces recentes com filtros opcionais."""
    filtros = [f"order=inicio.desc", f"limit={limit}"]
    if fase:
        filtros.append(f"fase=eq.{fase}")
    if resultado:
        filtros.append(f"resultado=eq.{resultado}")
    if step_min is not None:
        filtros.append(f"step=gte.{step_min}")
    if step_max is not None:
        filtros.append(f"step=lte.{step_max}")
    params = "&".join(filtros)

    traces = _buscar_traces(params)
    return {"total": len(traces), "traces": traces}


@router.get("/traces/{trace_id}")
def detalhar_trace(trace_id: str) -> dict:
    """Retorna trace + causal chain (pais recursivos)."""
    atual = _buscar_traces(f"trace_id=eq.{trace_id}&limit=1")
    if not atual:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} não encontrado")

    evento = atual[0]
    chain = [evento]
    parent_id = evento.get("causal_parent")
    depth = 0
    while parent_id and depth < 20:
        r = _buscar_traces(f"trace_id=eq.{parent_id}&limit=1")
        if not r:
            break
        chain.append(r[0])
        parent_id = r[0].get("causal_parent")
        depth += 1

    return {
        "evento": evento,
        "causal_chain": chain,
        "profundidade": len(chain) - 1,
    }


@router.get("/traces/agente/{agente_id}")
def traces_por_agente(
    agente_id: str,
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    """Traces de um agente específico, ordenados por step desc."""
    params = f"agente_id=eq.{agente_id}&order=step.desc,inicio.desc&limit={limit}"
    traces = _buscar_traces(params)
    return {
        "agente_id": agente_id,
        "total": len(traces),
        "traces": traces,
    }


@router.get("/metricas")
def metricas(
    limite_top: int = Query(10, ge=1, le=100),
) -> dict:
    """
    Agregações operacionais para a Torre do Observatório e Mercado da Atenção.

    Calcula em Python (Supabase REST não suporta GROUP BY direto).
    """
    traces = _buscar_traces("order=inicio.desc&limit=5000")

    if not traces:
        return {"total_amostra": 0, "top_agentes_por_custo": [], "por_fase": {}, "taxa_falha": 0.0}

    # Agregar por agente (custo + count)
    por_agente: dict[str, dict] = {}
    por_fase: dict[str, dict] = {}
    falhas = 0

    for t in traces:
        aid = t.get("agente_id", "desconhecido")
        custo = float(t.get("custo_usd") or 0)
        tokens = int(t.get("tokens_consumidos") or 0)
        fase = t.get("fase", "?")
        dur = int(t.get("duracao_ms") or 0)
        resultado = t.get("resultado", "sucesso")

        if aid not in por_agente:
            por_agente[aid] = {"agente_id": aid, "custo_usd": 0.0, "tokens": 0, "chamadas": 0}
        por_agente[aid]["custo_usd"] += custo
        por_agente[aid]["tokens"] += tokens
        por_agente[aid]["chamadas"] += 1

        if fase not in por_fase:
            por_fase[fase] = {"chamadas": 0, "tokens": 0, "custo_usd": 0.0, "duracao_total_ms": 0}
        por_fase[fase]["chamadas"] += 1
        por_fase[fase]["tokens"] += tokens
        por_fase[fase]["custo_usd"] += custo
        por_fase[fase]["duracao_total_ms"] += dur

        if resultado != "sucesso":
            falhas += 1

    top = sorted(por_agente.values(), key=lambda x: x["custo_usd"], reverse=True)[:limite_top]

    return {
        "total_amostra": len(traces),
        "top_agentes_por_custo": top,
        "por_fase": por_fase,
        "taxa_falha": round(falhas / len(traces), 4) if traces else 0.0,
        "falhas_count": falhas,
    }


@router.get("/orcamento")
def orcamentos_declarados() -> dict:
    """Tabela canônica de orçamentos por fase (HARNESS_VILA.md §3.2)."""
    from engine.harness import relatorio_orcamentos
    import os
    return {
        "track_habilitado": os.getenv("VILA_BUDGET_TRACK", "0") == "1",
        "env_var": "VILA_BUDGET_TRACK",
        "orcamentos": relatorio_orcamentos(),
        "fonte": "engine/harness/orcamento.py",
    }


@router.get("/orcamento/consumo")
def consumo_orcamento(
    limit: int = Query(500, ge=1, le=5000),
    agente_id: Optional[str] = None,
    fase: Optional[str] = None,
) -> dict:
    """Histórico de consumo do Mercado da Atenção."""
    filtros = [f"order=registrado_em.desc", f"limit={limit}"]
    if agente_id:
        filtros.append(f"agente_id=eq.{agente_id}")
    if fase:
        filtros.append(f"fase=eq.{fase}")
    params = "&".join(filtros)

    try:
        from engine import supabase_db
        rows = supabase_db.buscar("vila_orcamento_historico", params) or []
    except Exception as exc:
        logger.warning("Falha consumo: %s", exc)
        rows = []

    # Agregação leve
    por_agente: dict[str, dict] = {}
    por_fase: dict[str, dict] = {}
    total_tokens = 0
    total_custo = 0.0
    for r in rows:
        aid = r.get("agente_id", "?")
        f = r.get("fase", "?")
        tk = int(r.get("tokens_consumidos") or 0)
        cu = float(r.get("custo_usd") or 0)
        total_tokens += tk
        total_custo += cu
        por_agente.setdefault(aid, {"tokens": 0, "custo_usd": 0.0})
        por_agente[aid]["tokens"] += tk
        por_agente[aid]["custo_usd"] += cu
        por_fase.setdefault(f, {"tokens": 0, "custo_usd": 0.0})
        por_fase[f]["tokens"] += tk
        por_fase[f]["custo_usd"] += cu

    return {
        "amostra": len(rows),
        "total_tokens": total_tokens,
        "total_custo_usd": round(total_custo, 4),
        "por_agente": por_agente,
        "por_fase": por_fase,
    }


@router.post("/flush")
def forcar_flush(timeout_s: float = 10.0) -> dict:
    """Força drenagem imediata da fila de traces (administrativo)."""
    from engine.harness import flush_traces, habilitado

    if not habilitado():
        return {"ok": False, "motivo": "tracing desabilitado (VILA_TRACE_ENABLED != 1)"}

    flush_traces(timeout_s=timeout_s)
    return {"ok": True, "timeout_s": timeout_s}


# =====================================================================
# Skills canônicas (Onda 3 — Rua das Oficinas)
# =====================================================================

@router.get("/skills")
def listar_skills(nivel: int = Query(1, ge=1, le=3)) -> dict:
    """Lista skills registradas no nível de detalhe pedido (1=manifest, 3=completo)."""
    from engine.harness import skill_registry
    todas = skill_registry.listar(nivel=nivel)
    return {"total": len(todas), "nivel": nivel, "skills": todas}


@router.get("/skills/buscar")
def buscar_skills(
    q: str = Query(..., min_length=2, description="termos separados por vírgula"),
    top_n: int = Query(5, ge=1, le=20),
    nivel: int = Query(2, ge=1, le=3),
) -> dict:
    """Busca skills por termos (match em nome, descrição, capabilities, scope, tools)."""
    from engine.harness import skill_registry
    termos = [t.strip() for t in q.split(",") if t.strip()]
    res = skill_registry.buscar(termos, top_n=top_n, nivel=nivel)
    return {"termos": termos, "total": len(res), "resultados": res}


@router.get("/skills/{nome}")
def detalhar_skill(
    nome: str,
    nivel: int = Query(3, ge=1, le=3),
) -> dict:
    """Carrega uma skill específica no nível pedido."""
    from engine.harness import skill_registry
    s = skill_registry.carregar(nome, nivel=nivel)
    if not s:
        raise HTTPException(status_code=404, detail=f"Skill '{nome}' não encontrada")
    return s


# =====================================================================
# Capability cards (Onda 3 — Portal do Mercado)
# =====================================================================

@router.get("/capabilities")
def listar_capabilities() -> dict:
    """Lista capability cards discoveráveis (contratos MCP-like)."""
    from engine.harness import listar_cards
    cards = listar_cards()
    return {"total": len(cards), "capabilities": cards}


@router.get("/capabilities/{cap_id}")
def detalhar_capability(cap_id: str) -> dict:
    """Detalha um capability card específico."""
    from engine.harness import obter_card
    c = obter_card(cap_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Capability '{cap_id}' não encontrada")
    return c


# =====================================================================
# Ficha do Fundador (Onda 4 — Gap #5)
# =====================================================================

@router.get("/fundador")
def ficha_fundador() -> dict:
    """Retorna ficha consolidada do Fundador (Igor) para qualquer agente da Vila."""
    from engine.memoria.fundador import carregar_ficha
    return carregar_ficha(force=False).as_dict()


@router.get("/fundador/injecao")
def ficha_fundador_injecao(max_chars: int = Query(1500, ge=200, le=6000)) -> dict:
    """Versão textual compacta da ficha, pronta para injeção em prompt."""
    from engine.memoria.fundador import ficha_para_injecao
    return {"max_chars": max_chars, "texto": ficha_para_injecao(max_chars=max_chars)}


# =====================================================================
# Produto 1 — Simulação Decisional (HARNESS_VILA_FUNCIONAL.md §2)
# =====================================================================

@router.post("/simular-decisao")
def simular_decisao(payload: dict) -> dict:
    """
    Produto 1 — Simulação Decisional para Helena/Colmeia.

    MVP: consulta skills compatíveis, traz perspectivas de agentes
    disponíveis, retorna relatório estruturado com recomendação.

    Input esperado::

        {
          "contexto": "proposta comercial cliente Zeta",
          "agentes": ["themis","midas","chateaubriand"],
          "steps": 30,
          "restricoes": ["sem dados sensiveis reais"]
        }
    """
    import uuid
    from datetime import datetime, timezone
    from engine.harness import skill_registry, obter_orcamento

    contexto = str(payload.get("contexto", "")).strip()
    if not contexto:
        raise HTTPException(status_code=400, detail="campo 'contexto' é obrigatório")

    agentes = payload.get("agentes") or []
    steps = int(payload.get("steps") or 20)
    restricoes = payload.get("restricoes") or []

    # Descobre skills relevantes pelo contexto
    termos = [w for w in contexto.lower().split() if len(w) > 3][:8]
    skills_relevantes = skill_registry.buscar(termos, top_n=5, nivel=2)
    orcamento = obter_orcamento("sintetizar")

    relatorio_id = uuid.uuid4().hex
    votos = {a: "pendente" for a in agentes}
    riscos = []
    if "sensivel" in contexto.lower() or "sensível" in contexto.lower() or "lgpd" in contexto.lower():
        riscos.append("possível dado sensível — aplicar constituição art. compliance")
    if steps > 100:
        riscos.append("orçamento de steps alto — validar ROI antes de executar")
    if not agentes:
        riscos.append("nenhum agente selecionado — recomendação será heurística")

    confianca = max(0.3, min(0.85, 0.5 + 0.05 * len(skills_relevantes) - 0.05 * len(riscos)))

    relatorio = {
        "relatorio_id": relatorio_id,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "contexto": contexto,
        "agentes_selecionados": agentes,
        "votos_por_agente": votos,
        "steps_planejados": steps,
        "restricoes": restricoes,
        "skills_relevantes": [
            {"nome": s["nome"], "descricao": s["descricao"], "score": s.get("_score", 0)}
            for s in skills_relevantes
        ],
        "riscos_detectados": riscos,
        "orcamento_aplicavel": {
            "fase": orcamento.fase,
            "tokens_max": orcamento.tokens_max,
            "memoria_max": orcamento.memoria_max,
        },
        "decisao_recomendada": "investigar" if riscos else "prosseguir",
        "confianca": round(confianca, 3),
        "proxima_acao_sugerida": "rodar steps em modo sandbox + colher votos reais dos agentes",
        "status": "mvp_sincrono",
        "nota": "MVP da Onda 3. Execução real de N steps com agentes virá na Onda 4.",
        "trace_completo_url": f"/api/v1/harness/traces?limit=50",
    }
    return relatorio
