"""
Constituinte — ciclo de propostas com detecção de problema real.

Agente só propõe artigo se citar EVENTO DOCUMENTADO da vila. Evita
constituição hipotética.

Pipeline:
    detectar_problemas_reais(vila_id)   -> [{evento, natureza, afetados}]
    propor_via_agente(agente, problema) -> artigo em 'proposto'
    abrir_assembleia(artigo)            -> transiciona p/ 'em_votacao'
    colher_votos_sinteticos(...)        -> simula votação (opcional)
    apurar + promulgar_se_aprovado     -> (constituicao.py)
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from engine.ia_client import chamar_llm_conversa
from engine.constituicao import propor_artigo, abrir_votacao, votar
from engine.supabase_db import buscar

logger = logging.getLogger("vila-inteia.constituinte")


PERSONA_CONSTITUINTE = """Você é um habitante da Vila INTEIA, democrata e \
pragmático. Sua tarefa é identificar problemas REAIS (não hipotéticos) na \
vida da Vila e propor artigos constitucionais que resolvam. Regra-mãe: \
SEMPRE citar um evento concreto e recente da Vila como justificativa. \
Proibido propor regra sobre algo que não aconteceu."""


# =========================================================
# Detecção de problema real
# =========================================================

def detectar_problemas_reais(vila_id: str, limite: int = 5) -> list[dict]:
    """
    Varre eventos recentes da Vila e identifica lacunas/conflitos que
    merecem artigo constitucional.

    Heurísticas simples por enquanto:
      - matérias rejeitadas por Chateaubriand 3+ vezes pelo mesmo motivo
      - desafios interrompidos sem quórum
      - tickets executivos abertos há muito tempo
      - transações anômalas

    Retorna [{natureza, evento, afetados, severidade 1..5}].
    """
    problemas = []

    # 1. Matérias rejeitadas recorrentemente por mesmo motivo
    rejeitadas = buscar(
        "vila_submissoes_mirante",
        f"vila_id=eq.{vila_id}&status=in.(bloqueado_mirante,rejeitado)&order=submetido_em.desc&limit=30"
    )
    if len(rejeitadas) >= 3:
        problemas.append({
            "natureza": "publicacao",
            "evento": f"{len(rejeitadas)} matérias bloqueadas recentemente",
            "afetados": list({r.get("agente_id") for r in rejeitadas})[:10],
            "severidade": 3,
        })

    # 2. Tickets executivos antigos sem resposta
    tickets = buscar(
        "vila_tickets_executivo",
        "status=eq.aberto&order=criado_em.asc&limit=10"
    )
    if tickets:
        problemas.append({
            "natureza": "executivo_inerte",
            "evento": f"{len(tickets)} ticket(s) estrutural(is) aguardando implementação",
            "afetados": [],
            "severidade": 2,
        })

    # 3. Desigualdade econômica grande
    perfis = buscar(
        "vila_economia_perfis",
        f"vila_id=eq.{vila_id}&order=valor_reserva.desc&limit=50"
    )
    if len(perfis) >= 10:
        valores = [float(p.get("valor_reserva", 0)) for p in perfis]
        if valores and valores[0] > 10 * (valores[len(valores)//2] or 1):
            problemas.append({
                "natureza": "desigualdade_economica",
                "evento": "Top 1 tem mais de 10x a mediana",
                "afetados": [p["agente_id"] for p in perfis[:3]],
                "severidade": 4,
            })

    return problemas[:limite]


# =========================================================
# Proposta via agente (LLM)
# =========================================================

def propor_via_agente(
    vila_id: str,
    agente_id: str,
    agente_nome: str,
    problema: dict,
) -> Optional[dict]:
    """Agente redige artigo a partir do problema detectado."""
    prompt = f"""Problema REAL identificado na Vila:
  Natureza: {problema.get('natureza', '?')}
  Evento: {problema.get('evento', '?')}
  Afetados: {problema.get('afetados', [])}
  Severidade (1-5): {problema.get('severidade', 3)}

Proponha UM artigo constitucional que resolva. Responda em JSON:
{{
  "tipo": "operacional" | "economico" | "estrutural",
  "titulo": "até 120 caracteres",
  "texto": "o artigo em si, linguagem jurídica simples, 80-600 chars",
  "justificativa": "por que este artigo resolve, 100-400 chars"
}}

Regras:
  - operacional = sistema aplica automaticamente (filtros, revisores, etc)
  - economico   = muda regras de dinheiro/ambição
  - estrutural  = requer mudança de código/infra (gera ticket pro dev)"""

    try:
        resposta = chamar_llm_conversa(
            system=PERSONA_CONSTITUINTE,
            user=prompt,
            temperatura=0.6,
            max_tokens=800,
        )
        data = _extrair_json(resposta)
    except Exception as e:
        logger.error(f"LLM falhou ao propor: {e}")
        return None

    return propor_artigo(
        vila_id=vila_id,
        tipo=data.get("tipo", "operacional"),
        titulo=data.get("titulo", "(sem título)"),
        texto=data.get("texto", ""),
        justificativa=data.get("justificativa", ""),
        proposto_por=agente_id,
        evento_origem=problema.get("evento", ""),
    )


# =========================================================
# Assembleia sintética (votação por LLM)
# =========================================================

def colher_votos_sinteticos(
    artigo_id: str,
    artigo: dict,
    habitantes: list[dict],
    fracao_votantes: float = 0.5,
) -> dict:
    """
    Simula votação pedindo a cada habitante um voto em caráter.
    Ineficiente para milhares — aceita fração de votantes.

    habitantes: [{id, nome, categoria, traço_personalidade, ...}]
    """
    import random
    random.shuffle(habitantes)
    n = max(5, int(len(habitantes) * fracao_votantes))
    amostra = habitantes[:n]

    contagem = {"favor": 0, "contra": 0, "abstencao": 0}
    for h in amostra:
        prompt = f"""Vote no artigo:
Título: {artigo.get('titulo')}
Tipo: {artigo.get('tipo')}
Texto: {artigo.get('texto')}
Justificativa: {artigo.get('justificativa')}

Considerando seu perfil ({h.get('nome')}, {h.get('categoria','?')}), \
responda em JSON: {{"voto": "favor"|"contra"|"abstencao", "razao": "..."}}"""
        try:
            resp = chamar_llm_conversa(
                system=f"Você é {h.get('nome')}, habitante da Vila INTEIA.",
                user=prompt,
                temperatura=0.7,
                max_tokens=200,
            )
            data = _extrair_json(resp)
            voto = data.get("voto", "abstencao")
            if voto not in contagem:
                voto = "abstencao"
            ok = votar(artigo_id, h.get("id", ""), voto,
                       agente_nome=h.get("nome", ""),
                       justificativa=data.get("razao", ""))
            if ok:
                contagem[voto] += 1
        except Exception as e:
            logger.debug(f"Voto pulado ({h.get('nome')}): {e}")
            continue

    return {"total_votantes": n, **contagem}


def abrir_assembleia(artigo_id: str, total_habitantes_vila: int,
                     quorum_pct: float = 0.3) -> bool:
    """Abre votação com quórum derivado."""
    quorum = max(3, int(total_habitantes_vila * quorum_pct))
    return abrir_votacao(artigo_id, quorum)


# =========================================================
# Helpers
# =========================================================

def _extrair_json(texto: str) -> dict:
    t = texto.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.endswith("```"):
            t = t.rsplit("```", 1)[0]
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        t = t[i:j + 1]
    return json.loads(t)
