"""
Persistência Supabase — Vila INTEIA na nuvem.

Config via env:
    SUPABASE_VILA_URL  — https://<projeto>.supabase.co
    SUPABASE_VILA_KEY  — anon key

Tabelas:
    vila_desafios          — Desafios coletivos
    vila_fases             — Fases de cada desafio
    vila_contribuicoes     — Contribuições dos agentes
    vila_carteiras         — Economia INTEIA Coins
    vila_transacoes        — Histórico de transações
    vila_artefatos         — Produtos do workspace
    vila_publicacoes_mirante — Artigos no jornal

Usa REST API do Supabase com anon key (policies permitem tudo).
Sobrevive restart do Render. Dados na nuvem.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger("vila-inteia.supabase")

# Config do .env ou variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_VILA_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_VILA_KEY", "")

# Carregar .env se faltando
if not SUPABASE_KEY or not SUPABASE_URL:
    for env_path in [".env", "vila-inteia/.env", os.path.join(os.path.dirname(__file__), "..", ".env")]:
        try:
            with open(env_path) as f:
                for line in f:
                    if line.startswith("SUPABASE_VILA_KEY=") and not SUPABASE_KEY:
                        SUPABASE_KEY = line.split("=", 1)[1].strip()
                    elif line.startswith("SUPABASE_VILA_URL=") and not SUPABASE_URL:
                        SUPABASE_URL = line.split("=", 1)[1].strip()
            if SUPABASE_KEY and SUPABASE_URL:
                break
        except FileNotFoundError:
            continue


def _headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _request(method: str, table: str, data: dict = None, params: str = "") -> list | dict | None:
    """Faz request REST ao Supabase."""
    if not SUPABASE_KEY:
        logger.warning("SUPABASE_VILA_KEY não configurada")
        return None

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if params:
        url += f"?{params}"

    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=_headers(), method=method)

    try:
        with urlopen(req, timeout=10) as resp:
            text = resp.read().decode()
            return json.loads(text) if text else None
    except URLError as e:
        logger.error(f"Supabase {method} {table}: {e}")
        return None
    except json.JSONDecodeError:
        return None


# ============================================================
# OPERAÇÕES CRUD
# ============================================================

def inserir(table: str, data: dict) -> dict | None:
    """Insere registro. Retorna o registro criado."""
    result = _request("POST", table, data)
    if isinstance(result, list) and result:
        return result[0]
    return result


def buscar(table: str, params: str = "") -> list:
    """Busca registros. Retorna lista."""
    result = _request("GET", table, params=params)
    return result if isinstance(result, list) else []


def atualizar(table: str, filtro: str, data: dict) -> dict | None:
    """Atualiza registro por filtro. Ex: filtro='id=eq.abc'"""
    result = _request("PATCH", table, data, params=filtro)
    if isinstance(result, list) and result:
        return result[0]
    return result


def deletar(table: str, filtro: str) -> bool:
    """Deleta registro por filtro."""
    _request("DELETE", table, params=filtro)
    return True


# ============================================================
# FUNÇÕES ESPECÍFICAS DA VILA
# ============================================================

def salvar_desafio(desafio_dict: dict) -> bool:
    """Salva ou atualiza desafio no Supabase."""
    did = desafio_dict.get("id", "")
    if not did:
        return False

    # Upsert: tentar update, se não existe, insert
    dados = {
        "id": did,
        "nome": desafio_dict.get("nome", ""),
        "descricao": (desafio_dict.get("descricao", "") or "")[:5000],
        "icone": desafio_dict.get("icone", "🎯"),
        "status": desafio_dict.get("status", "inativo"),
        "fase_atual_idx": desafio_dict.get("fase_atual_idx", 0),
        "progresso_total": desafio_dict.get("progresso_total", 0),
        "consenso_minimo": desafio_dict.get("consenso_minimo", 0.6),
        "steps_por_fase": desafio_dict.get("steps_por_fase", 100),
        "total_contribuicoes": desafio_dict.get("metricas", {}).get("total_contribuicoes", 0),
        "total_votos": desafio_dict.get("metricas", {}).get("total_votos", 0),
    }

    # Tentar upsert via header
    url = f"{SUPABASE_URL}/rest/v1/vila_desafios"
    headers = _headers()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    body = json.dumps(dados).encode()
    req = Request(url, data=body, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        logger.error(f"Salvar desafio: {e}")
        return False


def salvar_contribuicao(desafio_id: str, contrib: dict) -> bool:
    """Salva contribuição no Supabase."""
    dados = {
        "desafio_id": desafio_id,
        "fase_id": contrib.get("fase_id", ""),
        "agente_id": contrib.get("agente_id", ""),
        "agente_nome": contrib.get("agente_nome", ""),
        "conteudo": (contrib.get("conteudo", "") or "")[:5000],
        "tipo": contrib.get("tipo", "proposta"),
        "step": contrib.get("step", 0),
    }
    return inserir("vila_contribuicoes", dados) is not None


def salvar_carteira(agente_id: str, carteira_dict: dict) -> bool:
    """Salva carteira no Supabase (upsert)."""
    dados = {
        "agente_id": agente_id,
        "saldo": carteira_dict.get("saldo", 1000),
        "reputacao": carteira_dict.get("reputacao", 50.0),
        "contribuicoes_total": carteira_dict.get("contribuicoes_total", 0),
        "cargo_atual": carteira_dict.get("cargo_atual", ""),
    }

    url = f"{SUPABASE_URL}/rest/v1/vila_carteiras"
    headers = _headers()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    body = json.dumps(dados).encode()
    req = Request(url, data=body, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        logger.error(f"Salvar carteira: {e}")
        return False


def salvar_artefato(desafio_id: str, artefato: dict) -> bool:
    """Salva artefato produzido."""
    dados = {
        "desafio_id": desafio_id,
        "agente_id": artefato.get("agente_id", ""),
        "agente_nome": artefato.get("agente_nome", ""),
        "nome_arquivo": artefato.get("arquivo", ""),
        "tipo": artefato.get("tipo", ""),
        "conteudo": (artefato.get("conteudo", "") or "")[:50000],
        "tamanho": artefato.get("tamanho", 0),
        "oficina": artefato.get("oficina", ""),
        "ferramenta": artefato.get("ferramenta", ""),
    }
    return inserir("vila_artefatos", dados) is not None


def carregar_desafio(desafio_id: str) -> dict | None:
    """Carrega desafio do Supabase."""
    resultados = buscar("vila_desafios", f"id=eq.{desafio_id}")
    return resultados[0] if resultados else None


def carregar_carteiras() -> dict:
    """Carrega todas as carteiras."""
    resultados = buscar("vila_carteiras")
    return {r["agente_id"]: r for r in resultados}


def carregar_artefatos(desafio_id: str) -> list:
    """Carrega artefatos de um desafio."""
    return buscar("vila_artefatos", f"desafio_id=eq.{desafio_id}&order=created_at.desc")


def status_conexao() -> dict:
    """Verifica conexão com Supabase."""
    if not SUPABASE_KEY:
        return {"conectado": False, "motivo": "SUPABASE_VILA_KEY não configurada"}

    try:
        result = buscar("vila_desafios", "select=id&limit=1")
        return {"conectado": True, "tabelas_ok": True}
    except Exception as e:
        return {"conectado": False, "motivo": str(e)}
