"""
Motor de Desafios Coletivos — O propósito da Vila INTEIA.

Cada simulação tem um DESAFIO CENTRAL: um objetivo concreto
que todos os agentes trabalham para construir coletivamente.

Os debates, trabalhos e gestão passam a orbitar o desafio.
Agentes contribuem com propostas, votam, debatem, refinam.

Exemplo de desafio:
    "Construir a Constituição Digital do Brasil"
    - Fases: Diagnóstico → Propostas → Debate → Síntese → Votação
    - Entregas: Artigos constitucionais aprovados por consenso
    - Progresso: % de artigos aprovados, nível de consenso

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
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ============================================================
# CATÁLOGO DE DESAFIOS
# ============================================================

CATALOGO_DESAFIOS = [
    {
        "id": "constituicao_digital",
        "nome": "Constituição Digital do Brasil",
        "descricao": (
            "144 mentes lendárias devem redigir, debater e aprovar uma "
            "Constituição Digital para o Brasil do século XXI. Cada artigo "
            "precisa de consenso mínimo de 60% dos participantes ativos."
        ),
        "icone": "📜",
        "fases": [
            {"id": "diagnostico", "nome": "Diagnóstico", "descricao": "Mapear os problemas digitais do Brasil", "peso": 0.15},
            {"id": "propostas", "nome": "Propostas", "descricao": "Cada agente propõe artigos constitucionais", "peso": 0.25},
            {"id": "debate", "nome": "Debate", "descricao": "Debates entre facções sobre cada artigo", "peso": 0.30},
            {"id": "sintese", "nome": "Síntese", "descricao": "Helena sintetiza consensos e divergências", "peso": 0.15},
            {"id": "votacao", "nome": "Votação", "descricao": "Votação final por artigo (mínimo 60%)", "peso": 0.15},
        ],
        "entregas_esperadas": ["artigos_aprovados", "principios_fundamentais", "mecanismos_governanca"],
        "steps_por_fase": 100,
        "consenso_minimo": 0.6,
    },
    {
        "id": "cidade_futuro",
        "nome": "Projetar a Cidade do Futuro",
        "descricao": (
            "Os consultores devem projetar coletivamente uma cidade ideal "
            "para 2050: infraestrutura, governança, tecnologia, cultura, "
            "sustentabilidade. Cada dimensão é um eixo de trabalho."
        ),
        "icone": "🏙️",
        "fases": [
            {"id": "visao", "nome": "Visão", "descricao": "Definir princípios e valores da cidade", "peso": 0.15},
            {"id": "eixos", "nome": "Eixos Temáticos", "descricao": "Grupos trabalham em cada dimensão", "peso": 0.25},
            {"id": "integrar", "nome": "Integração", "descricao": "Resolver conflitos entre eixos", "peso": 0.25},
            {"id": "prototipo", "nome": "Protótipo", "descricao": "Compilar o projeto final", "peso": 0.20},
            {"id": "apresentacao", "nome": "Apresentação", "descricao": "Defesa pública do projeto", "peso": 0.15},
        ],
        "entregas_esperadas": ["plano_urbanistico", "modelo_governanca", "pilares_tecnologicos"],
        "steps_por_fase": 80,
        "consenso_minimo": 0.5,
    },
    {
        "id": "educacao_universal",
        "nome": "Plano de Educação Universal 2050",
        "descricao": (
            "Criar um modelo educacional que funcione para qualquer pessoa "
            "em qualquer lugar do mundo. Combinar IA, pedagogia clássica, "
            "neurociência e cultura local."
        ),
        "icone": "🎓",
        "fases": [
            {"id": "diagnostico", "nome": "Diagnóstico", "descricao": "O que falha na educação atual?", "peso": 0.15},
            {"id": "principios", "nome": "Princípios", "descricao": "Pilares inegociáveis do modelo", "peso": 0.20},
            {"id": "curriculo", "nome": "Currículo", "descricao": "O que ensinar e como", "peso": 0.25},
            {"id": "tecnologia", "nome": "Tecnologia", "descricao": "IA, plataformas, acesso", "peso": 0.20},
            {"id": "piloto", "nome": "Piloto", "descricao": "Plano de implementação para 1 país", "peso": 0.20},
        ],
        "entregas_esperadas": ["modelo_pedagogico", "stack_tecnologico", "plano_piloto"],
        "steps_por_fase": 80,
        "consenso_minimo": 0.5,
    },
    {
        "id": "tribunal_ia",
        "nome": "Tribunal da Inteligência Artificial",
        "descricao": (
            "Julgar coletivamente se a IA deve ter direitos, deveres e limites. "
            "Formato: tribunal com acusação, defesa, jurados e veredito. "
            "Cada rodada julga um aspecto diferente."
        ),
        "icone": "⚖️",
        "fases": [
            {"id": "acusacao", "nome": "Acusação", "descricao": "Riscos e danos potenciais da IA", "peso": 0.20},
            {"id": "defesa", "nome": "Defesa", "descricao": "Benefícios e potencial transformador", "peso": 0.20},
            {"id": "testemunhas", "nome": "Testemunhas", "descricao": "Depoimentos de especialistas", "peso": 0.20},
            {"id": "deliberacao", "nome": "Deliberação", "descricao": "Jurados debatem entre si", "peso": 0.25},
            {"id": "veredito", "nome": "Veredito", "descricao": "Votação final e sentença coletiva", "peso": 0.15},
        ],
        "entregas_esperadas": ["vereditos", "jurisprudencia_ia", "marco_regulatorio"],
        "steps_por_fase": 60,
        "consenso_minimo": 0.55,
    },
    {
        "id": "empresa_perfeita",
        "nome": "A Empresa Perfeita",
        "descricao": (
            "Projetar a empresa ideal do século XXI: modelo de negócio, "
            "cultura, estrutura, tecnologia, impacto social. "
            "De Jobs a Buffett, cada mente contribui sua visão."
        ),
        "icone": "🏢",
        "fases": [
            {"id": "missao", "nome": "Missão & Visão", "descricao": "Por que essa empresa existe?", "peso": 0.15},
            {"id": "modelo", "nome": "Modelo de Negócio", "descricao": "Como gera valor e receita", "peso": 0.25},
            {"id": "cultura", "nome": "Cultura & Pessoas", "descricao": "Como trabalham e decidem", "peso": 0.20},
            {"id": "tecnologia", "nome": "Stack & Operações", "descricao": "Infraestrutura e processos", "peso": 0.20},
            {"id": "impacto", "nome": "Impacto & Legado", "descricao": "Marca no mundo", "peso": 0.20},
        ],
        "entregas_esperadas": ["business_plan", "manifesto_cultural", "stack_operacional"],
        "steps_por_fase": 80,
        "consenso_minimo": 0.5,
    },
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
# FACTORY
# ============================================================

def criar_desafio(desafio_id: str) -> Optional[DesafioColetivo]:
    """Cria um desafio a partir do catálogo."""
    for catalogo in CATALOGO_DESAFIOS:
        if catalogo["id"] == desafio_id:
            desafio = DesafioColetivo(
                id=catalogo["id"],
                nome=catalogo["nome"],
                descricao=catalogo["descricao"],
                icone=catalogo.get("icone", "🎯"),
                consenso_minimo=catalogo.get("consenso_minimo", 0.6),
                steps_por_fase=catalogo.get("steps_por_fase", 100),
                entregas_esperadas=catalogo.get("entregas_esperadas", []),
            )
            for fd in catalogo["fases"]:
                fase = FaseDesafio(
                    id=fd["id"],
                    nome=fd["nome"],
                    descricao=fd["descricao"],
                    peso=fd.get("peso", 0.2),
                )
                desafio.fases.append(fase)
            return desafio
    return None


def desafio_aleatorio() -> DesafioColetivo:
    """Cria um desafio aleatório do catálogo."""
    escolha = random.choice(CATALOGO_DESAFIOS)
    return criar_desafio(escolha["id"])


def listar_desafios() -> list[dict]:
    """Lista desafios disponíveis no catálogo."""
    return [
        {
            "id": d["id"],
            "nome": d["nome"],
            "descricao": d["descricao"],
            "icone": d.get("icone", "🎯"),
            "total_fases": len(d["fases"]),
        }
        for d in CATALOGO_DESAFIOS
    ]
