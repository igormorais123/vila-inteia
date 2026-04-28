# Vila INTEIA — Autoresearch 11 Strategies Real Benchmark (Onda 248)

**N**: 197 events Q1 2026 · **Source**: Yahoo Finance live · **Cache**: 1789 entries

## Ranking by Brier (lower = better)

| Rank | Strategy | Acc | Brier | vs Baseline | Origem |
|---|---|---|---|---|---|
| 1 | **bayesian** | 64.0% | **0.2410** | **-3.6%** | Jaynes 2003 |
| 2 | **momentum** | 65.5% | 0.2417 | -3.3% | Jegadeesh 1993 |
| 3 | vol_adj_momentum | 60.4% | 0.2451 | -2.0% | Moskowitz 2012 |
| 4 | hurst_regime | 64.0% | 0.2455 | -1.8% | Mandelbrot 1971 |
| 5 | kelly_calibrated | 65.5% | 0.2491 | -0.4% | Kelly 1956 |
| 6 | ichimoku | 57.4% | 0.2496 | -0.2% | Hosoda 1969 |
| 7 | **baseline** | 57.4% | **0.2500** | — | — |
| 8 | mean_reversion | 53.8% | 0.2540 | +1.6% | DeBondt 1985 |
| 9 | rsi | 56.3% | 0.2552 | +2.1% | Wilder 1978 |
| 10 | bollinger | 54.3% | 0.2553 | +2.1% | Bollinger 1980s |
| 11 | stochastic | 56.9% | 0.2566 | +2.6% | Lane 1950s |

## Key Findings

1. **Bayesian multi-signal wins brier**: 0.2410 (Cox/Jaynes likelihood ratios)
2. **Momentum + Kelly tie best accuracy**: 65.5% (+8.1pp baseline)
3. **5 strategies beat baseline**: bayesian, momentum, vol_adj, hurst, kelly
4. **6 strategies WORSE than baseline**: oscillators (rsi, bollinger, stochastic) + mean_rev fail Q1 2026

## Insights

- Q1 2026 era trending market → momentum-family wins
- Mean reversion fails (no reversion quando tudo tende up)
- Bayesian combinação supera each component individual
- Markets eficientes ⇒ alpha máximo limitado a ~8pp acc

## Strategies academic
- **Beat baseline**: Bayesian (Jaynes), Momentum (Jegadeesh), Moskowitz vol-adj, Mandelbrot Hurst, Kelly
- **Tie baseline**: Ichimoku
- **Underperform**: Mean-rev (DeBondt), RSI (Wilder), Bollinger, Stochastic (Lane)

🤖 Onda 248 — autoresearch sobre 11 strategies, sem memorization
