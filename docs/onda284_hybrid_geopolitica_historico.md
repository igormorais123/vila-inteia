# Onda 284 — Vila vs LLM vs Hybrid em geopolítica + históricos

**Data:** 2026-04-30
**Pergunta:** Onde Vila falha pior, o LLM forecaster (com hybrid prompt) fecha o gap vs Polymarket?
**Resposta curta:** Sim, e dramaticamente. LLM puro equipara Polymarket em geopolítica.

## Contexto

Onda 283 mostrou que Vila bate climatology em -10% no domínio cripto BTC-specific. Esta onda expande o teste para geopolítica e eventos históricos (impeachment, crise corporativa, lançamentos), onde o baseline Vila estava sangrando contra base-rate.

## Diagnóstico baseline (Vila pura, 100 eventos)

| dataset | n | brier | base | acc | delta |
|---|---:|---:|---:|---:|---:|
| geopolitics_q1_2026 | 10 | 0.2874 | 0.2500 | 70.0% | +0.0374 |
| eleicao_presidencial_br_2022 | 10 | 0.1585 | 0.0900 | 70.0% | +0.0685 |
| impeachment_dilma_2016 | 10 | 0.3578 | 0.0900 | 60.0% | +0.2678 |
| lava_jato_2014_2018 | 10 | 0.1562 | 0.0000 | 80.0% | +0.1562 |
| americanas_crise_2023 | 10 | 0.1392 | 0.1600 | 80.0% | -0.0208 |
| crypto_bitcoin_2024 | 10 | 0.4164 | 0.0000 | 10.0% | +0.4164 |
| lancamento_apple_vpro_2024 | 10 | 0.5286 | 0.2100 | 30.0% | +0.3186 |
| tiktok_viral_2024 | 10 | 0.2784 | 0.2100 | 60.0% | +0.0684 |
| twitter_musk_2022_2024 | 10 | 0.1557 | 0.0900 | 70.0% | +0.0657 |
| seed_eleicao_municipal_sp_2024 | 10 | 0.3478 | 0.2500 | 40.0% | +0.0978 |
| **TOTAL** | **100** | **0.2826** | **0.1875** | — | **+0.0951** |

**Vila perde em 9/10 datasets.** Total: brier +0.10 vs base-rate. Pior caso `crypto_bitcoin_2024`: brier 0.42 com **acc 10%** — pior que jogar moeda.

[Inferência] Causa: o classificador post-cutoff regride probabilidades para perto de 0.5. Em datasets com base baixa (eventos raros, 0.0–0.21), isso vira viés sistemático contra a base.

## Hybrid bench (Vila vs LLM vs Hybrid, 4 piores casos, 40 eventos)

LLM forecaster: Claude Opus 4.7 via Claude Code OAuth, com hybrid prompt ancorado na categoria Vila + EB prior.

| dataset | n | Vila brier | LLM brier | Hybrid brier | melhor | Δ(hyb−vila) |
|---|---:|---:|---:|---:|:-:|---:|
| crypto_bitcoin_2024 | 10 | 0.4164 | **0.1664** | 0.1729 | LLM | -0.2435 |
| lancamento_apple_vpro_2024 | 10 | 0.5286 | **0.4460** | 0.4665 | LLM | -0.0620 |
| impeachment_dilma_2016 | 10 | 0.3578 | **0.1505** | 0.2165 | LLM | -0.1414 |
| geopolitics_q1_2026 | 10 | 0.2874 | **0.0441** | 0.0448 | LLM | -0.2426 |

### Acc também explode

| dataset | Vila acc | LLM acc | Hybrid acc |
|---|---:|---:|---:|
| crypto_bitcoin_2024 | 10% | **70%** | 70% |
| impeachment_dilma_2016 | 60% | **80%** | 80% |
| geopolitics_q1_2026 | 70% | **100%** | 100% |
| apple_vpro_2024 | 30% | 30% | 20% |

### Comparação ao top mundial

Polymarket no holdout 140-event do README: **brier 0.047**.
LLM em `geopolitics_q1_2026`: **brier 0.044**.
LLM em `crypto_bitcoin_2024`: **brier 0.166** (cripto é difícil até pra Polymarket).

## Conclusões

1. **Vila pura é deadweight em domínios de cauda baixa.** O classificador estatístico não tem informação latente sobre eventos políticos/regulatórios/corporativos específicos — ele opera no nível da forma da pergunta, não do conhecimento de mundo.

2. **Hybrid w_llm=0.85 fica entre Vila e LLM puro, sempre pior que LLM puro nestes domínios.** A configuração padrão atual do `vila_llm_hybrid` está mal-tunada para este perfil de evento.

3. **Confirma a config "ótima" da Onda 281**: `gate=0.50 + w_llm=1.0` (quase sempre usar LLM, Vila só com confiança extrema p≤0.05 ou p≥0.95).

4. **Recomendação tática:** rotear por domínio. Cripto BTC-specific (Onda 283) → Vila. Geopolítica/histórico/M&A → LLM puro. Hybrid só vale a pena em eventos genéricos (Q-bench, sports, science).

## Limitações

- **n=10 por dataset** (40 total). Variância alta. Replicar com n=30 antes de fechar conclusão.
- **LLM com cache módulo** — chamadas repetidas batem cache, então tempo absoluto não reflete custo de produção.
- **Single-LLM (Claude Opus 4.7)** — não testado contra outros modelos.
- **Não testado em eventos verdadeiramente post-cutoff** (todos os "históricos" estavam no treino implícito do LLM via knowledge cutoff). Geopolitics_q1_2026 é o único genuinamente post-cutoff dos 4 — e foi o melhor (brier 0.044). Sugere que LLM tem skill genuíno, não só recall.

## Próximos passos sugeridos

1. **Onda 285 — autoroute por domínio**: classificador binário Vila-vs-LLM pré-bench, treinado nos features `n_keywords_geopol`, `base_rate_observed`, `framing_length`.
2. **Onda 286 — replicar com n=30**: validar significância nos 4 datasets com Diebold-Mariano.
3. **Onda 287 — multi-LLM ensemble**: Claude Opus + GPT-5.5 + Grok via OmniRoute, log-pool.

## Artefatos

- `scripts/bench_onda284_hybrid_per_domain.py` — bench reproduzível
- `data/onda284_geo_hist_pilot.json` — resultados raw
- Este documento
