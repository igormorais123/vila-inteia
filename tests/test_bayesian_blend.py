"""Testes Onda 125: Bayesian blend com base rate."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.bayesian_blend import (
    base_rate_dataset, bayesian_blend, blend_vetor, peso_adaptativo,
    bayesian_blend_ensemble, _logit, _sigmoid,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_base_rate_vazio():
    teste("vazio → 0.5", base_rate_dataset([]) == 0.5)


def t_base_rate_laplace():
    # 1 sucesso / 2 tentativas com Laplace 1 = (1+1)/(2+2) = 0.5
    teste("1/2 Laplace1 = 0.5", base_rate_dataset([1, 0]) == 0.5)
    # 10 de 10, com Laplace 1 = 11/12 ≈ 0.917
    teste("10/10 Laplace1 ≈ 0.917", abs(base_rate_dataset([1]*10) - 11/12) < 1e-6)


def t_logit_sigmoid_roundtrip():
    for p in [0.1, 0.3, 0.5, 0.7, 0.9]:
        z = _logit(p)
        back = _sigmoid(z)
        teste(f"roundtrip {p}", abs(back - p) < 1e-9)


def t_blend_peso_vila_1_preserva():
    teste("peso=1 preserva Vila",
          abs(bayesian_blend(0.8, 0.3, peso_vila=1.0) - 0.8) < 1e-6)


def t_blend_peso_vila_0_usa_prior():
    teste("peso=0 usa só prior",
          abs(bayesian_blend(0.8, 0.3, peso_vila=0.0) - 0.3) < 1e-6)


def t_blend_0_7_puxa_pra_prior_quando_discorda():
    # Vila 0.9, prior 0.1, peso 0.7 → blend < 0.9
    b = bayesian_blend(0.9, 0.1, peso_vila=0.7)
    teste(f"vila 0.9 prior 0.1 w=0.7 → {b:.3f} (puxa pra 0.1)", b < 0.9)


def t_blend_vetor_walk_forward():
    # y = [1,1,1,1] → base rate sobe ao longo
    probs = [0.5, 0.5, 0.5, 0.5]
    y = [1, 1, 1, 1]
    out = blend_vetor(probs, y, peso_vila=0.5)
    # Primeiro usa base_rate vazio = 0.5 → blend = 0.5
    teste("primeiro: base_rate vazio", abs(out[0] - 0.5) < 0.01)
    # Último: base_rate com [1,1,1] = 4/5 = 0.8 → blend > 0.5
    teste(f"último: puxa pra cima (got {out[-1]:.3f})", out[-1] > 0.5)


def t_peso_adaptativo_vila_confiante():
    # Vila 0.9 = certeza alta → peso deve subir
    w_conf = peso_adaptativo(0.9)
    w_incerto = peso_adaptativo(0.5)
    teste("vila confiante: peso maior", w_conf > w_incerto)


def t_peso_adaptativo_skill_ruim():
    # Skill -0.3 → peso baixo
    w = peso_adaptativo(0.8, skill_historico=-0.3)
    teste(f"skill ruim: peso < 0.7 (got {w:.3f})", w < 0.7)


def t_peso_adaptativo_range():
    for p in [0.01, 0.5, 0.99]:
        w = peso_adaptativo(p)
        teste(f"peso range 0.4-0.9 p={p} (got {w:.3f})", 0.4 <= w <= 0.9)


def t_peso_adaptativo_dispersao_alta_penaliza():
    # Onda 137: dispersão >0.3 reduz peso em 0.20
    w_sem = peso_adaptativo(0.8)
    w_com = peso_adaptativo(0.8, dispersao=0.35)
    teste(f"disp 0.35 penaliza (sem={w_sem:.3f} com={w_com:.3f})",
          w_com < w_sem - 0.15)


def t_peso_adaptativo_dispersao_baixa_sem_efeito():
    w_sem = peso_adaptativo(0.8)
    w_com = peso_adaptativo(0.8, dispersao=0.08)
    teste("disp 0.08 sem efeito", abs(w_sem - w_com) < 1e-6)


def t_blend_ensemble_median():
    # Com pesos [0.6, 0.7, 0.8], mediana deve estar entre min/max do blend
    p = bayesian_blend_ensemble(0.9, 0.3, pesos=(0.6, 0.7, 0.8))
    minimo = min(bayesian_blend(0.9, 0.3, w) for w in (0.6, 0.7, 0.8))
    maximo = max(bayesian_blend(0.9, 0.3, w) for w in (0.6, 0.7, 0.8))
    teste(f"ensemble median em range [{minimo:.3f}, {maximo:.3f}]",
          minimo <= p <= maximo)


def t_blend_ensemble_peso_unico_equiv_blend():
    # pesos=[0.7] deve igualar bayesian_blend com 0.7
    p_ens = bayesian_blend_ensemble(0.8, 0.3, pesos=(0.7,))
    p_b = bayesian_blend(0.8, 0.3, peso_vila=0.7)
    teste("peso único = bayesian_blend", abs(p_ens - p_b) < 1e-9)


def t_peso_adaptativo_dispersao_nao_viola_range():
    # Mesmo com dispersão máxima + skill ruim, peso >= 0.4
    w = peso_adaptativo(0.5, skill_historico=-0.3, dispersao=0.5)
    teste(f"floor 0.4 mantido (got {w:.3f})", w >= 0.4)


def main():
    print("=== test_bayesian_blend ===")
    for fn in [t_base_rate_vazio, t_base_rate_laplace,
               t_logit_sigmoid_roundtrip, t_blend_peso_vila_1_preserva,
               t_blend_peso_vila_0_usa_prior,
               t_blend_0_7_puxa_pra_prior_quando_discorda,
               t_blend_vetor_walk_forward,
               t_peso_adaptativo_vila_confiante,
               t_peso_adaptativo_skill_ruim,
               t_peso_adaptativo_range,
               t_peso_adaptativo_dispersao_alta_penaliza,
               t_peso_adaptativo_dispersao_baixa_sem_efeito,
               t_peso_adaptativo_dispersao_nao_viola_range,
               t_blend_ensemble_median,
               t_blend_ensemble_peso_unico_equiv_blend]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
