"""Onda 162: importa os 9 eventos legacy validados (3 datasets × 3 eventos)
do backtest_real_ondas_134_153_3ds.json para data/n100/legacy_v1.jsonl.

Os 100 eventos das pastas data/backtest/*.csv ficam fora — só os 9 que
efetivamente entraram no backtest validado contam como legacy_sanity.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.eventos_v1 import EventoPreditivoV1, FonteEvento, to_jsonl


REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "backtest_real_ondas_134_153_3ds.json"
OUT = REPO / "data" / "n100" / "legacy_v1.jsonl"


def _categoria_de(dataset: str) -> str:
    d = dataset.lower()
    if "impeachment" in d or "lava_jato" in d or "eleicao" in d:
        return "politica"
    if "crypto" in d or "bitcoin" in d or "americanas" in d:
        return "financeiro"
    if "tiktok" in d or "twitter" in d or "musk" in d:
        return "redes_sociais"
    if "apple" in d or "vpro" in d:
        return "produto_tech"
    if "pix" in d:
        return "adocao_tech"
    return "outro"


def main() -> int:
    raw = json.loads(SRC.read_text(encoding="utf-8"))
    eventos: list[EventoPreditivoV1] = []
    for ds in raw["datasets"]:
        # caminho normalizado: pega só o stem
        dataset = Path(ds["dataset"]).stem
        cat = _categoria_de(dataset)
        for e in ds["eventos"]:
            data_corte = date.fromisoformat(e["data"])
            data_res = data_corte + timedelta(days=30)  # placeholder seguro
            ev = EventoPreditivoV1(
                id=e["evento_id"],
                dataset=dataset,
                split="legacy_sanity",
                categoria=cat,
                pergunta=e["contexto"],
                outcome_framing=e["contexto"],
                contexto_pre_corte=e["contexto"],
                regra_resolucao="herdado_legacy_2026_04",
                outcome_binario=int(e["outcome_real"]),
                prob_oraculo_humano_se_houver=float(e["prob_prior"]),
                tipo_oraculo_humano="analyst_consensus",
                data_corte_informacao=data_corte,
                data_resolucao=data_res,
                leakage_risk="alto",
                leakage_mitigations=["legacy_pre_2024_assumido_alto_leakage"],
                audit_status="aprovado_helena",  # já validado em backtest anterior
            )
            eventos.append(ev)
    n = to_jsonl(eventos, OUT)
    print(f"Exportados {n} eventos legacy para {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
