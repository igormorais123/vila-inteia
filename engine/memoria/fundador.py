"""
engine/memoria/fundador — Onda 4 HARNESS_VILA.md (Gap #5).

Quarto tipo canônico de memória: a Ficha do Fundador. Consolida preferências,
projetos ativos e restrições operacionais do Igor Morais Vasconcelos a partir
de CLAUDE.md global, CLAUDE.md do projeto e histórico recente de interações.

A ficha é injetada em fases cognitivas que envolvam o Fundador (ex: Helena
recebendo pedido executivo, Chateaubriand avaliando material Vila-to-Mirante,
Cícero lidando com causa do escritório Paixão Cortes).

Não substitui memória semântica (saberes gerais) nem episódica (runs
passados). Complementa — hierarquia de prioridade:
    Fundador → INTEIA → Colmeia → Cliente.

Leitura é gratuita (apenas lê arquivos). Escrita é feita por promoção
manual ou pelo autoresearch quando detectar padrão recorrente.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("vila-inteia.memoria.fundador")

_HOME = Path(os.path.expanduser("~"))
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PATHS_CLAUDE_MD = [
    _HOME / ".claude" / "CLAUDE.md",
    _HOME / "CLAUDE.md",
]
_PATH_FUNDADOR_YAML = _REPO_ROOT / "data" / "fundador.yaml"


@dataclass
class FichaFundador:
    identificacao: dict = field(default_factory=dict)
    preferencias: list[str] = field(default_factory=list)
    projetos_ativos: list[str] = field(default_factory=list)
    restricoes_operacionais: list[str] = field(default_factory=list)
    neurocognicao: dict = field(default_factory=dict)
    hierarquia_servico: list[str] = field(default_factory=lambda: ["Fundador","INTEIA","Colmeia","Cliente"])
    ultima_atualizacao: str = ""
    fonte: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "identificacao": self.identificacao,
            "preferencias": self.preferencias,
            "projetos_ativos": self.projetos_ativos,
            "restricoes_operacionais": self.restricoes_operacionais,
            "neurocognicao": self.neurocognicao,
            "hierarquia_servico": self.hierarquia_servico,
            "ultima_atualizacao": self.ultima_atualizacao,
            "fonte": self.fonte,
        }


def _extrair_secao(texto: str, titulo: str) -> str:
    """Pega bloco markdown entre dois ## titulos."""
    padrao = re.compile(
        rf"##\s*{re.escape(titulo)}[^\n]*\n(.*?)(?=\n##\s|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    m = padrao.search(texto)
    return m.group(1).strip() if m else ""


def _bullets(texto: str, max_itens: int = 20) -> list[str]:
    """Extrai bullets '-' ou '*' de um bloco de texto."""
    out = []
    for linha in texto.splitlines():
        s = linha.strip()
        if s.startswith(("- ", "* ")):
            out.append(s[2:].strip())
        if len(out) >= max_itens:
            break
    return out


_cache: Optional[FichaFundador] = None


def _parse_yaml_simples(txt: str) -> dict:
    """Parser mínimo de YAML flat (sem depender de pyyaml)."""
    out: dict = {}
    chave = None
    lista: list = []
    subdict: dict = {}
    indent_bloco = None
    for linha in txt.splitlines():
        if not linha.strip() or linha.strip().startswith("#"):
            continue
        stripped = linha.rstrip()
        # top-level key: value
        if not linha.startswith(" ") and ":" in stripped:
            k, _, v = stripped.partition(":")
            k = k.strip()
            v = v.strip()
            chave = k
            if v:
                out[k] = v.strip('"').strip("'")
                chave = None
            else:
                lista = []
                subdict = {}
                out[k] = lista  # lista por default, vira dict se aparecer sub-chave
        elif linha.startswith("  - ") and chave:
            if not isinstance(out[chave], list):
                out[chave] = []
            out[chave].append(linha[4:].strip().strip('"').strip("'"))
        elif linha.startswith("  ") and ":" in linha and chave:
            # sub-dict key: value dentro do bloco
            sub_k, _, sub_v = linha.strip().partition(":")
            if not isinstance(out[chave], dict):
                out[chave] = {}
            out[chave][sub_k.strip()] = sub_v.strip().strip('"').strip("'")
    return out


def carregar_ficha(force: bool = False) -> FichaFundador:
    """
    Consolida ficha do Fundador a partir de (ordem de prioridade):
      1. data/fundador.yaml (commitado no repo — funciona em produção)
      2. ~/.claude/CLAUDE.md  (ambiente local do Igor)
      3. ~/CLAUDE.md          (ambiente local do Igor)

    Dados mais específicos sobrescrevem genéricos.
    """
    global _cache
    if _cache and not force:
        return _cache

    ficha = FichaFundador()
    ficha.ultima_atualizacao = datetime.now(timezone.utc).isoformat()

    # 1. YAML do repo (fonte primária)
    if _PATH_FUNDADOR_YAML.is_file():
        try:
            raw = _PATH_FUNDADOR_YAML.read_text(encoding="utf-8")
            data = _parse_yaml_simples(raw)
            ficha.fonte.append(str(_PATH_FUNDADOR_YAML.relative_to(_REPO_ROOT)))
            if isinstance(data.get("identificacao"), dict):
                ficha.identificacao = data["identificacao"]
            if isinstance(data.get("preferencias"), list):
                ficha.preferencias = list(data["preferencias"])
            if isinstance(data.get("projetos_ativos"), list):
                ficha.projetos_ativos = list(data["projetos_ativos"])
            if isinstance(data.get("restricoes_operacionais"), list):
                ficha.restricoes_operacionais = list(data["restricoes_operacionais"])
            if isinstance(data.get("neurocognicao"), dict):
                ficha.neurocognicao = data["neurocognicao"]
            if isinstance(data.get("hierarquia_servico"), list):
                ficha.hierarquia_servico = list(data["hierarquia_servico"])
        except Exception as exc:
            logger.warning("erro parseando fundador.yaml: %s", exc)

    # 2. CLAUDE.md locais (complementam sem sobrescrever o já preenchido)
    textos = []
    for p in _PATHS_CLAUDE_MD:
        if p.is_file():
            try:
                textos.append(p.read_text(encoding="utf-8"))
                ficha.fonte.append(str(p))
            except Exception as exc:
                logger.warning("erro lendo %s: %s", p, exc)

    texto_total = "\n\n".join(textos)

    # identificação — só preenche se o yaml não preencheu
    if not ficha.identificacao and (
        "Igor Morais Vasconcelos" in texto_total
        or "OAB-DF 35" in texto_total
        or "35.376" in texto_total
    ):
        ficha.identificacao = {
            "nome": "Igor Morais Vasconcelos",
            "papel": "Fundador INTEIA / Advogado OAB-DF 35.376 / Doutorando IDP",
            "contato": "igormorais123@gmail.com",
        }

    # preferências — só se yaml não preencheu
    if ficha.preferencias:
        pass
    else:
      diretrizes = _extrair_secao(texto_total, "Diretrizes")
      if diretrizes:
        ficha.preferencias = _bullets(diretrizes, max_itens=15) or [
            "Nunca inferência como fato — rotular [Inferência]",
            "Parceiro de raciocínio, não validador — sem bajulação",
            "Direto ao ponto, voz ativa, sem superlativos",
            "Apontar falhas e pontos cegos",
            "Português brasileiro sempre",
            "UTF-8 com acentuação completa em tudo que for publicado",
        ]

    # neurocognição
    if "TDAH" in texto_total or "TEA" in texto_total or "Altas Habilidades" in texto_total:
        ficha.neurocognicao = {
            "TEA_Grau_1": "comunicação direta, sistemas previsíveis",
            "TDAH": "tarefas de 15 a 30 min, lembretes, estrutura externa",
            "Altas_Habilidades": "profundidade intelectual, não simplificar excessivamente",
        }

    # projetos ativos — só se yaml não preencheu
    if not ficha.projetos_ativos:
        projetos_mencionados = [
            "Colmeia", "OmniRoute", "Mirante News", "Elexion", "Vila INTEIA",
            "Paixão Cortes Advogados", "Doutorado IDP",
        ]
        encontrados = [p for p in projetos_mencionados if p.lower() in texto_total.lower()]
        ficha.projetos_ativos = encontrados or projetos_mencionados

    # restrições operacionais — só se yaml não preencheu
    if not ficha.restricoes_operacionais:
        ficha.restricoes_operacionais = [
            "Terapia quinta às 16h — evitar agendamentos neste horário",
            "Hérnia L5-S1 — evitar sessões contínuas acima de 8h sentado",
            "Venvanse pausado — evitar tarefas que exigem hiperfoco longo e incontestado",
            "Nunca publicar conteúdo web sem acentuação UTF-8 completa",
            "Sem bajulação, siglas por extenso, emoticons evitados",
        ]

    _cache = ficha
    return ficha


def ficha_para_injecao(max_chars: int = 1500) -> str:
    """Versão textual compacta para injetar em prompt de fase cognitiva."""
    f = carregar_ficha()
    blocos = []
    if f.identificacao:
        blocos.append("FUNDADOR: " + ", ".join(
            f"{k}={v}" for k, v in f.identificacao.items()
        ))
    if f.preferencias:
        blocos.append("PREFERÊNCIAS:\n- " + "\n- ".join(f.preferencias[:8]))
    if f.restricoes_operacionais:
        blocos.append("RESTRIÇÕES:\n- " + "\n- ".join(f.restricoes_operacionais[:6]))
    blocos.append("HIERARQUIA DE SERVIÇO: " + " → ".join(f.hierarquia_servico))
    texto = "\n\n".join(blocos)
    if len(texto) > max_chars:
        texto = texto[:max_chars - 3] + "..."
    return texto
