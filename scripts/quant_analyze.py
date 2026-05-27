#!/usr/bin/env python3
"""CLI for Vila R-style quantitative analysis."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.quant_analysis import analyze_file, dumps, to_markdown


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="R-style quantitative analysis for tabular data.")
    p.add_argument("path", help="CSV/JSON/Parquet/XLSX path")
    p.add_argument("--target", help="numeric target for lm/anova/t-test")
    p.add_argument("--group", help="group column for t-test/anova")
    p.add_argument("--sep", default=",", help="CSV separator")
    p.add_argument("--format", choices=["json", "md"], default="json")
    p.add_argument("--out", help="optional output file")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = analyze_file(args.path, target=args.target, group=args.group, sep=args.sep)
    text = to_markdown(report) if args.format == "md" else dumps(report)
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Saved -> {out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
