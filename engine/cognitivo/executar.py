"""
EXECUTAR - Módulo de Execução de Ações.

Traduz o plano do agente em ação concreta:
- Move para o local planejado
- Atualiza estado (energia, humor)
- Registra a ação na memória
- USA FERRAMENTA REAL da oficina do local (se desafio ativo)
- PRODUZ ARTEFATO no workspace
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..persona import Persona

from ..campus import obter_local, calcular_distancia
from ..harness import trace_fase

logger = logging.getLogger("vila-inteia.executar")


@trace_fase("executar")
def executar(
    persona: Persona,
    hora_atual: datetime,
) -> dict:
    """
    Executa a ação planejada.

    Retorna:
    {
        "descricao": str,
        "emoji": str,
        "local_id": str,
        "moveu": bool,
        "energia_delta": int,
    }
    """
    rascunho = persona.rascunho
    resultado = {
        "descricao": rascunho.acao.descricao,
        "emoji": rascunho.acao.emoji,
        "local_id": rascunho.local_atual,
        "moveu": False,
        "energia_delta": 0,
    }

    # 1. Verificar se precisa se mover
    local_planejado = rascunho.acao.local_id
    if local_planejado and local_planejado != rascunho.local_atual:
        distancia = calcular_distancia(rascunho.local_atual, local_planejado)
        if distancia >= 0:  # rota existe
            # Mover para o local
            rascunho.local_atual = local_planejado
            persona.memoria_espacial.registrar_visita(local_planejado, hora_atual)
            resultado["local_id"] = local_planejado
            resultado["moveu"] = True

            # Custo de energia por movimento
            custo = distancia * 2
            rascunho.atualizar_energia(-custo)
            resultado["energia_delta"] -= custo

    # 2. Atualizar energia baseado na atividade
    desc_lower = rascunho.acao.descricao.lower()

    if any(p in desc_lower for p in ["dorm", "descans", "medita"]):
        delta = 15  # recuperação
    elif any(p in desc_lower for p in ["debate", "apresent", "sala de guerra"]):
        delta = -8  # alto consumo
    elif any(p in desc_lower for p in ["trabalh", "pesquis", "estud"]):
        delta = -5  # consumo moderado
    elif any(p in desc_lower for p in ["café", "almoç", "jant"]):
        delta = 5  # leve recuperação
    elif any(p in desc_lower for p in ["caminh", "jardim", "terraço"]):
        delta = 3  # leve recuperação
    else:
        delta = -2  # consumo base

    rascunho.atualizar_energia(delta)
    resultado["energia_delta"] += delta

    # 3. Atualizar humor baseado em energia e atividade
    if rascunho.energia > 80:
        rascunho.humor = "energizado"
    elif rascunho.energia > 60:
        rascunho.humor = "focado"
    elif rascunho.energia > 40:
        rascunho.humor = "neutro"
    elif rascunho.energia > 20:
        rascunho.humor = "cansado"
    else:
        rascunho.humor = "exausto"

    # 4. Atualizar progresso da ação
    rascunho.acao.progresso = min(
        rascunho.acao.progresso + 0.2, 1.0
    )

    # 5. Registrar na memória se ação é significativa
    importancia = 3
    if resultado["moveu"]:
        importancia = 4
    if any(p in desc_lower for p in ["debate", "apresent", "reuni"]):
        importancia = 5

    local_info = obter_local(resultado["local_id"])
    local_nome = local_info.nome if local_info else resultado["local_id"]

    persona.memoria.adicionar_evento(
        descricao=f"{persona.nome_exibicao} está {rascunho.acao.descricao} em {local_nome}",
        sujeito=persona.nome_exibicao,
        predicado=rascunho.acao.descricao,
        objeto=local_nome,
        local_id=resultado["local_id"],
        importancia=importancia,
        palavras_chave=set(desc_lower.split()[:4]),
    )

    # ================================================================
    # PRODUÇÃO REAL — Usar ferramenta da oficina do local
    # ================================================================
    # Se há desafio ativo e o local tem oficina, produzir artefato real.
    # Probabilidade: 20% por step (não toda vez — agente às vezes só observa).
    import random
    if random.random() < 0.20:
        artefato = _tentar_produzir(persona, resultado["local_id"], hora_atual)
        if artefato:
            resultado["artefato"] = artefato

    return resultado


def _tentar_produzir(persona: Persona, local_id: str, hora_atual: datetime) -> dict | None:
    """
    Tenta produzir artefato real usando a oficina do local.

    Retorna dict com info do artefato ou None se não produziu.
    """
    try:
        from ..oficinas import oficina_do_local
        from ..desafio import Contribuicao
    except ImportError:
        return None

    oficina = oficina_do_local(local_id)
    if not oficina or not oficina.ferramentas:
        return None

    # Verificar se há desafio ativo — buscar simulação sem circular import
    sim = None
    try:
        # Caminho 1: via referência global da rotas_vila (se API rodando)
        from api.rotas_vila import simulacao as _sim_global
        if _sim_global is not None:
            sim = _sim_global
    except Exception:
        pass
    if sim is None:
        try:
            from api.rotas_vila import obter_simulacao
            sim = obter_simulacao()
        except Exception:
            return None
    if not sim or not sim.desafio or not sim.desafio.ativo:
        return None
    desafio = sim.desafio
    fase = desafio.fase_atual
    if not fase:
        return None

    # Escolher ferramenta mais relevante para a fase
    ferramenta = oficina.ferramentas[0]  # default: primeira
    desc_fase = fase.descricao.lower()
    for f in oficina.ferramentas:
        if f.tipo == "codigo" and any(w in desc_fase for w in ("prototip", "modelo", "calcul")):
            ferramenta = f
            break
        if f.tipo == "pesquisa" and any(w in desc_fase for w in ("pesquis", "mapear", "diagnostic")):
            ferramenta = f
            break
        if f.tipo == "escrita" and any(w in desc_fase for w in ("redigir", "propor", "apresent")):
            ferramenta = f
            break
        if f.tipo == "analise" and any(w in desc_fase for w in ("analis", "simul", "cenario")):
            ferramenta = f
            break
        if f.tipo == "votacao" and any(w in desc_fase for w in ("votar", "deliber", "julg")):
            ferramenta = f
            break

    # Verificar saldo
    custo = ferramenta.custo_coins
    saldo = sim.incentivos.saldo(persona.id)
    if custo > saldo:
        return None

    # PRODUZIR ARTEFATO via LLM
    from ..ia_client import chamar_llm_conversa, MODELO_RAPIDO
    from ..arquetipos import gerar_prompt_profundo

    system = gerar_prompt_profundo(persona.dados_consultor)
    system += f"""

CONTEXTO DE PRODUÇÃO:
Você está no(a) {oficina.nome_oficina} da Vila INTEIA.
Ferramenta disponível: {ferramenta.nome} — {ferramenta.descricao}
Desafio: {desafio.nome}
Fase: {fase.nome} — {fase.descricao}

TAREFA: Produza um artefato CONCRETO usando a ferramenta '{ferramenta.nome}'.
Formato: {ferramenta.tipo_artefato.upper()}
Seja ESPECÍFICO, ACIONÁVEL e use sua EXPERTISE real.
Máximo 500 palavras. Vá direto ao conteúdo — sem introdução."""

    user_msg = (
        f"Usando a ferramenta '{ferramenta.nome}', produza uma entrega concreta "
        f"para a fase '{fase.nome}' do desafio '{desafio.nome}'. "
        f"Sua expertise: {', '.join(persona.rascunho.areas_expertise[:3])}."
    )

    conteudo = chamar_llm_conversa(system, user_msg, modelo=MODELO_RAPIDO, max_tokens=600)
    if not conteudo:
        return None

    # Salvar artefato no workspace (usar instância da simulação, não criar nova)
    workspace = sim.workspace
    ext = ferramenta.tipo_artefato or "md"
    slug = persona.id.lower()
    nome_arquivo = f"{fase.id}_{slug}_{ferramenta.id}.{ext}"

    meta = workspace.escrever(
        desafio_id=desafio.id,
        agente_id=persona.id,
        agente_nome=persona.nome_exibicao,
        nome_arquivo=nome_arquivo,
        conteudo=conteudo,
        tipo=ferramenta.tipo,
    )

    # Cobrar e recompensar
    sim.incentivos.cobrar_recurso(persona.id, custo, ferramenta.nome, sim.step)
    sim.incentivos.recompensar(persona.id, "proposta_nova", sim.step,
                                f"Produziu {nome_arquivo}")
    sim.incentivos.registrar_atividade(persona.id, sim.step)

    # Registrar como contribuição do desafio
    contrib = Contribuicao(
        agente_id=persona.id,
        agente_nome=persona.nome_exibicao,
        conteudo=f"[{ferramenta.nome}] {conteudo[:150]}",
        tipo="proposta",
    )
    desafio.registrar_contribuicao(contrib, sim.step)

    # Registrar na memória do agente
    persona.memoria.adicionar_pensamento(
        descricao=f"Produzi '{nome_arquivo}' usando {ferramenta.nome} no(a) {oficina.nome_oficina}",
        importancia=7,
        palavras_chave={ferramenta.id, fase.id, "producao"},
    )

    oficina.artefatos_produzidos += 1

    logger.info(
        f"ARTEFATO: {persona.nome_exibicao} produziu {nome_arquivo} "
        f"no(a) {oficina.nome_oficina} ({ferramenta.nome})"
    )

    return {
        "arquivo": nome_arquivo,
        "ferramenta": ferramenta.nome,
        "oficina": oficina.nome_oficina,
        "agente": persona.nome_exibicao,
        "tipo": ferramenta.tipo,
        "tamanho": len(conteudo),
    }
