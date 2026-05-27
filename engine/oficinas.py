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
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger("vila-inteia.oficinas")


# ============================================================
# WORKSPACE — Diretório de entregas reais
# ============================================================

class WorkspacePathError(ValueError):
    """Caminho fora do workspace ou nome de arquivo inseguro."""


class Workspace:
    """
    Diretório de trabalho de um desafio.
    Agentes escrevem arquivos REAIS aqui.
    """

    def __init__(self, base_dir: str = "data/entregas"):
        self.base_path = Path(base_dir).resolve()
        self.base_dir = str(self.base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._index: list[dict] = []

    @staticmethod
    def _validar_segmento(valor: str, campo: str) -> str:
        """Aceita apenas um segmento de caminho, nunca paths compostos."""
        valor = str(valor or "").strip()
        if (
            not valor
            or valor in {".", ".."}
            or "/" in valor
            or "\\" in valor
            or ":" in valor
            or Path(valor).is_absolute()
        ):
            raise WorkspacePathError(f"{campo} inseguro: {valor!r}")
        return valor

    def _garantir_dentro_base(self, caminho: Path) -> Path:
        resolvido = caminho.resolve()
        if resolvido != self.base_path and self.base_path not in resolvido.parents:
            raise WorkspacePathError(f"caminho fora do workspace: {caminho}")
        return resolvido

    def _dir_desafio(self, desafio_id: str, criar: bool = True) -> Path:
        desafio = self._validar_segmento(desafio_id, "desafio_id")
        d = self._garantir_dentro_base(self.base_path / desafio)
        if criar:
            d.mkdir(parents=True, exist_ok=True)
        return d

    def _arquivo_desafio(self, desafio_id: str, nome_arquivo: str, criar_dir: bool = True) -> Path:
        nome = self._validar_segmento(nome_arquivo, "nome_arquivo")
        pasta = self._dir_desafio(desafio_id, criar=criar_dir)
        return self._garantir_dentro_base(pasta / nome)

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
        caminho = self._arquivo_desafio(desafio_id, nome_arquivo)

        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)

        meta = {
            "arquivo": nome_arquivo,
            "caminho": str(caminho),
            "agente_id": agente_id,
            "agente_nome": agente_nome,
            "tipo": tipo,
            "tamanho": len(conteudo),
            "criado_em": datetime.now().isoformat(),
        }
        self._index.append(meta)

        # Salvar índice
        idx_path = pasta / "_index.json"
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)

        logger.info(f"Workspace: {agente_nome} escreveu {nome_arquivo} ({len(conteudo)} chars)")
        return meta

    def ler(self, desafio_id: str, nome_arquivo: str) -> str:
        """Agente lê arquivo do workspace."""
        caminho = self._arquivo_desafio(desafio_id, nome_arquivo, criar_dir=False)
        if not os.path.exists(caminho):
            return ""
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()

    def listar(self, desafio_id: str) -> list[dict]:
        """Lista todos os arquivos do workspace."""
        pasta = self._dir_desafio(desafio_id, criar=False)
        idx_path = pasta / "_index.json"
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
# DESIGN SPRINT — 5 oficinas do processo GV Sprint
# ============================================================
# Baseado no Google Ventures Design Sprint (Jake Knapp):
# Segunda: Entender → Terça: Divergir → Quarta: Decidir →
# Quinta: Prototipar → Sexta: Testar
#
# Cada dia do sprint é um LOCAL REAL no campus com ferramentas reais.

# ── SALA DE ENTENDIMENTO (Sprint Dia 1) ──
# Mapear o problema, ouvir especialistas, definir alvo
_reg(Oficina(
    local_id="sprint_entender",
    nome_oficina="Sala de Entendimento do Problema",
    descricao=(
        "Sprint Dia 1: Mapear o problema de ponta a ponta. "
        "Entrevistas com especialistas, mapa do usuário, perguntas-chave, "
        "How Might We, definição do alvo do sprint."
    ),
    ferramentas=[
        Ferramenta(
            id="mapa_problema", nome="Mapa do Problema",
            descricao=(
                "Diagrama end-to-end: ator → ações → resultado. "
                "Identifica onde está a dor, o gargalo, a oportunidade."
            ),
            tipo="escrita", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="entrevista_especialista", nome="Entrevista com Especialista",
            descricao=(
                "Perguntas estruturadas para extrair conhecimento profundo. "
                "Formato: contexto → problema → tentativas → insight."
            ),
            tipo="pesquisa", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="how_might_we", nome="How Might We (HMW)",
            descricao=(
                "Reformular problemas como oportunidades. "
                "Cada agente gera 5+ notas HMW sobre o tema."
            ),
            tipo="escrita", custo_coins=0,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="alvo_sprint", nome="Definição do Alvo",
            descricao=(
                "Escolher O que resolver neste sprint. "
                "Pergunta-alvo + métrica de sucesso + persona-alvo."
            ),
            tipo="escrita", custo_coins=2,
            tipo_artefato="json",
        ),
    ],
))

# ── SALA DE IDEAÇÃO (Sprint Dia 2) ──
# Divergir: cada agente gera soluções individualmente
_reg(Oficina(
    local_id="sprint_idear",
    nome_oficina="Sala de Ideação e Divergência",
    descricao=(
        "Sprint Dia 2: Divergir. Cada agente trabalha SOZINHO gerando soluções. "
        "Crazy 8s, Lightning Demos, Sketch de 3 painéis. "
        "Quantidade acima de qualidade — sem julgamento."
    ),
    ferramentas=[
        Ferramenta(
            id="crazy_8s", nome="Crazy 8s",
            descricao=(
                "8 variações de solução em 8 minutos (simulado). "
                "Esboços rápidos, sem autocensura, quantidade máxima."
            ),
            tipo="escrita", custo_coins=0,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="lightning_demo", nome="Lightning Demo",
            descricao=(
                "Pesquisar 3 referências de como outros resolveram "
                "problemas similares. Capturar padrões reutilizáveis."
            ),
            tipo="pesquisa", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="sketch_solucao", nome="Sketch de Solução (3 Painéis)",
            descricao=(
                "Solução detalhada em 3 quadros: antes → interação → depois. "
                "Narrativa visual da experiência do usuário."
            ),
            tipo="escrita", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="mapa_ideias", nome="Mapa de Ideias",
            descricao=(
                "Agrupar e conectar ideias por tema. "
                "Clusters visuais: quick wins, moonshots, incrementais."
            ),
            tipo="visual", custo_coins=2,
            tipo_artefato="md",
        ),
    ],
))

# ── SALA DE DECISÃO (Sprint Dia 3) ──
# Convergir: votar, decidir, criar storyboard
_reg(Oficina(
    local_id="sprint_decidir",
    nome_oficina="Sala de Decisão e Convergência",
    descricao=(
        "Sprint Dia 3: Convergir. Votação silenciosa, Supervoto do decisor, "
        "escolha da solução vencedora, storyboard da experiência."
    ),
    ferramentas=[
        Ferramenta(
            id="votacao_dot", nome="Votação por Pontos (Dot Voting)",
            descricao=(
                "Cada agente distribui 3 votos nas melhores ideias. "
                "Sem debate — votação silenciosa baseada em critérios."
            ),
            tipo="votacao", custo_coins=0,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="supervoto", nome="Supervoto do Decisor",
            descricao=(
                "Helena (CEO) dá o voto final. "
                "Resolve empates. Escolhe a direção do protótipo."
            ),
            tipo="votacao", custo_coins=0,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="storyboard", nome="Storyboard da Experiência",
            descricao=(
                "Sequência de 8-12 quadros mostrando a jornada completa "
                "do usuário com a solução escolhida. Narrativa passo a passo."
            ),
            tipo="escrita", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="criterios_sucesso", nome="Critérios de Sucesso",
            descricao=(
                "Definir: o que precisa ser verdade para o protótipo "
                "ser considerado um sucesso no teste?"
            ),
            tipo="escrita", custo_coins=2,
            tipo_artefato="json",
        ),
    ],
))

# ── LABORATÓRIO DE PROTOTIPAGEM (Sprint Dia 4) ──
# Construir: protótipo realista em 1 dia
_reg(Oficina(
    local_id="sprint_prototipar",
    nome_oficina="Laboratório de Prototipagem Rápida",
    descricao=(
        "Sprint Dia 4: Prototipar. Criar fachada realista da solução. "
        "Não precisa funcionar — precisa PARECER real para testar. "
        "Código funcional, mockups, documentos, simulações."
    ),
    ferramentas=[
        Ferramenta(
            id="prototipo_codigo", nome="Protótipo em Código",
            descricao=(
                "Código Python funcional que demonstra a lógica central "
                "da solução. Executável no sandbox."
            ),
            tipo="codigo", custo_coins=10,
            modulos_sandbox=["math", "statistics", "random", "json",
                             "re", "collections", "datetime", "csv"],
            tipo_artefato="py",
        ),
        Ferramenta(
            id="prototipo_doc", nome="Protótipo Documental",
            descricao=(
                "Documento que simula o produto final: relatório, contrato, "
                "plano, manual — como se já existisse."
            ),
            tipo="escrita", custo_coins=8,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="prototipo_fluxo", nome="Protótipo de Fluxo",
            descricao=(
                "Sequência de telas/etapas da solução em formato texto. "
                "Cada tela: título, conteúdo, ações possíveis, próxima tela."
            ),
            tipo="escrita", custo_coins=5,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="dados_teste", nome="Dados de Teste",
            descricao=(
                "Dataset simulado para alimentar o protótipo. "
                "JSON/CSV com dados realistas para demonstração."
            ),
            tipo="codigo", custo_coins=5,
            modulos_sandbox=["math", "random", "json", "csv", "datetime"],
            tipo_artefato="json",
        ),
    ],
))

# ── SALA DE TESTES (Sprint Dia 5) ──
# Testar: colocar o protótipo na frente de usuários simulados
_reg(Oficina(
    local_id="sprint_testar",
    nome_oficina="Sala de Testes com Usuários",
    descricao=(
        "Sprint Dia 5: Testar. 5 entrevistas com usuários simulados. "
        "Observar reações, coletar feedback, identificar padrões. "
        "Decidir: funciona, ajustar ou pivotar."
    ),
    ferramentas=[
        Ferramenta(
            id="roteiro_teste", nome="Roteiro de Teste",
            descricao=(
                "Script de entrevista: introdução, tarefas para o usuário, "
                "perguntas de acompanhamento, encerramento."
            ),
            tipo="escrita", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="teste_usuario", nome="Teste com Usuário Simulado",
            descricao=(
                "Simular reação de uma persona-alvo ao protótipo. "
                "O agente assume o papel do usuário e reage honestamente."
            ),
            tipo="analise", custo_coins=8,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="mapa_feedback", nome="Mapa de Feedback",
            descricao=(
                "Compilar padrões: o que funcionou (+), o que confundiu (?), "
                "o que falhou (-). Grid de 5 usuários × N observações."
            ),
            tipo="analise", custo_coins=5,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="decisao_sprint", nome="Decisão Final do Sprint",
            descricao=(
                "Veredito: a) Funciona — implementar, b) Ajustar — iterar, "
                "c) Pivotar — nova direção. Baseado nos testes."
            ),
            tipo="votacao", custo_coins=0,
            tipo_artefato="json",
        ),
    ],
))


# ============================================================
# PROBLEM SOLVING — Frameworks simultâneos
# ============================================================

# ── SALA DE ÁRVORE DE PROBLEMAS ──
# Issue Tree, MECE, root cause analysis
_reg(Oficina(
    local_id="arvore_problemas",
    nome_oficina="Sala de Decomposição de Problemas",
    descricao=(
        "Frameworks analíticos: Issue Tree (McKinsey), MECE, 5 Porquês, "
        "Fishbone/Ishikawa, First Principles. Decompor antes de resolver."
    ),
    ferramentas=[
        Ferramenta(
            id="issue_tree", nome="Issue Tree (McKinsey)",
            descricao=(
                "Decompor problema em sub-problemas MECE "
                "(Mutuamente Exclusivos, Coletivamente Exaustivos). "
                "Árvore de 3-4 níveis com hipóteses testáveis."
            ),
            tipo="analise", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="cinco_porques", nome="5 Porquês (Root Cause)",
            descricao=(
                "Perguntar 'por quê?' 5 vezes até chegar na causa raiz. "
                "Cada nível revela uma camada mais profunda do problema."
            ),
            tipo="analise", custo_coins=0,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="fishbone", nome="Diagrama Fishbone (Ishikawa)",
            descricao=(
                "Mapear causas por categoria: Pessoas, Processos, "
                "Tecnologia, Ambiente, Métodos, Materiais."
            ),
            tipo="visual", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="first_principles", nome="Raciocínio First Principles",
            descricao=(
                "Desconstruir até axiomas fundamentais. "
                "O que é VERDADE INEGÁVEL? Reconstruir de baixo para cima."
            ),
            tipo="analise", custo_coins=5,
            tipo_artefato="md",
        ),
    ],
))

# ── SALA DE FRAMEWORKS ESTRATÉGICOS ──
# Porter, Blue Ocean, Jobs-to-be-Done, teoria dos jogos
_reg(Oficina(
    local_id="frameworks_estrategicos",
    nome_oficina="Sala de Frameworks Estratégicos",
    descricao=(
        "Porter 5 Forças, Blue Ocean Canvas, Jobs-to-be-Done, "
        "Business Model Canvas, teoria dos jogos, matriz de decisão."
    ),
    ferramentas=[
        Ferramenta(
            id="porter_5", nome="5 Forças de Porter",
            descricao=(
                "Analisar: rivalidade, novos entrantes, substitutos, "
                "poder dos fornecedores, poder dos compradores."
            ),
            tipo="analise", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="blue_ocean", nome="Blue Ocean Canvas",
            descricao=(
                "Curva de valor: quais fatores eliminar, reduzir, "
                "elevar e criar vs. concorrência."
            ),
            tipo="analise", custo_coins=5,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="jtbd", nome="Jobs-to-be-Done",
            descricao=(
                "Qual JOB o cliente está contratando este produto para fazer? "
                "Contexto → Motivação → Resultado esperado."
            ),
            tipo="pesquisa", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="bmc", nome="Business Model Canvas",
            descricao=(
                "9 blocos: proposta de valor, segmentos, canais, "
                "relacionamento, receita, recursos, atividades, parceiros, custos."
            ),
            tipo="escrita", custo_coins=5,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="matriz_decisao", nome="Matriz de Decisão Ponderada",
            descricao=(
                "Critérios × Opções com pesos. "
                "Cada agente pontua, média ponderada decide."
            ),
            tipo="analise", custo_coins=3,
            modulos_sandbox=["math", "statistics", "json"],
            tipo_artefato="json",
        ),
        Ferramenta(
            id="teoria_jogos", nome="Análise de Teoria dos Jogos",
            descricao=(
                "Modelar interações estratégicas: payoff matrix, "
                "equilíbrio de Nash, dilema do prisioneiro aplicado."
            ),
            tipo="analise", custo_coins=8,
            modulos_sandbox=["math", "statistics", "random", "json"],
            tipo_artefato="json",
        ),
    ],
))

# ── SALA DE DESIGN THINKING ──
# Empatia, definição, ideação, prototipagem, teste (IDEO/Stanford d.school)
_reg(Oficina(
    local_id="design_thinking",
    nome_oficina="Sala de Design Thinking (d.school)",
    descricao=(
        "Processo IDEO/Stanford: Empatizar → Definir → Idear → "
        "Prototipar → Testar. Foco no humano, não na tecnologia."
    ),
    ferramentas=[
        Ferramenta(
            id="mapa_empatia", nome="Mapa de Empatia",
            descricao=(
                "O que o usuário PENSA, SENTE, VÊ, OUVE, FALA, FAZ? "
                "Dores e ganhos. Entrar na cabeça do usuário."
            ),
            tipo="pesquisa", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="persona_usuario", nome="Criação de Persona",
            descricao=(
                "Persona fictícia mas realista: nome, idade, contexto, "
                "motivações, frustrações, quote representativa."
            ),
            tipo="escrita", custo_coins=3,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="jornada_usuario", nome="Mapa de Jornada do Usuário",
            descricao=(
                "Fases da experiência: descoberta → consideração → uso → "
                "retenção. Emoções, touchpoints, oportunidades em cada fase."
            ),
            tipo="visual", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="pov_statement", nome="Point of View Statement",
            descricao=(
                "[USUÁRIO] precisa de [NECESSIDADE] porque [INSIGHT]. "
                "A definição do problema que guia a ideação."
            ),
            tipo="escrita", custo_coins=0,
            tipo_artefato="md",
        ),
    ],
))

# ── SALA DE PESQUISA CIENTÍFICA ──
# Método científico, hipóteses, experimentos, papers
_reg(Oficina(
    local_id="pesquisa_cientifica",
    nome_oficina="Laboratório de Pesquisa Científica",
    descricao=(
        "Método científico rigoroso: hipótese → experimento → dados → conclusão. "
        "Revisão de literatura, análise estatística, refutação."
    ),
    ferramentas=[
        Ferramenta(
            id="hipotese", nome="Formulação de Hipótese",
            descricao=(
                "H0 (nula) vs H1 (alternativa). "
                "Variáveis independentes, dependentes, controle. "
                "Critério de refutação definido a priori."
            ),
            tipo="analise", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="revisao_literatura", nome="Revisão de Literatura",
            descricao=(
                "Buscar e sintetizar o que já se sabe sobre o tema. "
                "Estado da arte, lacunas, oportunidades de pesquisa."
            ),
            tipo="pesquisa", custo_coins=5,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="experimento_estatistico", nome="Experimento Estatístico",
            descricao=(
                "Desenho experimental + análise: t-test, chi-quadrado, "
                "correlação, regressão. Código Python executável."
            ),
            tipo="codigo", custo_coins=10,
            modulos_sandbox=[
                "math", "statistics", "random", "json", "csv",
                "numpy", "pandas", "scipy", "statsmodels", "sklearn",
            ],
            tipo_artefato="py",
        ),
        Ferramenta(
            id="analise_quant_rstyle", nome="Análise Quantitativa R-style",
            descricao=(
                "summary, cor, partial cor, lm, glm binomial, t-test, "
                "chi-quadrado, ANOVA, PCA, VIF e relatórios tabulares."
            ),
            tipo="codigo", custo_coins=12,
            modulos_sandbox=[
                "math", "statistics", "json", "csv", "numpy", "pandas",
                "scipy", "statsmodels", "sklearn", "pingouin",
            ],
            tipo_artefato="py",
        ),
        Ferramenta(
            id="paper_academico", nome="Paper Acadêmico (Estrutura)",
            descricao=(
                "Abstract, Introdução, Metodologia, Resultados, "
                "Discussão, Conclusão, Referências. Formato ABNT/APA."
            ),
            tipo="escrita", custo_coins=8,
            tipo_artefato="md",
        ),
    ],
))

# ── SALA DE LEAN / AGILE ──
# MVP, Lean Canvas, Kanban, retrospectivas
_reg(Oficina(
    local_id="lean_agile",
    nome_oficina="Sala Lean Startup & Agile",
    descricao=(
        "Build-Measure-Learn. Lean Canvas, MVP definition, "
        "Kanban, retrospectivas, pivotar vs perseverar."
    ),
    ferramentas=[
        Ferramenta(
            id="lean_canvas", nome="Lean Canvas",
            descricao=(
                "1 página: problema, solução, métricas-chave, "
                "proposta de valor única, vantagem injusta, canais, "
                "segmentos, estrutura de custos, fontes de receita."
            ),
            tipo="escrita", custo_coins=5,
            tipo_artefato="json",
        ),
        Ferramenta(
            id="mvp_definition", nome="Definição de MVP",
            descricao=(
                "O menor produto viável que testa a hipótese central. "
                "O que incluir, o que cortar, como medir sucesso."
            ),
            tipo="escrita", custo_coins=3,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="retrospectiva", nome="Retrospectiva",
            descricao=(
                "O que funcionou? O que não funcionou? "
                "O que fazer diferente? Ações concretas para próximo ciclo."
            ),
            tipo="escrita", custo_coins=0,
            tipo_artefato="md",
        ),
        Ferramenta(
            id="pivotar_perseverar", nome="Pivotar ou Perseverar",
            descricao=(
                "Análise baseada em dados: os indicadores justificam "
                "continuar ou mudar de direção?"
            ),
            tipo="analise", custo_coins=5,
            tipo_artefato="json",
        ),
    ],
))


# ============================================================
# REDAÇÃO MIRANTE NEWS — Publicação real no jornal
# ============================================================

_reg(Oficina(
    local_id="redacao_mirante",
    nome_oficina="Redação Mirante News",
    descricao=(
        "Redação do jornal mirantenews.com.br. Agentes redigem artigos, "
        "Helena revisa, e o texto é publicado de verdade no site. "
        "Formato MDX com frontmatter validado."
    ),
    ferramentas=[
        Ferramenta(
            id="artigo_mirante", nome="Redigir Artigo para Publicação",
            descricao=(
                "Artigo completo para o Mirante News: título, lead, corpo, "
                "tags, categoria. Formato MDX publicável."
            ),
            tipo="escrita", custo_coins=15,
            tipo_artefato="mdx",
        ),
        Ferramenta(
            id="analise_mirante", nome="Análise para Publicação",
            descricao=(
                "Artigo analítico baseado em dados e descobertas do desafio. "
                "Tipo: Pesquisa IA, Dados, Política, Economia."
            ),
            tipo="escrita", custo_coins=10,
            tipo_artefato="mdx",
        ),
        Ferramenta(
            id="opiniao_mirante", nome="Artigo de Opinião",
            descricao=(
                "Coluna de opinião assinada pelo consultor. "
                "Perspectiva única baseada na expertise do agente."
            ),
            tipo="escrita", custo_coins=8,
            tipo_artefato="mdx",
        ),
        Ferramenta(
            id="revisao_editorial", nome="Revisão Editorial (Helena)",
            descricao=(
                "Helena revisa artigo: verifica fatos, qualidade, "
                "adequação editorial, e aprova para publicação."
            ),
            tipo="analise", custo_coins=5,
            tipo_artefato="json",
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
