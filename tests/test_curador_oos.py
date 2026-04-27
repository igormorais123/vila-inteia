"""Testes Onda 165: curador_oos."""

from __future__ import annotations
import sys, os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.curador_oos import (
    curar_evento, curar_lote, CUTOFF_LLM,
)
from engine.eventos_v1 import EventoPreditivoV1, FonteEvento


def _ev(corte="2024-12-01", res="2024-12-15", outcome=1, fontes_outcome=None):
    if fontes_outcome is None:
        fontes_outcome = [FonteEvento(
            url="https://nba.com/games/123/box",
            titulo="Box score oficial NBA",
            nivel="primaria",
            data_acesso=date(2024, 12, 16),
        )]
    return EventoPreditivoV1(
        id="oos01", dataset="nba_2024_25", split="holdout", categoria="esportes",
        pergunta="Lakers vencem Warriors?",
        outcome_framing="Lakers vencem em casa contra Warriors em 2024-12-15?",
        contexto_pre_corte="Lakers em casa, LeBron disponível, spread -3.5.",
        regra_resolucao="Vitória em tempo regulamentar (sem OT) conta como 1.",
        outcome_binario=outcome,
        prob_oraculo_humano_se_houver=0.62,
        tipo_oraculo_humano="closing_odds",
        data_corte_informacao=corte,
        data_resolucao=res,
        fonte_outcome=fontes_outcome,
        leakage_risk="medio",
    )


def _mock_llm_low_leakage(*args, **kwargs):
    """Probe sempre retorna p baixo → sem leakage."""
    msgs = args[0] if args else kwargs.get("mensagens", [])
    content = msgs[0]["content"] if msgs else ""
    if "Reescreva" in content or "variações" in content:
        return "1. Q1\n2. Q2\n3. Q3"
    return "PROBABILIDADE FINAL: 0.45"


def _mock_llm_high_leakage(*args, **kwargs):
    """Probe retorna p alto → leakage detectado."""
    msgs = args[0] if args else kwargs.get("mensagens", [])
    content = msgs[0]["content"] if msgs else ""
    if "Reescreva" in content or "variações" in content:
        return "1. Q1\n2. Q2\n3. Q3"
    return "PROBABILIDADE FINAL: 0.85"


def test_evento_pos_cutoff_aprovado():
    r = curar_evento(_ev(), rodar_probe=True,
                     probe_kwargs={"chamar_llm": _mock_llm_low_leakage})
    assert r.aprovado, r.razao
    assert r.p_leakage < 0.65
    assert r.evento.audit_status == "aprovado_helena"
    assert r.evento.leakage_risk == "baixo"
    assert "curador_oos_v1" in r.evento.leakage_mitigations[-2]


def test_evento_pre_cutoff_vetado():
    r = curar_evento(_ev(corte="2024-01-15", res="2024-01-20"),
                     rodar_probe=False)
    assert not r.aprovado
    assert "CUTOFF_LLM" in r.razao


def test_evento_sem_fonte_primaria_vetado():
    fontes = [FonteEvento(url="https://blog.com/x", nivel="secundaria",
                          data_acesso=date(2024, 12, 16))]
    r = curar_evento(_ev(fontes_outcome=fontes), rodar_probe=False)
    assert not r.aprovado
    assert "primaria" in r.razao


def test_fonte_primaria_sem_data_acesso_vetada():
    fontes = [FonteEvento(url="https://nba.com/x", nivel="primaria")]
    r = curar_evento(_ev(fontes_outcome=fontes), rodar_probe=False)
    assert not r.aprovado
    assert "data_acesso" in r.razao


def test_fonte_primaria_acessada_antes_da_resolucao_vetada():
    fontes = [FonteEvento(url="https://nba.com/x", nivel="primaria",
                          data_acesso=date(2024, 12, 10))]  # antes do jogo
    r = curar_evento(_ev(fontes_outcome=fontes), rodar_probe=False)
    assert not r.aprovado
    assert "data_acesso" in r.razao


def test_probe_alto_leakage_veta():
    r = curar_evento(_ev(), rodar_probe=True,
                     probe_kwargs={"chamar_llm": _mock_llm_high_leakage})
    assert not r.aprovado
    assert "leakage" in r.razao
    assert r.p_leakage >= 0.65


def test_hash_estavel():
    ev = _ev()
    r1 = curar_evento(ev, rodar_probe=False)
    r2 = curar_evento(ev, rodar_probe=False)
    # Hash não muda entre rodadas (depende só do schema canônico)
    assert r1.hash_sha256 == r2.hash_sha256


def test_lote_estatisticas():
    eventos = [_ev() for _ in range(3)]  # 3 OK
    eventos.append(_ev(corte="2024-01-15", res="2024-01-20"))  # 1 pre-cutoff
    fontes_ruins = [FonteEvento(url="x", nivel="secundaria",
                                data_acesso=date(2024, 12, 16))]
    eventos.append(_ev(fontes_outcome=fontes_ruins))  # 1 fonte ruim
    r = curar_lote(eventos, rodar_probe=True,
                   probe_kwargs={"chamar_llm": _mock_llm_low_leakage})
    assert r["n_total"] == 5
    assert r["n_aprovados"] == 3
    assert r["n_vetados"] == 2
    assert r["taxa_aprovacao"] == 0.6


def test_cutoff_default_2024_08():
    assert CUTOFF_LLM == date(2024, 8, 1)


def test_evento_no_cutoff_exato_aprovado():
    """Evento exatamente no CUTOFF passa (>= cutoff)."""
    r = curar_evento(_ev(corte="2024-08-01", res="2024-08-15"),
                     rodar_probe=False)
    assert r.aprovado
