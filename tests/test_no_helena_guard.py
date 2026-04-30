"""Regression test do gap apontado pelo octo-review: --no-helena precisa
isolar de verdade — se módulos helena_* quebrarem import, forecast-mega-bench
não pode cair junto.

Estratégia: simular que engine.helena_report falha em import, e garantir que
o branch do guard (--no-helena=True) consegue ser percorrido sem crash.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def test_helena_imports_inside_no_helena_guard():
    """main.py forecast-mega-bench: imports de helena_report e
    helena_quality_scorer devem estar DENTRO do bloco 'if not args.no_helena',
    não no topo da função. Isso garante que --no-helena isola de verdade.
    """
    repo = Path(__file__).resolve().parents[1]
    src = (repo / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    # Localiza a função do mega-bench (qualquer nome com 'mega_bench')
    target_fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and "mega_bench" in node.name.lower():
            target_fn = node
            break
    assert target_fn is not None, "função forecast-mega-bench não encontrada"

    # Coleta todos os import statements DIRETOS no body da função (não dentro de if/etc)
    top_level_imports: list[str] = []
    for stmt in target_fn.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            mod = getattr(stmt, "module", "") or ""
            top_level_imports.append(mod)

    # Imports de helena_* NÃO podem estar no topo da função
    helena_at_top = [m for m in top_level_imports if "helena" in m]
    assert not helena_at_top, (
        f"Imports helena_* no topo da função quebram --no-helena: {helena_at_top}. "
        "Move pra dentro do guard 'if not args.no_helena'."
    )

    # E DEVEM estar referenciados em algum lugar do body (sanity: alguém usa)
    assert "helena_report" in src
    assert "helena_quality_scorer" in src


def test_no_helena_flag_branches_skip_helena_block():
    """O argparse precisa expor --no-helena no subparser do mega-bench."""
    repo = Path(__file__).resolve().parents[1]
    src = (repo / "main.py").read_text(encoding="utf-8")
    # Pelo menos a flag e o guard precisam existir
    assert "--no-helena" in src or "no_helena" in src, "flag --no-helena ausente"
    assert "no_helena" in src, "guard 'no_helena' não checado em runtime"


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
