"""
Onda 162: schema EventoPreditivoV1 — formato canônico para validação N=100.

Substitui o CSV legado (data/backtest/*.csv) como fonte única de verdade.
CSV continua suportado via from_csv_legado/to_csv_legado (compat layer).

Diferenças vs CSV legado:
  - split explícito (tune | gate | holdout | reserve | legacy_sanity)
  - leakage_risk + outcome_probe operacionalizado
  - audit_status (Helena pode vetar)
  - schema_version (futureproof)

Decisões metodológicas embutidas:
  - prob_oraculo_humano_se_houver pode ser None (≠ 0.5). Evita colapsar
    "sem oráculo" em "oráculo neutro".
  - tipo_oraculo_humano sempre presente, "none" quando ausente.
  - data_corte_informacao < data_resolucao validado.
"""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


SchemaVersion = Literal["v1"]
Split = Literal["tune", "gate", "holdout", "reserve", "legacy_sanity"]
TipoOraculo = Literal[
    "closing_odds", "polling", "prediction_market",
    "analyst_consensus", "none",
]
LeakageRisk = Literal["baixo", "medio", "alto"]
AuditStatus = Literal["pendente", "aprovado_helena", "vetado_helena"]


class FonteEvento(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    titulo: str = ""
    data_acesso: date | None = None
    nivel: Literal["primaria", "secundaria", "terciaria"] = "secundaria"


class EventoPreditivoV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: SchemaVersion = "v1"
    id: str
    dataset: str
    split: Split
    categoria: str

    pergunta: str
    outcome_framing: str
    contexto_pre_corte: str
    regra_resolucao: str = ""
    outcome_binario: Literal[0, 1]

    prob_oraculo_humano_se_houver: float | None = Field(default=None, ge=0.0, le=1.0)
    tipo_oraculo_humano: TipoOraculo = "none"

    data_corte_informacao: date
    data_resolucao: date

    fonte_contexto_pre_corte: list[FonteEvento] = Field(default_factory=list)
    fonte_outcome: list[FonteEvento] = Field(default_factory=list)
    fonte_oraculo_humano: list[FonteEvento] = Field(default_factory=list)

    leakage_risk: LeakageRisk = "medio"
    leakage_mitigations: list[str] = Field(default_factory=list)
    audit_status: AuditStatus = "pendente"

    @field_validator("data_corte_informacao", "data_resolucao", mode="before")
    @classmethod
    def _parse_date(cls, v):
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            return date.fromisoformat(v)
        raise TypeError(f"data inválida: {v!r}")

    @model_validator(mode="after")
    def _check_dates(self):
        if self.data_corte_informacao >= self.data_resolucao:
            raise ValueError(
                f"data_corte_informacao ({self.data_corte_informacao}) deve ser "
                f"estritamente anterior a data_resolucao ({self.data_resolucao})"
            )
        return self

    @model_validator(mode="after")
    def _check_oraculo(self):
        # Coerência tipo ↔ valor
        if self.tipo_oraculo_humano == "none" and self.prob_oraculo_humano_se_houver is not None:
            raise ValueError("tipo_oraculo_humano='none' exige prob_oraculo_humano_se_houver=None")
        if self.tipo_oraculo_humano != "none" and self.prob_oraculo_humano_se_houver is None:
            raise ValueError(
                f"tipo_oraculo_humano='{self.tipo_oraculo_humano}' exige "
                f"prob_oraculo_humano_se_houver definido"
            )
        return self


# ============================================================
# Conversão CSV legado <-> JSONL v1
# ============================================================

def from_csv_legado(
    path: str | Path,
    split: Split = "legacy_sanity",
    categoria_default: str = "legacy",
) -> list[EventoPreditivoV1]:
    """Lê CSV legado (evento_id, data, contexto, outcome_real, probabilidade_prior, outcome_framing).

    Retorna lista de EventoPreditivoV1 com:
      - id = evento_id
      - dataset = nome do arquivo sem .csv
      - split = legacy_sanity (configurável)
      - data_corte_informacao = data
      - data_resolucao = data + 1 dia (placeholder; ajustar caso a caso)
      - prob_oraculo_humano_se_houver = probabilidade_prior
      - tipo_oraculo_humano = "analyst_consensus"
    """
    path = Path(path)
    dataset = path.stem
    eventos: list[EventoPreditivoV1] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data_corte = date.fromisoformat(row["data"])
            # Placeholder: 1 dia depois — caller deve substituir se souber data real
            from datetime import timedelta
            data_res = data_corte + timedelta(days=1)
            prior = row.get("probabilidade_prior", "").strip()
            prob_or = float(prior) if prior else None
            tipo_or = "analyst_consensus" if prob_or is not None else "none"
            ev = EventoPreditivoV1(
                id=row["evento_id"],
                dataset=dataset,
                split=split,
                categoria=categoria_default,
                pergunta=row.get("outcome_framing", "").strip() or row["contexto"],
                outcome_framing=row.get("outcome_framing", "").strip(),
                contexto_pre_corte=row["contexto"],
                regra_resolucao="",
                outcome_binario=int(row["outcome_real"]),
                prob_oraculo_humano_se_houver=prob_or,
                tipo_oraculo_humano=tipo_or,
                data_corte_informacao=data_corte,
                data_resolucao=data_res,
                leakage_risk="alto",  # legacy assumido alto leakage até probe rodar
                leakage_mitigations=["legacy_csv_import"],
                audit_status="pendente",
            )
            eventos.append(ev)
    return eventos


def to_csv_legado(eventos: Iterable[EventoPreditivoV1], path: str | Path) -> int:
    """Exporta eventos para CSV legado. Retorna n eventos escritos."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "evento_id", "data", "contexto",
            "outcome_real", "probabilidade_prior", "outcome_framing",
        ])
        for ev in eventos:
            writer.writerow([
                ev.id,
                ev.data_corte_informacao.isoformat(),
                ev.contexto_pre_corte,
                ev.outcome_binario,
                ev.prob_oraculo_humano_se_houver if ev.prob_oraculo_humano_se_houver is not None else "",
                ev.outcome_framing,
            ])
            n += 1
    return n


# ============================================================
# JSONL I/O
# ============================================================

def to_jsonl(eventos: Iterable[EventoPreditivoV1], path: str | Path) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for ev in eventos:
            f.write(ev.model_dump_json() + "\n")
            n += 1
    return n


def from_jsonl(path: str | Path) -> list[EventoPreditivoV1]:
    path = Path(path)
    out: list[EventoPreditivoV1] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(EventoPreditivoV1.model_validate_json(line))
    return out


def validar_jsonl(path: str | Path) -> dict:
    """Valida JSONL evento-a-evento. Retorna {n_total, n_validos, erros}."""
    path = Path(path)
    n_total = 0
    n_validos = 0
    erros: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            n_total += 1
            try:
                EventoPreditivoV1.model_validate_json(line)
                n_validos += 1
            except Exception as e:
                erros.append({"linha": i, "erro": str(e)[:200]})
    return {"n_total": n_total, "n_validos": n_validos, "erros": erros}
