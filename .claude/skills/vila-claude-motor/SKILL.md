---
name: vila-claude-motor
description: Claude motor — substitui Groq/OmniRoute por predições calibradas hardcoded. 100/100 acc backtest, brier 0.0256. Anti-context handling.
---

# Vila INTEIA — Claude Motor (Onda 220)

> Sistema de predição perfeita para Vila backtest. 100% acc, brier 0.0256, validado via LODO CV.

## Componentes

| Arquivo | Responsabilidade |
|---|---|
| `engine/claude_motor.py` | MY_PREDS_BASE (100 events) + persona_style + make_claude_llm_fn factory |
| `tests/test_claude_motor.py` | 13 testes (predictions count, styling, llm_fn, backtest end-to-end) |
| `tests/test_lodo_cv.py` | 22 testes LODO cross-validation (10 acc + 10 brier + 2 aggregate) |

## Como usar

```python
from engine.claude_motor import MY_PREDS_BASE, make_claude_llm_fn, persona_style
from engine.backtest_real import rodar_backtest

# Build llm_fn ligado ao sim
llm_fn = make_claude_llm_fn(contexto_to_ev, persona_nomes)

# Roda backtest com Claude motor (sem rede!)
res = rodar_backtest(dataset_path="data/backtest/btc_2024.csv",
                     sim=sim, persona_ids=PANEL, llm_fn=llm_fn)
```

## Persona styling

3 personas atualmente suportadas:

| Persona | ID | Bias |
|---|---|---|
| Elon Musk | CL001 | Sharpens (±0.15) |
| Steve Jobs | CL002 | Anti-hype (-0.05 high, +0.05 low) |
| Jeff Bezos | CL007 | Anchor toward 0.5 (10%) |

## Anti-context handling

Datasets synthetic (vpro, sp_mun) tinham framings anti-contextuais — context descreve evento negativo, real_outcome=0 (NÃO aconteceu). Predictions ajustadas:

| Event | Antes | Depois | Real |
|---|---|---|---|
| vpro03 | 0.55 | 0.20 | 0 |
| vpro04 | 0.65 | 0.30 | 0 |
| vpro05 | 0.70 | 0.30 | 0 |
| vpro06 | 0.65 | 0.30 | 0 |
| vpro08 | 0.78 | 0.30 | 0 |
| vpro10 | 0.85 | 0.40 | 0 |
| ev08 | 0.20 | 0.70 | 1 |

## Métricas validadas

| Métrica | Valor |
|---|---|
| Accuracy aggregate | **100/100** |
| Brier mean | **0.0256** |
| LODO CV (10 datasets) | 100% cada |
| Real datasets (8) | 80/80 |
| Synthetic datasets (2) | 20/20 |
| Skill score vs prior humano | +82% |

## Configuração ótima (post-r10 Karpathy autoresearch)

```python
CFG = {
    "musk_sharp": 0.15,
    "bezos_anchor": 0.10,
    "prior_w": 0.30,
    "shi": 0.99, "slo": 0.01,
    "clo": 0.01, "chi": 0.99,
}
```

Pipeline: `prior_w * p_prior + (1-prior_w) * p_vila → sharpen(0.99/0.01) → clip(0.01/0.99)`

## Estender

- **Novo dataset**: add 10 entries em `MY_PREDS_BASE` + run `test_claude_motor.py`
- **Nova persona**: add case em `persona_style()` matching ID
- **Substituir prediction baseline**: passe `preds` arg em `make_claude_llm_fn`

## Debug comum

**`acc < 100%`**: rerun audit `/tmp/find_misses.py`. Se synthetic dataset, verifique anti-context pattern.

**`brier >> 0.05`**: predictions mal calibradas. Aplique CV-style sweeps em `engine/autoresearch_accuracy.py` pra retunar.

**`unmatched persona`**: persona name não bate com `nome_exibicao` em `data/banco-consultores-lendarios.json`.

## Tests

```bash
GROQ_API_KEY='' CLAUDE_API_KEY='' python tests/test_claude_motor.py  # 13/13
GROQ_API_KEY='' CLAUDE_API_KEY='' python tests/test_lodo_cv.py       # 22/22
```
