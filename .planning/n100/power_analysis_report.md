# Power Analysis — Vila INTEIA Holdout (Onda 167)

Iter bootstrap: 5000, réplicas por célula: 20

## Tabela: largura média do IC 95% por (N, brier_esperado)

| N \ Brier | 0.10 | 0.13 | 0.18 | 0.22 |
|---|---:|---:|---:|---:|
| **20** | 0.055 | 0.063 | 0.068 | 0.075 |
| **30** | 0.046 | 0.052 | 0.058 | 0.060 |
| **40** | 0.040 | 0.046 | 0.050 | 0.054 |
| **50** | 0.037 | 0.041 | 0.045 | 0.049 |
| **75** | 0.030 | 0.034 | 0.037 | 0.038 |
| **100** | 0.026 | 0.029 | 0.033 | 0.034 |

## Recomendação Helena P2.6

Critério: IC95% superior <= 0.14 com brier_pontual esperado ~0.15.
Largura tolerável: ~0.06-0.08 (para que pontual+meia-largura < 0.14).

- N=20, brier≈0.13: largura média 0.063 ✓ ATINGE
- N=30, brier≈0.13: largura média 0.052 ✓ ATINGE
- N=40, brier≈0.13: largura média 0.046 ✓ ATINGE
- N=50, brier≈0.13: largura média 0.041 ✓ ATINGE
- N=75, brier≈0.13: largura média 0.034 ✓ ATINGE
- N=100, brier≈0.13: largura média 0.029 ✓ ATINGE
