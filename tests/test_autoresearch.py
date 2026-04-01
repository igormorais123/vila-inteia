"""Testes do Motor de Autoresearch."""

import pytest
from unittest.mock import patch
from engine.autoresearch import MotorAutoresearch, CicloResearch, PesquisaCompleta


@pytest.fixture
def motor():
    return MotorAutoresearch(intervalo_steps=50, max_ciclos=2)


def test_deve_pesquisar(motor):
    assert motor.deve_pesquisar(0) is False  # step 0, ultimo 0
    assert motor.deve_pesquisar(50) is True
    assert motor.deve_pesquisar(49) is False


def test_selecionar_tema_sem_dados(motor):
    assert motor.selecionar_tema() is None


def test_selecionar_tema_com_topicos_ativos(motor):
    tema = motor.selecionar_tema(topicos_ativos=["IA no Brasil", "eleicoes 2026"])
    assert tema == "IA no Brasil"


def test_selecionar_tema_ignora_ja_pesquisados(motor):
    motor.pesquisas.append(PesquisaCompleta(tema_original="IA no Brasil"))
    tema = motor.selecionar_tema(topicos_ativos=["IA no Brasil", "eleicoes 2026"])
    assert tema == "eleicoes 2026"


def test_ciclo_research_to_dict():
    ciclo = CicloResearch(
        ciclo=1, tipo="semente", tema="teste",
        participantes=[{"id": "CL001", "nome": "Teste", "cat": "tech"}],
        respostas=[{"consultor": "Teste", "texto": "resposta"}],
        sintese="sintese teste",
        perguntas_geradas=["Pergunta 1?"],
    )
    d = ciclo.to_dict()
    assert d["ciclo"] == 1
    assert d["tipo"] == "semente"
    assert len(d["respostas"]) == 1


def test_pesquisa_completa_to_dict():
    p = PesquisaCompleta(
        tema_original="tema teste",
        descoberta_principal="Descoberta X",
        recomendacoes=["R1", "R2"],
        topicos_gerados=["T1"],
    )
    d = p.to_dict()
    assert d["tema_original"] == "tema teste"
    assert d["descoberta_principal"] == "Descoberta X"


def test_motor_to_dict(motor):
    d = motor.to_dict()
    assert d["total_pesquisas"] == 0
    assert d["ultimo_research_step"] == 0


def test_selecionar_respondentes(motor):
    """Testa selecao com personas mock."""
    from unittest.mock import MagicMock

    personas = {}
    for i in range(20):
        p = MagicMock()
        p.id = f"CL{i:03d}"
        p.ativo = True
        p.nome_exibicao = f"Consultor {i}"
        p.categoria = "tech"
        p.dados_consultor = {
            "areas_expertise": ["IA", "tecnologia"],
            "tags": ["inovacao"],
            "biografia_resumida": "Especialista em IA",
            "consultor_para": "estrategia",
            "tier": "A",
        }
        personas[p.id] = p

    respondentes = motor._selecionar_respondentes("inteligencia artificial", personas, n=5)
    assert len(respondentes) <= 5
    assert len(respondentes) >= 2  # pelo menos 2 devem ser selecionados


def test_executar_pesquisa_sem_ia(motor):
    """Testa pesquisa com IA mockada retornando None (fallback heuristico)."""
    from unittest.mock import MagicMock

    personas = {}
    for i in range(5):
        p = MagicMock()
        p.id = f"CL{i:03d}"
        p.ativo = True
        p.nome_exibicao = f"Consultor {i}"
        p.categoria = "tech"
        p.dados_consultor = {
            "areas_expertise": ["tecnologia"],
            "tags": [],
            "biografia_resumida": "",
            "consultor_para": "",
            "tier": "B",
            "titulo": "Consultor",
            "personalidade_resumo": "Analitico",
        }
        personas[p.id] = p

    # Mock chamar_llm para retornar None (sem IA)
    with patch("engine.autoresearch.chamar_llm_conversa", return_value=None):
        pesquisa = motor.executar_pesquisa("teste sem IA", personas, step=100)

    # Pesquisa deve completar mesmo sem IA (com ciclos vazios)
    assert pesquisa is not None
    assert pesquisa.tema_original == "teste sem IA"
