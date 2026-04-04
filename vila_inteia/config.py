"""
Configuração da Vila INTEIA.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConfigSimulacao:
    """Parâmetros da simulação."""

    # Tempo
    segundos_por_step: int = 600  # 10 minutos in-game por step
    data_inicio: str = "2026-03-01"
    hora_inicio: str = "06:00:00"

    # Agentes
    max_agentes_ativos: int = 140
    raio_percepcao: int = 2  # quantos locais adjacentes o agente percebe
    max_eventos_percepcao: int = 5
    retencao_memoria_curta: int = 50  # últimos N eventos
    decay_recencia: float = 0.995
    limiar_reflexao: int = 100  # acumular importância antes de refletir
    max_turnos_conversa: int = 10

    # IA
    omniroute_url: str = field(default_factory=lambda: os.getenv(
        "OMNIROUTE_URL", "http://localhost:20128"
    ))
    omniroute_api_key: str = field(default_factory=lambda: os.getenv(
        "OMNIROUTE_API_KEY", ""
    ))
    # Modelos via OmniRoute (definido por OMNIROUTE_URL) — todos gratuitos
    #
    # | Tarefa              | Combo           | Natureza                     | Volume    | Tokens |
    # |---------------------|-----------------|------------------------------|-----------|--------|
    # | Síntese estratégica | osa-elite       | 8+ perspectivas → insight    | Baixo     | ~300   |
    # | Diálogos/posts      | BestFREE        | Persona multi-turn, social   | Alto (30) | ~200   |
    # | FlockVote/rápido    | BestFREE        | Classificação, voto, ação    | Altíssimo | ~100   |
    # | Síntese tática      | osa-specialist  | Resumo, compressão           | Baixo     | ~200   |
    # | Embeddings          | openai/emb-3    | Vetores memória semântica    | Inativo   | —      |
    #
    modelo_pensamento: str = "osa-elite"  # Síntese de 8+ consultores (kr/sonnet-4.5 > grok-3 > llama-70b)
    modelo_conversa: str = "BestFREE"  # Diálogos + posts sociais — volume (kr/sonnet > haiku > groq/llama)
    modelo_rapido: str = "BestFREE"  # FlockVote (200+ eleitores), recomendações, ações rápidas
    modelo_sintese: str = "osa-specialist"  # Resumo tático, compressão (kr/haiku-4.5 > groq/llama > grok-3)
    modelo_embedding: str = "openai/text-embedding-3-small"  # Memória semântica (inativo, fallback keyword)

    # OSA (Optimal System Agent) — agente inteligente integrado
    osa_url: str = field(default_factory=lambda: os.getenv(
        "OSA_URL", "http://localhost:8089"
    ))
    osa_habilitado: bool = True  # Signal Theory + Web Search + Vault Memory
    osa_signal_threshold_elite: float = 0.6  # weight >= 0.6 → osa-elite
    osa_signal_threshold_specialist: float = 0.2  # weight >= 0.2 → osa-specialist

    # Persistência
    diretorio_dados: str = "/app/state"
    auto_save_intervalo: int = 50  # salvar a cada N steps

    # Simulação
    topicos_ativos: list = field(default_factory=list)
    modo_debug: bool = False


@dataclass
class ConfigCampus:
    """Layout do Campus INTEIA."""

    nome: str = "Campus INTEIA"
    descricao: str = (
        "Um campus de elite para pensadores lendários. "
        "Jardins amplos conectam prédios de arquitetura moderna, "
        "onde as maiores mentes da história debatem o futuro."
    )

    # Horários padrão
    hora_abertura: int = 6   # 6:00
    hora_fechamento: int = 23  # 23:00
    hora_almoco: int = 12
    hora_jantar: int = 19


# Singleton
config = ConfigSimulacao()
config_campus = ConfigCampus()
