"""Testes event-sourcing (Onda 31)."""

from __future__ import annotations
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.event_log import (
    EventLog, Evento, ler_eventos, filtrar_por_tipo, resumo_eventos,
    reconstituir_trajetoria,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _tmppath():
    f = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    f.close()
    os.unlink(f.name)
    return f.name


def t_escrever_e_ler():
    p = _tmppath()
    try:
        log = EventLog(p, vila_id="test")
        log.escrever(Evento(tipo="step", step=1, payload={"estado": "bootstrap"}))
        log.escrever(Evento(tipo="step", step=2, payload={"estado": "expansao"}))
        eventos = ler_eventos(p)
        teste("2 eventos persistidos", len(eventos) == 2)
        teste("tipo preservado", eventos[0].tipo == "step")
        teste("payload preservado", eventos[0].payload["estado"] == "bootstrap")
    finally:
        if os.path.exists(p): os.unlink(p)


def t_filtrar_por_tipo():
    p = _tmppath()
    try:
        log = EventLog(p)
        log.escrever(Evento(tipo="step", step=1))
        log.escrever(Evento(tipo="mule", step=2, payload={"z": 3.5}))
        log.escrever(Evento(tipo="step", step=3))
        eventos = ler_eventos(p)
        steps = filtrar_por_tipo(eventos, "step")
        mules = filtrar_por_tipo(eventos, "mule")
        teste("2 eventos step", len(steps) == 2)
        teste("1 evento mule", len(mules) == 1)
    finally:
        if os.path.exists(p): os.unlink(p)


def t_resumo_eventos():
    p = _tmppath()
    try:
        log = EventLog(p)
        for i in range(5):
            log.escrever(Evento(tipo="step", step=i))
        r = resumo_eventos(ler_eventos(p))
        teste("resumo total=5", r["total"] == 5)
        teste("resumo step_max=4", r["step_max"] == 4)
        teste("resumo por_tipo", r["por_tipo"]["step"] == 5)
    finally:
        if os.path.exists(p): os.unlink(p)


def t_reconstituir_trajetoria():
    p = _tmppath()
    try:
        log = EventLog(p)
        log.escrever(Evento(tipo="step", step=1, payload={"estado": "a"}))
        log.escrever(Evento(tipo="mule", step=2))  # sem estado
        log.escrever(Evento(tipo="step", step=3, payload={"estado": "b"}))
        traj = reconstituir_trajetoria(ler_eventos(p))
        teste("trajetória reconstituída 2 estados", traj == ["a", "b"],
              f"got {traj}")
    finally:
        if os.path.exists(p): os.unlink(p)


def t_stats_eventlog():
    p = _tmppath()
    try:
        log = EventLog(p, vila_id="teste")
        log.escrever(Evento(tipo="step", step=1))
        log.escrever(Evento(tipo="step", step=2))
        log.escrever(Evento(tipo="mule", step=3))
        s = log.stats()
        teste("stats.total=3", s["total_eventos"] == 3)
        teste("stats.tamanho>0", s["tamanho_bytes"] > 0)
        teste("stats.contador por tipo",
              s["contador_por_tipo"]["step"] == 2 and
              s["contador_por_tipo"]["mule"] == 1)
    finally:
        if os.path.exists(p): os.unlink(p)


def t_append_only():
    # Duas writes não sobrescrevem
    p = _tmppath()
    try:
        log1 = EventLog(p)
        log1.escrever(Evento(tipo="step", step=1))
        log2 = EventLog(p)  # re-abre mesmo arquivo
        log2.escrever(Evento(tipo="step", step=2))
        teste("append-only: 2 eventos",
              len(ler_eventos(p)) == 2)
    finally:
        if os.path.exists(p): os.unlink(p)


def main():
    print("=== test_event_log ===")
    for fn in [t_escrever_e_ler, t_filtrar_por_tipo, t_resumo_eventos,
               t_reconstituir_trajetoria, t_stats_eventlog, t_append_only]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
