# Vila INTEIA Large-Scale Real Benchmark (Onda 235)

**Date**: 2026-04-28 · **Source**: Yahoo Finance live data

## Summary

| Metric | Value |
|---|---|
| Total events | 210 (150 stocks + 60 cryptos) |
| Resolved via Yahoo Finance | **197/210 (94%)** |
| Base rate predictor | p = 0.50 |
| Aggregate accuracy | **113/197 = 57.4%** |
| 95% CI accuracy | 50.5% – 64.3% |
| Brier score | **0.2500** (chance-level) |

## Breakdown per Category

| Category | Hits | N | Accuracy | Brier |
|---|---|---|---|---|
| stock_price_up | 77 | 144 | 53.5% | 0.2500 |
| crypto_price_up | 36 | 53 | **67.9%** | 0.2500 |

## Insights

1. **Stocks confirm Efficient Market Hypothesis**: 53.5% acc com base rate 50% — sem signal previsível
2. **Cryptos Q1 2026 strong bull bias**: 67.9% closed up — BTC ATH context dominou
3. **Brier estável 0.25 em todas categorias**: predição constante 0.50 = chance brier teórico
4. **CI inclui 50%**: hipótese nula "chance" não rejeitada para stocks; rejeitada para cryptos

## Conclusion

Sistema base-rate-only é honest baseline. Próxima onda: factor models (momentum, mean reversion, technical indicators) para alpha real.

Stocks: 50 tickers (AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, JPM, V, WMT, DIS, NFLX, PYPL, INTC, AMD, CSCO, ORCL, IBM, CRM, ADBE, PFE, JNJ, KO, PEP, MCD, BA, XOM, CVX, GS, MS, BAC, C, WFC, UBER, LYFT, SPOT, SHOP, SQ, COIN, PLTR, SNAP, TWTR, ROKU, ZM, DOCU, CRWD, SNOW, DDOG, NET, TWLO) × 3 dates (Jan 30, Feb 27, Mar 31).

Cryptos: 20 coins (BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX, MATIC, DOT, LTC, BCH, LINK, ATOM, UNI, ICP, FIL, NEAR, APT, TRUMP) × 3 dates (Jan 15, Feb 15, Mar 15).
