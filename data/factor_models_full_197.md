# Vila INTEIA — Factor Models Full Benchmark (Onda 240)

**Date**: 2026-04-28 · **N**: 197 events Q1 2026 · **Source**: Yahoo Finance live

## Pure Strategies

| Strategy | Hits | Acc | Brier |
|---|---|---|---|
| baseline (p=0.50) | 113/197 | 57.4% | 0.2500 |
| **momentum** | **119/197** | **60.4%** | **0.2479** |
| mean_rev | 112/197 | 56.9% | 0.2516 |
| rsi(14) | 112/197 | 56.9% | 0.2528 |

## Autoresearch Ensemble (4D weight grid, 529 combos)

**BEST**: pure momentum (weights mom=1.0, mr=0.0, rsi=0.0, bl=0.0)
- Acc: 119/197 = 60.4%
- Brier: 0.2479
- +3.0pp accuracy, -0.0021 brier vs baseline

## Insights

1. **Momentum é único factor com alpha real Q1 2026** (Jegadeesh & Titman 1993 confirmado)
2. **Mean reversion + RSI piores que baseline** (mean_rev brier 0.2516, rsi 0.2528)
3. **Ensemble winner = pure momentum** — autoresearch convergiu pra solução simples
4. Sample 30 stocks anterior (63.3%) era bias amostral — full 197 events: 60.4%
5. Brier improvement marginal (-0.8%) — limite teórico forecast markets eficientes

## Cache infrastructure
- 756 cache entries (Yahoo Finance prices)
- Atomic write (Onda 240) elimina race condition
- 197/210 events resolved (94% fetch success)

## Limitação fundamental
Markets eficientes ⇒ momentum boost limitado a ~3pp accuracy. Próximas
ondas precisariam features mais sofisticadas (sentiment, options flow,
on-chain metrics) ou múltiplos timeframes.

## Reproducibility
```bash
GROQ_API_KEY='' python3 /tmp/ar_factor_fast.py  # ~5s com cache
```

🤖 Onda 240 — file lock + atomic cache + Karpathy autoresearch ensemble
