"""Testes detector estado Vila (Onda 11)."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.psicohistoria.detector_estado_vila import (
    MetricasStep, classificar_estado, RastreadorPsicohistoria,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_bootstrap_step_baixo():
    m = MetricasStep(step=5, n_conversas=0, n_reflexoes=0,
                     n_agentes_ativos=20, n_agentes_latentes=0, total_agentes=100)
    teste("bootstrap: step<20 + ativos<60%",
          classificar_estado(m) == "bootstrap")


def t_recrutamento():
    m = MetricasStep(step=50, n_conversas=2, n_reflexoes=0,
                     n_agentes_ativos=30, n_agentes_latentes=70, total_agentes=100)
    teste("recrutamento: ativos<40%",
          classificar_estado(m) == "recrutamento")


def t_crise_economica():
    m = MetricasStep(step=100, n_conversas=5, n_reflexoes=1,
                     n_agentes_ativos=80, n_agentes_latentes=20, total_agentes=100,
                     gini_economia=0.85)
    teste("crise_economica: Gini>0.75",
          classificar_estado(m) == "crise_economica")


def t_polarizacao():
    m = MetricasStep(step=200, n_conversas=15, n_reflexoes=3,
                     n_agentes_ativos=90, n_agentes_latentes=10, total_agentes=100,
                     polarizacao_media=0.75)
    teste("polarizacao: pol>0.6",
          classificar_estado(m) == "polarizacao")


def t_renovacao_constituinte_prioridade():
    # Mesmo com polarização alta, se há proposta const. ativa, ganha
    m = MetricasStep(step=300, n_conversas=10, n_reflexoes=2,
                     n_agentes_ativos=90, n_agentes_latentes=10, total_agentes=100,
                     polarizacao_media=0.80, propostas_constituintes_ativas=1)
    teste("renovacao_constituinte prioridade",
          classificar_estado(m) == "renovacao_constituinte")


def t_expansao():
    m = MetricasStep(step=80, n_conversas=30, n_reflexoes=5,
                     n_agentes_ativos=80, n_agentes_latentes=20, total_agentes=100,
                     contribuicoes_ao_desafio=50)
    teste("expansao: contribs>=20 + ativos>70%",
          classificar_estado(m) == "expansao")


def t_consenso_fragil():
    m = MetricasStep(step=100, n_conversas=10, n_reflexoes=2,
                     n_agentes_ativos=80, n_agentes_latentes=20, total_agentes=100,
                     polarizacao_media=0.25)
    teste("consenso_fragil: pol em [0.15, 0.40]",
          classificar_estado(m) == "consenso_fragil")


def t_equilibrio():
    m = MetricasStep(step=500, n_conversas=5, n_reflexoes=1,
                     n_agentes_ativos=90, n_agentes_latentes=10, total_agentes=100,
                     polarizacao_media=0.05)
    teste("equilibrio: demais",
          classificar_estado(m) == "equilibrio")


def t_rastreador_registra():
    r = RastreadorPsicohistoria()
    m1 = MetricasStep(step=1, n_conversas=0, n_reflexoes=0,
                      n_agentes_ativos=10, n_agentes_latentes=0, total_agentes=100)
    m2 = MetricasStep(step=50, n_conversas=5, n_reflexoes=1,
                      n_agentes_ativos=30, n_agentes_latentes=70, total_agentes=100)
    r.registrar_step(m1); r.registrar_step(m2)
    teste("rastreador 2 estados registrados",
          len(r.trajetoria.estados) == 2)
    teste("último estado = recrutamento (step>=20 + ativos<40%)",
          r.trajetoria.ultimo_estado() == "recrutamento",
          f"got {r.trajetoria.ultimo_estado()}")


def t_distribuicao_historica():
    r = RastreadorPsicohistoria()
    for i in range(10):
        m = MetricasStep(step=i, n_conversas=5, n_reflexoes=1,
                         n_agentes_ativos=90, n_agentes_latentes=10, total_agentes=100,
                         polarizacao_media=0.05)
        r.registrar_step(m)
    d = r.trajetoria.distribuicao_historica()
    teste("equilibrio domina 10/10",
          d.get("equilibrio", 0) == 1.0, f"got {d}")


def t_detector_mules_real_time():
    r = RastreadorPsicohistoria()
    # trajetória anômala: bootstrap → equilibrio direto
    for step, estado_forcado in enumerate(["bootstrap", "equilibrio", "equilibrio"]):
        m = MetricasStep(step=step, n_conversas=5, n_reflexoes=1,
                         n_agentes_ativos=50 if estado_forcado == "bootstrap" else 95,
                         n_agentes_latentes=0, total_agentes=100)
        # Força estado (bypass classifier) p/ teste determinístico
        r.trajetoria.estados.append(estado_forcado)
        r.trajetoria.steps.append(step)
        r.trajetoria.metricas_por_step.append(m)
    mules = r.detectar_mules_recentes(janela=10, z_score=2.0)
    teste("detecta Mule em transição anômala",
          len(mules) >= 1, f"mules={mules}")


def t_podagem_max_historico():
    r = RastreadorPsicohistoria(max_historico=5)
    for i in range(20):
        m = MetricasStep(step=i, n_conversas=0, n_reflexoes=0,
                         n_agentes_ativos=90, n_agentes_latentes=10, total_agentes=100,
                         polarizacao_media=0.05)
        r.registrar_step(m)
    teste("podagem para max=5",
          len(r.trajetoria.estados) == 5)


def main():
    print("=== test_detector_estado_vila ===")
    for fn in [t_bootstrap_step_baixo, t_recrutamento, t_crise_economica, t_polarizacao,
               t_renovacao_constituinte_prioridade, t_expansao, t_consenso_fragil,
               t_equilibrio, t_rastreador_registra, t_distribuicao_historica,
               t_detector_mules_real_time, t_podagem_max_historico]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
