"""
engine/harness/skill_registry — Onda 3 do HARNESS_VILA.md (Gap #3).

Registry + discovery de skills canônicas.

Duas fontes ordenadas por prioridade:
    1. engine/skills_oficinas/<nome>/SKILL.md  (preferido — manifest YAML)
    2. engine/oficinas.py OFICINAS dict        (fallback bootstrap — converte
                                                cada oficina em skill stub)

Progressive disclosure em 3 níveis:
    N1 manifest (nome + descrição curta, <50 tokens)
    N2 applicability (preconditions + scope + heurísticas, <400 tokens)
    N3 guia completo (procedimento + exemplos + constraints, <2000 tokens)

Expõe:
    listar(nivel=1|2|3)                 — lista todas skills no nível pedido
    buscar(termos: list[str], top_n=5)  — semantic-ish score por palavra
    carregar(nome, nivel=3)             — carrega skill específica
    manifest(nome)                      — só N1
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("vila-inteia.harness.skill_registry")

_DIR_SKILLS = Path(__file__).resolve().parent.parent / "skills_oficinas"


# ---------------------------------------------------------------------
# Schema

@dataclass
class SkillManifest:
    """Representação canônica de uma skill da Vila (compatível com Claude Code Skills)."""
    nome: str
    descricao: str                                # usado em N1
    origem: str                                   # "authored" | "bootstrap_oficina"
    familia: str = ""                             # ex: problem-solving, pesquisa, debate
    capabilities: list[str] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    scope: list[str] = field(default_factory=list)
    bind_tools: list[str] = field(default_factory=list)   # tools do local
    constraints: list[str] = field(default_factory=list)
    tokens_n1: int = 50
    tokens_n2: int = 400
    tokens_n3: int = 2000
    guia_n2: str = ""                             # applicability
    guia_n3: str = ""                             # procedimento completo
    local_id: str = ""                            # se bootstrapped, local de origem

    def render(self, nivel: int) -> dict:
        base = {
            "nome": self.nome,
            "descricao": self.descricao,
            "origem": self.origem,
        }
        if nivel >= 2:
            base.update({
                "familia": self.familia,
                "capabilities": self.capabilities,
                "preconditions": self.preconditions,
                "scope": self.scope,
                "bind_tools": self.bind_tools,
                "constraints": self.constraints,
                "applicability": self.guia_n2,
            })
        if nivel >= 3:
            base["procedimento"] = self.guia_n3
            base["local_id"] = self.local_id
        return base


# ---------------------------------------------------------------------
# Loader — SKILL.md authored

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def _parse_yaml_lite(txt: str) -> dict:
    """Parser minimalista de YAML flat (sem dependência externa)."""
    out: dict = {}
    chave_atual = None
    lista_atual: list[str] = []
    for linha in txt.splitlines():
        if not linha.strip() or linha.strip().startswith("#"):
            continue
        if linha.startswith("  - ") and chave_atual:
            lista_atual.append(linha[4:].strip().strip('"').strip("'"))
            out[chave_atual] = lista_atual
        elif ":" in linha and not linha.startswith(" "):
            k, _, v = linha.partition(":")
            k = k.strip()
            v = v.strip()
            if not v:
                chave_atual = k
                lista_atual = []
                out[k] = lista_atual
            else:
                chave_atual = None
                out[k] = v.strip('"').strip("'")
    return out


def _load_authored(dir_skill: Path) -> Optional[SkillManifest]:
    path = dir_skill / "SKILL.md"
    if not path.is_file():
        return None
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("erro lendo %s: %s", path, exc)
        return None

    m = _FRONTMATTER_RE.match(txt)
    if not m:
        return None
    frontmatter, corpo = m.group(1), m.group(2)
    data = _parse_yaml_lite(frontmatter)

    # separa corpo em N2 e N3 por marcador
    n2 = n3 = ""
    # convenção: seções "## N2" e "## N3" se existirem; senão corpo inteiro vai em N3
    s2 = re.search(r"##\s*N2[^\n]*\n(.*?)(?=\n##\s|\Z)", corpo, re.DOTALL | re.IGNORECASE)
    s3 = re.search(r"##\s*N3[^\n]*\n(.*?)\Z", corpo, re.DOTALL | re.IGNORECASE)
    if s2:
        n2 = s2.group(1).strip()
    if s3:
        n3 = s3.group(1).strip()
    if not n2 and not n3:
        n3 = corpo.strip()

    def _as_list(v):
        if isinstance(v, list):
            return v
        if isinstance(v, str) and v:
            return [x.strip() for x in v.split(",")]
        return []

    return SkillManifest(
        nome=str(data.get("name") or dir_skill.name),
        descricao=str(data.get("description") or data.get("descricao") or ""),
        origem="authored",
        familia=str(data.get("familia") or data.get("family") or ""),
        capabilities=_as_list(data.get("capabilities")),
        preconditions=_as_list(data.get("preconditions")),
        scope=_as_list(data.get("scope")),
        bind_tools=_as_list(data.get("bind_tools")),
        constraints=_as_list(data.get("constraints")),
        guia_n2=n2,
        guia_n3=n3,
        local_id=str(data.get("local_id") or ""),
    )


# ---------------------------------------------------------------------
# Loader — bootstrap a partir de engine/oficinas.py

def _bootstrap_from_oficinas() -> list[SkillManifest]:
    try:
        from ..oficinas import OFICINAS
    except Exception as exc:
        logger.warning("bootstrap skills: %s", exc)
        return []

    out: list[SkillManifest] = []
    for local_id, of in OFICINAS.items():
        ferramentas_nomes = [f.nome for f in getattr(of, "ferramentas", [])]
        capabilities = [f.tipo for f in getattr(of, "ferramentas", [])]
        out.append(SkillManifest(
            nome=local_id,
            descricao=(of.descricao or of.nome_oficina or local_id)[:280],
            origem="bootstrap_oficina",
            familia="oficina",
            capabilities=list(set(capabilities)),
            preconditions=[f"agente_presente_em:{local_id}"],
            scope=[local_id],
            bind_tools=ferramentas_nomes,
            constraints=[
                "respeita custo em INTEIA Coins por ferramenta",
                "produz artefato no workspace do desafio ativo",
            ],
            guia_n2=f"Oficina {of.nome_oficina}: {of.descricao}",
            guia_n3=(
                f"# {of.nome_oficina}\n\n"
                f"{of.descricao}\n\n"
                f"## Ferramentas disponíveis ({len(ferramentas_nomes)})\n"
                + "\n".join(f"- {f.nome} ({f.tipo}) — {f.descricao}" for f in getattr(of, 'ferramentas', []))
                + "\n\n*Skill bootstrapped automaticamente de engine/oficinas.py. "
                "Substituir por SKILL.md authored em engine/skills_oficinas/ "
                f"{local_id}/SKILL.md para refinamento.*"
            ),
            local_id=local_id,
        ))
    return out


# ---------------------------------------------------------------------
# Registry

_cache: dict[str, SkillManifest] = {}
_loaded = False


def _carregar_tudo(force: bool = False) -> dict[str, SkillManifest]:
    global _loaded, _cache
    if _loaded and not force:
        return _cache
    _cache = {}
    # 1) Authored
    if _DIR_SKILLS.is_dir():
        for sub in sorted(_DIR_SKILLS.iterdir()):
            if sub.is_dir():
                s = _load_authored(sub)
                if s:
                    _cache[s.nome] = s
    # 2) Bootstrap fallback apenas para nomes ausentes
    for s in _bootstrap_from_oficinas():
        _cache.setdefault(s.nome, s)
    _loaded = True
    return _cache


def listar(nivel: int = 1) -> list[dict]:
    return [s.render(nivel) for s in _carregar_tudo().values()]


def carregar(nome: str, nivel: int = 3) -> Optional[dict]:
    s = _carregar_tudo().get(nome)
    return s.render(nivel) if s else None


def manifest(nome: str) -> Optional[dict]:
    return carregar(nome, nivel=1)


# ---------------------------------------------------------------------
# Busca semântica-lite — score por palavra em descrição/capabilities/scope

def _score(skill: SkillManifest, termos: list[str]) -> int:
    if not termos:
        return 0
    texto = " ".join([
        skill.nome, skill.descricao, skill.familia,
        " ".join(skill.capabilities), " ".join(skill.scope),
        " ".join(skill.bind_tools),
    ]).lower()
    total = 0
    for t in termos:
        t = t.strip().lower()
        if not t:
            continue
        total += texto.count(t)
    return total


def buscar(termos: list[str], top_n: int = 5, nivel: int = 2) -> list[dict]:
    resultados = []
    for s in _carregar_tudo().values():
        score = _score(s, termos)
        if score > 0:
            r = s.render(nivel)
            r["_score"] = score
            resultados.append(r)
    resultados.sort(key=lambda x: x["_score"], reverse=True)
    return resultados[:top_n]
