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
_PATHS_CLAUDE_MD = [
    _HOME / ".claude" / "CLAUDE.md",
    _HOME / "CLAUDE.md",
]


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


def carregar_ficha(force: bool = False) -> FichaFundador:
    """Lê os CLAUDE.md disponíveis e devolve FichaFundador consolidada."""
    global _cache
    if _cache and not force:
        return _cache

    ficha = FichaFundador()
    ficha.ultima_atualizacao = datetime.now(timezone.utc).isoformat()

    textos = []
    for p in _PATHS_CLAUDE_MD:
        if p.is_file():
            try:
                textos.append(p.read_text(encoding="utf-8"))
                ficha.fonte.append(str(p))
            except Exception as exc:
                logger.warning("erro lendo %s: %s", p, exc)

    texto_total = "\n\n".join(textos)

    # identificação
    if "Igor Morais Vasconcelos" in texto_total or "OAB-DF 35" in texto_total or "35.376" in texto_total:
        ficha.identificacao = {
            "nome": "Igor Morais Vasconcelos",
            "papel": "Fundador INTEIA / Advogado OAB-DF 35.376 / Doutorando IDP",
            "contato": "igormorais123@gmail.com",
        }

    # preferências
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

    # projetos ativos
    projetos_mencionados = [
        "Colmeia", "OmniRoute", "Mirante News", "Elexion", "Vila INTEIA",
        "Paixão Cortes Advogados", "Doutorado IDP",
    ]
    ficha.projetos_ativos = [p for p in projetos_mencionados if p.lower() in texto_total.lower()]
    if not ficha.projetos_ativos:
        ficha.projetos_ativos = projetos_mencionados

    # restrições operacionais
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
