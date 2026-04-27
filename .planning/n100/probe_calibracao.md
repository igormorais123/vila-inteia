# Calibração do threshold outcome_probe — Onda 164

Threshold congelado em `outcome_probe.py`: **0.65**

## Dados

- Probes carregados: 100
- Eventos com brier real conhecido: 9
- Eventos rotuláveis (intersecção): 9

## Curva ROC (threshold vs TPR/FPR)

| threshold | TP | FP | FN | TN | TPR | FPR | Youden J | n_alto |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 4 | 5 | 0 | 0 | 1.0 | 1.0 | 0.0 | 9 |
| 0.05 | 4 | 5 | 0 | 0 | 1.0 | 1.0 | 0.0 | 9 |
| 0.1 | 4 | 5 | 0 | 0 | 1.0 | 1.0 | 0.0 | 9 |
| 0.15 | 4 | 5 | 0 | 0 | 1.0 | 1.0 | 0.0 | 9 |
| 0.2 | 4 | 5 | 0 | 0 | 1.0 | 1.0 | 0.0 | 9 |
| 0.25 | 4 | 5 | 0 | 0 | 1.0 | 1.0 | 0.0 | 9 |
| 0.3 | 4 | 5 | 0 | 0 | 1.0 | 1.0 | 0.0 | 9 |
| 0.35 | 4 | 4 | 0 | 1 | 1.0 | 0.8 | 0.2 | 8 |
| 0.4 | 4 | 4 | 0 | 1 | 1.0 | 0.8 | 0.2 | 8 |
| 0.45 | 3 | 3 | 1 | 2 | 0.75 | 0.6 | 0.15 | 6 |
| 0.5 | 3 | 3 | 1 | 2 | 0.75 | 0.6 | 0.15 | 6 |
| 0.55 | 3 | 3 | 1 | 2 | 0.75 | 0.6 | 0.15 | 6 |
| 0.6 | 3 | 3 | 1 | 2 | 0.75 | 0.6 | 0.15 | 6 |
| 0.65 | 2 | 2 | 2 | 3 | 0.5 | 0.4 | 0.1 | 4 |
| 0.7 | 2 | 2 | 2 | 3 | 0.5 | 0.4 | 0.1 | 4 |
| 0.75 | 2 | 2 | 2 | 3 | 0.5 | 0.4 | 0.1 | 4 |
| 0.8 | 2 | 1 | 2 | 4 | 0.5 | 0.2 | 0.3 | 3 |
| 0.85 | 2 | 1 | 2 | 4 | 0.5 | 0.2 | 0.3 | 3 |
| 0.9 | 2 | 1 | 2 | 4 | 0.5 | 0.2 | 0.3 | 3 |
| 0.95 | 1 | 0 | 3 | 5 | 0.25 | 0.0 | 0.25 | 1 |
| 1.0 | 0 | 0 | 4 | 5 | 0.0 | 0.0 | 0.0 | 0 |

## Threshold ótimo (Youden's J)

- Threshold: **0.8**
- TPR: 0.5, FPR: 0.2, J: 0.3
- **Atenção**: ótimo Youden (0.8) difere do default em 0.15. Considerar ajuste ANTES de iniciar campanha.

## Classificação dos 100 legacy

- Alto leakage (>= 0.65): **49**
- Médio leakage (0.55–0.65): **13**
- Baixo leakage (< 0.55): **38**

### Top 10 mais suspeitos

| id | dataset | p_outcome_mean | leakage |
|---|---|---:|---|
| amer01 | americanas_crise_2023 | 0.990 | alto |
| tw04 | twitter_musk_2022_2024 | 0.990 | alto |
| amer04 | americanas_crise_2023 | 0.980 | alto |
| imp08 | impeachment_dilma_2016 | 0.980 | alto |
| lj07 | lava_jato_2014_2018 | 0.977 | alto |
| btc03 | crypto_bitcoin_2024 | 0.973 | alto |
| pix08 | pix_adoption_2020 | 0.973 | alto |
| lj04 | lava_jato_2014_2018 | 0.957 | alto |
| amer10 | americanas_crise_2023 | 0.953 | alto |
| btc01 | crypto_bitcoin_2024 | 0.943 | alto |

## Decisão metodológica

Threshold mantido em 0.65 (default da Onda 163) salvo veto explícito acima.
Eventos classificados 'alto' ficam fora do holdout. Vão para `reserve` ou são re-curados.
