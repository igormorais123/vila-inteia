"""
Economia viva da Vila INTEIA.

Cada habitante tem ambição financeira (0..1) que modula:
    - probabilidade de aceitar trabalho
    - esforço / qualidade entregue
    - tolerância a risco

Cada ação produz valor:
    - matéria publicada no Mirante      → R$ 50..300 (base) × multiplicadores
    - oficina concluída                  → R$ 20..100
    - desafio vencido                    → R$ 200..1000
    - voto em assembleia (quórum)       → R$ 1..5
    - contribuição em fase               → R$ 5..30

Multiplicadores:
    qualidade (Chateaubriand score)   × (0.5 .. 1.5)
    publicação Mirante                 × 1.5
    matéria capa                       × 2.0
    engajamento (curtidas, comentários) × (1 .. 1.3)

A tabela vila_transacoes registra tudo. vila_economia_perfis mantém saldo
corrente + ambição + histórico de ganhos por habitante.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from engine.supabase_db import inserir, buscar, atualizar

logger = logging.getLogger("vila-inteia.economia")


# =========================================================
# Tabela de precificação base (R$ sintéticos)
# =========================================================

PRECO_BASE = {
    "materia_submetida": 30.0,         # só por submeter
    "materia_aprovada": 100.0,          # + Chateaubriand aprovou
    "materia_publicada_mirante": 200.0, # + Mirante publicou
    "materia_capa": 500.0,              # + virou capa
    "oficina_concluida": 50.0,
    "desafio_fase_completa": 150.0,
    "desafio_vencido": 800.0,
    "voto_assembleia": 3.0,
    "contribuicao": 15.0,
    "post_rede_social": 2.0,
    "comentario_util": 1.0,
}


# =========================================================
# Perfis econômicos
# =========================================================

def garantir_perfil(
    vila_id: str,
    agente_id: str,
    ambicao: float = 0.5,
    propensao_risco: float = 0.5,
    especialidades: Optional[list] = None,
) -> dict:
    """Cria ou retorna perfil econômico do habitante."""
    existentes = buscar(
        "vila_economia_perfis",
        f"vila_id=eq.{vila_id}&agente_id=eq.{agente_id}",
    )
    if existentes:
        return existentes[0]

    registro = {
        "vila_id": vila_id,
        "agente_id": agente_id,
        "ambicao_financeira": round(max(0.0, min(1.0, ambicao)), 3),
        "propensao_risco": round(max(0.0, min(1.0, propensao_risco)), 3),
        "valor_reserva": 0,
        "especialidades": especialidades or [],
        "historico_ganhos": 0,
    }
    return inserir("vila_economia_perfis", registro) or registro


def get_perfil(vila_id: str, agente_id: str) -> Optional[dict]:
    rs = buscar("vila_economia_perfis",
                f"vila_id=eq.{vila_id}&agente_id=eq.{agente_id}")
    return rs[0] if rs else None


def atualizar_ambicao(vila_id: str, agente_id: str, ambicao: float) -> bool:
    data = {"ambicao_financeira": round(max(0.0, min(1.0, ambicao)), 3)}
    return atualizar(
        "vila_economia_perfis",
        f"vila_id=eq.{vila_id}&agente_id=eq.{agente_id}",
        data,
    ) is not None


# =========================================================
# Precificação
# =========================================================

def precificar(tipo_trabalho: str, contexto: Optional[dict] = None) -> float:
    """Calcula valor final de um trabalho, aplicando multiplicadores."""
    contexto = contexto or {}
    base = PRECO_BASE.get(tipo_trabalho, 10.0)

    # Qualidade: score 0..1 → 0.5..1.5
    score = float(contexto.get("score", 0.7))
    mult_qualidade = 0.5 + score  # score=1 => 1.5

    # Engajamento: 0..1 → 1.0..1.3
    engajamento = float(contexto.get("engajamento", 0.0))
    mult_engajamento = 1.0 + (engajamento * 0.3)

    # Destaque
    mult_destaque = 1.0
    if contexto.get("capa"):
        mult_destaque = 2.0
    elif contexto.get("publicado_mirante"):
        mult_destaque = 1.5

    valor = base * mult_qualidade * mult_engajamento * mult_destaque
    return round(valor, 2)


# =========================================================
# Decisão do habitante: aceita ou não?
# =========================================================

def decidir_aceitar(
    perfil: dict,
    tipo_trabalho: str,
    contexto: Optional[dict] = None,
    custo_cognitivo: float = 0.3,
) -> tuple[bool, float]:
    """
    Decide se o habitante aceita o trabalho.

    Retorna (aceita, probabilidade).
    """
    contexto = contexto or {}
    ambicao = float(perfil.get("ambicao_financeira", 0.5))
    propensao = float(perfil.get("propensao_risco", 0.5))

    recompensa = precificar(tipo_trabalho, contexto)
    recompensa_norm = min(recompensa / 500.0, 1.0)  # normaliza em 0..1

    # Função de utilidade simples
    utilidade = (
        ambicao * recompensa_norm
        + propensao * float(contexto.get("risco", 0.0)) * 0.3
        - custo_cognitivo * (1 - ambicao)
    )
    prob = max(0.0, min(1.0, 0.3 + utilidade * 0.7))
    # Determinístico aqui (o caller pode rolar dado se quiser estocástico):
    aceita = prob >= 0.5
    return aceita, round(prob, 3)


# =========================================================
# Creditar trabalho (transação positiva)
# =========================================================

def creditar(
    vila_id: str,
    agente_id: str,
    tipo_trabalho: str,
    contexto: Optional[dict] = None,
    descricao: str = "",
) -> Optional[dict]:
    """Credita valor pelo trabalho realizado. Retorna a transação."""
    valor = precificar(tipo_trabalho, contexto)

    transacao = {
        "id": str(uuid.uuid4()),
        "vila_id": vila_id,
        "agente_id": agente_id,
        "tipo": tipo_trabalho,
        "valor": valor,
        "descricao": descricao or f"Crédito por {tipo_trabalho}",
        "contexto": contexto or {},
        "criado_em": datetime.now(timezone.utc).isoformat(),
    }
    registrada = inserir("vila_transacoes", transacao)

    # Atualizar saldo e histórico
    perfil = get_perfil(vila_id, agente_id)
    if perfil:
        novo_saldo = float(perfil.get("valor_reserva", 0)) + valor
        novo_historico = float(perfil.get("historico_ganhos", 0)) + valor
        atualizar(
            "vila_economia_perfis",
            f"vila_id=eq.{vila_id}&agente_id=eq.{agente_id}",
            {
                "valor_reserva": round(novo_saldo, 2),
                "historico_ganhos": round(novo_historico, 2),
            },
        )

    return registrada


def debitar(
    vila_id: str,
    agente_id: str,
    valor: float,
    motivo: str,
    contexto: Optional[dict] = None,
) -> tuple[bool, Optional[dict]]:
    """Debita (contratar colaborador, patrocinar, multa). Valida saldo."""
    perfil = get_perfil(vila_id, agente_id)
    if not perfil:
        return False, None

    saldo = float(perfil.get("valor_reserva", 0))
    if valor > saldo:
        return False, None

    transacao = {
        "id": str(uuid.uuid4()),
        "vila_id": vila_id,
        "agente_id": agente_id,
        "tipo": f"debito_{motivo}",
        "valor": -valor,
        "descricao": motivo,
        "contexto": contexto or {},
        "criado_em": datetime.now(timezone.utc).isoformat(),
    }
    registrada = inserir("vila_transacoes", transacao)
    atualizar(
        "vila_economia_perfis",
        f"vila_id=eq.{vila_id}&agente_id=eq.{agente_id}",
        {"valor_reserva": round(saldo - valor, 2)},
    )
    return True, registrada


# =========================================================
# Relatório
# =========================================================

def top_ricos(vila_id: str, n: int = 10) -> list[dict]:
    return buscar(
        "vila_economia_perfis",
        f"vila_id=eq.{vila_id}&order=valor_reserva.desc&limit={n}",
    )


def historico_agente(vila_id: str, agente_id: str, limite: int = 50) -> list[dict]:
    return buscar(
        "vila_transacoes",
        f"vila_id=eq.{vila_id}&agente_id=eq.{agente_id}&order=criado_em.desc&limit={limite}",
    )
