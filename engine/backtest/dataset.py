"""
Loader de datasets históricos para backtest.

Formato CSV esperado:
    evento_id,data,contexto,outcome_real,probabilidade_prior
    ev01,2024-10-01,"Candidato X campanha 30% tempo TV",1,0.42
    ...

outcome_real ∈ {0, 1} (sim/não)
probabilidade_prior ∈ [0, 1] — estimativa inicial (uniforme = 0.5 se desconhecida)
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EventoHistorico:
    id: str
    data: str
    contexto: str
    outcome_real: int         # 0 ou 1
    prior: float = 0.5


@dataclass
class DatasetBacktest:
    nome: str
    eventos: list[EventoHistorico] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.eventos)


def carregar_dataset(nome: str, base_dir: Path | str = "data/backtest") -> DatasetBacktest:
    """
    Carrega CSV de `data/backtest/<nome>.csv`.
    """
    base = Path(base_dir)
    path = base / f"{nome}.csv"
    if not path.exists():
        raise FileNotFoundError(f"dataset não encontrado: {path}")

    eventos: list[EventoHistorico] = []
    with path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            eventos.append(EventoHistorico(
                id=row["evento_id"].strip(),
                data=row["data"].strip(),
                contexto=row["contexto"].strip(),
                outcome_real=int(row["outcome_real"]),
                prior=float(row.get("probabilidade_prior", 0.5)),
            ))
    return DatasetBacktest(nome=nome, eventos=eventos)
