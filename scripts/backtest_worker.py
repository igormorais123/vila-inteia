#!/usr/bin/env python3
"""
Onda 110: backtest worker daemon.

Roda backtest periódico em background, atualiza Platt coefs runtime,
salva histórico. Default: 1x a cada 6h. Env override VILA_WORKER_INTERVAL_S.

Uso:
    python scripts/backtest_worker.py              # rodar 1x e sair
    python scripts/backtest_worker.py --daemon     # loop contínuo
    python scripts/backtest_worker.py --daemon --interval 3600   # 1h

Systemd: veja scripts/systemd/vila-backtest-worker.service
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("vila.worker")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)


_SHOULD_STOP = False


def _handle_sig(signum, _frame):
    global _SHOULD_STOP
    _SHOULD_STOP = True
    logger.info(f"Received signal {signum}, shutting down...")


def _carregar_env():
    env_file = Path.home() / ".vila_env"
    if env_file.exists():
        for linha in env_file.read_text().splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    os.environ.setdefault("GROQ_MODEL_RAPIDO", "llama-3.1-8b-instant")
    os.environ.setdefault(
        "GROQ_MODEL_CHAIN",
        "openai/gpt-oss-120b,meta-llama/llama-4-scout-17b-16e-instruct",
    )


class _SimMinima:
    def __init__(self, persona_ids: list[str]):
        import json as _j
        from engine.persona import Persona
        banco = _j.load(open("data/banco-consultores-lendarios.json"))
        self.personas = {}
        for p in banco:
            if p["id"] in persona_ids:
                self.personas[p["id"]] = Persona(p)


def rodar_um_ciclo(
    personas: list[str],
    max_eventos: int = 3,
    sleep_eventos: float = 6.0,
) -> dict:
    from engine.backtest_real import rodar_backtest_todos
    from engine.calibracao_platt import avaliar_calibracao
    from engine.calibracao_runtime import salvar_coefs
    from engine.backtest_history import salvar as salvar_hist

    logger.info(f"backtest worker: personas={personas} max={max_eventos}")
    sim = _SimMinima(personas)
    if not sim.personas:
        logger.error("nenhuma persona válida carregada")
        return {"erro": "personas inválidas"}

    saida = rodar_backtest_todos(
        base_dir="data/backtest", sim=sim, persona_ids=personas,
        max_eventos_por_ds=max_eventos,
        sleep_entre_eventos_s=sleep_eventos,
        sleep_entre_datasets_s=sleep_eventos * 2,
    )

    # Platt refit se >= 5 amostras
    probs, ys = [], []
    for ds in saida.get("datasets", []):
        for e in ds.get("eventos", []):
            if e.get("prob_vila") is not None:
                probs.append(e["prob_vila"])
                ys.append(e["outcome_real"])

    if len(probs) >= 5:
        try:
            cal = avaliar_calibracao(probs, ys)
            salvar_coefs(cal["platt_a"], cal["platt_b"], cal["n"],
                          fonte=f"worker_{int(time.time())}")
            logger.info(f"Platt atualizado: a={cal['platt_a']:.3f} b={cal['platt_b']:.3f} "
                         f"ECE {cal['ece_antes']:.3f}→{cal['ece_depois']:.3f}")
            saida["calibracao_platt"] = {k: v for k, v in cal.items() if k != "probs_calibradas"}
        except Exception as e:
            logger.error(f"Platt fit falhou: {e}")

    # Persist history
    try:
        saida["persistencia"] = salvar_hist(saida)
    except Exception as e:
        logger.error(f"salvar history falhou: {e}")

    ag = saida.get("agregado", {})
    logger.info(
        f"ciclo completo: acc={ag.get('accuracy_global', 0)*100:.1f}% "
        f"skill={ag.get('skill_brier_vs_prior_macro')}"
    )
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--daemon", action="store_true", help="loop contínuo")
    ap.add_argument("--interval", type=int,
                     default=int(os.getenv("VILA_WORKER_INTERVAL_S", "21600")),
                     help="segundos entre ciclos (default 6h)")
    ap.add_argument("--max", type=int, default=3, help="max eventos por dataset")
    ap.add_argument("--personas", default="CL001,CL002,CL007")
    ap.add_argument("--sleep-eventos", type=float, default=6.0)
    args = ap.parse_args()

    _carregar_env()
    signal.signal(signal.SIGTERM, _handle_sig)
    signal.signal(signal.SIGINT, _handle_sig)

    personas = [p.strip() for p in args.personas.split(",") if p.strip()]

    ciclo = 0
    while True:
        ciclo += 1
        logger.info(f"=== ciclo {ciclo} ===")
        try:
            rodar_um_ciclo(personas, args.max, args.sleep_eventos)
        except Exception as e:
            logger.error(f"ciclo {ciclo} falhou: {e}")
            import traceback
            logger.error(traceback.format_exc())

        if not args.daemon:
            break

        # Sleep w/ signal awareness
        logger.info(f"sleeping {args.interval}s até próximo ciclo")
        elapsed = 0
        while elapsed < args.interval and not _SHOULD_STOP:
            time.sleep(min(10, args.interval - elapsed))
            elapsed += 10
        if _SHOULD_STOP:
            logger.info("daemon stopped cleanly")
            break


if __name__ == "__main__":
    main()
