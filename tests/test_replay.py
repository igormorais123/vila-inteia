"""Testes replay + export trajetória (Onda 20)."""

from __future__ import annotations
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.psicohistoria.replay import (
    exportar_run, carregar_run, comparar_runs, replay_no_rastreador, resumo_run,
    ExportRun,
)
from engine.psicohistoria.detector_estado_vila import RASTREADOR_GLOBAL, MetricasStep

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _tmppath():
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.close()
    os.unlink(f.name)
    return f.name


def _popular_rastreador(n: int, estados: list[str]):
    RASTREADOR_GLOBAL.trajetoria.estados.clear()
    RASTREADOR_GLOBAL.trajetoria.steps.clear()
    RASTREADOR_GLOBAL.trajetoria.metricas_por_step.clear()
    for i in range(n):
        m = MetricasStep(step=i, n_conversas=i, n_reflexoes=i % 3,
                         n_agentes_ativos=80 + i % 10, n_agentes_latentes=20,
                         total_agentes=100, polarizacao_media=0.1)
        # Força estado pra ser determinístico no teste
        RASTREADOR_GLOBAL.trajetoria.estados.append(estados[i % len(estados)])
        RASTREADOR_GLOBAL.trajetoria.steps.append(i)
        RASTREADOR_GLOBAL.trajetoria.metricas_por_step.append(m)


def t_exportar_retorna_bytes():
    _popular_rastreador(5, ["bootstrap", "expansao"])
    p = _tmppath()
    try:
        nbytes = exportar_run(p, vila_id="teste_a")
        teste("export retorna bytes > 0", nbytes > 0)
    finally:
        if os.path.exists(p): os.unlink(p)


def t_carregar_preserva_dados():
    _popular_rastreador(8, ["expansao", "equilibrio"])
    p = _tmppath()
    try:
        exportar_run(p, vila_id="teste_b")
        run = carregar_run(p)
        teste("vila_id preservado", run.vila_id == "teste_b")
        teste("n_steps preservado", run.n_steps == 8)
        teste("estados preservados", len(run.estados) == 8)
    finally:
        if os.path.exists(p): os.unlink(p)


def t_comparar_runs_identicos():
    _popular_rastreador(10, ["expansao"])
    p1, p2 = _tmppath(), _tmppath()
    try:
        exportar_run(p1, vila_id="a")
        exportar_run(p2, vila_id="b")
        r1 = carregar_run(p1)
        r2 = carregar_run(p2)
        c = comparar_runs(r1, r2)
        teste("runs idênticos: KL ≈ 0", abs(c.kl_divergence) < 1e-6)
        teste("runs idênticos: TV ≈ 0", abs(c.total_variation) < 1e-6)
        teste("mesmo final", c.ambos_convergem_mesmo)
    finally:
        for p in (p1, p2):
            if os.path.exists(p): os.unlink(p)


def t_comparar_runs_diferentes():
    _popular_rastreador(10, ["expansao"])
    p1 = _tmppath()
    p2 = _tmppath()
    try:
        exportar_run(p1, vila_id="a")
        r1 = carregar_run(p1)
        _popular_rastreador(10, ["polarizacao"])
        exportar_run(p2, vila_id="b")
        r2 = carregar_run(p2)
        c = comparar_runs(r1, r2)
        teste("runs diferentes: KL > 0", c.kl_divergence > 0)
        teste("runs diferentes: TV ≈ 1", abs(c.total_variation - 1.0) < 0.01,
              f"TV={c.total_variation}")
        teste("finais diferentes", not c.ambos_convergem_mesmo)
    finally:
        for p in (p1, p2):
            if os.path.exists(p): os.unlink(p)


def t_replay_restaura_rastreador():
    _popular_rastreador(6, ["expansao"])
    p = _tmppath()
    try:
        exportar_run(p, vila_id="r1")
        # Muda rastreador
        _popular_rastreador(3, ["polarizacao"])
        # Replay
        run = carregar_run(p)
        n = replay_no_rastreador(run)
        teste("replay retorna n_steps", n == 6)
        teste("rastreador tem 6 estados após replay",
              len(RASTREADOR_GLOBAL.trajetoria.estados) == 6)
        teste("estado após replay = expansao",
              RASTREADOR_GLOBAL.trajetoria.estados[0] == "expansao")
    finally:
        if os.path.exists(p): os.unlink(p)


def t_resumo_run():
    _popular_rastreador(5, ["bootstrap", "expansao"])
    p = _tmppath()
    try:
        exportar_run(p, vila_id="sum_test")
        run = carregar_run(p)
        r = resumo_run(run)
        teste("resumo vila_id", r["vila_id"] == "sum_test")
        teste("resumo n_steps", r["n_steps"] == 5)
        teste("resumo distribuição preenchida",
              len(r["distribuicao"]) >= 1)
        teste("resumo estado_inicial", r["estado_inicial"] == "bootstrap")
    finally:
        if os.path.exists(p): os.unlink(p)


def main():
    print("=== test_replay ===")
    for fn in [t_exportar_retorna_bytes, t_carregar_preserva_dados,
               t_comparar_runs_identicos, t_comparar_runs_diferentes,
               t_replay_restaura_rastreador, t_resumo_run]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
