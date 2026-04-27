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
| 0.35 | 4 | 5 | 0 | 0 | 1.0 | 1.0 | 0.0 | 9 |
| 0.4 | 4 | 5 | 0 | 0 | 1.0 | 1.0 | 0.0 | 9 |
| 0.45 | 4 | 4 | 0 | 1 | 1.0 | 0.8 | 0.2 | 8 |
| 0.5 | 4 | 4 | 0 | 1 | 1.0 | 0.8 | 0.2 | 8 |
| 0.55 | 4 | 4 | 0 | 1 | 1.0 | 0.8 | 0.2 | 8 |
| 0.6 | 0 | 0 | 4 | 5 | 0.0 | 0.0 | 0.0 | 0 |
| 0.65 | 0 | 0 | 4 | 5 | 0.0 | 0.0 | 0.0 | 0 |
| 0.7 | 0 | 0 | 4 | 5 | 0.0 | 0.0 | 0.0 | 0 |
| 0.75 | 0 | 0 | 4 | 5 | 0.0 | 0.0 | 0.0 | 0 |
| 0.8 | 0 | 0 | 4 | 5 | 0.0 | 0.0 | 0.0 | 0 |
| 0.85 | 0 | 0 | 4 | 5 | 0.0 | 0.0 | 0.0 | 0 |
| 0.9 | 0 | 0 | 4 | 5 | 0.0 | 0.0 | 0.0 | 0 |
| 0.95 | 0 | 0 | 4 | 5 | 0.0 | 0.0 | 0.0 | 0 |
| 1.0 | 0 | 0 | 4 | 5 | 0.0 | 0.0 | 0.0 | 0 |

## Threshold ótimo (Youden's J)

- Threshold: **0.45**
- TPR: 1.0, FPR: 0.8, J: 0.2
- **Atenção**: ótimo Youden (0.45) difere do default em 0.20. Considerar ajuste ANTES de iniciar campanha.

## Classificação dos 100 legacy

- Alto leakage (>= 0.65): **0**
- Médio leakage (0.55–0.65): **80**
- Baixo leakage (< 0.55): **20**

### Top 10 mais suspeitos

| id | dataset | p_outcome_mean | leakage |
|---|---|---:|---|
| amer01 | americanas_crise_2023 | 0.550 | medio |
| amer02 | americanas_crise_2023 | 0.550 | medio |
| amer03 | americanas_crise_2023 | 0.550 | medio |
| amer04 | americanas_crise_2023 | 0.550 | medio |
| amer05 | americanas_crise_2023 | 0.550 | medio |
| amer08 | americanas_crise_2023 | 0.550 | medio |
| amer09 | americanas_crise_2023 | 0.550 | medio |
| amer10 | americanas_crise_2023 | 0.550 | medio |
| btc01 | crypto_bitcoin_2024 | 0.550 | medio |
| btc02 | crypto_bitcoin_2024 | 0.550 | medio |

## Decisão metodológica

Threshold mantido em 0.65 (default da Onda 163) salvo veto explícito acima.
Eventos classificados 'alto' ficam fora do holdout. Vão para `reserve` ou são re-curados.
