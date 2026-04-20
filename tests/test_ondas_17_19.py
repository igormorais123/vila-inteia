"""Testes ondas 17 (UI implícito), 18 (auto-calibrador), 19 (MCP tools)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.psicohistoria.auto_calibrador import (
    AutoCalibrador, AUTO_CALIBRADOR_GLOBAL,
)
from engine.mcp_server.tools import TOOLS, executar_tool, lista_tools_disponiveis
from engine.psicohistoria.detector_estado_vila import (
    RASTREADOR_GLOBAL, MetricasStep,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_auto_calibrador_inicial():
    ac = AutoCalibrador(intervalo_steps=10, min_transicoes=5)
    teste("stats iniciais: 0 calibrações", ac.stats()["n_calibracoes"] == 0)


def t_auto_calibrador_sem_intervalo():
    ac = AutoCalibrador(intervalo_steps=50, min_transicoes=3)
    # Step 5 < 50, não calibra
    r = ac.talvez_calibrar(5, ["bootstrap", "recrutamento", "expansao"])
    teste("não calibra antes do intervalo", r is None)


def t_auto_calibrador_calibra():
    ac = AutoCalibrador(intervalo_steps=10, min_transicoes=3)
    traj = ["bootstrap", "recrutamento", "expansao", "consenso_fragil", "equilibrio"]
    r = ac.talvez_calibrar(10, traj)
    teste("calibra após intervalo", r is not None)
    teste("registro tem step", r.step == 10)
    teste("n_transicoes correto", r.n_transicoes == 4)


def t_auto_calibrador_nao_recalibra_seguido():
    ac = AutoCalibrador(intervalo_steps=10)
    traj = ["bootstrap"] * 5 + ["expansao"] * 5
    ac.talvez_calibrar(10, traj)
    # Step 15 < 10 + 10 = 20
    r = ac.talvez_calibrar(15, traj)
    teste("não recalibra se < intervalo", r is None)


def t_auto_calibrador_historico():
    ac = AutoCalibrador(intervalo_steps=10, min_transicoes=3)
    traj = ["bootstrap", "recrutamento", "expansao", "consenso_fragil"]
    ac.talvez_calibrar(10, traj)
    ac.talvez_calibrar(20, traj + ["equilibrio", "equilibrio"])
    h = ac.historico()
    teste("histórico: 2 calibrações", len(h) == 2)


def t_auto_calibrador_matriz_muda():
    ac = AutoCalibrador(intervalo_steps=10, min_transicoes=3)
    M_antes = ac.matriz_atual()
    traj = ["bootstrap", "expansao"] * 10
    ac.talvez_calibrar(10, traj)
    M_depois = ac.matriz_atual()
    import numpy as np
    teste("matriz mudou após calibração",
          np.linalg.norm(M_depois - M_antes) > 0.001)


# ========== Onda 19: MCP tools ==========

def t_mcp_tool_recomendacao_registrada():
    nomes = {t["name"] for t in lista_tools_disponiveis()}
    teste("vila.recomendacao_estrategica registrada",
          "vila.recomendacao_estrategica" in nomes)


def t_mcp_tool_calibrar_registrada():
    nomes = {t["name"] for t in lista_tools_disponiveis()}
    teste("vila.calibrar_online registrada",
          "vila.calibrar_online" in nomes)


def t_mcp_tool_hmm_registrada():
    nomes = {t["name"] for t in lista_tools_disponiveis()}
    teste("vila.hmm_descobrir registrada",
          "vila.hmm_descobrir" in nomes)


def t_mcp_recomendacao_sem_dados():
    # Limpa rastreador
    RASTREADOR_GLOBAL.trajetoria.estados = []
    r = executar_tool("vila.recomendacao_estrategica", {})
    teste("MCP recomendação retorna estrutura", "urgencia" in r)


def t_mcp_calibrar_sem_dados():
    RASTREADOR_GLOBAL.trajetoria.estados = []
    r = executar_tool("vila.calibrar_online", {})
    teste("MCP calibrar sem dados retorna erro",
          r.get("erro") is not None)


def t_mcp_hmm_com_dados():
    RASTREADOR_GLOBAL.trajetoria.estados = []
    for i in range(20):
        m = MetricasStep(step=i, n_conversas=i, n_reflexoes=i % 3,
                         n_agentes_ativos=80 + i % 10, n_agentes_latentes=20 - i % 10,
                         total_agentes=100, polarizacao_media=(i % 5) / 5,
                         gini_economia=0.3, contribuicoes_ao_desafio=i)
        RASTREADOR_GLOBAL.registrar_step(m)
    r = executar_tool("vila.hmm_descobrir", {"k": 4})
    teste("MCP hmm retorna clusters",
          r.get("k") == 4 and len(r.get("clusters", [])) == 4)


def main():
    print("=== test_ondas_17_19 ===")
    for fn in [t_auto_calibrador_inicial, t_auto_calibrador_sem_intervalo,
               t_auto_calibrador_calibra, t_auto_calibrador_nao_recalibra_seguido,
               t_auto_calibrador_historico, t_auto_calibrador_matriz_muda,
               t_mcp_tool_recomendacao_registrada, t_mcp_tool_calibrar_registrada,
               t_mcp_tool_hmm_registrada, t_mcp_recomendacao_sem_dados,
               t_mcp_calibrar_sem_dados, t_mcp_hmm_com_dados]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
