"""
Motor de Desafios Coletivos — O propósito da Vila INTEIA.

O USUÁRIO define o tema. Digita texto livre, cola documento, anexa arquivo.
A Vila cria fases automaticamente e os agentes trabalham no que foi pedido.

SEM catálogo fixo. SEM temas clichê. O input é do fundador.

Arquitetura:
    DesafioColetivo (meta + fases + progresso)
    └── Fase (etapa do desafio)
        └── Entrega (artefato produzido coletivamente)
            └── Contribuicao (proposta de um agente)
"""

from __future__ import annotations

import json
import os
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ============================================================
# FASES PADRÃO — geradas dinamicamente a partir do tema
# ============================================================

# Pipeline universal: funciona para qualquer tema
FASES_PADRAO = [
    {"id": "pesquisa", "nome": "Pesquisa", "descricao_template": "Pesquisar e mapear tudo sobre: {tema}", "peso": 0.15},
    {"id": "analise", "nome": "Análise", "descricao_template": "Analisar dados, argumentos e perspectivas sobre: {tema}", "peso": 0.20},
    {"id": "propostas", "nome": "Propostas", "descricao_template": "Cada agente propõe soluções concretas para: {tema}", "peso": 0.25},
    {"id": "debate", "nome": "Debate", "descricao_template": "Debater e refinar as melhores propostas sobre: {tema}", "peso": 0.25},
    {"id": "entrega", "nome": "Entrega Final", "descricao_template": "Compilar resultado final sobre: {tema}", "peso": 0.15},
]


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class Contribuicao:
    """Uma proposta/contribuição de um agente para uma entrega."""
    agente_id: str
    agente_nome: str
    conteudo: str
    tipo: str = "proposta"  # proposta | emenda | apoio | oposicao | sintese
    votos_favor: int = 0
    votos_contra: int = 0
    timestamp: str = ""
    fase_id: str = ""

    def to_dict(self) -> dict:
        return {
            "agente_id": self.agente_id,
            "agente_nome": self.agente_nome,
            "conteudo": self.conteudo,
            "tipo": self.tipo,
            "votos_favor": self.votos_favor,
            "votos_contra": self.votos_contra,
            "timestamp": self.timestamp,
            "fase_id": self.fase_id,
        }


@dataclass
class Entrega:
    """Um artefato produzido coletivamente durante o desafio."""
    id: str
    nome: str
    descricao: str = ""
    contribuicoes: list[Contribuicao] = field(default_factory=list)
    status: str = "aberta"  # aberta | em_debate | votando | aprovada | rejeitada
    consenso: float = 0.0  # 0-1
    conteudo_final: str = ""
    votos_favor: int = 0
    votos_contra: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "contribuicoes": [c.to_dict() for c in self.contribuicoes[-20:]],
            "total_contribuicoes": len(self.contribuicoes),
            "status": self.status,
            "consenso": self.consenso,
            "conteudo_final": self.conteudo_final,
            "votos_favor": self.votos_favor,
            "votos_contra": self.votos_contra,
        }


@dataclass
class FaseDesafio:
    """Uma fase/etapa do desafio coletivo."""
    id: str
    nome: str
    descricao: str
    peso: float = 0.2  # peso no progresso total
    status: str = "pendente"  # pendente | ativa | concluida
    progresso: float = 0.0  # 0-1
    step_inicio: int = 0
    step_fim: int = 0
    entregas: list[Entrega] = field(default_factory=list)
    insights_fase: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "peso": self.peso,
            "status": self.status,
            "progresso": round(self.progresso, 3),
            "step_inicio": self.step_inicio,
            "step_fim": self.step_fim,
            "entregas": [e.to_dict() for e in self.entregas],
            "insights_fase": self.insights_fase[-10:],
        }


@dataclass
class DesafioColetivo:
    """O desafio central que dá propósito à simulação."""
    id: str = ""
    nome: str = ""
    descricao: str = ""
    icone: str = "🎯"
    fases: list[FaseDesafio] = field(default_factory=list)
    fase_atual_idx: int = 0
    status: str = "inativo"  # inativo | ativo | concluido
    progresso_total: float = 0.0
    consenso_minimo: float = 0.6
    steps_por_fase: int = 100
    step_inicio: int = 0
    entregas_esperadas: list[str] = field(default_factory=list)

    # Métricas acumuladas
    total_contribuicoes: int = 0
    total_debates: int = 0
    total_votos: int = 0
    agentes_participantes: set = field(default_factory=set)
    _contribuicoes_recentes: list[Contribuicao] = field(default_factory=list)

    # Onda 10: distribuição Shapley calculada ao concluir
    shapley_final: dict = field(default_factory=dict)

    @property
    def fase_atual(self) -> Optional[FaseDesafio]:
        if 0 <= self.fase_atual_idx < len(self.fases):
            return self.fases[self.fase_atual_idx]
        return None

    @property
    def ativo(self) -> bool:
        return self.status == "ativo"

    def iniciar(self, step: int):
        """Inicia o desafio na fase 0."""
        self.status = "ativo"
        self.step_inicio = step
        if self.fases:
            self.fases[0].status = "ativa"
            self.fases[0].step_inicio = step

    def registrar_contribuicao(self, contribuicao: Contribuicao, step: int):
        """Registra uma contribuição de um agente."""
        fase = self.fase_atual
        if not fase or fase.status != "ativa":
            return

        contribuicao.fase_id = fase.id
        contribuicao.timestamp = str(step)

        # Adicionar à entrega correspondente ou criar nova
        if fase.entregas:
            entrega = fase.entregas[-1]
            if entrega.status in ("aberta", "em_debate"):
                entrega.contribuicoes.append(contribuicao)
            else:
                nova = Entrega(
                    id=f"{fase.id}_{len(fase.entregas)}",
                    nome=f"Proposta #{len(fase.entregas) + 1}",
                    contribuicoes=[contribuicao],
                )
                fase.entregas.append(nova)
        else:
            nova = Entrega(
                id=f"{fase.id}_0",
                nome="Proposta #1",
                contribuicoes=[contribuicao],
            )
            fase.entregas.append(nova)

        self.total_contribuicoes += 1
        self.agentes_participantes.add(contribuicao.agente_id)
        self._contribuicoes_recentes.append(contribuicao)
        if len(self._contribuicoes_recentes) > 100:
            self._contribuicoes_recentes = self._contribuicoes_recentes[-100:]

    def registrar_voto(self, agente_id: str, entrega_id: str, favor: bool):
        """Registra voto em uma entrega e atualiza status se atingir consenso."""
        for fase in self.fases:
            for entrega in fase.entregas:
                if entrega.id == entrega_id:
                    if favor:
                        entrega.votos_favor += 1
                    else:
                        entrega.votos_contra += 1
                    total = entrega.votos_favor + entrega.votos_contra
                    if total > 0:
                        entrega.consenso = entrega.votos_favor / total
                    self.total_votos += 1
                    # Aprovar/rejeitar com base no consenso mínimo (quórum: 5+ votos)
                    if total >= 5:
                        if entrega.consenso >= self.consenso_minimo:
                            entrega.status = "aprovada"
                        elif entrega.consenso < (1 - self.consenso_minimo):
                            entrega.status = "rejeitada"
                        else:
                            entrega.status = "em_debate"
                    return

    def atualizar_progresso(self, step: int):
        """Recalcula progresso total e verifica transições de fase."""
        fase = self.fase_atual
        if not fase or not self.ativo:
            return

        # Progresso da fase = combinação de contribuições + tempo
        steps_na_fase = step - fase.step_inicio
        progresso_tempo = min(steps_na_fase / max(self.steps_por_fase, 1), 1.0)

        n_contribuicoes = sum(len(e.contribuicoes) for e in fase.entregas)
        progresso_contrib = min(n_contribuicoes / 20, 1.0)  # 20 contribuições = 100%

        # Média ponderada: 40% tempo, 60% contribuições
        fase.progresso = progresso_tempo * 0.4 + progresso_contrib * 0.6
        fase.progresso = min(fase.progresso, 1.0)

        # Transição automática de fase
        if fase.progresso >= 0.95 or steps_na_fase >= self.steps_por_fase:
            self._avancar_fase(step)

        # Progresso total = soma ponderada das fases
        self.progresso_total = sum(
            f.progresso * f.peso for f in self.fases
        )
        self.progresso_total = min(self.progresso_total, 1.0)

        # Desafio concluído?
        if self.fase_atual_idx >= len(self.fases):
            self.status = "concluido"
            # Onda 10: distribuição Shapley por contribuições aprovadas
            self._calcular_shapley_final()

    def _calcular_shapley_final(self):
        """Calcula Shapley value para contribuintes (Onda 10 integration)."""
        try:
            from engine.simulacao_avancada.coalizoes import shapley_value
            # Coleta contribuições aprovadas por autor
            contrib_por_autor: dict[str, int] = {}
            for fase in self.fases:
                for entrega in fase.entregas:
                    if entrega.status == "aprovada":
                        for c in entrega.contribuicoes:
                            contrib_por_autor[c.autor_id] = contrib_por_autor.get(c.autor_id, 0) + 1
            if not contrib_por_autor:
                return
            # Top-8 para viabilizar O(n!) do Shapley
            autores = sorted(contrib_por_autor.items(), key=lambda x: -x[1])[:8]
            jogadores = [a for a, _ in autores]
            counts = dict(autores)

            def v(coal: frozenset) -> float:
                # Valor = soma de contribuições dos membros (super-aditivo simples)
                return float(sum(counts[j] for j in coal))

            self.shapley_final = shapley_value(jogadores, v)
        except Exception:
            self.shapley_final = {}

    def _avancar_fase(self, step: int):
        """Avança para a próxima fase."""
        fase = self.fase_atual
        if fase:
            fase.status = "concluida"
            fase.progresso = 1.0
            fase.step_fim = step

        self.fase_atual_idx += 1
        nova = self.fase_atual
        if nova:
            nova.status = "ativa"
            nova.step_inicio = step

    def gerar_contexto_para_agente(self) -> str:
        """Gera contexto textual do desafio para injetar no prompt dos agentes."""
        if not self.ativo:
            return ""

        fase = self.fase_atual
        if not fase:
            return ""

        linhas = [
            f"DESAFIO COLETIVO DA VILA: {self.icone} {self.nome}",
            f"Objetivo: {self.descricao}",
            f"Fase atual: {fase.nome} — {fase.descricao}",
            f"Progresso: {self.progresso_total:.0%} geral, {fase.progresso:.0%} nesta fase",
        ]

        # Últimas contribuições relevantes
        recentes = self._contribuicoes_recentes[-5:]
        if recentes:
            linhas.append("Contribuições recentes:")
            for c in recentes:
                linhas.append(f"  - {c.agente_nome}: {c.conteudo[:100]}")

        linhas.append(
            f"Sua tarefa nesta fase: contribua com sua expertise sobre '{fase.descricao}'. "
            f"Proponha, debata, refine ou vote."
        )

        return "\n".join(linhas)

    def gerar_topicos_fase(self) -> list[str]:
        """Gera tópicos de discussão baseados na fase atual."""
        fase = self.fase_atual
        if not fase:
            return []

        base = f"{self.nome}: {fase.descricao}"
        return [
            base,
            f"Qual a prioridade na fase '{fase.nome}'?",
            f"Divergências sobre {fase.descricao.lower()}",
        ]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "icone": self.icone,
            "status": self.status,
            "fase_atual": self.fase_atual.to_dict() if self.fase_atual else None,
            "fase_atual_idx": self.fase_atual_idx,
            "total_fases": len(self.fases),
            "fases": [f.to_dict() for f in self.fases],
            "progresso_total": round(self.progresso_total, 3),
            "consenso_minimo": self.consenso_minimo,
            "metricas": {
                "total_contribuicoes": self.total_contribuicoes,
                "total_debates": self.total_debates,
                "total_votos": self.total_votos,
                "agentes_participantes": len(self.agentes_participantes),
            },
            "contribuicoes_recentes": [
                c.to_dict() for c in self._contribuicoes_recentes[-10:]
            ],
        }

    def salvar(self, caminho: str):
        """Salva estado do desafio em JSON."""
        dados = self.to_dict()
        # agentes_participantes não é serializável como set
        dados["agentes_participantes_lista"] = list(self.agentes_participantes)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    @classmethod
    def carregar(cls, caminho: str) -> Optional[DesafioColetivo]:
        """Carrega desafio de JSON."""
        if not os.path.exists(caminho):
            return None
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        desafio = cls()
        desafio.id = dados.get("id", "")
        desafio.nome = dados.get("nome", "")
        desafio.descricao = dados.get("descricao", "")
        desafio.icone = dados.get("icone", "🎯")
        desafio.status = dados.get("status", "inativo")
        desafio.fase_atual_idx = dados.get("fase_atual_idx", 0)
        desafio.progresso_total = dados.get("progresso_total", 0)
        desafio.consenso_minimo = dados.get("consenso_minimo", 0.6)
        desafio.agentes_participantes = set(dados.get("agentes_participantes_lista", []))
        metricas = dados.get("metricas", {})
        desafio.total_contribuicoes = metricas.get("total_contribuicoes", 0)
        desafio.total_debates = metricas.get("total_debates", 0)
        desafio.total_votos = metricas.get("total_votos", 0)
        # Reconstruir fases
        for fd in dados.get("fases", []):
            fase = FaseDesafio(
                id=fd["id"], nome=fd["nome"], descricao=fd["descricao"],
                peso=fd.get("peso", 0.2), status=fd.get("status", "pendente"),
                progresso=fd.get("progresso", 0),
                step_inicio=fd.get("step_inicio", 0),
                step_fim=fd.get("step_fim", 0),
            )
            desafio.fases.append(fase)
        return desafio


# ============================================================
# FACTORY — Criação a partir do input do USUÁRIO
# ============================================================

def _gerar_id(nome: str) -> str:
    """Gera ID slug a partir do nome."""
    slug = re.sub(r'[^a-z0-9]+', '_', nome.lower().strip())
    return slug[:50].strip('_') or f"desafio_{random.randint(1000,9999)}"


def criar_desafio_livre(
    tema: str,
    descricao: str = "",
    documento: str = "",
    steps_por_fase: int = 100,
    consenso_minimo: float = 0.6,
) -> DesafioColetivo:
    """
    Cria desafio a partir de input do usuário.

    Args:
        tema: Texto livre do usuário (ex: "Analisar eleições 2026 no DF")
        descricao: Contexto adicional (opcional)
        documento: Conteúdo de arquivo anexado (texto extraído)
        steps_por_fase: Duração de cada fase
        consenso_minimo: % mínimo para aprovar entrega
    """
    nome = tema[:100]
    desc_completa = descricao or tema

    # Se tem documento anexado, incluir no contexto
    if documento:
        # Truncar documento longo para ficar manejável
        doc_resumo = documento[:5000]
        desc_completa = f"{desc_completa}\n\nDOCUMENTO ANEXADO:\n{doc_resumo}"

    desafio = DesafioColetivo(
        id=_gerar_id(nome),
        nome=nome,
        descricao=desc_completa,
        icone="🎯",
        consenso_minimo=consenso_minimo,
        steps_por_fase=steps_por_fase,
    )

    # Gerar fases dinâmicas a partir do pipeline padrão
    for fp in FASES_PADRAO:
        fase = FaseDesafio(
            id=fp["id"],
            nome=fp["nome"],
            descricao=fp["descricao_template"].format(tema=nome),
            peso=fp.get("peso", 0.2),
        )
        desafio.fases.append(fase)

    return desafio


def criar_desafio(tema_ou_id: str, descricao: str = "", documento: str = "") -> DesafioColetivo:
    """
    Cria desafio a partir de qualquer input.
    Compatível com chamadas antigas (aceita ID ou texto livre).
    """
    return criar_desafio_livre(tema_ou_id, descricao, documento)


def desafio_aleatorio() -> DesafioColetivo:
    """Cria desafio placeholder — o usuário deve definir o tema."""
    return criar_desafio_livre("Tema a ser definido pelo usuário")


def listar_desafios() -> list[dict]:
    """Não há catálogo fixo. Retorna instruções."""
    return [
        {
            "id": "livre",
            "nome": "Desafio Livre",
            "descricao": "Digite o tema, cole texto ou anexe documento. A Vila trabalha no que VOCÊ definir.",
            "icone": "🎯",
            "total_fases": len(FASES_PADRAO),
        }
    ]
