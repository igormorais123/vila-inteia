# Onda 133 — Real Full-Stack Backtest Validation

**Data**: 2026-04-21
**Dataset**: impeachment_dilma_2016 (3 eventos)
**Panel**: Musk + Jobs + Bezos
**Modelo**: meta-llama/llama-4-scout-17b-16e-instruct (Groq)

## Configuração ativa

| Feature | Status | Onda |
|---|---|---|
| Few-shot walk-forward | ✅ (k=1) | 121 |
| CoT structured | ✅ | 123 |
| Bayesian blend | ✅ (peso_vila=0.7) | 125 |
| Platt calibration runtime | ✅ | 97 |
| Weighted ensemble | ❌ (sem pesos) | 122 |
| Debate | ❌ (single round) | 124 |
| Self-consistency | ❌ (custo 3x) | 128/129 |
| Adversarial | ❌ (custo 2x) | 130 |
| Judge filter | ❌ (1 call/persona) | 131 |

## Resultados

| Métrica | Valor | vs Onda 92 v1 (baseline) |
|---|---:|---:|
| accuracy | 66.7% | igual |
| Brier Vila calibrada | **0.204** | −29% (0.28) |
| Brier prior humano | 0.181 | — |
| Skill vs prior | −0.125 | melhor que v1 (-0.72) |
| Média prob Vila | 0.73 | antes 0.88 (over-conf cortada) |

## Per-evento

| evento | real | prior | vila cal | blend | ✓ |
|---|:-:|---:|---:|---:|:-:|
| imp01 Cunha aceita | 1 | 0.55 | **0.73** | 0.67 | ✓ |
| imp02 Manifestações 3M | 1 | 0.70 | **0.76** | 0.73 | ✓ |
| imp03 Lula ministro bloqueado | 0 | 0.50 | **0.69** | 0.71 | ✗ |

## Achados

1. **Platt + CoT cortaram over-confidence drasticamente** (0.88 → 0.73 média).
2. **Brier −29%** mesmo com accuracy igual (2/3) — predições mais calibradas.
3. **imp03 continua sendo failure mode** — Vila falha em eventos de rejeição social mesmo com CoT + few_shot.
4. **Bayesian blend piorou aqui** (Brier 0.20 → 0.23) — com apenas 2 eventos de histórico + Laplace, prior puxa mal.
5. Full stack com SC + adversarial + judge não foi testado — quota protege contra 3x-6x custo.

## Próximos passos

- Testar SC + adversarial quando quota permitir (custo combinado 6-10x)
- Dataset maior (10+ eventos) pra Bayesian blend ter base rate significativa
- Specialized panel per evento (imp03 = constitutional law → Sun Tzu? Montesquieu?)

## Artifacts

- `~/Downloads/vila_bt_acc_fullstack.json` (resultado raw)
