#!/usr/bin/env python3
"""
Backup + restore da Vila INTEIA (Onda 47).

Dump estado completo em tarball:
    - data/events/*.jsonl (event-sourcing)
    - data/vila_inteia_default/*.json (personas, sinteses, rede_social, desafio)
    - data/colmeia_estado.json
    - data/backtest/*.csv (read-only, incluídos p/ reprodutibilidade)
    - trajetória atual via API export

Uso:
    python scripts/vila_backup.py dump --arquivo vila-backup.tar.gz [--url http://localhost:8100]
    python scripts/vila_backup.py restore --arquivo vila-backup.tar.gz [--apenas events]
    python scripts/vila_backup.py list --arquivo vila-backup.tar.gz
"""

from __future__ import annotations

import argparse
import json
import sys
import tarfile
import time
import urllib.request
import urllib.error
from pathlib import Path


def _http_get(url: str, timeout: int = 30):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"erro": str(e)}


def cmd_dump(args):
    """Cria tarball com state + trajetória live via API."""
    arquivo = Path(args.arquivo)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    incluidos = []

    with tarfile.open(arquivo, "w:gz") as tar:
        # Files em disco
        paths = [
            "data/events",
            "data/vila_inteia_default",
            "data/colmeia_estado.json",
            "data/banco-consultores-lendarios.json",
            "data/backtest",
            "VERSION",
            "CHANGELOG.md",
            "MANIFEST.md",
        ]
        for p in paths:
            path = Path(p)
            if path.exists():
                tar.add(str(path), arcname=str(path))
                incluidos.append(str(path))

        # Trajetória live via API (se servidor rodando)
        if args.url:
            traj = _http_get(f"{args.url}/api/v1/psicohistoria/trajetoria-atual?janela=10000")
            div = _http_get(f"{args.url}/api/v1/psicohistoria/divergencia-atual")
            health = _http_get(f"{args.url}/api/v1/vila/health")
            grafo = _http_get(f"{args.url}/api/v1/grafo/export?limite_nos=1000")
            live_payload = {
                "backup_timestamp": time.time(),
                "source_url": args.url,
                "trajetoria": traj,
                "divergencia": div,
                "health": health,
                "grafo": grafo,
            }
            import io
            data = json.dumps(live_payload, indent=2, ensure_ascii=False).encode("utf-8")
            info = tarfile.TarInfo(name="live_state.json")
            info.size = len(data)
            info.mtime = int(time.time())
            tar.addfile(info, io.BytesIO(data))
            incluidos.append("live_state.json")

    size_mb = arquivo.stat().st_size / (1024 * 1024)
    print(f"Backup criado: {arquivo}")
    print(f"Tamanho: {size_mb:.2f} MB")
    print(f"Incluídos ({len(incluidos)}):")
    for p in incluidos:
        print(f"  - {p}")


def cmd_list(args):
    """Lista conteúdo do tarball."""
    arquivo = Path(args.arquivo)
    if not arquivo.exists():
        print(f"erro: {arquivo} não existe")
        sys.exit(1)
    with tarfile.open(arquivo, "r:gz") as tar:
        total_size = 0
        for m in tar.getmembers():
            total_size += m.size
            kind = "d" if m.isdir() else "-"
            print(f"  {kind} {m.size:>10} {m.name}")
        print(f"\nTotal: {len(tar.getmembers())} entries, {total_size / (1024*1024):.2f} MB descomprimido")


def cmd_restore(args):
    """Extrai tarball no cwd."""
    arquivo = Path(args.arquivo)
    if not arquivo.exists():
        print(f"erro: {arquivo} não existe")
        sys.exit(1)

    with tarfile.open(arquivo, "r:gz") as tar:
        membros = tar.getmembers()
        if args.apenas:
            membros = [m for m in membros if m.name.startswith(args.apenas)]
            print(f"Filtro aplicado: '{args.apenas}' → {len(membros)} entries")
        # Safety: não extrair paths absolutos
        for m in membros:
            if m.name.startswith("/") or ".." in m.name:
                print(f"SKIP path suspeito: {m.name}")
                continue
            tar.extract(m, path=".")
        print(f"Restaurados: {len(membros)} entries")


def main():
    ap = argparse.ArgumentParser(description="Backup/restore Vila INTEIA")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_dump = sub.add_parser("dump", help="Criar backup tarball")
    p_dump.add_argument("--arquivo", required=True)
    p_dump.add_argument("--url", default="",
                         help="URL Vila live (opcional, inclui live_state.json)")

    p_list = sub.add_parser("list", help="Listar conteúdo do tarball")
    p_list.add_argument("--arquivo", required=True)

    p_rest = sub.add_parser("restore", help="Restaurar tarball em cwd")
    p_rest.add_argument("--arquivo", required=True)
    p_rest.add_argument("--apenas", default="",
                         help="Restaurar apenas entries com prefixo (ex: 'data/events')")

    args = ap.parse_args()
    cmd_map = {"dump": cmd_dump, "list": cmd_list, "restore": cmd_restore}
    cmd_map[args.cmd](args)


if __name__ == "__main__":
    main()
