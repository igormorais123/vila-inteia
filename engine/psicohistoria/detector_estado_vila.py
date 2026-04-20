"""
Detector de estado social atual da Vila em tempo real (Onda 11).

Mapeia métricas do step atual (n_conversas, n_reflexoes, polarização de crenças,
ativos vs latentes, economia Gini, etc.) → um dos 8 estados canônicos da
psico-história.

Permite construir trajetória real observada para comparar com Plano de Seldon
e acionar detector de Mule.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MetricasStep:
    step: int
    n_conversas: int
    n_reflexoes: int
    n_agentes_ativos: int
    n_agentes_latentes: int
    total_agentes: int
    polarizacao_media: float = 0.0       # 0 (consenso) a 1 (bimodal extremo)
    gini_economia: float = 0.0           # 0 (igualdade) a 1 (desigual extrema)
    propostas_constituintes_ativas: int = 0
    contribuicoes_ao_desafio: int = 0


ESTADOS_CANONICOS = [
    "bootstrap", "recrutamento", "expansao", "consenso_fragil",
    "polarizacao", "crise_economica", "renovacao_constituinte", "equilibrio",
]


def classificar_estado(m: MetricasStep) -> str:
    """
    Heurística de classificação. Prioridade top-down:

    1. Propostas constituintes ativas → renovacao_constituinte
    2. Gini > 0.75 → crise_economica
    3. Polarização > 0.6 → polarizacao
    4. Step < 20 AND ativos < 60% do total → bootstrap
    5. Ativos < 40% do total → recrutamento
    6. Contribuições > 20/step AND ativos > 70% → expansao
    7. Polarização 0.15–0.40 → consenso_fragil
    8. Senão → equilibrio
    """
    if m.total_agentes == 0:
        return "bootstrap"

    frac_ativos = m.n_agentes_ativos / m.total_agentes

    if m.propostas_constituintes_ativas >= 1:
        return "renovacao_constituinte"
    if m.gini_economia > 0.75:
        return "crise_economica"
    if m.polarizacao_media > 0.60:
        return "polarizacao"
    if m.step < 20 and frac_ativos < 0.60:
        return "bootstrap"
    if frac_ativos < 0.40:
        return "recrutamento"
    if m.contribuicoes_ao_desafio >= 20 and frac_ativos > 0.70:
        return "expansao"
    if 0.15 <= m.polarizacao_media <= 0.40:
        return "consenso_fragil"
    return "equilibrio"


@dataclass
class TrajetoriaRastreada:
    estados: list[str]
    steps: list[int]
    metricas_por_step: list[MetricasStep]
    mules_detectados: list[dict]

    def ultimo_estado(self) -> str:
        return self.estados[-1] if self.estados else "bootstrap"

    def distribuicao_historica(self) -> dict[str, float]:
        """Fração de steps em cada estado."""
        if not self.estados:
            return {}
        from collections import Counter
        c = Counter(self.estados)
        total = len(self.estados)
        return {e: c[e] / total for e in ESTADOS_CANONICOS if e in c}


class RastreadorPsicohistoria:
    """
    Mantém buffer thread-compatible de estados rastreados por step.
    Integra com engine.psicohistoria para detectar Mules em tempo real.
    """

    def __init__(self, max_historico: int = 1000):
        self.trajetoria = TrajetoriaRastreada([], [], [], [])
        self.max_historico = max_historico

    def registrar_step(self, metricas: MetricasStep) -> str:
        estado = classificar_estado(metricas)
        self.trajetoria.estados.append(estado)
        self.trajetoria.steps.append(metricas.step)
        self.trajetoria.metricas_por_step.append(metricas)

        # Podar histórico FIFO
        if len(self.trajetoria.estados) > self.max_historico:
            corte = len(self.trajetoria.estados) - self.max_historico
            self.trajetoria.estados = self.trajetoria.estados[corte:]
            self.trajetoria.steps = self.trajetoria.steps[corte:]
            self.trajetoria.metricas_por_step = self.trajetoria.metricas_por_step[corte:]

        return estado

    def detectar_mules_recentes(self, janela: int = 20, z_score: float = 2.5) -> list[dict]:
        """
        Rodar detector_mule sobre últimos `janela` steps. Usa baseline do grafo.
        """
        from engine.psicohistoria.grafo_eventos import construir_grafo_vila
        from engine.psicohistoria.equacoes import prever_trajetoria
        from engine.psicohistoria.detectores import detectar_mule

        if len(self.trajetoria.estados) < 2:
            return []
        recentes = self.trajetoria.estados[-janela:]
        if not recentes:
            return []
        g = construir_grafo_vila()
        prev = prever_trajetoria(g, recentes[0], len(recentes) - 1)
        mules = detectar_mule(recentes, prev, g, z_score_limite=z_score)
        registros = [
            {"tipo": m.tipo, "passo_relativo": m.passo,
             "z_score": m.z_score, "descricao": m.descricao}
            for m in mules
        ]
        self.trajetoria.mules_detectados.extend(registros)
        self.trajetoria.mules_detectados = self.trajetoria.mules_detectados[-100:]
        return registros


# Singleton — usado por simulacao.py
RASTREADOR_GLOBAL = RastreadorPsicohistoria()
