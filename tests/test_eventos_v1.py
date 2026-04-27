"""Testes Onda 162: schema EventoPreditivoV1 + conversão CSV/JSONL."""

from __future__ import annotations
import sys, os, tempfile
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pydantic import ValidationError

from engine.eventos_v1 import (
    EventoPreditivoV1, FonteEvento,
    from_csv_legado, to_csv_legado,
    to_jsonl, from_jsonl, validar_jsonl,
)


def _ev_minimo(**kwargs) -> dict:
    base = dict(
        id="t01",
        dataset="teste",
        split="tune",
        categoria="esportes",
        pergunta="Time A vence?",
        outcome_framing="Time A vence o jogo de domingo?",
        contexto_pre_corte="Time A líder na temporada com 12 vitórias seguidas.",
        regra_resolucao="Vitória em tempo regulamentar conta como 1; OT/empate=0.",
        outcome_binario=1,
        prob_oraculo_humano_se_houver=0.62,
        tipo_oraculo_humano="closing_odds",
        data_corte_informacao="2025-01-10",
        data_resolucao="2025-01-12",
        leakage_risk="baixo",
    )
    base.update(kwargs)
    return base


def test_constroi_evento_minimo():
    ev = EventoPreditivoV1(**_ev_minimo())
    assert ev.schema_version == "v1"
    assert ev.split == "tune"
    assert ev.outcome_binario == 1


def test_data_corte_deve_ser_anterior_a_resolucao():
    with pytest.raises(ValidationError, match="anterior"):
        EventoPreditivoV1(**_ev_minimo(
            data_corte_informacao="2025-01-12",
            data_resolucao="2025-01-12",
        ))


def test_oraculo_none_exige_prob_none():
    with pytest.raises(ValidationError, match="tipo_oraculo_humano='none'"):
        EventoPreditivoV1(**_ev_minimo(
            tipo_oraculo_humano="none",
            prob_oraculo_humano_se_houver=0.5,
        ))


def test_oraculo_definido_exige_prob():
    with pytest.raises(ValidationError, match="exige"):
        EventoPreditivoV1(**_ev_minimo(
            tipo_oraculo_humano="closing_odds",
            prob_oraculo_humano_se_houver=None,
        ))


def test_fonte_evento_validacao():
    f = FonteEvento(url="https://espn.com/x", titulo="Recap", nivel="primaria")
    ev = EventoPreditivoV1(**_ev_minimo(fonte_outcome=[f]))
    assert ev.fonte_outcome[0].nivel == "primaria"


def test_jsonl_roundtrip():
    eventos = [EventoPreditivoV1(**_ev_minimo(id=f"t{i:02d}")) for i in range(5)]
    f = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    f.close()
    p = f.name
    try:
        n = to_jsonl(eventos, p)
        assert n == 5
        carregados = from_jsonl(p)
        assert len(carregados) == 5
        assert carregados[0].id == "t00"
        assert carregados[4].outcome_framing == eventos[4].outcome_framing
    finally:
        if os.path.exists(p): os.unlink(p)


def test_validar_jsonl_detecta_erro():
    f = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8")
    f.write('{"id": "x"}\n')  # incompleto
    f.write(EventoPreditivoV1(**_ev_minimo(id="ok01")).model_dump_json() + "\n")
    f.close()
    try:
        r = validar_jsonl(f.name)
        assert r["n_total"] == 2
        assert r["n_validos"] == 1
        assert len(r["erros"]) == 1
    finally:
        os.unlink(f.name)


def test_csv_legado_import():
    """Lê CSV legado real do repo."""
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "backtest", "impeachment_dilma_2016.csv",
    )
    if not os.path.exists(csv_path):
        pytest.skip(f"{csv_path} não existe")
    eventos = from_csv_legado(csv_path)
    assert len(eventos) == 10
    assert all(e.split == "legacy_sanity" for e in eventos)
    assert all(e.dataset == "impeachment_dilma_2016" for e in eventos)
    assert all(e.leakage_risk == "alto" for e in eventos)  # legacy assumido alto


def test_csv_to_jsonl_roundtrip():
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "backtest", "impeachment_dilma_2016.csv",
    )
    if not os.path.exists(csv_path):
        pytest.skip(f"{csv_path} não existe")
    eventos = from_csv_legado(csv_path)
    f = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    f.close()
    try:
        to_jsonl(eventos, f.name)
        carregados = from_jsonl(f.name)
        assert len(carregados) == 10
        assert carregados[0].id == eventos[0].id
        assert carregados[0].outcome_binario == eventos[0].outcome_binario
    finally:
        if os.path.exists(f.name): os.unlink(f.name)


def test_csv_legado_export_roundtrip():
    """Importa CSV → exporta CSV → importa de novo. Outcomes preservados."""
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "backtest", "impeachment_dilma_2016.csv",
    )
    if not os.path.exists(csv_path):
        pytest.skip(f"{csv_path} não existe")
    eventos = from_csv_legado(csv_path)
    f = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    f.close()
    try:
        n = to_csv_legado(eventos, f.name)
        assert n == 10
        eventos2 = from_csv_legado(f.name)
        assert len(eventos2) == 10
        for a, b in zip(eventos, eventos2):
            assert a.id == b.id
            assert a.outcome_binario == b.outcome_binario
            assert a.contexto_pre_corte == b.contexto_pre_corte
    finally:
        if os.path.exists(f.name): os.unlink(f.name)


def test_split_invalido_rejeitado():
    with pytest.raises(ValidationError):
        EventoPreditivoV1(**_ev_minimo(split="treinamento"))


def test_outcome_invalido_rejeitado():
    with pytest.raises(ValidationError):
        EventoPreditivoV1(**_ev_minimo(outcome_binario=2))
