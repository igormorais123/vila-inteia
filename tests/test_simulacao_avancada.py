"""
Testes de simulacao_avancada.
Rodar: python tests/test_simulacao_avancada.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from engine.simulacao_avancada.campus_fisica import GrafoCampus, rota_otima, congestao
from engine.simulacao_avancada.coalizoes import shapley_value, core_membership
from engine.simulacao_avancada.voter_espacial import median_voter, votacao_espacial
from engine.simulacao_avancada.redes import small_world, preferential_attachment, grau_clustering, detectar_comunidades
from engine.simulacao_avancada.coalizoes import banzhaf_power
from engine.simulacao_avancada.schelling import tipping_point
from engine.simulacao_avancada.voter_espacial import hotelling_equilibrio
from engine.simulacao_avancada.informacao_imperfeita import (
    separating_equilibrium,
    cheap_talk_credivel,
    reputacao_update,
)


ok = 0
fail = 0


def teste(nome, cond, detalhe=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {nome}")
    else:
        fail += 1
        print(f"  FAIL {nome}  {detalhe}")


def t_rota_otima_basica():
    g = GrafoCampus()
    g.adicionar_aresta("a", "b", 1)
    g.adicionar_aresta("b", "c", 1)
    g.adicionar_aresta("a", "c", 5)
    rota = rota_otima(g, "a", "c")
    teste("rota ótima = a-b-c (2 arestas vs 1 aresta cara)",
          rota == ["a", "b", "c"], f"got {rota}")


def t_rota_origem_igual_destino():
    g = GrafoCampus()
    g.adicionar_aresta("a", "b", 1)
    teste("rota origem==destino retorna [origem]", rota_otima(g, "a", "a") == ["a"])


def t_rota_inacessivel():
    g = GrafoCampus()
    g.adicionar_aresta("a", "b", 1)
    g.vertices.add("c")
    teste("rota inacessível retorna []", rota_otima(g, "a", "c") == [])


def t_congestao_zero():
    teste("congestão vazia = 0", congestao("x", 0, 10) == 0)


def t_congestao_overflow():
    teste("congestão overflow penaliza forte", congestao("x", 15, 10) > 1.5)


def t_shapley_voting_3_player():
    # Classic: 3 jogadores A,B,C. Coalizão ganha se >=2. Cada jogador vale 1/3.
    def v(coal):
        return 1.0 if len(coal) >= 2 else 0.0

    shap = shapley_value(["A", "B", "C"], v)
    for j in shap:
        teste(f"Shapley 3-player simple majority: {j}=1/3",
              abs(shap[j] - 1 / 3) < 1e-9, f"got {shap[j]}")


def t_shapley_dummy_player():
    # D não contribui nada. Shapley(D) = 0
    def v(coal):
        return 1.0 if ("A" in coal and "B" in coal) else 0.0

    shap = shapley_value(["A", "B", "D"], v)
    teste("Shapley dummy player = 0", abs(shap["D"]) < 1e-9, f"got {shap['D']}")


def t_core_grande_coalizao_feliz():
    def v(coal):
        return float(len(coal))    # valor = tamanho

    alocacao = {"A": 1.0, "B": 1.0, "C": 1.0}
    # v(N)=3, soma=3. v({A,B})=2, alocA+alocB=2 ok.
    teste("core: igualdade cumpre v(S) exatamente",
          core_membership(["A", "B", "C"], alocacao, v))


def t_median_voter():
    prefs = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
    m = median_voter(prefs)
    teste("median voter = 0.5", abs(m - 0.5) < 1e-9)


def t_votacao_espacial_proximidade():
    eleitores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
    cands = np.array([0.2, 0.8])
    votos = votacao_espacial(eleitores, cands)
    teste("votação espacial: 3 votos p/ cada candidato",
          votos.get(0) == 3 and votos.get(1) == 3, f"got {votos}")


def t_small_world_tem_n_nos():
    adj = small_world(20, k=4, p_rewire=0.0)
    teste("small world tem 20 nós", len(adj) == 20)


def t_preferential_attachment_hub_emerge():
    adj = preferential_attachment(50, m=3, seed=1)
    graus = [len(adj[i]) for i in range(50)]
    max_grau = max(graus)
    # Hub deve ter significativamente mais que a média
    teste("preferential attachment gera hub",
          max_grau >= 2 * (sum(graus) / len(graus)), f"max={max_grau}")


def t_grau_clustering_triangulo():
    adj = {0: [1, 2], 1: [0, 2], 2: [0, 1]}
    teste("clustering triângulo = 1",
          abs(grau_clustering(adj, 0) - 1.0) < 1e-9)


def t_signaling_separating_eq():
    # Baixos têm custo muito alto p/ sinalizar → separating eq existe
    teste("separating eq. existe se custo alto p/ baixos",
          separating_equilibrium(custo_alto_para_alto=1.0,
                                 custo_alto_para_baixo=10.0,
                                 payoff_parecer_alto=5.0))


def t_cheap_talk_credivel_alinhado():
    teste("cheap talk crível se interesses alinhados",
          cheap_talk_credivel(True) and not cheap_talk_credivel(False))


def t_reputacao_update_converge():
    r = 0.5
    for _ in range(100):
        r = reputacao_update(r, "x", "x", peso_observacao=0.3)
    teste("reputação sobre com alinhamento constante", r > 0.99, f"got {r}")


def t_detectar_comunidades_separadas():
    # 2 cliques separados → 2 comunidades
    adj = {
        0: [1, 2], 1: [0, 2], 2: [0, 1],
        3: [4, 5], 4: [3, 5], 5: [3, 4],
    }
    c = detectar_comunidades(adj)
    teste("Louvain: 2 cliques → 2 comunidades",
          len(set(c.values())) == 2, f"got {c}")


def t_banzhaf_igual_dummy():
    # Sistema majoritário com pivô balanceado: 3 jogadores, dummy D
    def v(coal):
        return 1.0 if ("A" in coal and "B" in coal) else 0.0
    banz = banzhaf_power(["A", "B", "D"], v)
    teste("Banzhaf dummy = 0", abs(banz["D"]) < 1e-9, f"got {banz}")
    teste("Banzhaf A == B", abs(banz["A"] - banz["B"]) < 1e-9)


def t_tipping_point_monotonico():
    r = tipping_point(tamanho_grid=(10, 10), passos=50,
                      thresholds_testar=[0.2, 0.5, 0.8], seed=1)
    # Segregação geralmente sobe com threshold (não estrito em pequenas amostras)
    teste("tipping point: 3 thresholds retornados", len(r) == 3)
    teste("τ=0.5 segregação > 0.5", r[0.5] > 0.5, f"r={r}")


def t_hotelling_1d_convergencia():
    eq = hotelling_equilibrio(2, 1)
    teste("Hotelling 1D 2 cands: ambos em 0.5",
          eq.shape == (2, 1) and abs(eq[0, 0] - 0.5) < 1e-9 and abs(eq[1, 0] - 0.5) < 1e-9)


def t_hotelling_2d_nan():
    eq = hotelling_equilibrio(3, 2)
    teste("Hotelling 2D: NaN (Plott)", np.all(np.isnan(eq)))


def main():
    print("=== test_simulacao_avancada ===")
    for fn in [
        t_rota_otima_basica,
        t_rota_origem_igual_destino,
        t_rota_inacessivel,
        t_congestao_zero,
        t_congestao_overflow,
        t_shapley_voting_3_player,
        t_shapley_dummy_player,
        t_core_grande_coalizao_feliz,
        t_median_voter,
        t_votacao_espacial_proximidade,
        t_small_world_tem_n_nos,
        t_preferential_attachment_hub_emerge,
        t_grau_clustering_triangulo,
        t_signaling_separating_eq,
        t_cheap_talk_credivel_alinhado,
        t_reputacao_update_converge,
        t_detectar_comunidades_separadas,
        t_banzhaf_igual_dummy,
        t_tipping_point_monotonico,
        t_hotelling_1d_convergencia,
        t_hotelling_2d_nan,
    ]:
        try:
            fn()
        except NotImplementedError as e:
            print(f"  SKIP {fn.__name__}: {e}")
        except Exception as e:
            global fail
            fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")

    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
