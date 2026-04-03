"""
Oficinas da Vila INTEIA — Cada local é um centro de produção real.

O campus não é decoração. Cada local tem FERRAMENTAS REAIS que agentes
usam para PRODUZIR ARTEFATOS CONCRETOS:

    Laboratório de Ideias → Python, prototipagem, análise de dados
    Biblioteca Infinita   → Pesquisa web real, compilação de referências
    Torre de Estratégia   → Simulação Monte Carlo, cenários, SWOT
    Tribunal da Razão     → Votação formal, pareceres jurídicos
    Arena de Debates      → Debate estruturado com veredito
    Sala de Guerra        → Análise de crise, war gaming
    Observatório do Futuro→ Tendências, previsões, dados globais
    Ateliê dos Artesãos   → Design, diagramas, visualizações
    Auditório INTEIA      → Apresentações, relatórios executivos
    Café dos Filósofos    → Brainstorm, ideação livre
    Ágora Central         → Assembleia, votação pública, discurso

Quando um agente vai ao Laboratório, ele TEM acesso a Python.
Quando vai à Biblioteca, ele TEM acesso a pesquisa web.
O local não é flavor text — é a interface para ferramentas reais.
"""

from __future__ import annotations

import json
import os
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

logger = logging.getLogger("vila-inteia.oficinas")


# ============================================================
# WORKSPACE — Diretório de entregas reais
# ============================================================

class Workspace:
    """
    Diretório de trabalho de um desafio.
    Agentes escrevem arquivos REAIS aqui.
    """

    def __init__(self, base_dir: str = "data/entregas"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self._index: list[dict] = []

    def _dir_desafio(self, desafio_id: str) -> str:
        d = os.path.join(self.base_dir, desafio_id)
        os.makedirs(d, exist_ok=True)
        return d

    def escrever(
        self,
        desafio_id: str,
        agente_id: str,
        agente_nome: str,
        nome_arquivo: str,
        conteudo: str,
        tipo: str = "documento",
    ) -> dict:
        """Agente escreve um arquivo real no workspace."""
        pasta = self._dir_desafio(desafio_id)
        caminho = os.path.join(pasta, nome_arquivo)

        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)

        meta = {
            "arquivo": nome_arquivo,
            "caminho": caminho,
            "agente_id": agente_id,
            "agente_nome": agente_nome,
            "tipo": tipo,
            "tamanho": len(conteudo),
            "criado_em": datetime.now().isoformat(),
        }
        self._index.append(meta)

        # Salvar índice
        idx_path = os.path.join(pasta, "_index.json")
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)

        logger.info(f"Workspace: {agente_nome} escreveu {nome_arquivo} ({len(conteudo)} chars)")
        return meta

    def ler(self, desafio_id: str, nome_arquivo: str) -> str:
        """Agente lê arquivo do workspace."""
        caminho = os.path.join(self._dir_desafio(desafio_id), nome_arquivo)
        if not os.path.exists(caminho):
            return ""
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()

    def listar(self, desafio_id: str) -> list[dict]:
        """Lista todos os arquivos do workspace."""
        pasta = self._dir_desafio(desafio_id)
        idx_path = os.path.join(pasta, "_index.json")
        if os.path.exists(idx_path):
            with open(idx_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def compilar(self, desafio_id: str) -> str:
        """Compila todas as entregas em documento único."""
        arquivos = self.listar(desafio_id)
        partes = [f"# Entregas do Desafio: {desafio_id}\n"]
        partes.append(f"Total de arquivos: {len(arquivos)}\n")

        for meta in arquivos:
            conteudo = self.ler(desafio_id, meta["arquivo"])
            partes.append(f"\n---\n## {meta['arquivo']}")
            partes.append(f"**Autor**: {meta['agente_nome']} | **Tipo**: {meta['tipo']}")
            partes.append(f"\n{conteudo}\n")

        return "\n".join(partes)

    def to_dict(self, desafio_id: str = "") -> dict:
        if desafio_id:
            arquivos = self.listar(desafio_id)
        else:
            arquivos = self._index
        return {
            "total_arquivos": len(arquivos),
            "arquivos": arquivos[-20:],
        }


# ============================================================
# OFICINAS — Ferramentas reais por local
# ============================================================

@dataclass
class Ferramenta:
    """Uma ferramenta real disponível num local."""
    id: str
    nome: str
    descricao: str
    tipo: str  # "codigo" | "pesquisa" | "escrita" | "analise" | "visual" | "votacao" | "comunicacao"
    custo_coins: int = 0
    # Módulos Python que a ferramenta disponibiliza no sandbox
    modulos_sandbox: list[str] = field(default_factory=list)
    # Tipo de artefato que produz
    tipo_artefato: str = ""  # "py" | "md" | "json" | "html" | "svg" | "csv"


@dataclass
class Oficina:
    """Conjunto de ferramentas reais de um local do campus."""
    local_id: str
    nome_oficina: str
    descricao: str
    ferramentas: list[Ferramenta] = field(default_factory=list)
    artefatos_produzidos: int = 0

    def tem_ferramenta(self, tipo: str) -> bool:
        return any(f.tipo == tipo for f in self.ferramentas)

    def obter_ferramenta(self, tipo: str) -> Optional[Ferramenta]:
        for f in self.ferramentas:
            if f.tipo == tipo:
                return f
        return None

    def to_dict(self) -> dict:
        return {
            "local_id": self.local_id,
            "nome": self.nome_oficina,
            "descricao": self.descricao,
            "ferramentas": [
                {"id": f.id, "nome": f.nome, "tipo": f.tipo,
                 "custo": f.custo_coins, "artefato": f.tipo_artefato}
                for f in self.ferramentas
            ],
            "artefatos_produzidos": self.artefatos_produzidos,
        }


# ============================================================
# REGISTRO DE OFICINAS — cada local = centro de produção real
# ============================================================

OFICINAS: dict[str, Oficina] = {}


def _reg(oficina: Oficina):
    OFICINAS[oficina.local_id] = oficina


# ── LABORATÓRIO DE IDEIAS ──
# Centro de Ciência da Computação: Python real, prototipagem, análise
_reg(Oficina(
    local_id="laboratorio",
    nome_oficina="Laboratório de Ciência da Computação",
    descricao="Python sandbox completo, prototipagem, análise de dados, machine learning",
    ferramentas=[
        Ferramenta(
            id="python_completo", nome="Python Sandbox",
            descricao="Execução de código Python com math, statistics, json, collections, datetime",
            tipo="codigo", custo_coins=5,
            modulos_sandbox=["math", "statistics", "random", "json", "re",
                             "collections", "itertools", "datetime", "decimal", "csv"],
            tipo_artefato="py",
        ),
        Ferramenta(
            id="analise_dados", nome="Análise de Dados",
            descricao="Cálculos estatísticos, distribuições, testes de hipótese",
            tipo="analise", custo_coins=8,
            modulos_sandbox=["math", "statistics", "random", "json", "csv"],
            tipo_artefato="json",
        ),
        Ferramenta(
            id="prototipagem", nome="Prototipagem Rápida",
            descricao="Criar protótipos de algoritmos e estruturas de dados",
            tipo="codigo", custo_coins=5,
            modulos_sandbox=["math", "json", "collections", "itertools"],
            tipo_artefato="py",
        ),
    ],
))

# ── BIBLIOTECA INFINITA ──
# Centro de Pesquisa: web search real, compilação de referências
_reg(Oficina(
    local_id="biblioteca",
    nome_oficina="Centro de Pesquisa e Referências",
    descricao="Pesquisa web real (Tavily/Exa), compilação bibliográfica, revisão de literatura",
    ferramentas=[
        Ferramenta(
            id="pesquisa_web", nome="Pesquisa Web",
            descricao="Busca real na internet via Tavily/Exa/OmniRoute",
            tipo="pesquisa", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="compilar_refs", nome="Compilador de Referências",
            descricao="Organiza e sintetiza múltiplas fontes em documento estruturado",
            tipo="escrita", custo_coins=2,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="fichamento", nome="Fichamento Acadêmico",
            descricao="Extrai argumentos-chave de textos e organiza por tema",
            tipo="escrita", custo_coins=2,
            tipo_artefato="md",
        ),
    ],
))

# ── TORRE DE ESTRATÉGIA ──
# Centro de Simulação: cenários, Monte Carlo, SWOT, war gaming
_reg(Oficina(
    local_id="torre_estrategia",
    nome_oficina="Centro de Simulação Estratégica",
    descricao="Simulação Monte Carlo, análise de cenários, SWOT, modelagem de decisões",
    ferramentas=[
        Ferramenta(
            id="monte_carlo", nome="Simulação Monte Carlo",
            descricao="Simulação estocástica com milhares de cenários",
            tipo="analise", custo_coins=10,
            modulos_sandbox=["math", "statistics", "random", "json", "collections"],
            tipo_artefato="json",
        ),
        Ferramenta(
            id="cenarios", nome="Gerador de Cenários",
            descricao="Matriz de cenários otimista/base/pessimista com probabilidades",
            tipo="analise", custo_coins=8,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="swot", nome="Análise SWOT",
            descricao="Forças, fraquezas, oportunidades e ameaças estruturadas",
            tipo="escrita", custo_coins=5,
            tipo_artefato="md",
        ),
    ],
))

# ── TRIBUNAL DA RAZÃO ──
# Centro Jurídico: pareceres, votação formal, legislação
_reg(Oficina(
    local_id="tribunal",
    nome_oficina="Centro Jurídico e de Governança",
    descricao="Redação de pareceres, votação formal, análise de legislação, regimento",
    ferramentas=[
        Ferramenta(
            id="parecer_juridico", nome="Redação de Parecer",
            descricao="Parecer jurídico formal com fundamentação legal",
            tipo="escrita", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="votacao_formal", nome="Votação Formal",
            descricao="Sessão de votação com quórum, registro de votos e veredito",
            tipo="votacao", custo_coins=0,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="analise_legal", nome="Análise de Legislação",
            descricao="Pesquisa e análise de marcos legais e regulatórios",
            tipo="pesquisa", custo_coins=3,
            tipo_artefato="md",
        ),
    ],
))

# ── ARENA DE DEBATES ──
# Centro de Argumentação: debate estruturado com veredito
_reg(Oficina(
    local_id="arena_debates",
    nome_oficina="Centro de Argumentação e Debate",
    descricao="Debates estruturados com moderação, placar, veredito por jurados",
    ferramentas=[
        Ferramenta(
            id="debate_formal", nome="Debate Formal",
            descricao="Debate estruturado: abertura → argumentos → réplicas → veredito",
            tipo="comunicacao", custo_coins=0,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="mocao", nome="Proposição de Moção",
            descricao="Propor moção formal para votação na assembleia",
            tipo="votacao", custo_coins=0,
            tipo_artefato="json",
        ),
    ],
))

# ── SALA DE GUERRA ──
# Centro de Crise: war gaming, análise tática, decisões sob pressão
_reg(Oficina(
    local_id="sala_guerra",
    nome_oficina="Centro de Análise Tática",
    descricao="War gaming, análise de crise, simulação de adversários, decisão sob incerteza",
    ferramentas=[
        Ferramenta(
            id="war_game", nome="War Gaming",
            descricao="Simulação de cenário adversarial com múltiplos jogadores",
            tipo="analise", custo_coins=10,
            modulos_sandbox=["math", "statistics", "random", "json"],
            tipo_artefato="json",
        ),
        Ferramenta(
            id="analise_risco", nome="Análise de Risco",
            descricao="Matriz probabilidade × impacto com mitigações",
            tipo="analise", custo_coins=5,
            modulos_sandbox=["math", "statistics", "random"],
            tipo_artefato="json",
        ),
        Ferramenta(
            id="plano_contingencia", nome="Plano de Contingência",
            descricao="Documento: se X acontecer, fazer Y",
            tipo="escrita", custo_coins=3,
            tipo_artefato="md",
        ),
    ],
))

# ── OBSERVATÓRIO DO FUTURO ──
# Centro de Inteligência: tendências, previsões, dados globais
_reg(Oficina(
    local_id="observatorio",
    nome_oficina="Centro de Inteligência e Previsões",
    descricao="Monitoramento de tendências, previsões, análise de dados globais em tempo real",
    ferramentas=[
        Ferramenta(
            id="radar_tendencias", nome="Radar de Tendências",
            descricao="Pesquisa web focada em tendências emergentes e sinais fracos",
            tipo="pesquisa", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="previsao", nome="Modelo Preditivo",
            descricao="Previsões baseadas em dados históricos e tendências",
            tipo="analise", custo_coins=8,
            modulos_sandbox=["math", "statistics", "random", "json"],
            tipo_artefato="json",
        ),
        Ferramenta(
            id="briefing_inteligencia", nome="Briefing de Inteligência",
            descricao="Documento síntese: o que está acontecendo e o que vai acontecer",
            tipo="escrita", custo_coins=5,
            tipo_artefato="md",
        ),
    ],
))

# ── ATELIÊ DOS ARTESÃOS ──
# Centro Criativo: design, diagramas, visualizações, narrativas
_reg(Oficina(
    local_id="atelie",
    nome_oficina="Centro Criativo e de Design",
    descricao="Visualizações, diagramas, narrativas, design de soluções, storytelling",
    ferramentas=[
        Ferramenta(
            id="diagrama", nome="Gerador de Diagramas",
            descricao="Diagramas de arquitetura, fluxo, mapa mental em texto",
            tipo="visual", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="narrativa", nome="Redação Criativa",
            descricao="Textos persuasivos, storytelling, copy",
            tipo="escrita", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="manifesto", nome="Manifesto / Declaração",
            descricao="Documento de princípios, visão, valores",
            tipo="escrita", custo_coins=3,
            tipo_artefato="md",
        ),
    ],
))

# ── AUDITÓRIO INTEIA ──
# Centro de Apresentações: relatórios executivos, keynotes
_reg(Oficina(
    local_id="auditorio",
    nome_oficina="Centro de Apresentações e Relatórios",
    descricao="Relatórios executivos, apresentações, compilação final de entregas",
    ferramentas=[
        Ferramenta(
            id="relatorio_executivo", nome="Relatório Executivo",
            descricao="Compilação profissional de todas as entregas em relatório HTML",
            tipo="escrita", custo_coins=15,
            tipo_artefato="html",
        ),
        Ferramenta(
            id="apresentacao", nome="Apresentação Estruturada",
            descricao="Keynote com slides conceituais em formato texto",
            tipo="escrita", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="sumario_executivo", nome="Sumário Executivo",
            descricao="1 página: problema, solução, resultados, próximos passos",
            tipo="escrita", custo_coins=5,
            tipo_artefato="md",
        ),
    ],
))

# ── CAFÉ DOS FILÓSOFOS ──
# Centro de Ideação: brainstorm livre, conexões improváveis
_reg(Oficina(
    local_id="cafe_filosofos",
    nome_oficina="Centro de Ideação e Brainstorm",
    descricao="Brainstorm livre, conexões improváveis, pensamento lateral, ideação",
    ferramentas=[
        Ferramenta(
            id="brainstorm", nome="Sessão de Brainstorm",
            descricao="Gerar 10+ ideias sem filtro sobre qualquer tema",
            tipo="escrita", custo_coins=0,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="analogia", nome="Pensamento por Analogia",
            descricao="Conectar domínios diferentes para gerar insight",
            tipo="escrita", custo_coins=0,
            tipo_artefato="md",
        ),
    ],
))

# ── ÁGORA CENTRAL ──
# Centro de Assembleia: votação pública, discursos, anúncios
_reg(Oficina(
    local_id="agora",
    nome_oficina="Assembleia Pública",
    descricao="Votação pública, discursos, anúncios oficiais, assembleia constituinte",
    ferramentas=[
        Ferramenta(
            id="discurso", nome="Discurso Público",
            descricao="Discurso formal para toda a vila ouvir",
            tipo="comunicacao", custo_coins=0,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="votacao_publica", nome="Votação Pública",
            descricao="Plebiscito aberto a todos os habitantes",
            tipo="votacao", custo_coins=0,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="edital", nome="Publicação de Edital",
            descricao="Anúncio oficial: contratação, convocação, resultado",
            tipo="comunicacao", custo_coins=2,
            tipo_artefato="md",
        ),
    ],
))

# ── JARDIM DOS VISIONÁRIOS ──
# Centro de Visão: pensamento de longo prazo, futurismo
_reg(Oficina(
    local_id="jardim_visionarios",
    nome_oficina="Centro de Visão e Futurismo",
    descricao="Pensamento de longo prazo, cenários futuristas, visão de 10-50 anos",
    ferramentas=[
        Ferramenta(
            id="visao_futuro", nome="Visão de Futuro",
            descricao="Documento: como o mundo será em 10/20/50 anos",
            tipo="escrita", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="moonshot", nome="Proposta Moonshot",
            descricao="Ideia ambiciosa que muda tudo se funcionar",
            tipo="escrita", custo_coins=5,
            tipo_artefato="md",
        ),
    ],
))


# ============================================================
# API — consultar oficinas e ferramentas
# ============================================================

def oficina_do_local(local_id: str) -> Optional[Oficina]:
    """Retorna a oficina (ferramentas reais) de um local."""
    return OFICINAS.get(local_id)


def ferramentas_no_local(local_id: str) -> list[dict]:
    """Retorna lista de ferramentas disponíveis num local."""
    oficina = OFICINAS.get(local_id)
    if not oficina:
        return []
    return [
        {"id": f.id, "nome": f.nome, "descricao": f.descricao,
         "tipo": f.tipo, "custo": f.custo_coins, "artefato": f.tipo_artefato}
        for f in oficina.ferramentas
    ]


def todas_oficinas() -> list[dict]:
    """Lista todas as oficinas do campus."""
    return [o.to_dict() for o in OFICINAS.values()]


def ferramenta_por_id(ferramenta_id: str) -> Optional[tuple[Oficina, Ferramenta]]:
    """Busca ferramenta por ID em qualquer oficina."""
    for oficina in OFICINAS.values():
        for f in oficina.ferramentas:
            if f.id == ferramenta_id:
                return oficina, f
    return None
