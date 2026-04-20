"""
Decision helper para agentes vivos (Onda 16).

Consulta posição atual da Vila no Plano de Seldon e recomenda ação.
Usado por Helena (auditoria estratégica) e Efesto (health técnico) para
tomar decisões informadas sobre curso da simulação.
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.psicohistoria.grafo_eventos import construir_grafo_vila
from engine.psicohistoria.plano import plano_seldon
from engine.psicohistoria.equacoes import prever_trajetoria
from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL


@dataclass
class Recomendacao:
    estado_atual: str
    destino_previsto: str
    urgencia: str                    # "baixa" | "média" | "alta" | "crítica"
    acao_recomendada: str
    justificativa: str
    crises_proximas: list[dict]


def recomendar_acao() -> Recomendacao:
    """
    Analisa trajetória atual + Plano Seldon + Mules → retorna recomendação.
    """
    traj = RASTREADOR_GLOBAL.trajetoria
    if not traj.estados:
        return Recomendacao(
            estado_atual="desconhecido",
            destino_previsto="—",
            urgencia="baixa",
            acao_recomendada="aguardar simulação iniciar",
            justificativa="sem dados de trajetória",
            crises_proximas=[],
        )

    atual = traj.ultimo_estado()
    g = construir_grafo_vila()
    p = plano_seldon(g, atual, horizonte=100)
    destino = p.destino_provavel

    # Classificar urgência
    if atual in ("crise_economica", "polarizacao"):
        urgencia = "alta"
        acao = f"intervir: estado '{atual}' é desestabilizador"
    elif len(RASTREADOR_GLOBAL.trajetoria.mules_detectados) > 5:
        urgencia = "crítica"
        acao = "investigar: múltiplos Mules recentes indicam modelo desalinhado"
    elif atual == "renovacao_constituinte":
        urgencia = "média"
        acao = "acompanhar: Vila em processo constitucional, deixar fluir"
    elif atual == destino:
        urgencia = "baixa"
        acao = "manter curso: Vila em estado alinhado com Plano"
    else:
        urgencia = "média"
        acao = f"monitorar: trajetória deve convergir para '{destino}'"

    justificativa = (
        f"Estado atual '{atual}' (observado em {len(traj.estados)} steps). "
        f"Plano Seldon projeta destino '{destino}' em {len(p.estados_modais)} passos. "
        f"{len(p.crises)} crise(s) prevista(s). "
        f"{len(traj.mules_detectados)} Mule(s) detectado(s) historicamente."
    )

    crises_proximas = [
        {"passo": c.passo, "antes": c.estado_antes, "depois": c.estado_depois,
         "probabilidade": c.probabilidade}
        for c in p.crises[:3]
    ]

    return Recomendacao(
        estado_atual=atual,
        destino_previsto=destino,
        urgencia=urgencia,
        acao_recomendada=acao,
        justificativa=justificativa,
        crises_proximas=crises_proximas,
    )


def relatorio_estrategico_helena() -> dict:
    """
    Parecer formatado p/ Helena Strategos (agente vivo).
    Integra com engine.agentes_vivos.helena na Onda 16.2.
    """
    r = recomendar_acao()
    return {
        "tipo": "parecer_psicohistorico",
        "estado": r.estado_atual,
        "destino": r.destino_previsto,
        "urgencia": r.urgencia,
        "recomendacao": r.acao_recomendada,
        "justificativa": r.justificativa,
        "proximas_crises": r.crises_proximas,
    }
