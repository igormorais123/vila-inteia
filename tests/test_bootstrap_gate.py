"""Testes Onda 166: bootstrap pareado para gate + skill score IC."""

from __future__ import annotations
import sys, os, random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.bootstrap_gate import (
    avaliar_gate, skill_score, skill_score_ic, _percentile,
)


def test_gate_aceita_quando_brier_iguais():
    """Tune e gate com mesma distribuição: delta ≈ 0, deve aceitar."""
    rng = random.Random(123)
    briers_tune = [rng.gauss(0.15, 0.05) for _ in range(35)]
    briers_gate = [rng.gauss(0.15, 0.05) for _ in range(15)]
    r = avaliar_gate(briers_tune, briers_gate, n_iter=2000, seed=42)
    assert r.aceito, r.razao
    assert abs(r.delta_observado) < 0.05


def test_gate_reprova_quando_gate_muito_pior():
    """Gate com brier 0.30 vs tune 0.10 — degradação clara."""
    briers_tune = [0.10] * 35
    briers_gate = [0.30] * 15
    r = avaliar_gate(briers_tune, briers_gate, n_iter=2000, seed=42)
    assert not r.aceito
    assert "REPROVADO" in r.razao
    assert r.delta_observado > 0.15


def test_gate_aceita_quando_gate_levemente_melhor():
    """Gate igual ou levemente melhor que tune — aceitar."""
    briers_tune = [0.15, 0.16, 0.14, 0.18, 0.13, 0.17, 0.15, 0.14, 0.16, 0.15] * 4
    briers_gate = [0.13, 0.14, 0.15, 0.12, 0.16, 0.13, 0.14, 0.13, 0.15, 0.14] * 2
    # gate_avg ≈ 0.139, tune_avg ≈ 0.153, delta ≈ -0.014
    r = avaliar_gate(briers_tune, briers_gate[:15], n_iter=2000, seed=42)
    assert r.aceito


def test_gate_reprova_briers_vazios():
    r = avaliar_gate([], [0.1], n_iter=100, seed=42)
    assert not r.aceito
    assert "vazios" in r.razao


def test_gate_reproducivel_com_seed():
    briers_tune = [0.12, 0.15, 0.18, 0.10] * 10
    briers_gate = [0.13, 0.14, 0.16, 0.11] * 4
    r1 = avaliar_gate(briers_tune, briers_gate, n_iter=1000, seed=42)
    r2 = avaliar_gate(briers_tune, briers_gate, n_iter=1000, seed=42)
    assert r1.ic_95_inferior == r2.ic_95_inferior
    assert r1.ic_95_superior == r2.ic_95_superior
    assert r1.p_valor_unilateral == r2.p_valor_unilateral


def test_gate_n_iter_default_10k():
    """Helena exigiu 10k iter como default — não sub-amostrar silenciosamente."""
    import inspect
    sig = inspect.signature(avaliar_gate)
    assert sig.parameters['n_iter'].default == 10_000


def test_gate_thresholds_default_helena():
    """delta_max=0.05, p_valor_max=0.10 são os valores Helena."""
    import inspect
    sig = inspect.signature(avaliar_gate)
    assert sig.parameters['delta_max_aceitavel'].default == 0.05
    assert sig.parameters['p_valor_max'].default == 0.10


# ---------- skill_score ----------

def test_skill_score_basico():
    # Modelo brier 0.10, referência brier 0.20: skill = 0.5
    assert abs(skill_score(0.10, 0.20) - 0.5) < 1e-9


def test_skill_score_zero_quando_igual():
    assert skill_score(0.20, 0.20) == 0.0


def test_skill_score_negativo_quando_perde():
    assert skill_score(0.30, 0.20) < 0


def test_skill_score_referencia_zero():
    """Divisão por zero: retorna 0.0 silenciosamente."""
    assert skill_score(0.10, 0.0) == 0.0


# ---------- skill_score_ic ----------

def test_ic_skill_exclui_zero_quando_modelo_melhor():
    """Modelo consistentemente melhor que referência — IC deve excluir zero."""
    rng = random.Random(7)
    briers_modelo = [rng.uniform(0.08, 0.12) for _ in range(50)]
    briers_referencia = [rng.uniform(0.20, 0.25) for _ in range(50)]
    r = skill_score_ic(briers_modelo, briers_referencia, n_iter=2000, seed=42)
    assert r["exclui_zero"]
    assert r["skill_score_pontual"] > 0


def test_ic_skill_inclui_zero_quando_iguais():
    """Brier iguais: IC deve cruzar zero."""
    rng = random.Random(11)
    briers_modelo = [rng.uniform(0.14, 0.16) for _ in range(50)]
    briers_referencia = [rng.uniform(0.14, 0.16) for _ in range(50)]
    r = skill_score_ic(briers_modelo, briers_referencia, n_iter=2000, seed=42)
    assert not r["exclui_zero"]


def test_ic_skill_briers_vazios():
    r = skill_score_ic([], [0.1], n_iter=100)
    assert "erro" in r


# ---------- _percentile ----------

def test_percentile_lista_unica():
    assert _percentile([0.5], 0.5) == 0.5


def test_percentile_mediana():
    assert _percentile([0.0, 0.5, 1.0], 0.5) == 0.5


def test_percentile_extremos():
    xs = [0.1, 0.2, 0.3, 0.4, 0.5]
    assert _percentile(xs, 0.025) <= 0.2
    assert _percentile(xs, 0.975) >= 0.4
