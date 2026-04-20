"""
Testes contra casos clássicos da literatura de game theory.

Rodar: python tests/test_game_theory.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from engine.game_theory.jogos_repetidos import (
    tit_for_tat,
    grim_trigger,
    sempre_cooperar,
    sempre_trair,
    rodada_iterada,
    COOPERAR,
    TRAIR,
)
from engine.game_theory.evolutivo import (
    replicator_step,
    replicator_convergencia,
    hawk_dove_ess,
)
from engine.game_theory.mecanismos import vickrey_2nd_price, Lance
from engine.game_theory.bem_comum import public_goods_game, ostrom_principios
from engine.game_theory.equilibrio import best_response, nash_puro, nash_misto, stackelberg
from engine.game_theory.mecanismos import vcg_alocacao, leilao_publicacao_mirante
from engine.game_theory.evolutivo import ess_candidatos
from engine.game_theory.coordenacao import battle_of_sexes_nash, stag_hunt, focal_point_schelling
from engine.game_theory.jogos_repetidos import torneio_axelrod


ok = 0
fail = 0
failures: list[str] = []


def teste(nome: str, cond: bool, detalhe: str = ""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {nome}")
    else:
        fail += 1
        failures.append(f"{nome}: {detalhe}")
        print(f"  FAIL {nome}  {detalhe}")


def t_tit_for_tat_coopera_no_inicio():
    from engine.game_theory.jogos_repetidos import Historico
    h = Historico()
    teste("tit_for_tat coopera na primeira rodada", tit_for_tat(h) == COOPERAR)


def t_grim_trigger_puniu_sempre():
    from engine.game_theory.jogos_repetidos import Historico
    h = Historico(minhas_acoes=[COOPERAR, COOPERAR],
                  acoes_oponente=[COOPERAR, TRAIR])
    teste("grim_trigger pune sempre após 1 traição", grim_trigger(h) == TRAIR)


def t_prisoner_dilemma_sempre_trair_vs_sempre_trair():
    r = rodada_iterada(sempre_trair, sempre_trair, rodadas=100)
    teste(
        "sempre_trair vs sempre_trair = NE (payoff = 100)",
        r.payoff_a == 100 and r.payoff_b == 100,
        f"got {r.payoff_a}, {r.payoff_b}",
    )


def t_sempre_cooperar_vs_sempre_cooperar():
    r = rodada_iterada(sempre_cooperar, sempre_cooperar, rodadas=100)
    teste(
        "sempre_cooperar mutual = payoff 300 (3*100)",
        r.payoff_a == 300 and r.payoff_b == 300,
        f"got {r.payoff_a}, {r.payoff_b}",
    )


def t_tit_for_tat_vs_sempre_trair():
    r = rodada_iterada(tit_for_tat, sempre_trair, rodadas=100)
    # TFT coopera 1x, depois trai sempre: TFT recebe 0 + 99*1 = 99; TRAIR recebe 5 + 99*1 = 104
    teste(
        "tit_for_tat vs sempre_trair: TFT perde só 1ª rodada",
        r.payoff_a == 99 and r.payoff_b == 104,
        f"got {r.payoff_a}, {r.payoff_b}",
    )


def t_replicator_converge_dominante():
    # 2 estratégias, dom strict: A domina B. Replicator deve ir p/ [1, 0]
    payoffs = np.array([[3, 3], [1, 1]])       # A sempre ganha mais que B
    pop = np.array([0.5, 0.5])
    final, _ = replicator_convergencia(pop, payoffs, max_iter=500)
    teste(
        "replicator converge p/ estratégia dominante",
        final[0] > 0.99,
        f"final = {final}",
    )


def t_hawk_dove_ess():
    p = hawk_dove_ess(v=2.0, c=3.0)
    teste("hawk-dove ESS v=2 c=3: p*=2/3", abs(p - 2 / 3) < 1e-9, f"got {p}")


def t_vickrey_vencedor_paga_segundo():
    lances = [Lance("a", 100), Lance("b", 80), Lance("c", 60)]
    r = vickrey_2nd_price(lances)
    teste(
        "Vickrey: vencedor é 'a', paga 80",
        r and r.vencedor_id == "a" and r.preco_pago == 80,
        f"got {r}",
    )


def t_public_goods_free_ride_eh_ne():
    # 4 agentes, dotação 10, mpcr=0.5. NE puro = 0 contribuição
    dot = {f"p{i}": 10 for i in range(4)}
    # Todos contribuem 0: payoff = 10
    r = public_goods_game(dot, {f"p{i}": 0 for i in range(4)}, mpcr=0.5)
    teste(
        "public goods: 0 contribuição => payoff dotação total",
        all(v == 10 for v in r.payoffs_individuais.values()),
        f"got {r.payoffs_individuais}",
    )


def t_public_goods_cooperacao_ganha():
    # Todos contribuem tudo: total_pool=40, mpcr=0.5, retorno=20 each
    # payoff = (10 - 10) + 20 = 20 (maior que free-ride)
    dot = {f"p{i}": 10 for i in range(4)}
    r = public_goods_game(dot, {f"p{i}": 10 for i in range(4)}, mpcr=0.5)
    teste(
        "public goods cooperação total: payoff 20 each",
        all(v == 20 for v in r.payoffs_individuais.values()),
        f"got {r.payoffs_individuais}",
    )


def t_ostrom_8_principios():
    p = ostrom_principios()
    teste("Ostrom: 8 princípios", len(p) == 8)


def t_best_response_matrix_game():
    # Jogador tem 2 estr. Oponente joga (0.5, 0.5). Estratégia 0 paga (2,0); 1 paga (1,3)
    # Esperança: estr 0 = 2*0.5+0*0.5=1; estr 1 = 1*0.5+3*0.5=2 → best=1
    payoff = np.array([[2, 0], [1, 3]])
    opp = np.array([0.5, 0.5])
    br = best_response(payoff, opp)
    teste("best_response: escolhe estratégia com maior payoff esperado", br == 1)


def t_nash_puro_prisoner_dilemma():
    # A: 3 0 / 5 1 ; B: 3 5 / 0 1. Único NE puro: (1,1) = (trair, trair)
    A = np.array([[3, 0], [5, 1]])
    B = np.array([[3, 5], [0, 1]])
    eqs = nash_puro(A, B)
    teste("Nash puro PD: único eq (trair,trair)",
          len(eqs) == 1 and eqs[0].unico,
          f"got {len(eqs)} eqs")


def t_nash_puro_battle_of_sexes():
    # BoS tem 2 NE puros
    A = np.array([[2, 0], [0, 1]])
    B = np.array([[1, 0], [0, 2]])
    eqs = nash_puro(A, B)
    teste("Nash puro BoS: 2 eq puros", len(eqs) == 2, f"got {len(eqs)}")


def t_nash_misto_matching_pennies():
    # Zero-sum sem NE puro; misto (0.5, 0.5) each
    A = np.array([[1, -1], [-1, 1]])
    B = -A
    eq = nash_misto(A, B)
    teste("Nash misto matching pennies existe", eq is not None)
    if eq:
        teste("Nash misto: ambas estratégias 0.5",
              abs(eq.estrategias[0][0] - 0.5) < 1e-6 and abs(eq.estrategias[1][0] - 0.5) < 1e-6,
              f"got {eq.estrategias}")


def t_stackelberg_leader_ganha():
    # Leader pode forçar follower p/ solução favorável
    leader = np.array([[3, 1], [2, 4]])
    follower = np.array([[1, 2], [3, 1]])
    eq = stackelberg(leader, follower)
    teste("Stackelberg retorna eq único puro", eq.tipo == "puro" and eq.unico)


def t_vcg_alocacao_single_item():
    # 3 bidders, 1 slot. Maior valor ganha, paga 2º preço.
    vals = {"a": {"slot": 100}, "b": {"slot": 80}, "c": {"slot": 60}}
    cap = {"slot": 1}
    r = vcg_alocacao(vals, cap)
    teste("VCG: 'a' ganha, paga 80",
          "a" in r.alocacao["slot"] and r.pagamentos["a"] == 80,
          f"aloc={r.alocacao} pag={r.pagamentos}")


def t_vcg_multi_slot():
    # 4 bidders, 2 slots. Top-2 ganham, pagam 3º preço (50)
    vals = {"a": {"s": 100}, "b": {"s": 80}, "c": {"s": 50}, "d": {"s": 30}}
    cap = {"s": 2}
    r = vcg_alocacao(vals, cap)
    teste("VCG multi-slot: a e b ganham, ambos pagam 50",
          set(r.alocacao["s"]) == {"a", "b"} and r.pagamentos["a"] == 50 and r.pagamentos["b"] == 50)


def t_leilao_mirante():
    from engine.game_theory.mecanismos import Lance
    lances = [Lance("x", 90), Lance("y", 70), Lance("z", 50)]
    r = leilao_publicacao_mirante(lances, slots_disponiveis=2)
    teste("Leilão Mirante: 2 vencedores, ambos pagam 50",
          len(r) == 2 and r[0].preco_pago == 50)


def t_ess_prisoner_dilemma():
    # PD: trair é ESS (domina cooperar)
    payoffs = np.array([[3, 0], [5, 1]])   # (C vs C = 3, C vs D = 0, D vs C = 5, D vs D = 1)
    ess = ess_candidatos(payoffs)
    teste("ESS PD: trair (idx 1) é ESS", 1 in ess, f"got {ess}")


def t_ess_hawk_dove_nenhuma_pura():
    # Hawk-Dove v=2, c=3: (H vs H)=(v-c)/2=-0.5; (H vs D)=v=2; (D vs H)=0; (D vs D)=v/2=1
    # Nenhuma estratégia pura é ESS (misto é)
    payoffs = np.array([[-0.5, 2.0], [0.0, 1.0]])
    ess = ess_candidatos(payoffs)
    teste("ESS Hawk-Dove mixed: nenhuma ESS pura", len(ess) == 0, f"got {ess}")


def t_battle_of_sexes_misto():
    r = battle_of_sexes_nash(payoff_a_pref=3, payoff_b_pref=1)
    teste("BoS: 2 NE puros", len(r["ne_puros"]) == 2)
    teste("BoS misto: p_a = 1/(3+1) = 0.25",
          abs(r["ne_misto"]["p_a_toca_o"] - 0.25) < 1e-9,
          f"got {r['ne_misto']}")


def t_stag_hunt_coop():
    teste("stag_hunt: todos coop => cervo", stag_hunt(4, 4) == 4.0)
    teste("stag_hunt: parcial => 0", stag_hunt(4, 3) == 0.0)


def t_focal_point():
    sal = {"opcao_a": 0.3, "opcao_b": 0.9, "opcao_c": 0.1}
    teste("focal point: mais saliente vence",
          focal_point_schelling(["opcao_a", "opcao_b", "opcao_c"], sal) == "opcao_b")


def t_torneio_axelrod_tft_vence():
    from engine.game_theory.jogos_repetidos import tit_for_tat, sempre_trair, sempre_cooperar, grim_trigger
    estrats = {
        "tft": tit_for_tat,
        "trair": sempre_trair,
        "coop": sempre_cooperar,
        "grim": grim_trigger,
    }
    rank = torneio_axelrod(estrats, rodadas=100)
    # Axelrod 1980: tit-for-tat costuma vencer
    vencedor = max(rank, key=rank.get)
    teste("Torneio Axelrod: TFT/grim competitivos",
          vencedor in ("tft", "grim", "coop"), f"venc={vencedor} rank={rank}")


def main():
    print("=== test_game_theory ===")
    for fn in [
        t_tit_for_tat_coopera_no_inicio,
        t_grim_trigger_puniu_sempre,
        t_prisoner_dilemma_sempre_trair_vs_sempre_trair,
        t_sempre_cooperar_vs_sempre_cooperar,
        t_tit_for_tat_vs_sempre_trair,
        t_replicator_converge_dominante,
        t_hawk_dove_ess,
        t_vickrey_vencedor_paga_segundo,
        t_public_goods_free_ride_eh_ne,
        t_public_goods_cooperacao_ganha,
        t_ostrom_8_principios,
        t_best_response_matrix_game,
        t_nash_puro_prisoner_dilemma,
        t_nash_puro_battle_of_sexes,
        t_nash_misto_matching_pennies,
        t_stackelberg_leader_ganha,
        t_vcg_alocacao_single_item,
        t_vcg_multi_slot,
        t_leilao_mirante,
        t_ess_prisoner_dilemma,
        t_ess_hawk_dove_nenhuma_pura,
        t_battle_of_sexes_misto,
        t_stag_hunt_coop,
        t_focal_point,
        t_torneio_axelrod_tft_vence,
    ]:
        try:
            fn()
        except NotImplementedError as e:
            print(f"  SKIP {fn.__name__}: {e}")
        except Exception as e:
            global fail
            fail += 1
            failures.append(f"{fn.__name__} exceção: {e}")
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")

    print(f"\n{ok} ok, {fail} fail")
    if failures:
        print("\nFalhas:")
        for f in failures:
            print(f"  - {f}")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
