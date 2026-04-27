"""Testes Onda 163: outcome_probe runner com mocks (não toca LLM real)."""

from __future__ import annotations
import sys, os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from engine.outcome_probe import (
    extrair_probabilidade, probar_evento, classificar_leakage,
    LEAKAGE_THRESHOLD_DEFAULT,
)
from engine.eventos_v1 import EventoPreditivoV1


def _ev(outcome=1, **kwargs):
    base = dict(
        id="e01", dataset="teste", split="reserve", categoria="esportes",
        pergunta="Time A vence?", outcome_framing="Time A vence?",
        contexto_pre_corte="contexto", regra_resolucao="",
        outcome_binario=outcome,
        prob_oraculo_humano_se_houver=0.5, tipo_oraculo_humano="closing_odds",
        data_corte_informacao="2024-01-01", data_resolucao="2024-01-10",
        leakage_risk="medio",
    )
    base.update(kwargs)
    return EventoPreditivoV1(**base)


# ---------- extrair_probabilidade ----------

def test_extrair_formato_canonico():
    assert extrair_probabilidade("PROBABILIDADE FINAL: 0.72") == pytest.approx(0.72)


def test_extrair_porcentagem():
    assert extrair_probabilidade("PROBABILIDADE FINAL: 80%") == pytest.approx(0.80)


def test_extrair_virgula():
    assert extrair_probabilidade("PROBABILIDADE FINAL: 0,65") == pytest.approx(0.65)


def test_extrair_ultima_ocorrencia():
    """Se há múltiplas, pega a última (raciocínio inicial pode mencionar 0.5)."""
    txt = "Inicialmente 0.40, mas considerando X, ajusto.\nPROBABILIDADE FINAL: 0.78"
    assert extrair_probabilidade(txt) == pytest.approx(0.78)


def test_extrair_falha_silenciosa():
    assert extrair_probabilidade("Não posso responder.") is None
    assert extrair_probabilidade("") is None


def test_extrair_clamp():
    # Decimal malformado >1 e <5 → clamp para 1.0
    assert extrair_probabilidade("PROBABILIDADE FINAL: 1.2") == 1.0
    # Negativo: regex não captura sinal, então pega magnitude — comportamento
    # aceitável para input malformado (resultado em [0,1])
    v = extrair_probabilidade("PROBABILIDADE FINAL: -0.1")
    assert v is None or (0.0 <= v <= 1.0)


# ---------- classificar_leakage ----------

def test_classificar_alto():
    assert classificar_leakage(0.80) == "alto"


def test_classificar_medio():
    assert classificar_leakage(0.60) == "medio"


def test_classificar_baixo():
    assert classificar_leakage(0.40) == "baixo"


# ---------- probar_evento (mock LLM) ----------

class _MockLLM:
    """Mock: 1ª chamada retorna paráfrases, depois retorna probs em ordem."""

    def __init__(self, parafrases_text: str, probs_text: list[str]):
        self._parafrases = parafrases_text
        self._probs = list(probs_text)
        self.calls: list[dict] = []

    def __call__(self, mensagens, modelo="rapido", max_tokens=300,
                 temperatura=0.8, system_prompt="", bypass_step_cap=False):
        self.calls.append({"mensagens": mensagens, "modelo": modelo,
                           "temperatura": temperatura})
        # Heurística: se mensagem pede "Reescreva", é paráfrase
        content = mensagens[0]["content"]
        if "Reescreva" in content or "variações" in content:
            return self._parafrases
        if self._probs:
            return self._probs.pop(0)
        return None


def test_probar_evento_outcome_1_modelo_acerta():
    """Modelo prevê 0.8, outcome real = 1. p_outcome = 0.8 (alto leakage)."""
    mock = _MockLLM(
        parafrases_text="1. Time A vence?\n2. Resultado favorece A?\n3. A é favorito?",
        probs_text=[
            "PROBABILIDADE FINAL: 0.80",
            "PROBABILIDADE FINAL: 0.75",
            "PROBABILIDADE FINAL: 0.85",
        ],
    )
    r = probar_evento(_ev(outcome=1), n_parafrases=3, chamar_llm=mock)
    assert r.n_validas == 3
    assert r.p_outcome_mean == pytest.approx(0.80, abs=0.01)
    assert r.is_leakage()  # 0.80 >= 0.65


def test_probar_evento_outcome_0_inverte():
    """Outcome real = 0. Modelo prevê 0.8 (de outcome=1) → p_outcome = 0.2."""
    mock = _MockLLM(
        parafrases_text="1. Q1\n2. Q2\n3. Q3",
        probs_text=[
            "PROBABILIDADE FINAL: 0.80",
            "PROBABILIDADE FINAL: 0.80",
            "PROBABILIDADE FINAL: 0.80",
        ],
    )
    r = probar_evento(_ev(outcome=0), n_parafrases=3, chamar_llm=mock)
    assert r.p_outcome_mean == pytest.approx(0.20, abs=0.01)
    assert not r.is_leakage()


def test_probar_evento_baixo_leakage():
    mock = _MockLLM(
        parafrases_text="1. A\n2. B\n3. C",
        probs_text=[
            "PROBABILIDADE FINAL: 0.45",
            "PROBABILIDADE FINAL: 0.50",
            "PROBABILIDADE FINAL: 0.40",
        ],
    )
    r = probar_evento(_ev(outcome=1), n_parafrases=3, chamar_llm=mock)
    assert r.p_outcome_mean == pytest.approx(0.45, abs=0.01)
    assert not r.is_leakage()
    assert classificar_leakage(r.p_outcome_mean) == "baixo"


def test_probar_evento_resposta_invalida():
    mock = _MockLLM(
        parafrases_text="1. A\n2. B\n3. C",
        probs_text=["não sei", "indeterminado", "..."],
    )
    r = probar_evento(_ev(), n_parafrases=3, chamar_llm=mock)
    assert r.n_validas == 0
    assert r.erro is not None


def test_probar_evento_parafrase_fallback():
    """Quando modelo dá menos paráfrases que pedido, usa pergunta original."""
    mock = _MockLLM(
        parafrases_text="1. Apenas uma",
        probs_text=[
            "PROBABILIDADE FINAL: 0.5",
            "PROBABILIDADE FINAL: 0.5",
            "PROBABILIDADE FINAL: 0.5",
        ],
    )
    r = probar_evento(_ev(outcome=1), n_parafrases=3, chamar_llm=mock)
    assert r.n_validas == 3


def test_probar_evento_threshold_default_e_065():
    assert LEAKAGE_THRESHOLD_DEFAULT == 0.65
