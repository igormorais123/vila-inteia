"""
Testes de opinion dynamics.
Rodar: python tests/test_opinion_dynamics.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from engine.opinion_dynamics.degroot import degroot_step, degroot_convergencia
from engine.opinion_dynamics.bounded_confidence import deffuant_simular, polarization_index, hk_step
from engine.opinion_dynamics.cascatas import bikhchandani
from engine.opinion_dynamics.bayesiano import atualizar_crenca_bayes
from engine.opinion_dynamics.social_impact import impacto_social


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


def t_degroot_converge_matriz_uniforme():
    # W uniforme: W[i,j] = 1/n. Converge imediato para média.
    n = 5
    W = np.full((n, n), 1 / n)
    x0 = np.array([0.0, 0.2, 0.5, 0.8, 1.0])
    final, it = degroot_convergencia(x0, W)
    media = x0.mean()
    teste(
        "DeGroot W uniforme converge para média",
        abs(final[0] - media) < 1e-6 and it <= 2,
        f"final[0]={final[0]} media={media} it={it}",
    )


def t_degroot_consenso():
    # W estocástica qualquer conectada converge para mesmo valor todos
    W = np.array([
        [0.5, 0.3, 0.2],
        [0.2, 0.5, 0.3],
        [0.3, 0.2, 0.5],
    ])
    x0 = np.array([1.0, 0.0, 0.5])
    final, _ = degroot_convergencia(x0, W, max_iter=5000)
    teste(
        "DeGroot converge para consenso",
        abs(final[0] - final[1]) < 1e-4 and abs(final[1] - final[2]) < 1e-4,
        f"final = {final}",
    )


def t_deffuant_alto_epsilon_consenso():
    # epsilon=0.8, mu=0.5: quase todo par dentro do threshold, converge
    x0 = np.linspace(0, 1, 20)
    final = deffuant_simular(x0, epsilon=0.8, mu=0.5, passos=5000)
    std_final = final.std()
    teste(
        "Deffuant epsilon alto => baixa dispersão",
        std_final < 0.05,
        f"std final = {std_final}",
    )


def t_deffuant_baixo_epsilon_polariza():
    # epsilon=0.1: cluster isolados
    x0 = np.linspace(0, 1, 20)
    final = deffuant_simular(x0, epsilon=0.1, mu=0.5, passos=5000)
    # mantém variância alta
    teste(
        "Deffuant epsilon baixo => polarização mantida",
        final.std() > 0.15,
        f"std final = {final.std()}",
    )


def t_polarization_index_range():
    teste("polarization_index consenso = 0",
          polarization_index(np.array([0.5] * 10)) < 0.01)
    teste("polarization_index extremo ~ 1",
          polarization_index(np.array([0.0] * 5 + [1.0] * 5)) > 0.9,
          f"got {polarization_index(np.array([0.0]*5+[1.0]*5))}")


def t_hk_passo_reduz_variancia():
    x0 = np.array([0.1, 0.2, 0.5, 0.8, 0.9])
    x1 = hk_step(x0, epsilon=0.3)
    teste("HK step reduz variância", x1.std() < x0.std(),
          f"before={x0.std():.3f} after={x1.std():.3f}")


def t_bikhchandani_forma_cascata():
    # 10 sinais mistos: 1,0,1,1,1,0,0,0,1,0 — esperado cascata formar
    sinais = [1, 0, 1, 1, 1, 0, 0, 0, 1, 0]
    r = bikhchandani(sinais, prior=0.5, precisao_sinal=0.7, seed=1)
    teste("Bikhchandani produz decisões", len(r.decisoes) == 10)
    teste("Bikhchandani cascata_formada=bool", isinstance(r.cascata_formada, bool))


def t_bayes_update_coerente():
    # prior=0.5, likelihood_h1=0.8, likelihood_h0=0.2 → posterior=0.8
    post = atualizar_crenca_bayes(0.5, 0.8, 0.2)
    teste("Bayes posterior correto", abs(post - 0.8) < 1e-6, f"got {post}")


def t_impacto_social_quadratico_imediacy():
    i1 = impacto_social(1.0, 1.0, 1)    # 1.0
    i2 = impacto_social(1.0, 0.5, 1)    # 0.25 (metade de imediacy, 1/4 do impacto)
    teste("impacto_social: imediacy quadrático",
          abs(i1 - 1.0) < 1e-9 and abs(i2 - 0.25) < 1e-9,
          f"i1={i1} i2={i2}")


def main():
    print("=== test_opinion_dynamics ===")
    for fn in [
        t_degroot_converge_matriz_uniforme,
        t_degroot_consenso,
        t_deffuant_alto_epsilon_consenso,
        t_deffuant_baixo_epsilon_polariza,
        t_polarization_index_range,
        t_hk_passo_reduz_variancia,
        t_bikhchandani_forma_cascata,
        t_bayes_update_coerente,
        t_impacto_social_quadratico_imediacy,
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
