#!/usr/bin/env python3
"""
Testes do sistema de evolução de genomas de NPCs.

Executa: python teste_colmeia_evolucao.py

Valida:
- Inicialização e getter obter_genoma()
- Ciclo completo de evolução (iniciação → teste → aprovação/rejeição)
- Integração com step()
- Logging e eventos
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.colmeia import MotorColmeia, GenomaNPC


def test_inicializacao():
    """Teste 1: Inicialização básica."""
    m = MotorColmeia()
    assert isinstance(m, MotorColmeia)

    g = m.obter_genoma("inexistente")
    assert isinstance(g, GenomaNPC)
    assert g.temperatura == 0.5

    print("[OK] Teste 1: Inicializacao")


def test_obter_genoma():
    """Teste 2: obter_genoma retorna genoma correto."""
    m = MotorColmeia()
    m.inicializar_npc("Helena", {"tier": "S"})

    # Sem experimento: retorna principal
    g = m.obter_genoma("Helena")
    assert g == m.genomas["Helena"]

    # Com experimento: retorna candidato
    m.experimentos_evolucao["Helena"] = {
        "genoma_candidato": GenomaNPC(temperatura=0.7),
    }
    g = m.obter_genoma("Helena")
    assert g.temperatura == 0.7

    print("[OK] Teste 2: obter_genoma")


def test_evolucao_aprovada():
    """Teste 3: Ciclo de evolução com aprovação."""
    random.seed(42)
    m = MotorColmeia()
    m.inicializar_npc("Themis", {"tier": "S"})

    # Baseline
    for _ in range(10):
        m.historico["Themis"].append(65.0)

    # Iniciar
    eventos = m.evoluir_genomas(100)
    assert any(e["tipo"] == "evolucao_iniciada" for e in eventos)
    assert "Themis" in m.experimentos_evolucao

    genoma_inicial = m.genomas["Themis"].temperatura
    genoma_candidato = m.experimentos_evolucao["Themis"]["genoma_candidato"].temperatura
    assert genoma_inicial != genoma_candidato  # Mutou

    # Teste com melhoria
    for _ in range(5):
        m.historico["Themis"].append(75.0)

    # Finalizar
    eventos = m.evoluir_genomas(105)
    assert any(e["tipo"] == "evolucao_aprovada" for e in eventos)
    assert "Themis" not in m.experimentos_evolucao

    # Verificar aprovação
    genoma_final = m.genomas["Themis"].temperatura
    assert genoma_final == genoma_candidato  # Manteve mutação
    assert m.genomas["Themis"].melhorias == 1

    print("[OK] Teste 3: Evolucao aprovada")


def test_evolucao_rejeitada():
    """Teste 4: Ciclo de evolução com rejeição."""
    random.seed(99)
    m = MotorColmeia()
    m.inicializar_npc("Ares", {"tier": "S"})

    # Baseline bom
    for _ in range(10):
        m.historico["Ares"].append(80.0)

    # Iniciar
    eventos = m.evoluir_genomas(100)
    assert any(e["tipo"] == "evolucao_iniciada" for e in eventos)

    genoma_inicial = m.genomas["Ares"].temperatura

    # Teste com PIORA
    for _ in range(5):
        m.historico["Ares"].append(75.0)

    # Finalizar
    eventos = m.evoluir_genomas(105)
    assert any(e["tipo"] == "evolucao_revertida" for e in eventos)
    assert "Ares" not in m.experimentos_evolucao

    # Verificar rejeição
    genoma_final = m.genomas["Ares"].temperatura
    assert genoma_final == genoma_inicial  # Reverteu
    assert m.genomas["Ares"].melhorias == 0

    print("[OK] Teste 4: Evolucao rejeitada")


def test_integracao_step():
    """Teste 5: Integração com step()."""
    m = MotorColmeia()
    m.inicializar_npc("Helena", {"tier": "S"})

    for _ in range(10):
        m.historico["Helena"].append(70.0)

    # step() deve chamar evoluir_genomas()
    eventos = m.step(1, ["Helena"])

    evo_eventos = [e for e in eventos if "evolucao" in e.get("tipo", "")]
    assert len(evo_eventos) > 0
    assert any(e["tipo"] == "evolucao_iniciada" for e in evo_eventos)

    print("[OK] Teste 5: Integracao step")


def test_multiplos_npcs():
    """Teste 6: Multiplos NPCs evoluindo simultaneamente."""
    m = MotorColmeia()
    npcs = ["Helena", "Themis", "Ares"]

    for nome in npcs:
        m.inicializar_npc(nome, {"tier": "S"})
        for _ in range(10):
            m.historico[nome].append(70.0)

    # Todos devem iniciar experimentos
    eventos = m.evoluir_genomas(100)
    assert len(m.experimentos_evolucao) == 3

    # Simular melhoria
    for nome in npcs:
        for _ in range(5):
            m.historico[nome].append(75.0)

    # Finalizar
    eventos = m.evoluir_genomas(105)
    aprovados = [e for e in eventos if e["tipo"] == "evolucao_aprovada"]
    rejetados = [e for e in eventos if e["tipo"] == "evolucao_revertida"]

    assert len(aprovados) + len(rejetados) == 3
    assert len(m.experimentos_evolucao) == 0

    print("[OK] Teste 6: Multiplos NPCs")


def test_selecao_criterio():
    """Teste 7: Selecao de criterio varia (nao eh sempre o mesmo)."""
    criterios_testados = set()

    for seed in range(20):
        random.seed(seed)
        m = MotorColmeia()
        m.inicializar_npc("NPC", {"tier": "S"})

        for _ in range(10):
            m.historico["NPC"].append(70.0)

        m.evoluir_genomas(100)

        if "NPC" in m.experimentos_evolucao:
            param = m.experimentos_evolucao["NPC"]["param_mutado"]
            criterios_testados.add(param)

        m.experimentos_evolucao.clear()

    # Deve ter testado multiplos parametros
    assert len(criterios_testados) >= 2, f"So testou: {criterios_testados}"

    print(f"[OK] Teste 7: Selecao criterio (testados: {criterios_testados})")


def test_sem_experimento_sem_historia():
    """Teste 8: NPCs sem historico nao evoluem."""
    m = MotorColmeia()
    m.inicializar_npc("Novo", {"tier": "S"})

    # Sem historico
    eventos = m.evoluir_genomas(100)
    assert len(m.experimentos_evolucao) == 0

    # Com 9 scores (insuficiente)
    for _ in range(9):
        m.historico["Novo"].append(70.0)

    eventos = m.evoluir_genomas(100)
    assert len(m.experimentos_evolucao) == 0

    # Com 10 scores (suficiente)
    m.historico["Novo"].append(70.0)
    eventos = m.evoluir_genomas(100)
    assert len(m.experimentos_evolucao) == 1

    print("[OK] Teste 8: Requisito 10+ scores")


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("TESTES: Sistema de Evolucao de Genomas de NPCs")
    print("="*60 + "\n")

    tests = [
        test_inicializacao,
        test_obter_genoma,
        test_evolucao_aprovada,
        test_evolucao_rejeitada,
        test_integracao_step,
        test_multiplos_npcs,
        test_selecao_criterio,
        test_sem_experimento_sem_historia,
    ]

    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
        except Exception as e:
            print(f"[FAIL] {test.__name__}: Erro inesperado: {e}")

    print(f"\n{'='*60}")
    print(f"Resultado: {passed}/{len(tests)} testes passaram")
    print("="*60 + "\n")

    return passed == len(tests)


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
