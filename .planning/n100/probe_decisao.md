# Decisão Oracle Gnosis sobre threshold do outcome_probe

> Data: 2026-04-27
> Onda: 164R (calibração com dados reais)

## Contexto

Onda 163R rodou outcome_probe contra GPT-5.5 via OmniRoute em 100 eventos legacy.
- 100/100 sucesso (0 falhas).
- Distribuição: 49 alto, 13 médio, 38 baixo (threshold default 0.65).
- Tempo: 24 minutos.

## Análise ROC

Com 9 eventos rotuláveis (intersecção probe ∩ brier real conhecido):

- Youden's J máximo: threshold = 0.80 (TPR 0.5, FPR 0.2, J 0.30)
- Default 0.65: TPR/FPR não computado por baixa amostra
- Diferença vs default: 0.15

## Decisão

**Mantido em 0.65.** Não ajustado para 0.80.

## Justificativa

1. **Poder estatístico baixo**: ROC com N=9 rotuláveis tem variância alta. Qualquer evento sozinho desloca o ótimo. IC bootstrap sobre Youden seria muito largo.

2. **Assimetria de erros**: na campanha N=100, o objetivo do probe é blindar o holdout contra contaminação. Erro tipo II (deixar evento contaminado passar) destrói o claim. Erro tipo I (marcar evento limpo como leakage e jogar em reserve) só reduz n disponível. **Threshold mais baixo (mais conservador) é seguro**.

3. **Coerência com brier legacy**: 49 dos 100 eventos legacy classificados como alto leakage. Os 9 originais têm brier 0.10-0.12. Se ~50% têm memorização forte, o brier baixo do dataset legacy é explicado em parte por memorização — exatamente o sinal que o probe deveria detectar.

4. **Re-calibração ex-post se necessário**: após Ondas 165-180 com eventos novos curados, teremos mais dados rotuláveis (≥ 50 com brier real). Aí a ROC tem poder. Aceitar ajuste posterior é P2, não P1.

## Implicação para a campanha

- Eventos legacy com `p_outcome_mean >= 0.65` ficam excluídos definitivamente do claim. Não vão pra `reserve`, vão pra `legacy_alto_leakage` (split novo, conceitual).
- Eventos novos curados (Ondas 165+) passam pelo mesmo probe antes de receber split. `p_outcome_mean >= 0.65` → vai pra `reserve`, não pra holdout.
- Threshold 0.65 fica congelado até 4 datasets validados completos com brier real (~Onda 175). Reabertura é decisão Oracle, escala pra Helena se ajuste > 0.10.

## Top 10 mais suspeitos (todos com p ≥ 0.94)

| id | dataset | p_outcome_mean |
|---|---|---:|
| amer01 | americanas_crise_2023 | 0.990 |
| tw04 | twitter_musk_2022_2024 | 0.990 |
| amer04 | americanas_crise_2023 | 0.980 |
| imp08 | impeachment_dilma_2016 | 0.980 |
| lj07 | lava_jato_2014_2018 | 0.977 |
| btc03 | crypto_bitcoin_2024 | 0.973 |
| pix08 | pix_adoption_2020 | 0.973 |
| lj04 | lava_jato_2014_2018 | 0.957 |
| amer10 | americanas_crise_2023 | 0.953 |
| btc01 | crypto_bitcoin_2024 | 0.943 |

Esses eventos não voltam para o pipeline. Documentados como referência de memorização forte.

## Achado lateral importante

49% dos eventos legacy memorizados sugere que o brier baseline 0.10-0.12 da Vila é
otimista para eventos OOS. Ajuste de expectativa para a campanha:

- Brier esperado em eventos NOVOS (não memorizados): provavelmente 0.18-0.25.
- Skill score esperado contra prior: 0.05-0.15 se Vila tiver capacidade real.
- Se eventos novos derem brier ~0.10 também, isso é evidência de leakage residual mesmo com probe — investigar antes de claim.

— Oracle Gnosis
*Conclusão: threshold 0.65 segue. Memorização legacy é forte (49%). Expectativa de brier para holdout limpo: 0.18-0.25.*
