#!/usr/bin/env python3
"""
Dump OpenAPI spec da Vila INTEIA (Onda 53).

Carrega app FastAPI sem subir servidor, extrai schema OpenAPI, escreve JSON.

Uso:
    python scripts/dump_openapi.py [--out docs/openapi.json]
"""

from __future__ import annotations

import argparse
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/openapi.json")
    args = ap.parse_args()

    from fastapi import FastAPI

    app = FastAPI(title="Vila INTEIA", version="1.0.0")

    # Monta todos routers disponíveis
    routers = [
        ("api.rotas_vila", "router"),
        ("api.rotas_rede_social", "router"),
        ("api.rotas_colmeia", "router"),
        ("api.rotas_harness", "router"),
        ("api.rotas_vivos", "router"),
        ("api.rotas_gametheory", "router"),
        ("api.rotas_psicohistoria", "router"),
        ("api.rotas_proveniencia", "router"),
        ("api.rotas_health", "router"),
        ("api.rotas_grafo", "router"),
        ("api.rotas_metrics", "router"),
    ]
    montados = []
    for mod_name, attr in routers:
        try:
            mod = __import__(mod_name, fromlist=[attr])
            app.include_router(getattr(mod, attr))
            montados.append(mod_name)
        except Exception as e:
            print(f"SKIP {mod_name}: {type(e).__name__}: {e}")

    spec = app.openapi()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2, ensure_ascii=False)

    n_paths = len(spec.get("paths", {}))
    size_kb = out.stat().st_size / 1024
    print(f"OpenAPI spec gerado: {out}")
    print(f"  Routers montados: {len(montados)}/{len(routers)}")
    print(f"  Paths: {n_paths}")
    print(f"  Tamanho: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
