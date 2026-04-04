"""
Rotas extras para compatibilidade com o frontend Vila INTEIA.
Implementa: oficinas, workspace, desafio, economia.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/vila", tags=["Vila Extras"])

# ============================================================
# ESTADO (armazenamento em memoria)
# ============================================================

_desafio_ativo = None
_workspace_arquivos = []
_economia = {
    "moeda": "Xi",
    "simbolo": "\u039e",
    "supply_total": 14600,
    "supply_circulante": 8760,
    "gini": 0.32,
    "transacoes_hoje": 47,
    "top_ricos": [
        {"nome": "Warren Buffett", "saldo": 850},
        {"nome": "Bernard Arnault", "saldo": 720},
        {"nome": "Elon Musk", "saldo": 680},
    ],
}

# Oficinas: cada local do campus pode ter uma oficina com ferramentas
_oficinas = {
    "laboratorio": {
        "id": "laboratorio",
        "nome": "Laboratorio de Ideias",
        "ferramentas": ["Monte Carlo", "Random Forest", "Analise de Sentimento", "Design Sprint"],
        "artefatos": [],
        "agentes_presentes": [],
    },
    "torre_estrategia": {
        "id": "torre_estrategia",
        "nome": "Torre de Estrategia",
        "ferramentas": ["SWOT", "PESTEL", "Cenarios Prospectivos", "Teoria dos Jogos"],
        "artefatos": [],
        "agentes_presentes": [],
    },
    "tribunal": {
        "id": "tribunal",
        "nome": "Tribunal",
        "ferramentas": ["Analise Jurisprudencial", "Parecer Juridico", "Due Diligence"],
        "artefatos": [],
        "agentes_presentes": [],
    },
    "biblioteca": {
        "id": "biblioteca",
        "nome": "Biblioteca",
        "ferramentas": ["Pesquisa Academica", "Revisao Sistematica", "Meta-Analise"],
        "artefatos": [],
        "agentes_presentes": [],
    },
    "arena_debates": {
        "id": "arena_debates",
        "nome": "Arena de Debates",
        "ferramentas": ["Debate Estruturado", "Advocacia do Diabo", "Deliberacao"],
        "artefatos": [],
        "agentes_presentes": [],
    },
    "atelie": {
        "id": "atelie",
        "nome": "Atelie Criativo",
        "ferramentas": ["Brainstorm", "SCAMPER", "Mapa Mental", "Prototipagem"],
        "artefatos": [],
        "agentes_presentes": [],
    },
    "observatorio": {
        "id": "observatorio",
        "nome": "Observatorio",
        "ferramentas": ["Monitoramento", "Radar de Tendencias", "Analise de Redes"],
        "artefatos": [],
        "agentes_presentes": [],
    },
}

# ============================================================
# OFICINAS
# ============================================================

@router.get("/oficinas")
def listar_oficinas():
    """Oficinas com agentes presentes em tempo real."""
    from .rotas_vila import obter_simulacao
    oficinas = []
    try:
        sim = obter_simulacao()
        for oid, ofi in _oficinas.items():
            # Encontrar agentes presentes neste local
            presentes = []
            for p in sim.personas.values():
                local = p.rascunho.local_atual if hasattr(p.rascunho, "local_atual") else ""
                if local == oid:
                    presentes.append({
                        "id": p.id,
                        "nome": p.nome_exibicao,
                        "titulo": p.titulo,
                        "acao": p.rascunho.acao.descricao if hasattr(p.rascunho.acao, "descricao") else str(p.rascunho.acao),
                    })
            ofi_copy = dict(ofi)
            ofi_copy["agentes_presentes"] = presentes
            ofi_copy["total_presentes"] = len(presentes)
            oficinas.append(ofi_copy)
    except Exception:
        oficinas = list(_oficinas.values())
    return {"oficinas": oficinas, "total": len(oficinas)}

@router.get("/oficinas/{oficina_id}")
def obter_oficina(oficina_id: str):
    if oficina_id not in _oficinas:
        raise HTTPException(404, f"Oficina {oficina_id} nao encontrada")
    return _oficinas[oficina_id]

# ============================================================
# WORKSPACE
# ============================================================

@router.get("/workspace")
def listar_workspace():
    """Workspace dinamico - agrega artefatos da simulacao."""
    from .rotas_vila import obter_simulacao
    arquivos = list(_workspace_arquivos)  # manter os manuais
    try:
        sim = obter_simulacao()
        # Adicionar sinteses como artefatos
        for i, s in enumerate(sim.sinteses):
            arquivos.append({
                "id": f"sintese-{i}",
                "tipo": "sintese",
                "nome": f"Sintese: {s.get('topico','?')[:40]}",
                "conteudo": s.get("sintese", ""),
                "participantes": s.get("participantes", []),
                "confianca": s.get("confianca", 0),
                "criado_em": s.get("timestamp", ""),
            })
        # Adicionar conversas recentes como artefatos
        for i, c in enumerate(sim.conversas_recentes[-10:]):
            parceiro = c.get("parceiro_nome", "?")
            arquivos.append({
                "id": f"conversa-{i}",
                "tipo": "conversa",
                "nome": f"Conversa sobre {c.get('topico','?')[:30]}",
                "participantes": [parceiro],
                "local": c.get("local_id", "?"),
                "turnos": len(c.get("turnos", [])),
            })
    except Exception:
        pass
    return {"arquivos": arquivos, "total": len(arquivos)}

@router.get("/workspace/{desafio_id}/arquivo/{nome_arquivo}")
def obter_arquivo(desafio_id: str, nome_arquivo: str):
    for arq in _workspace_arquivos:
        if arq.get("desafio_id") == desafio_id and arq.get("nome") == nome_arquivo:
            return arq
    raise HTTPException(404, "Arquivo nao encontrado")

# ============================================================
# DESAFIO
# ============================================================

class DesafioInput(BaseModel):
    tema: str

@router.get("/desafio")
def obter_desafio():
    if not _desafio_ativo:
        return {"ativo": False, "desafio": None}
    return {"ativo": True, "desafio": _desafio_ativo}

@router.post("/desafio/iniciar")
def iniciar_desafio(dados: DesafioInput):
    global _desafio_ativo
    _desafio_ativo = {
        "id": str(uuid.uuid4())[:8],
        "tema": dados.tema,
        "fase": "entender",
        "fases": ["entender", "divergir", "decidir", "prototipar", "testar"],
        "fase_atual": 0,
        "progresso": 0,
        "contribuicoes": [],
        "artefatos": [],
        "criado_em": datetime.now().isoformat(),
    }
    return {"status": "ok", "desafio": _desafio_ativo}


@router.post("/desafio/avancar")
def avancar_desafio():
    """Avanca para proxima fase do Design Sprint com contribuicoes LLM dos agentes."""
    global _desafio_ativo
    if not _desafio_ativo:
        from fastapi import HTTPException
        raise HTTPException(400, "Nenhum desafio ativo")
    
    from .rotas_vila import obter_simulacao
    from ..engine.ia_client import chamar_llm_conversa
    
    sim = obter_simulacao()
    fase_idx = _desafio_ativo["fase_atual"]
    fases = _desafio_ativo["fases"]
    
    if fase_idx >= len(fases):
        return {"status": "concluido", "desafio": _desafio_ativo}
    
    fase = fases[fase_idx]
    tema = _desafio_ativo["tema"]
    
    # Selecionar agentes relevantes por fase
    AGENTES_POR_FASE = {
        "entender": ["visionario", "estrategia", "mindset"],
        "divergir": ["visionario", "tech", "ia_futuro", "ficticio"],
        "decidir": ["estrategia", "investidor", "negociacao"],
        "prototipar": ["tech", "ia_futuro", "marca", "mkt_digital"],
        "testar": ["estrategia", "investidor", "qi_extremo", "lado_negro"],
    }
    categorias = AGENTES_POR_FASE.get(fase, ["visionario"])
    
    # Pegar 5 agentes das categorias relevantes
    candidatos = [p for p in sim.personas.values() if p.categoria in categorias and p.ativo]
    import random
    selecionados = random.sample(candidatos, min(5, len(candidatos))) if candidatos else list(sim.personas.values())[:3]
    
    PROMPTS_FASE = {
        "entender": "Analise o problema: {tema}. Qual e a dor real? Quem sao os afetados? Que dados faltam? Max 3 frases.",
        "divergir": "Proponha uma solucao criativa e nao-obvia para: {tema}. Pense fora da caixa. Max 3 frases.",
        "decidir": "De todas as ideias para {tema}, qual e a mais viavel e por que? Que criterios usar? Max 3 frases.",
        "prototipar": "Como voce prototiparia a solucao para {tema}? Que MVP minimo validaria a hipotese? Max 3 frases.",
        "testar": "Como testar se a solucao para {tema} realmente funciona? Que metricas? Que riscos? Max 3 frases.",
    }
    
    contribuicoes_fase = []
    for agente in selecionados:
        system = f"Voce e {agente.nome_exibicao}, {agente.titulo}. Responda como voce mesmo, com seu estilo e expertise."
        user = PROMPTS_FASE[fase].format(tema=tema)
        
        resp = chamar_llm_conversa(system, user, modelo="rapido", max_tokens=150)
        if not resp:
            resp = f"{agente.nome_exibicao} contribui com sua perspectiva de {agente.categoria}."
        
        contrib = {
            "agente_id": agente.id,
            "agente_nome": agente.nome_exibicao,
            "categoria": agente.categoria,
            "fase": fase,
            "contribuicao": resp,
            "timestamp": datetime.now().isoformat(),
        }
        contribuicoes_fase.append(contrib)
        _desafio_ativo["contribuicoes"].append(contrib)
    
    # Avancar fase
    _desafio_ativo["fase_atual"] = fase_idx + 1
    _desafio_ativo["fase"] = fases[fase_idx + 1] if fase_idx + 1 < len(fases) else "concluido"
    _desafio_ativo["progresso"] = int(((fase_idx + 1) / len(fases)) * 100)
    
    # Salvar artefato da fase
    _desafio_ativo["artefatos"].append({
        "fase": fase,
        "contribuicoes": contribuicoes_fase,
        "total_agentes": len(contribuicoes_fase),
    })
    
    # Adicionar ao workspace
    _workspace_arquivos.append({
        "id": f"sprint-{_desafio_ativo['id']}-{fase}",
        "tipo": "design_sprint",
        "nome": f"Design Sprint: {tema[:30]} - Fase {fase}",
        "fase": fase,
        "contribuicoes": len(contribuicoes_fase),
        "desafio_id": _desafio_ativo["id"],
    })
    
    return {
        "status": "ok",
        "fase_concluida": fase,
        "proxima_fase": _desafio_ativo["fase"],
        "progresso": _desafio_ativo["progresso"],
        "contribuicoes": contribuicoes_fase,
        "desafio": _desafio_ativo,
    }

# ============================================================
# ECONOMIA
# ============================================================

@router.get("/economia")
def obter_economia():
    """Economia dinamica - atualiza com base na simulacao."""
    from .rotas_vila import obter_simulacao
    try:
        sim = obter_simulacao()
        # Calcular economia baseada na atividade real
        total_agentes = len(sim.personas)
        ativos = sum(1 for p in sim.personas.values() if p.ativo and p.rascunho.energia > 20)
        conversas = sim.stats.get("total_conversas", 0)
        reflexoes = sim.stats.get("total_reflexoes", 0)
        
        # Supply proporcional aos agentes
        supply_total = total_agentes * 100
        supply_circulante = int(supply_total * 0.6 + conversas * 2 + reflexoes * 5)
        supply_circulante = min(supply_circulante, supply_total)
        
        # Top ricos = agentes com mais memorias
        ranking = sorted(
            sim.personas.values(),
            key=lambda p: p.memoria_total if hasattr(p, "memoria_total") else len(p.memoria.fluxo) if hasattr(p.memoria, "fluxo") else 0,
            reverse=True
        )[:5]
        
        top = []
        for p in ranking:
            mem = p.memoria_total if hasattr(p, "memoria_total") else 0
            top.append({"nome": p.nome_exibicao, "saldo": 100 + mem * 10 + int(p.rascunho.energia)})
        
        # Gini baseado na distribuicao de memorias
        memorias = [len(p.memoria.fluxo) if hasattr(p.memoria, "fluxo") else 0 for p in sim.personas.values()]
        media = sum(memorias) / max(len(memorias), 1)
        variancia = sum((m - media)**2 for m in memorias) / max(len(memorias), 1)
        gini = min(round((variancia**0.5) / max(media, 1) * 0.5, 2), 0.99)
        
        return {
            "moeda": "Xi",
            "simbolo": "Ξ",
            "supply_total": supply_total,
            "supply_circulante": supply_circulante,
            "gini": gini,
            "transacoes_hoje": conversas + reflexoes,
            "agentes_ativos": ativos,
            "top_ricos": top,
        }
    except Exception:
        return _economia

# ============================================================
# RELATORIO (stub — sera integrado com Helena/Agent Zero)
# ============================================================

@router.get("/relatorio")
def gerar_relatorio():
    """Gera relatorio real com base no estado da simulacao."""
    from .rotas_vila import obter_simulacao
    sim = obter_simulacao()
    
    # Coletar dados reais
    stats = sim.stats
    total_agentes = len(sim.personas)
    ativos = sum(1 for p in sim.personas.values() if p.ativo)
    
    # Top conversadores
    conversadores = {}
    for c in sim.conversas_recentes[-50:]:
        nome = c.get("parceiro_nome", "?")
        conversadores[nome] = conversadores.get(nome, 0) + 1
    top_conversadores = sorted(conversadores.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Distribuicao por local
    por_local = {}
    for p in sim.personas.values():
        local = p.rascunho.local_atual if hasattr(p.rascunho, "local_atual") else "?"
        por_local[local] = por_local.get(local, 0) + 1
    
    # Topicos ativos
    topicos = [t for t in getattr(sim, "_topicos_ativos", []) if t] if hasattr(sim, "_topicos_ativos") else []
    
    # Sinteses produzidas
    sinteses_resumo = [{"topico": s.get("topico"), "confianca": s.get("confianca"), "participantes": len(s.get("participantes",[]))} for s in sim.sinteses]
    
    return {
        "titulo": "Relatorio de Atividade — Vila INTEIA",
        "gerado_em": datetime.now().isoformat(),
        "periodo": f"Step 0 a {sim.step} ({sim.hora_atual.strftime('%H:%M') if sim.hora_atual else '?'})",
        "resumo": {
            "total_agentes": total_agentes,
            "agentes_ativos": ativos,
            "total_conversas": stats.get("total_conversas", 0),
            "total_reflexoes": stats.get("total_reflexoes", 0),
            "total_movimentos": stats.get("total_movimentos", 0),
            "total_sinteses": len(sim.sinteses),
        },
        "top_conversadores": [{"nome": n, "conversas": c} for n, c in top_conversadores],
        "distribuicao_campus": {k: v for k, v in sorted(por_local.items(), key=lambda x: x[1], reverse=True) if v > 0},
        "topicos_ativos": topicos,
        "sinteses": sinteses_resumo,
        "status": "real",
    }

@router.post("/oficinas/{oficina_id}/executar")
def executar_ferramenta(oficina_id: str, ferramenta: str = "SWOT", tema: str = "analise geral"):
    """Executa ferramenta real de uma oficina com agentes presentes."""
    if oficina_id not in _oficinas:
        raise HTTPException(404, f"Oficina {oficina_id} nao encontrada")
    
    from .rotas_vila import obter_simulacao
    from ..engine.ia_client import chamar_llm_conversa
    
    sim = obter_simulacao()
    oficina = _oficinas[oficina_id]
    
    if ferramenta not in oficina["ferramentas"]:
        raise HTTPException(400, f"Ferramenta {ferramenta} nao disponivel nesta oficina. Disponiveis: {oficina['ferramentas']}")
    
    # Selecionar 3-5 agentes mais relevantes
    import random
    agentes = list(sim.personas.values())
    selecionados = random.sample(agentes, min(5, len(agentes)))
    
    PROMPTS_FERRAMENTA = {
        "SWOT": "Faca uma analise SWOT completa sobre: {tema}. Liste Forcas, Fraquezas, Oportunidades e Ameacas. Seja especifico e acionavel.",
        "PESTEL": "Analise PESTEL para: {tema}. Cubra fatores Politicos, Economicos, Sociais, Tecnologicos, Ambientais e Legais.",
        "Monte Carlo": "Simule cenarios probabilisticos para: {tema}. Liste 3 cenarios (otimista 25%, base 50%, pessimista 25%) com impacto estimado.",
        "Random Forest": "Identifique os 5 fatores mais importantes que influenciam: {tema}. Ordene por importancia relativa (%) e explique cada um.",
        "Teoria dos Jogos": "Analise {tema} como jogo estrategico. Quem sao os jogadores? Quais estrategias? Qual o equilibrio de Nash?",
        "Design Sprint": "Proponha um sprint de 5 dias para resolver: {tema}. Dia 1: Mapear. Dia 2: Divergir. Dia 3: Decidir. Dia 4: Prototipar. Dia 5: Testar.",
        "Cenarios Prospectivos": "Construa 3 cenarios para {tema} no horizonte 2027. Cenario otimista, tendencial e disruptivo.",
        "Brainstorm": "Gere 10 ideias criativas e nao-obvias para: {tema}. Nao filtre — quantidade > qualidade.",
        "Analise de Sentimento": "Analise o sentimento publico sobre: {tema}. Qual a percepcao dominante? Que narrativas competem?",
        "Pesquisa Academica": "Indique 5 referencias academicas relevantes para: {tema}. Autor, ano, contribuicao principal.",
        "Debate Estruturado": "Apresente argumentos pro e contra para: {tema}. 3 de cada lado, com evidencia.",
        "Analise Jurisprudencial": "Analise aspectos juridicos de: {tema}. Legislacao aplicavel, precedentes, riscos legais.",
        "SCAMPER": "Aplique SCAMPER a {tema}: Substituir, Combinar, Adaptar, Modificar, Propor outros usos, Eliminar, Reorganizar.",
    }
    
    prompt_base = PROMPTS_FERRAMENTA.get(ferramenta, "Analise {tema} usando a ferramenta {ferramenta}.")
    
    contribuicoes = []
    for agente in selecionados:
        system = f"Voce e {agente.nome_exibicao}, {agente.titulo}. Use sua expertise em {", ".join(agente.rascunho.areas_expertise[:3] if hasattr(agente.rascunho, 'areas_expertise') else ['analise'])}. Responda em portugues, max 200 palavras."
        user = prompt_base.format(tema=tema, ferramenta=ferramenta)
        
        resp = chamar_llm_conversa(system, user, modelo="rapido", max_tokens=400)
        if not resp:
            resp = f"{agente.nome_exibicao} aplicou {ferramenta} ao tema."
        
        contribuicoes.append({
            "agente_id": agente.id,
            "agente_nome": agente.nome_exibicao,
            "titulo": agente.titulo,
            "categoria": agente.categoria,
            "analise": resp,
        })
    
    # Salvar artefato
    artefato = {
        "id": f"oficina-{oficina_id}-{str(uuid.uuid4())[:6]}",
        "tipo": "analise_oficina",
        "oficina": oficina["nome"],
        "ferramenta": ferramenta,
        "tema": tema,
        "contribuicoes": contribuicoes,
        "total_agentes": len(contribuicoes),
        "criado_em": datetime.now().isoformat(),
    }
    oficina["artefatos"].append(artefato)
    _workspace_arquivos.append({
        "id": artefato["id"],
        "tipo": "analise_oficina",
        "nome": f"{ferramenta}: {tema[:40]}",
        "oficina": oficina["nome"],
        "agentes": len(contribuicoes),
    })
    
    return artefato



# ============================================================
# BRIEFING EXECUTIVO
# ============================================================

@router.get("/briefing")
def gerar_briefing():
    """Gera briefing executivo com insights acionáveis da Vila."""
    from .rotas_vila import obter_simulacao
    from ..engine.ia_client import chamar_llm_conversa
    
    sim = obter_simulacao()
    stats = sim.stats
    
    # Coletar dados relevantes
    sinteses = sim.sinteses[-3:] if sim.sinteses else []
    conversas = sim.conversas_recentes[-10:]
    topicos = getattr(sim, "_topicos_ativos", []) if hasattr(sim, "_topicos_ativos") else []
    from ..config import config
    topicos = config.topicos_ativos
    
    # Resumir conversas por tema
    temas_conv = {}
    for c in conversas:
        t = c.get("topico", "geral")
        temas_conv[t] = temas_conv.get(t, 0) + 1
    top_temas = sorted(temas_conv.items(), key=lambda x: -x[1])[:5]
    
    # Top agentes mais ativos
    atividade = {}
    for c in sim.conversas_recentes[-50:]:
        nome = c.get("parceiro_nome", "?")
        atividade[nome] = atividade.get(nome, 0) + 1
    top_ativos = sorted(atividade.items(), key=lambda x: -x[1])[:5]
    
    # Gerar insight via LLM
    contexto = f"""Vila INTEIA - {len(sim.personas)} consultores lendários ativos.
Step {sim.step}, {stats.get("total_conversas",0)} conversas, {stats.get("total_reflexoes",0)} reflexões.
Tópicos ativos: {", ".join(topicos) if topicos else "nenhum específico"}.
Temas mais discutidos: {", ".join(f"{t} ({n}x)" for t,n in top_temas)}.
Consultores mais ativos: {", ".join(f"{n} ({c})" for n,c in top_ativos)}.
Sínteses produzidas: {len(sinteses)}."""
    
    if sinteses:
        contexto += f"\nÚltima síntese: {sinteses[-1].get(sintese,)[:300]}"
    
    insight = chamar_llm_conversa(
        "Você é um analista estratégico da INTEIA. Gere um briefing executivo de 3 parágrafos com: 1) O que a Vila está discutindo 2) Insight principal emergente 3) Recomendação de ação. Seja específico e acionável. Max 200 palavras. Português.",
        contexto,
        modelo="rapido",
        max_tokens=400
    )
    
    return {
        "titulo": "Briefing Executivo — Vila INTEIA",
        "gerado_em": datetime.now().isoformat(),
        "step": sim.step,
        "metricas": {
            "agentes": len(sim.personas),
            "conversas": stats.get("total_conversas", 0),
            "reflexoes": stats.get("total_reflexoes", 0),
            "sinteses": len(sim.sinteses),
        },
        "temas_quentes": [{"tema": t, "mencoes": n} for t, n in top_temas],
        "consultores_ativos": [{"nome": n, "interacoes": c} for n, c in top_ativos],
        "insight_ia": insight or "Sem insight disponível. Rode mais steps.",
        "sinteses_recentes": [{"topico": s.get("topico"), "resumo": s.get("sintese","")[:200]} for s in sinteses],
    }


@router.post("/briefing/personalizado")
def briefing_personalizado(dados: dict):
    """Gera briefing focado num tema específico do cliente."""
    from .rotas_vila import obter_simulacao
    from ..engine.ia_client import chamar_llm_conversa
    import random
    
    tema = dados.get("tema", "estratégia geral")
    n_consultores = dados.get("n_consultores", 5)
    
    sim = obter_simulacao()
    agentes = list(sim.personas.values())
    selecionados = random.sample(agentes, min(n_consultores, len(agentes)))
    
    contribuicoes = []
    for ag in selecionados:
        resp = chamar_llm_conversa(
            f"Você é {ag.nome_exibicao}, {ag.titulo}. Responda com seu estilo único.",
            f"Em 3 frases, qual seu principal insight sobre: {tema}? Foque no que é acionável AGORA.",
            modelo="rapido",
            max_tokens=200
        )
        if resp:
            contribuicoes.append({"nome": ag.nome_exibicao, "categoria": ag.categoria, "tier": ag.tier, "insight": resp})
    
    # Síntese final
    todas = "\n".join([f"- {c["nome"]}: {c["insight"]}" for c in contribuicoes])
    sintese = chamar_llm_conversa(
        "Você é o sintetizador da INTEIA. Combine os insights abaixo em uma recomendação executiva de 1 parágrafo. Identifique convergências e divergências. Max 100 palavras.",
        todas,
        modelo="rapido",
        max_tokens=200
    )
    
    return {
        "tema": tema,
        "total_consultores": len(contribuicoes),
        "contribuicoes": contribuicoes,
        "sintese_executiva": sintese or "Síntese não disponível.",
        "gerado_em": datetime.now().isoformat(),
    }


# ============================================================
# AUTO-RESEARCH (Karpathy Loop)
# ============================================================

@router.post("/auto-research")
async def auto_research(dados: dict):
    """
    Auto-Research Loop inspirado em Andrej Karpathy.

    Loop iterativo: Gerar -> Avaliar -> Criticar -> Refinar -> Sintetizar
    Cada iteracao melhora a qualidade usando critica cruzada entre consultores.
    Para quando score >= threshold ou max_iterations atingido.

    Body:
        pergunta: str - A questao a ser pesquisada
        n_consultores: int (default 5) - Quantos consultores participam
        max_iterations: int (default 3) - Maximo de iteracoes do loop
        quality_threshold: float (default 8.0) - Score minimo para parar
        categorias: list (optional) - Filtrar por categorias de consultor
    """
    import asyncio
    from .rotas_vila import obter_simulacao
    from ..engine.auto_research import AutoResearchLoop

    sim = obter_simulacao()
    loop = AutoResearchLoop(sim)

    pergunta = dados.get("pergunta", "")
    if not pergunta:
        raise HTTPException(400, "Campo 'pergunta' obrigatorio")

    result = await asyncio.to_thread(
        loop.run,
        pergunta=pergunta,
        n_consultores=dados.get("n_consultores", 5),
        max_iterations=dados.get("max_iterations", 3),
        quality_threshold=dados.get("quality_threshold", 8.0),
        categorias=dados.get("categorias"),
    )

    return result


@router.get("/auto-research/history")
def auto_research_history():
    """Retorna historico de auto-research sessions."""
    from .rotas_vila import obter_simulacao
    from ..engine.auto_research import AutoResearchLoop

    sim = obter_simulacao()
    # AutoResearchLoop e stateless por enquanto, retorna vazio
    return {"total": 0, "sessions": []}
