"""
Hash canônico da cadeia de traces. Nunca usa conteúdo textual — só metadados.
"""

from __future__ import annotations

import hashlib
import json

from engine.proveniencia.construcao import Proveniencia, serializar_arvore


def hash_trace(prov: Proveniencia) -> str:
    """
    SHA-256 determinístico da árvore serializada + lista de agentes.
    Não inclui timestamps em milissegundo para permitir reprodução.
    """
    payload = {
        "materia_id": prov.materia_id,
        "agentes": sorted(prov.agentes_envolvidos),
        "fases": prov.fases_cobertas,
        "tokens_totais": prov.tokens_totais,
        "arvore": serializar_arvore(prov.raiz),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    h = hashlib.sha256(raw).hexdigest()
    prov.trace_hash = h
    return h


def hash_materia(materia_conteudo: str, trace_hash: str) -> str:
    """Hash composto para publicação: conteúdo + proveniência."""
    raw = (materia_conteudo + "|" + trace_hash).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
