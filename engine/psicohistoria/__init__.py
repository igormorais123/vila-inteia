"""
engine.psicohistoria — implementação da Psico-História de Asimov via grafos.

Inspirado em Isaac Asimov, Foundation series (1951+). Modela comportamento
coletivo de grandes populações como sistema dinâmico estatístico. Premissas
originais de Asimov:

    1. População grande o bastante para que flutuações individuais cancelem
    2. Agentes não conscientes de estarem sendo modelados (anti-Heisenberg social)
    3. Transições entre estados sociais governadas por probabilidades estáveis

Esta implementação materializa as Equações Psico-Históricas como **grafo de
estados sociais** onde:

    - Nós  = estados macro da Vila (ex: "polarização alta", "consenso emergente",
             "crise econômica", "expansão editorial")
    - Arestas ponderadas = probabilidades de transição Markov entre estados
    - Trajetória do grafo = "Plano" (trajetória prevista)
    - Desvios significativos = "Mule" (ver `detectores.py`)

Módulos:
    grafo_eventos  — Construção e consulta do grafo Markov
    equacoes       — Predição analítica via potências da matriz de transição
    plano          — Plano de longo prazo (Seldon Plan); comparação prevista vs real
    detectores     — Detecção de "Mule" = outliers que quebram a previsão

Uso típico:
    from engine.psicohistoria import (
        construir_grafo_vila, prever_trajetoria, detectar_mule,
        plano_seldon,
    )
    grafo = construir_grafo_vila(traces_recentes)
    traj = prever_trajetoria(grafo, estado_inicial="consenso_fragil", passos=50)
    plano = plano_seldon(grafo, estado_inicial="recrutamento", horizonte=500)
    anomalias = detectar_mule(traj_real, traj_prevista, z_score=3.0)
"""

from engine.psicohistoria.grafo_eventos import (
    GrafoPsicohistoria,
    Estado,
    Transicao,
    construir_grafo_vila,
)
from engine.psicohistoria.equacoes import (
    prever_trajetoria,
    distribuicao_estacionaria,
    tempo_ate_absorver,
)
from engine.psicohistoria.plano import (
    PlanoSeldon,
    plano_seldon,
    divergencia_plano_realidade,
)
from engine.psicohistoria.detectores import (
    detectar_mule,
    criticidade_evento,
    MuleEvento,
)

__all__ = [
    "GrafoPsicohistoria",
    "Estado",
    "Transicao",
    "construir_grafo_vila",
    "prever_trajetoria",
    "distribuicao_estacionaria",
    "tempo_ate_absorver",
    "PlanoSeldon",
    "plano_seldon",
    "divergencia_plano_realidade",
    "detectar_mule",
    "criticidade_evento",
    "MuleEvento",
]
