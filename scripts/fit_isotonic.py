"""
Onda 149: CLI fit isotonic calibration.

Input: JSON de backtest (resultado de rodar_backtest_acc) OU CSV
       com colunas prob_raw, outcome_real.
Output: calibracao_platt.json em formato isotonic.

Uso:
    python scripts/fit_isotonic.py --input <backtest.json> [--out <path>]
    python scripts/fit_isotonic.py --input <pairs.csv> [--out <path>]

Default out: data/calibracao_platt.json (overwrite).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def extrair_pares_de_backtest_json(payload: dict) -> list[tuple[float, int]]:
    """Extrai (prob_vila_raw, outcome_real) de backtest_acc ou backtest_real JSON."""
    pares: list[tuple[float, int]] = []
    # Pode ser um dataset individual OU wrapper com datasets:[]
    datasets = payload.get("datasets") or [payload]
    for ds in datasets:
        if "erro" in ds:
            continue
        for ev in ds.get("eventos", []):
            p = ev.get("prob_vila_raw") or ev.get("prob_vila")
            y = ev.get("outcome_real")
            if p is None or y is None:
                continue
            pares.append((float(p), int(y)))
    return pares


def extrair_pares_de_csv(path: str) -> list[tuple[float, int]]:
    pares = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                p = float(row["prob_raw"])
                y = int(row["outcome_real"])
                pares.append((p, y))
            except Exception:
                continue
    return pares


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="data/calibracao_platt.json")
    parser.add_argument("--fonte", default=None)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERRO: input {args.input} não existe")
        sys.exit(1)

    if input_path.suffix == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        pares = extrair_pares_de_backtest_json(payload)
    elif input_path.suffix == ".csv":
        pares = extrair_pares_de_csv(str(input_path))
    else:
        print(f"ERRO: tipo desconhecido {input_path.suffix} (use .json ou .csv)")
        sys.exit(1)

    if len(pares) < 5:
        print(f"ERRO: poucos pares ({len(pares)}); mínimo 5 pra fit isotonic")
        sys.exit(1)

    probs = [p for p, _ in pares]
    ys = [y for _, y in pares]

    from engine.calibracao_stats import isotonic_fit, isotonic_aplicar
    from engine.calibracao_platt import brier
    from engine.calibracao_runtime import salvar_isotonic

    mapping = isotonic_fit(probs, ys)
    if not mapping:
        print("ERRO: isotonic_fit retornou mapping vazio")
        sys.exit(1)

    probs_cal = [isotonic_aplicar(p, mapping) for p in probs]
    brier_antes = brier(probs, ys)
    brier_depois = brier(probs_cal, ys)

    fonte = args.fonte or f"isotonic_fit_{len(pares)}ev_{input_path.stem}"
    salvar_isotonic(mapping, n_amostras=len(pares), fonte=fonte, path=args.out)

    print(f"Input: {args.input}")
    print(f"N pares: {len(pares)}")
    print(f"Mapping size: {len(mapping)}")
    print(f"Brier antes: {brier_antes:.4f}")
    print(f"Brier depois: {brier_depois:.4f}  "
          f"({(brier_depois - brier_antes) / brier_antes * 100:+.1f}%)")
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()
