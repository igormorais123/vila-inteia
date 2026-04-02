"""
Motor de Previsibilidade da Vila INTEIA.

Analisa padroes emergentes para prever:
- Quais topicos vao gerar mais engajamento
- Quais pares de consultores vao convergir/divergir
- Quando a vila vai saturar um tema
- Tendencias de opiniao coletiva

Alimenta Helena com dados preditivos.
"""

from __future__ import annotations

import math
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger("vila-inteia.previsibilidade")


@dataclass
class Tendencia:
    """Uma tendencia detectada na vila."""
    topico: str
    direcao: str  # "crescendo", "saturando", "emergente", "declinando"
    forca: float  # 0.0 a 1.0
    confianca: float  # 0.0 a 1.0
    evidencias: list[str] = field(default_factory=list)
    previsao: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "topico": self.topico,
            "direcao": self.direcao,
            "forca": round(self.forca, 2),
            "confianca": round(self.confianca, 2),
            "evidencias": self.evidencias[:5],
            "previsao": self.previsao,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PrevisaoDebate:
    """Previsao de resultado de debate entre consultores."""
    consultor_a: str
    consultor_b: str
    tema: str
    convergencia: float  # -1.0 (total divergencia) a 1.0 (total convergencia)
    engajamento_previsto: float  # 0-100
    categorias_interessadas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "par": f"{self.consultor_a} vs {self.consultor_b}",
            "tema": self.tema,
            "convergencia": round(self.convergencia, 2),
            "engajamento_previsto": round(self.engajamento_previsto, 1),
            "categorias_interessadas": self.categorias_interessadas,
        }


class MotorPrevisibilidade:
    """
    Analisa historico da vila para gerar previsoes.

    Roda a cada N steps e alimenta Helena com dados preditivos.
    """

    def __init__(self):
        # Historico de engajamento por topico
        self.engajamento_historico: dict[str, list[float]] = defaultdict(list)
        # Historico de categorias ativas
        self.categorias_por_step: list[set[str]] = []
        # Palavras-chave por step (para detectar tendencias)
        self.palavras_por_step: list[Counter] = []
        # Previsoes geradas
        self.tendencias: list[Tendencia] = []
        self.previsoes_debate: list[PrevisaoDebate] = []
        # Metricas de acuracia
        self.previsoes_feitas: int = 0
        self.previsoes_acertadas: int = 0

    def registrar_step(self, resumo_step: dict, rede_social=None):
        """Registra dados de um step para analise futura."""
        # Extrair categorias ativas
        categorias = set()
        for acao in resumo_step.get("acoes", []):
            if acao.get("tipo") == "conversa":
                categorias.add(acao.get("agente_nome", ""))
        self.categorias_por_step.append(categorias)

        # Extrair palavras-chave das conversas
        palavras = Counter()
        for conv in resumo_step.get("conversas", []):
            topico = conv.get("topico", "")
            for palavra in topico.lower().split():
                if len(palavra) > 3:
                    palavras[palavra] += 1
        self.palavras_por_step.append(palavras)

        # Registrar engajamento dos posts
        if rede_social:
            for post in rede_social.postagens[-10:]:
                for tag in post.tags:
                    self.engajamento_historico[tag].append(post.engajamento)

        # Limitar historico
        if len(self.palavras_por_step) > 500:
            self.palavras_por_step = self.palavras_por_step[-500:]
        if len(self.categorias_por_step) > 500:
            self.categorias_por_step = self.categorias_por_step[-500:]

    def analisar_tendencias(self) -> list[Tendencia]:
        """Detecta tendencias nos ultimos 50 steps."""
        if len(self.palavras_por_step) < 10:
            return []

        tendencias = []
        recente = self.palavras_por_step[-20:]
        antigo = self.palavras_por_step[-50:-20] if len(self.palavras_por_step) >= 50 else self.palavras_por_step[:max(len(self.palavras_por_step) - 20, 1)]

        # Contar frequencia recente vs antiga
        freq_recente = Counter()
        for step in recente:
            freq_recente.update(step)

        freq_antigo = Counter()
        for step in antigo:
            freq_antigo.update(step)

        n_recente = max(len(recente), 1)
        n_antigo = max(len(antigo), 1)

        # Detectar topicos emergentes (crescendo) e saturando (declinando)
        todas_palavras = set(freq_recente.keys()) | set(freq_antigo.keys())

        # Filtrar stopwords e palavras vazias
        _STOPWORDS = {
            "algo", "pessoas", "primeiro", "forma", "tudo", "construir",
            "conheca", "design", "sobre", "como", "para", "mais", "pode",
            "deve", "esta", "esse", "essa", "muito", "cada", "mesmo",
            "ainda", "quando", "onde", "fazer", "sendo", "entre", "desde",
            "antes", "depois", "aqui", "numa", "outro", "outra", "apenas",
            "tambem", "sempre", "nunca", "coisa", "parte", "mundo", "hoje",
            "futuro", "grande", "nova", "novo", "melhor", "pior", "precisa",
        }

        for palavra in todas_palavras:
            if palavra in _STOPWORDS or len(palavra) < 5:
                continue

            taxa_recente = freq_recente[palavra] / n_recente
            taxa_antigo = freq_antigo[palavra] / n_antigo

            if taxa_antigo == 0 and taxa_recente > 0.3:
                tendencias.append(Tendencia(
                    topico=f"Tema '{palavra}' emergindo",
                    direcao="emergente",
                    forca=min(taxa_recente, 1.0),
                    confianca=min(taxa_recente * 2, 0.9),
                    evidencias=[f"Apareceu {freq_recente[palavra]}x nos ultimos {n_recente} steps (novo)"],
                    previsao=f"'{palavra}' deve gerar novos debates nos proximos 20 steps",
                ))
            elif taxa_antigo > 0 and taxa_recente > taxa_antigo * 1.5:
                forca = min((taxa_recente - taxa_antigo) / max(taxa_antigo, 0.1), 1.0)
                tendencias.append(Tendencia(
                    topico=f"'{palavra}' em aceleracao",
                    direcao="crescendo",
                    forca=forca,
                    confianca=min(forca * 0.8, 0.85),
                    evidencias=[
                        f"Cresceu {(taxa_recente/max(taxa_antigo,0.01)-1)*100:.0f}% vs periodo anterior",
                    ],
                    previsao=f"Engajamento em '{palavra}' deve aumentar ~{forca*50:.0f}% — monitorar",
                ))
            elif taxa_antigo > 0.3 and taxa_recente < taxa_antigo * 0.5:
                tendencias.append(Tendencia(
                    topico=f"'{palavra}' esgotando",
                    direcao="saturando",
                    forca=1.0 - min(taxa_recente / max(taxa_antigo, 0.1), 1.0),
                    confianca=0.7,
                    evidencias=[f"Caiu {(1-taxa_recente/max(taxa_antigo,0.01))*100:.0f}% vs periodo anterior"],
                    previsao=f"Tema '{palavra}' precisa de novo angulo ou sera abandonado",
                ))

        # Ordenar por forca
        tendencias.sort(key=lambda t: t.forca, reverse=True)
        self.tendencias = tendencias[:10]
        return self.tendencias

    def prever_engajamento(self, topico: str) -> float:
        """Preve engajamento esperado para um topico (0-100)."""
        historico = self.engajamento_historico.get(topico, [])
        if not historico:
            return 50.0  # neutro

        # Media ponderada exponencial (recente pesa mais)
        if len(historico) == 1:
            return min(historico[0], 100)

        peso_total = 0
        soma_ponderada = 0
        for i, eng in enumerate(historico):
            peso = math.exp(i * 0.1)  # exponencial
            soma_ponderada += eng * peso
            peso_total += peso

        return min(soma_ponderada / peso_total, 100)

    def prever_saturacao(self, topico: str) -> float:
        """Preve nivel de saturacao de um topico (0.0 a 1.0)."""
        if len(self.palavras_por_step) < 5:
            return 0.0

        # Contar aparicoes nas ultimas janelas
        janela = self.palavras_por_step[-20:]
        aparicoes = sum(1 for step in janela if topico.lower() in step)
        taxa = aparicoes / len(janela)

        # Se aparece em >80% dos steps, esta saturado
        if taxa > 0.8:
            return 0.9
        elif taxa > 0.6:
            return 0.6
        elif taxa > 0.3:
            return 0.3
        return 0.1

    def sugerir_proximo_topico(self, topicos_atuais: list[str]) -> Optional[str]:
        """Sugere topico que geraria mais engajamento."""
        if not self.tendencias:
            self.analisar_tendencias()

        # Priorizar topicos emergentes que nao estao ativos
        for t in self.tendencias:
            if t.direcao == "emergente" and t.topico not in topicos_atuais:
                return t.topico

        # Se nao ha emergentes, sugerir o crescendo mais forte
        for t in self.tendencias:
            if t.direcao == "crescendo" and t.topico not in topicos_atuais:
                return t.topico

        return None

    def gerar_briefing_helena(self) -> dict:
        """Gera briefing preditivo para Helena consumir."""
        tendencias = self.analisar_tendencias()

        emergentes = [t.to_dict() for t in tendencias if t.direcao == "emergente"][:3]
        crescendo = [t.to_dict() for t in tendencias if t.direcao == "crescendo"][:3]
        saturando = [t.to_dict() for t in tendencias if t.direcao == "saturando"][:3]

        return {
            "tipo": "briefing_preditivo",
            "emergentes": emergentes,
            "crescendo": crescendo,
            "saturando": saturando,
            "total_tendencias": len(tendencias),
            "sugestao_topico": self.sugerir_proximo_topico(
                [t.topico for t in tendencias if t.direcao != "saturando"]
            ),
            "timestamp": datetime.now().isoformat(),
        }

    def to_dict(self) -> dict:
        return {
            "tendencias": [t.to_dict() for t in self.tendencias],
            "previsoes_debate": [p.to_dict() for p in self.previsoes_debate],
            "total_steps_analisados": len(self.palavras_por_step),
        }
