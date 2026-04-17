"""
Executor Constitucional — aplica artigos vigentes ao runtime.

Outros módulos consultam este aqui quando vão tomar decisão que PODE estar
restringida pela Constituição:

    from engine import executor_constitucional as exec_const

    # Chateaubriand antes de aprovar matéria
    if not exec_const.pode_publicar(vila_id, materia_dict):
        rejeitar("regra operacional bloqueou")

    # Motor de economia antes de precificar
    multiplicador = exec_const.multiplicador_economico(vila_id, tipo_trabalho)

    # Engine de habitantes antes de admitir
    if not exec_const.pode_admitir(vila_id, novo_agente_dict):
        ...

Implementa parsing simples de regras em linguagem natural via keywords.
Para lógica complexa, um artigo pode apontar `metadados.handler` = nome de função.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from engine.constituicao import listar_vigentes

logger = logging.getLogger("vila-inteia.executor_constitucional")


# =========================================================
# Cache simples por vila (invalidar quando artigo promulgado/revogado)
# =========================================================

_cache_artigos: dict[str, list[dict]] = {}


def _artigos(vila_id: str, tipo: Optional[str] = None) -> list[dict]:
    chave = f"{vila_id}:{tipo or 'all'}"
    if chave not in _cache_artigos:
        _cache_artigos[chave] = listar_vigentes(vila_id, tipo)
    return _cache_artigos[chave]


def invalidar_cache(vila_id: str):
    for k in list(_cache_artigos.keys()):
        if k.startswith(f"{vila_id}:"):
            del _cache_artigos[k]


# =========================================================
# Enforcement: publicação
# =========================================================

def pode_publicar(vila_id: str, materia: dict) -> tuple[bool, str]:
    """
    Verifica se a publicação proposta viola alguma regra operacional.

    Regras reconhecidas (por keyword no texto do artigo):
      - "proibid" + tema  → bloqueia se matéria menciona tema
      - "exige 2 revisores" → exige flag materia['revisores'] >= 2
      - "apenas categoria X" → exige categoria == X
    """
    for a in _artigos(vila_id, tipo="operacional"):
        texto = a.get("texto", "").lower()
        titulo_mat = (materia.get("titulo") or "").lower()
        corpo_mat = (materia.get("corpo") or "").lower()

        # Proibição de tema
        m = re.search(r"proibid\w*\s+(mat[eé]rias?|posts?)\s+sobre\s+([a-zà-úA-ZÀ-Ú\s\-]+?)(?:\.|;|$)", texto)
        if m:
            tema = m.group(2).strip()
            if tema and (tema in titulo_mat or tema in corpo_mat):
                return False, f"Art. {a['numero']}: proibido matérias sobre '{tema}'"

        # Exigência de revisores
        if "revisor" in texto or "revisores" in texto:
            m2 = re.search(r"(\d+)\s+revisor", texto)
            if m2:
                minimo = int(m2.group(1))
                if materia.get("qtd_revisores", 0) < minimo:
                    return False, f"Art. {a['numero']}: exige {minimo} revisores"

    return True, ""


# =========================================================
# Enforcement: economia
# =========================================================

def multiplicador_economico(vila_id: str, tipo_trabalho: str) -> float:
    """Procura artigos econômicos que alterem precificação."""
    mult = 1.0
    for a in _artigos(vila_id, tipo="economico"):
        texto = a.get("texto", "").lower()
        if tipo_trabalho.lower() in texto:
            # Regex: "<tipo> ... receb(e|erá) N× ou Nx"
            m = re.search(r"(\d+(?:[\.,]\d+)?)\s*[x×]", texto)
            if m:
                try:
                    fator = float(m.group(1).replace(",", "."))
                    if 0.1 <= fator <= 10:
                        mult *= fator
                except ValueError:
                    pass
    return mult


# =========================================================
# Enforcement: admissão/exclusão de habitantes (estrutural)
# =========================================================

def deve_banir(vila_id: str, agente_id: str) -> bool:
    """Verifica se artigo estrutural determinou banimento."""
    for a in _artigos(vila_id, tipo="estrutural"):
        texto = a.get("texto", "").lower()
        # "banir" + agente_id ou nome
        if agente_id.lower() in texto and ("banir" in texto or "excluir" in texto):
            return True
    return False


# =========================================================
# Resumo
# =========================================================

def status_vila(vila_id: str) -> dict:
    return {
        "operacionais_vigentes": len(_artigos(vila_id, "operacional")),
        "economicos_vigentes": len(_artigos(vila_id, "economico")),
        "estruturais_vigentes": len(_artigos(vila_id, "estrutural")),
    }
