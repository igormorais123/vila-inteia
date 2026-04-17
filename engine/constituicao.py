"""
Constituição viva da Vila INTEIA.

Três tipos de artigo constitucional:

    OPERACIONAL — regra que o sistema aplica automaticamente
        ex: "Matérias sobre tema X precisam de 2 revisores antes do envio"
        enforcement: lido por Chateaubriand, motor de oficinas, etc.

    ECONÔMICO — altera precificação / ambição / repartição
        ex: "Autor de matéria capa recebe 2x"
        enforcement: lido por engine.economia.precificar()

    ESTRUTURAL — requer mudança de código/infra
        ex: "Banir habitante Y", "Adicionar módulo de votação secreta"
        enforcement: gera ticket em vila_tickets_executivo → dev humano

Ciclo de vida:
    proposto → em_votacao → aprovado|rejeitado → vigente → (eventualmente) revogado

Quórum: mínimo 30% dos habitantes ativos votarem, maioria simples aprova.
(configurável via vila_instancias.metadados.quorum_pct)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from engine.supabase_db import inserir, buscar, atualizar

logger = logging.getLogger("vila-inteia.constituicao")


TIPOS_VALIDOS = {"operacional", "economico", "estrutural"}
STATUS_VALIDOS = {"proposto", "em_votacao", "aprovado", "rejeitado", "vigente", "revogado"}


# =========================================================
# Proposta
# =========================================================

def propor_artigo(
    vila_id: str,
    tipo: str,
    titulo: str,
    texto: str,
    justificativa: str,
    proposto_por: str,
    evento_origem: str = "",
) -> Optional[dict]:
    """
    Propõe novo artigo. Exige evento_origem não-vazio: forçar que o agente
    aponte um evento real da vila, não hipótese.
    """
    if tipo not in TIPOS_VALIDOS:
        logger.error(f"Tipo inválido: {tipo}")
        return None
    if not evento_origem or len(evento_origem) < 10:
        logger.warning(f"Proposta sem evento_origem concreto, rejeitada: {titulo}")
        return None
    if len(texto) < 40:
        logger.warning(f"Texto muito curto: {titulo}")
        return None

    # Próximo número
    ultimos = buscar("vila_constituicao_artigos",
                     f"vila_id=eq.{vila_id}&order=numero.desc&limit=1")
    proximo_num = (ultimos[0]["numero"] + 1) if ultimos else 1

    artigo = {
        "id": str(uuid.uuid4()),
        "vila_id": vila_id,
        "numero": proximo_num,
        "tipo": tipo,
        "titulo": titulo[:200],
        "texto": texto[:4000],
        "justificativa": justificativa[:2000],
        "proposto_por": proposto_por,
        "evento_origem": evento_origem[:1000],
        "status": "proposto",
    }
    return inserir("vila_constituicao_artigos", artigo)


def abrir_votacao(artigo_id: str, quorum_necessario: int) -> bool:
    return atualizar(
        "vila_constituicao_artigos",
        f"id=eq.{artigo_id}",
        {"status": "em_votacao", "quorum_necessario": int(quorum_necessario)},
    ) is not None


# =========================================================
# Voto
# =========================================================

def votar(
    artigo_id: str,
    agente_id: str,
    voto: str,
    agente_nome: str = "",
    justificativa: str = "",
) -> bool:
    """Registra voto (favor/contra/abstencao)."""
    if voto not in {"favor", "contra", "abstencao"}:
        return False

    # Upsert-ish: conflito no UNIQUE(artigo, agente) retorna erro, o que é ok
    registro = {
        "id": str(uuid.uuid4()),
        "artigo_id": artigo_id,
        "agente_id": agente_id,
        "agente_nome": agente_nome,
        "voto": voto,
        "justificativa": justificativa[:1000],
    }
    ok = inserir("vila_constituicao_votos", registro) is not None

    # Recalcular contagens
    if ok:
        _atualizar_contagem_votos(artigo_id)
    return ok


def _atualizar_contagem_votos(artigo_id: str):
    votos = buscar("vila_constituicao_votos", f"artigo_id=eq.{artigo_id}")
    favor = sum(1 for v in votos if v["voto"] == "favor")
    contra = sum(1 for v in votos if v["voto"] == "contra")
    abstencao = sum(1 for v in votos if v["voto"] == "abstencao")
    atualizar(
        "vila_constituicao_artigos",
        f"id=eq.{artigo_id}",
        {
            "votos_favor": favor,
            "votos_contra": contra,
            "votos_abstencao": abstencao,
        },
    )


# =========================================================
# Apuração e promulgação
# =========================================================

def apurar(artigo_id: str) -> dict:
    """
    Verifica se atingiu quórum e decide aprovação.
    Retorna {status, favor, contra, abstencao, total, aprovado}.
    """
    rs = buscar("vila_constituicao_artigos", f"id=eq.{artigo_id}")
    if not rs:
        return {"erro": "artigo não encontrado"}
    a = rs[0]

    favor = a.get("votos_favor", 0)
    contra = a.get("votos_contra", 0)
    abstencao = a.get("votos_abstencao", 0)
    total = favor + contra + abstencao
    quorum = a.get("quorum_necessario", 0)

    atingiu_quorum = total >= quorum
    aprovado = atingiu_quorum and favor > contra

    return {
        "artigo_id": artigo_id,
        "status_atual": a["status"],
        "favor": favor,
        "contra": contra,
        "abstencao": abstencao,
        "total": total,
        "quorum_necessario": quorum,
        "atingiu_quorum": atingiu_quorum,
        "aprovado": aprovado,
    }


def promulgar_se_aprovado(artigo_id: str) -> Optional[dict]:
    """Se aprovado, promulga. Se estrutural, cria ticket executivo."""
    apuracao = apurar(artigo_id)
    if not apuracao.get("aprovado"):
        return None

    rs = buscar("vila_constituicao_artigos", f"id=eq.{artigo_id}")
    if not rs:
        return None
    artigo = rs[0]

    agora = datetime.now(timezone.utc).isoformat()
    atualizado = atualizar(
        "vila_constituicao_artigos",
        f"id=eq.{artigo_id}",
        {"status": "vigente", "promulgado_em": agora},
    )

    # Estrutural → gera ticket pro dev humano
    if artigo.get("tipo") == "estrutural":
        ticket = {
            "id": str(uuid.uuid4()),
            "vila_id": artigo.get("vila_id"),
            "artigo_id": artigo_id,
            "titulo": f"[Constituinte] {artigo.get('titulo','')}",
            "descricao": (
                f"Artigo estrutural promulgado pela Vila.\n\n"
                f"Texto: {artigo.get('texto','')}\n\n"
                f"Justificativa: {artigo.get('justificativa','')}\n\n"
                f"Proposto por: {artigo.get('proposto_por','')}"
            ),
            "tipo": "implementacao_estrutural",
            "urgencia": 3,
            "status": "aberto",
        }
        inserir("vila_tickets_executivo", ticket)
        logger.info(f"Ticket executivo gerado para artigo {artigo_id}")

    return atualizado


def revogar(artigo_id: str, motivo: str = "") -> bool:
    return atualizar(
        "vila_constituicao_artigos",
        f"id=eq.{artigo_id}",
        {
            "status": "revogado",
            "revogado_em": datetime.now(timezone.utc).isoformat(),
        },
    ) is not None


# =========================================================
# Consulta
# =========================================================

def listar_vigentes(vila_id: str, tipo: Optional[str] = None) -> list[dict]:
    q = f"vila_id=eq.{vila_id}&status=eq.vigente&order=numero.asc"
    if tipo:
        q = f"tipo=eq.{tipo}&{q}"
    return buscar("vila_constituicao_artigos", q)


def listar_em_votacao(vila_id: str) -> list[dict]:
    return buscar(
        "vila_constituicao_artigos",
        f"vila_id=eq.{vila_id}&status=eq.em_votacao&order=numero.asc",
    )


def listar_tickets_executivo(status: str = "aberto", limite: int = 50) -> list[dict]:
    return buscar(
        "vila_tickets_executivo",
        f"status=eq.{status}&order=criado_em.desc&limit={limite}",
    )
