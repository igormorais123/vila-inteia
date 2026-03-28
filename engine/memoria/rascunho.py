"""
Rascunho (Scratch Memory) - Memória de trabalho do agente.

Estado atual, planos, ação em execução, conversa ativa.
Equivalente à "memória de trabalho" humana.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional


@dataclass
class AcaoAtual:
    """A ação que o agente está executando agora."""

    descricao: str = "dormindo"
    emoji: str = "😴"
    local_id: str = ""
    objeto_alvo: str = ""
    duracao_minutos: int = 60
    inicio: datetime = field(default_factory=datetime.now)
    progresso: float = 0.0  # 0-1


@dataclass
class PlanoItem:
    """Um item no plano do agente."""

    descricao: str
    hora_inicio: str  # "08:00"
    duracao_minutos: int
    local_id: str = ""
    prioridade: int = 5  # 1-10
    concluido: bool = False


@dataclass
class ConversaAtiva:
    """Estado de uma conversa em andamento."""

    parceiro_id: str
    parceiro_nome: str
    local_id: str
    turnos: list[tuple[str, str]] = field(default_factory=list)  # [(nome, fala)]
    inicio: datetime = field(default_factory=datetime.now)
    topico: str = ""
    encerrada: bool = False


class Rascunho:
    """
    Memória de trabalho do agente.

    Contém o estado atual, planos e informações transientes
    que não precisam persistir a longo prazo.
    """

    def __init__(self):
        # Identidade (preenchida do consultor lendário)
        self.nome: str = ""
        self.titulo: str = ""
        self.categoria: str = ""
        self.personalidade_resumo: str = ""
        self.estilo_comunicacao: str = ""
        self.tom_voz: str = ""
        self.areas_expertise: list[str] = []
        self.frase_chave: str = ""

        # Estado atual
        self.local_atual: str = ""
        self.acao: AcaoAtual = AcaoAtual()
        self.humor: str = "neutro"  # neutro, animado, pensativo, irritado, etc.
        self.energia: int = 100  # 0-100

        # Planejamento
        self.plano_diario: list[PlanoItem] = []
        self.proxima_acao: Optional[PlanoItem] = None

        # Conversa
        self.conversa_ativa: Optional[ConversaAtiva] = None
        self.conversando_com: Optional[str] = None  # ID do parceiro

        # Hiperparâmetros cognitivos (do consultor)
        self.raio_percepcao: int = 2
        self.nivel_agressividade: int = 5
        self.nivel_empatia: int = 5
        self.nivel_carisma: int = 5
        self.nivel_extroversao: int = 5
        self.tolerancia_risco: int = 5
        self.nivel_formalidade: int = 5

        # Relacionamentos especiais (carregados do consultor)
        self.mentores: list[str] = []
        self.rivais: list[str] = []
        self.influenciou: list[str] = []
        self.influenciado_por: list[str] = []

        # Tópicos de interesse atual
        self.topicos_interesse: list[str] = []

        # Última reflexão
        self.ultima_reflexao: Optional[datetime] = None
        self.reflexoes_hoje: int = 0

    @property
    def esta_conversando(self) -> bool:
        return self.conversa_ativa is not None and not self.conversa_ativa.encerrada

    @property
    def esta_dormindo(self) -> bool:
        return "dorm" in self.acao.descricao.lower()

    @property
    def esta_ocupado(self) -> bool:
        return self.esta_conversando or self.acao.progresso < 0.9

    def iniciar_conversa(
        self,
        parceiro_id: str,
        parceiro_nome: str,
        local_id: str,
        topico: str = "",
    ):
        """Inicia uma conversa com outro agente."""
        self.conversa_ativa = ConversaAtiva(
            parceiro_id=parceiro_id,
            parceiro_nome=parceiro_nome,
            local_id=local_id,
            topico=topico,
        )
        self.conversando_com = parceiro_id

    def adicionar_turno_conversa(self, nome: str, fala: str):
        """Adiciona um turno à conversa ativa."""
        if self.conversa_ativa:
            self.conversa_ativa.turnos.append((nome, fala))

    def encerrar_conversa(self) -> Optional[ConversaAtiva]:
        """Encerra a conversa ativa e retorna o registro."""
        if self.conversa_ativa:
            self.conversa_ativa.encerrada = True
            conversa = self.conversa_ativa
            self.conversa_ativa = None
            self.conversando_com = None
            return conversa
        return None

    def atualizar_acao(
        self,
        descricao: str,
        emoji: str = "",
        local_id: str = "",
        duracao: int = 30,
    ):
        """Atualiza a ação atual do agente."""
        self.acao = AcaoAtual(
            descricao=descricao,
            emoji=emoji or self._emoji_para_acao(descricao),
            local_id=local_id or self.local_atual,
            duracao_minutos=duracao,
        )

    def atualizar_energia(self, delta: int):
        """Ajusta energia do agente."""
        self.energia = max(0, min(100, self.energia + delta))

    def _emoji_para_acao(self, descricao: str) -> str:
        """Gera emoji baseado na descrição da ação."""
        desc_lower = descricao.lower()
        mapa = {
            "dorm": "😴", "descans": "😌", "acord": "🌅",
            "café": "☕", "com": "🍽️", "almoç": "🍽️", "jant": "🍽️",
            "debate": "🗣️", "discut": "💬", "convers": "💬",
            "estud": "📚", "pesquis": "🔍", "le": "📖",
            "escrev": "✍️", "trabalh": "💼", "reuni": "👥",
            "pens": "🤔", "reflet": "💭", "medita": "🧘",
            "apresent": "🎤", "palestra": "🎓", "aula": "📝",
            "caminh": "🚶", "observ": "👀", "explo": "🔭",
            "cria": "🎨", "inov": "💡", "projet": "📐",
        }
        for chave, emoji in mapa.items():
            if chave in desc_lower:
                return emoji
        return "🔵"

    def contexto_para_prompt(self) -> str:
        """Gera contexto textual para uso em prompts de IA."""
        linhas = [
            f"Nome: {self.nome}",
            f"Título: {self.titulo}",
            f"Personalidade: {self.personalidade_resumo}",
            f"Tom de voz: {self.tom_voz}",
            f"Estilo: {self.estilo_comunicacao}",
            f"Expertise: {', '.join(self.areas_expertise[:5])}",
            f"Local atual: {self.local_atual}",
            f"Ação atual: {self.acao.descricao}",
            f"Humor: {self.humor}",
            f"Energia: {self.energia}%",
        ]
        if self.frase_chave:
            linhas.append(f"Frase marcante: \"{self.frase_chave}\"")
        return "\n".join(linhas)

    def to_dict(self) -> dict:
        return {
            "nome": self.nome,
            "local_atual": self.local_atual,
            "acao": {
                "descricao": self.acao.descricao,
                "emoji": self.acao.emoji,
                "local_id": self.acao.local_id,
                "duracao_minutos": self.acao.duracao_minutos,
                "progresso": self.acao.progresso,
            },
            "humor": self.humor,
            "energia": self.energia,
            "conversando_com": self.conversando_com,
            "plano_diario": [
                {
                    "descricao": p.descricao,
                    "hora_inicio": p.hora_inicio,
                    "duracao_minutos": p.duracao_minutos,
                    "concluido": p.concluido,
                }
                for p in self.plano_diario
            ],
        }
