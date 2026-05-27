# Quant Analysis R-style

Camada quantitativa da Vila em Python, com interface parecida com R.

## Capacidades

- `summary`: dimensoes, tipos, faltantes, quantis, assimetria, curtose.
- `cor`: Pearson, Spearman, Kendall, p-value e q-value Benjamini-Hochberg.
- `partial_cor`: correlacao parcial com covariaveis.
- `lm`: regressao linear por formula, estilo `y ~ x1 + x2`.
- `glm_binomial`: regressao logistica por formula.
- `t_test`, `chisq_test`, `anova`.
- `pca` e `vif`.

## Python

```python
from engine.quant_analysis import analyze_file, r_lm, r_cor

report = analyze_file("data/backtest/eleicao_presidencial_br_2022.csv")
model = r_lm(df, formula="outcome_real ~ poll_lead_pp + incumbente")
```

## CLI

```bash
python scripts/quant_analyze.py data/backtest/eleicao_presidencial_br_2022.csv \
  --target outcome_real --format md --out data/quant_report.md
```

## API

```bash
curl -X POST http://localhost:8100/api/v1/quant/analyze \
  -H "Content-Type: application/json" \
  -d '{"csv_text":"x,y\n1,2\n2,4\n3,6","target":"y"}'
```

Endpoints:

- `GET /api/v1/quant/capabilities`
- `POST /api/v1/quant/analyze`
- `POST /api/v1/quant/cor`
- `POST /api/v1/quant/partial-cor`
- `POST /api/v1/quant/lm`
- `POST /api/v1/quant/glm-binomial`
- `POST /api/v1/quant/t-test`
- `POST /api/v1/quant/chisq-test`

## Tool interna

MCP tool: `vila.quant_analisar_csv`.

Entrada minima:

```json
{"path": "data/backtest/eleicao_presidencial_br_2022.csv", "target": "outcome_real"}
```
