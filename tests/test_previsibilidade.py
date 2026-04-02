"""Testes do Motor de Previsibilidade."""

import pytest
from collections import Counter
from engine.previsibilidade import MotorPrevisibilidade, Tendencia


@pytest.fixture
def motor():
    return MotorPrevisibilidade()


def test_registrar_step_basico(motor):
    resumo = {"acoes": [], "conversas": [{"topico": "inteligencia artificial"}]}
    motor.registrar_step(resumo)
    assert len(motor.palavras_por_step) == 1
    assert "inteligencia" in motor.palavras_por_step[0] or "artificial" in motor.palavras_por_step[0]


def test_analisar_sem_dados(motor):
    assert motor.analisar_tendencias() == []


def test_analisar_tendencias_emergente(motor):
    # Simular 30 steps sem o topico
    for _ in range(30):
        motor.palavras_por_step.append(Counter({"economia": 1}))

    # Ultimos 20 steps com topico novo
    for _ in range(20):
        motor.palavras_por_step.append(Counter({"blockchain": 2, "economia": 1}))

    tendencias = motor.analisar_tendencias()
    nomes = [t.topico for t in tendencias]
    assert any("blockchain" in n for n in nomes)


def test_analisar_tendencias_saturando(motor):
    # Topico forte no passado
    for _ in range(30):
        motor.palavras_por_step.append(Counter({"eleicoes": 5}))

    # Desaparece nos ultimos 20
    for _ in range(20):
        motor.palavras_por_step.append(Counter({"tecnologia": 2}))

    tendencias = motor.analisar_tendencias()
    saturando = [t for t in tendencias if t.direcao == "saturando"]
    assert any("eleicoes" in t.topico for t in saturando)


def test_prever_engajamento_sem_dados(motor):
    assert motor.prever_engajamento("novo_topico") == 50.0


def test_prever_engajamento_com_historico(motor):
    motor.engajamento_historico["ia"] = [10, 20, 30, 40, 50]
    resultado = motor.prever_engajamento("ia")
    assert resultado > 20  # ponderado para recente


def test_prever_saturacao(motor):
    # Topico em todos os steps
    for _ in range(20):
        motor.palavras_por_step.append(Counter({"saturado": 3}))
    assert motor.prever_saturacao("saturado") > 0.5


def test_sugerir_proximo_topico(motor):
    motor.tendencias = [
        Tendencia(topico="blockchain", direcao="emergente", forca=0.8, confianca=0.7),
        Tendencia(topico="eleicoes", direcao="saturando", forca=0.6, confianca=0.5),
    ]
    sugestao = motor.sugerir_proximo_topico(["eleicoes"])
    assert sugestao == "blockchain"


def test_gerar_briefing_helena(motor):
    for _ in range(50):
        motor.palavras_por_step.append(Counter({"democracia": 2, "tecnologia": 1}))

    briefing = motor.gerar_briefing_helena()
    assert briefing["tipo"] == "briefing_preditivo"
    assert isinstance(briefing["emergentes"], list)
    assert isinstance(briefing["saturando"], list)


def test_to_dict(motor):
    d = motor.to_dict()
    assert "tendencias" in d
    assert "total_steps_analisados" in d
