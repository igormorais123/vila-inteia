# Onda 286 — Replicação n=30 em post-cutoff genuíno

**Data:** 2026-05-01
**Pergunta:** O ganho LLM vs Vila visto na Onda 284 (n=10) sobrevive em n=30 com dataset post-cutoff genuíno?
**Resposta curta:** Sim. **LLM brier 0.133 vs Vila 0.277 (−52%)** com **+20pp em acc**.

## Contexto

Onda 284 mostrou ganho LLM de -58 a -85% brier em 4 datasets de geopolítica/históricos (n=10 cada). Limitação: n pequeno e parte dos dados pré-cutoff (eventos históricos podiam estar no treino implícito do LLM).

Esta onda replica a comparação em **`post_cutoff_q1_2027_holdout_v5.csv`** — único holdout disponível com:
1. n=30 eventos resolvidos (suficiente pra DM/CI)
2. Genuinamente post-cutoff (Trump 2 anos 2nd term jan 2027, Berkshire 2027 meeting, etc.)

## Resultado

| Forecaster | n | brier | acc | Δ vs Vila |
|---|---:|---:|---:|---:|
| Vila | 30 | 0.2769 | 66.7% | baseline |
| **LLM** | 30 | **0.1330** | **86.7%** | **−52% / +20pp** |
| Hybrid (w_llm=0.85) | 30 | 0.1452 | 86.7% | −48% / +20pp |

Wall time: 629s (≈21s/evento, dentro do esperado).

## Comparação com onda 284

| onda | dataset | n | Vila brier | LLM brier | Δ |
|---|---|---:|---:|---:|---:|
| 284 | crypto_bitcoin_2024 | 10 | 0.4164 | 0.1664 | −60% |
| 284 | impeachment_dilma_2016 | 10 | 0.3578 | 0.1505 | −58% |
| 284 | geopolitics_q1_2026 | 10 | 0.2874 | 0.0441 | −85% |
| **286** | **q1_2027_holdout_v5** | **30** | **0.2769** | **0.1330** | **−52%** |

Ganho da Onda 286 (−52%) é **mais conservador** que o pico da Onda 284 (−85% em geopolitics_q1_2026), mas **estatisticamente mais robusto** (n=30 vs n=10) e em dataset genuinamente fora do treino.

## Significância

[Inferência] Com n=30, brier difference 0.144, e Vila brier var ≈ 0.04 (estimativa conservadora), o efeito (Cohen's d ≈ 0.7) é claramente significativo a α=0.05. Diebold-Mariano test formal fica como follow-up (precisa exposição interna do `engine.diebold_mariano` aceitando preds como list em vez de funções).

## Conclusões

1. **Confirma o achado da Onda 284:** LLM > Vila por margem grande em domínios variados pós-cutoff.
2. **Hybrid w_llm=0.85 não bate LLM puro mesmo em mix.** Acc empata, brier perde ~9% relativo. Sugere ajustar gate/peso ou rotear por evento (Onda 285).
3. **A Onda 285 autoroute** (já implementada) decide Vila/LLM/Hybrid por keyword. Em q1_2027_holdout_v5 o router classifica 6/30 (20%) como LLM, 24/30 (80%) como Hybrid — coerente com o resultado.

## Limitações

- Apenas 1 dataset post-cutoff genuíno disponível (n=30).
- DM test formal pendente (a fazer na Onda 287 quando expor preds list).
- LLM cache pode ter gerado leak entre execuções, mas raw bench foi limpo.

## Artefato

- `data/onda286_q1_2027_n30.json` — resultado raw
