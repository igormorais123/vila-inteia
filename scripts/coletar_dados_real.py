#!/usr/bin/env python3
"""
Coletor de dados de simulação real (Onda 68).

Conecta numa Vila live + agrega snapshots em arquivo JSON longitudinal.
Útil para análise post-mortem de experimentos LLM.

Uso:
    python scripts/coletar_dados_real.py --url http://localhost:8900 \\
        --intervalo 5 --duracao 300 --out /tmp/dados_groq.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request


def http_get(url: str, timeout: int = 5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"erro": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8900")
    ap.add_argument("--intervalo", type=int, default=10)
    ap.add_argument("--duracao", type=int, default=300)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    inicio = time.time()
    n_snapshots = 0

    with open(args.out, "w", encoding="utf-8") as fh:
        while time.time() - inicio < args.duracao:
            snap = {
                "ts": time.time(),
                "elapsed_s": time.time() - inicio,
                "trajetoria": http_get(f"{args.url}/api/v1/psicohistoria/trajetoria-atual?janela=10000"),
                "llm": http_get(f"{args.url}/api/v1/llm/stats"),
                "health": http_get(f"{args.url}/api/v1/vila/health"),
            }
            fh.write(json.dumps(snap, ensure_ascii=False) + "\n")
            fh.flush()
            n_snapshots += 1
            traj = snap["trajetoria"]
            llm = snap["llm"]
            print(f"[{snap['elapsed_s']:.0f}s] steps={traj.get('n_steps_rastreados', 0)} "
                  f"estado={traj.get('ultimo_estado','?')} "
                  f"llm_chamadas={llm.get('budget',{}).get('n_chamadas',0)} "
                  f"USD={llm.get('budget',{}).get('total_usd',0):.6f}",
                  flush=True)
            time.sleep(args.intervalo)

    print(f"\nColetado: {n_snapshots} snapshots em {args.out}")


if __name__ == "__main__":
    main()
