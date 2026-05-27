"""R-style quantitative analysis toolkit for Vila.

Single import surface for tabular analysis: summary, correlations, formula
models, classical tests, PCA, VIF and complete report generation.
"""
from __future__ import annotations

import io
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

try:  # optional but installed in the quantitative profile
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from statsmodels.stats.outliers_influence import variance_inflation_factor
except Exception:  # pragma: no cover - fallback path
    sm = None
    smf = None
    variance_inflation_factor = None

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
except Exception:  # pragma: no cover - fallback path
    PCA = None
    StandardScaler = None

try:
    import pingouin as pg
except Exception:  # pragma: no cover - fallback path
    pg = None


ROOT = Path(__file__).resolve().parent.parent


def _jsonify(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _jsonify(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonify(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return None if not math.isfinite(float(x)) else float(x)
    if isinstance(x, np.ndarray):
        return [_jsonify(v) for v in x.tolist()]
    if pd.isna(x):
        return None
    return x


def _resolve_path(path: str | Path) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return p.resolve()


def load_table(path: str | Path, *, sep: str = ",") -> pd.DataFrame:
    """Load csv/json/parquet/xlsx into a DataFrame."""
    p = _resolve_path(path)
    suffix = p.suffix.lower()
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(p, sep=sep)
    if suffix in {".json", ".jsonl"}:
        return pd.read_json(p, lines=(suffix == ".jsonl"))
    if suffix == ".parquet":
        return pd.read_parquet(p)
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(p)
    raise ValueError(f"unsupported table extension: {suffix}")


def load_csv_text(csv_text: str, *, sep: str = ",") -> pd.DataFrame:
    return pd.read_csv(io.StringIO(csv_text), sep=sep)


def numeric_columns(df: pd.DataFrame, columns: list[str] | None = None) -> list[str]:
    cols = list(columns) if columns else list(df.columns)
    return [c for c in cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]


def _bh_qvalues(p_values: list[float | None]) -> list[float | None]:
    indexed = [(i, float(p)) for i, p in enumerate(p_values) if p is not None and math.isfinite(float(p))]
    m = len(indexed)
    out: list[float | None] = [None] * len(p_values)
    if m == 0:
        return out
    ranked = sorted(indexed, key=lambda x: x[1])
    prev = 1.0
    for rank, (idx, p) in reversed(list(enumerate(ranked, start=1))):
        q = min(prev, p * m / rank)
        out[idx] = q
        prev = q
    return out


def r_summary(df: pd.DataFrame, *, max_levels: int = 12) -> dict:
    """R-like summary() for a DataFrame."""
    numeric = numeric_columns(df)
    categorical = [c for c in df.columns if c not in numeric]
    numeric_summary: dict[str, Any] = {}
    for c in numeric:
        s = pd.to_numeric(df[c], errors="coerce")
        numeric_summary[c] = {
            "n": int(s.notna().sum()),
            "missing": int(s.isna().sum()),
            "mean": s.mean(),
            "sd": s.std(ddof=1),
            "min": s.min(),
            "q25": s.quantile(0.25),
            "median": s.median(),
            "q75": s.quantile(0.75),
            "max": s.max(),
            "skew": s.skew(),
            "kurtosis": s.kurtosis(),
        }
    categorical_summary: dict[str, Any] = {}
    for c in categorical:
        vc = df[c].astype("object").value_counts(dropna=False).head(max_levels)
        categorical_summary[c] = {
            "n": int(df[c].notna().sum()),
            "missing": int(df[c].isna().sum()),
            "levels": int(df[c].nunique(dropna=True)),
            "top": [{"value": str(k), "n": int(v)} for k, v in vc.items()],
        }
    return _jsonify({
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": list(df.columns),
        "numeric": numeric_summary,
        "categorical": categorical_summary,
    })


def r_cor(
    df: pd.DataFrame,
    *,
    columns: list[str] | None = None,
    method: str = "pearson",
    min_n: int = 3,
) -> dict:
    """Correlation matrix and pair table with p-values and BH q-values."""
    cols = numeric_columns(df, columns)
    if method not in {"pearson", "spearman", "kendall"}:
        raise ValueError("method must be pearson, spearman or kendall")
    mat = df[cols].corr(method=method).replace({np.nan: None}).to_dict()
    pairs: list[dict[str, Any]] = []
    p_values: list[float | None] = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            xy = df[[a, b]].dropna()
            n = len(xy)
            if n < min_n:
                r, p = None, None
            elif method == "pearson":
                r, p = stats.pearsonr(xy[a], xy[b])
            elif method == "spearman":
                r, p = stats.spearmanr(xy[a], xy[b])
            else:
                r, p = stats.kendalltau(xy[a], xy[b])
            pairs.append({"x": a, "y": b, "n": n, "r": r, "p": p})
            p_values.append(p)
    q_values = _bh_qvalues(p_values)
    for row, q in zip(pairs, q_values):
        row["q_bh"] = q
    pairs.sort(key=lambda x: abs(x["r"]) if x["r"] is not None else -1, reverse=True)
    return _jsonify({"method": method, "columns": cols, "matrix": mat, "pairs": pairs})


def r_partial_cor(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    covar: list[str],
    method: str = "pearson",
) -> dict:
    """Partial correlation, pingouin-backed when available."""
    needed = [x, y] + list(covar)
    data = df[needed].dropna()
    if len(data) < len(covar) + 4:
        return {"n": len(data), "r": None, "p": None}
    if pg is not None:
        res = pg.partial_corr(data=data, x=x, y=y, covar=covar, method=method)
        row = res.iloc[0].to_dict()
        return _jsonify({"n": int(row.get("n", len(data))), "r": row.get("r"), "p": row.get("p-val")})

    def resid(col: str) -> np.ndarray:
        z = data[covar].to_numpy(dtype=float)
        z = np.column_stack([np.ones(len(z)), z])
        beta = np.linalg.lstsq(z, data[col].to_numpy(dtype=float), rcond=None)[0]
        return data[col].to_numpy(dtype=float) - z @ beta

    rx, ry = resid(x), resid(y)
    r, p = stats.pearsonr(rx, ry)
    return _jsonify({"n": len(data), "r": r, "p": p})


def r_lm(
    df: pd.DataFrame,
    *,
    formula: str | None = None,
    y: str | None = None,
    x: list[str] | None = None,
) -> dict:
    """Linear model like R lm(). Prefer formula='y ~ x1 + x2'."""
    if smf is not None and formula:
        model = smf.ols(formula=formula, data=df).fit()
    else:
        if not y or not x:
            raise ValueError("provide formula or y+x")
        data = df[[y] + x].dropna()
        X = data[x].to_numpy(dtype=float)
        X = np.column_stack([np.ones(len(X)), X])
        yy = data[y].to_numpy(dtype=float)
        beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
        pred = X @ beta
        resid = yy - pred
        ss_res = float(np.sum(resid ** 2))
        ss_tot = float(np.sum((yy - yy.mean()) ** 2))
        return _jsonify({
            "engine": "numpy_lstsq",
            "n": len(data),
            "formula": f"{y} ~ {' + '.join(x)}",
            "coefficients": [
                {"term": term, "estimate": est}
                for term, est in zip(["Intercept"] + x, beta)
            ],
            "metrics": {
                "r_squared": 1 - ss_res / ss_tot if ss_tot else None,
                "rmse": math.sqrt(ss_res / len(data)) if len(data) else None,
            },
        })
    conf = model.conf_int()
    coeffs = []
    for term in model.params.index:
        coeffs.append({
            "term": term,
            "estimate": model.params[term],
            "std_error": model.bse[term],
            "t": model.tvalues[term],
            "p": model.pvalues[term],
            "ci_low": conf.loc[term, 0],
            "ci_high": conf.loc[term, 1],
        })
    return _jsonify({
        "engine": "statsmodels_ols",
        "formula": formula or f"{y} ~ {' + '.join(x or [])}",
        "n": int(model.nobs),
        "coefficients": coeffs,
        "metrics": {
            "r_squared": model.rsquared,
            "adj_r_squared": model.rsquared_adj,
            "aic": model.aic,
            "bic": model.bic,
            "f_pvalue": model.f_pvalue,
            "rmse": math.sqrt(float(np.mean(model.resid ** 2))),
        },
    })


def r_glm_binomial(
    df: pd.DataFrame,
    *,
    formula: str | None = None,
    y: str | None = None,
    x: list[str] | None = None,
) -> dict:
    """Binomial GLM / logistic regression like R glm(..., family=binomial)."""
    if smf is None or sm is None:
        raise RuntimeError("statsmodels is required for r_glm_binomial")
    if formula:
        model = smf.glm(formula=formula, data=df, family=sm.families.Binomial()).fit()
        model_formula = formula
    else:
        if not y or not x:
            raise ValueError("provide formula or y+x")
        model_formula = f"{y} ~ {' + '.join(x)}"
        model = smf.glm(formula=model_formula, data=df, family=sm.families.Binomial()).fit()
    coeffs = []
    conf = model.conf_int()
    for term in model.params.index:
        coeffs.append({
            "term": term,
            "estimate": model.params[term],
            "odds_ratio": math.exp(model.params[term]),
            "std_error": model.bse[term],
            "z": model.tvalues[term],
            "p": model.pvalues[term],
            "ci_low": conf.loc[term, 0],
            "ci_high": conf.loc[term, 1],
        })
    probs = model.predict()
    y_obs = np.asarray(model.model.endog)
    acc = float(np.mean((probs >= 0.5) == y_obs)) if len(y_obs) else None
    return _jsonify({
        "engine": "statsmodels_glm_binomial",
        "formula": model_formula,
        "n": int(model.nobs),
        "coefficients": coeffs,
        "metrics": {
            "aic": model.aic,
            "bic": getattr(model, "bic_llf", None),
            "deviance": model.deviance,
            "accuracy_0_5": acc,
        },
    })


def r_t_test(df: pd.DataFrame, *, value: str, group: str | None = None, mu: float = 0.0) -> dict:
    data = df[[value] + ([group] if group else [])].dropna()
    if group:
        levels = list(data[group].dropna().unique())
        if len(levels) != 2:
            raise ValueError("group must have exactly two levels")
        a = data.loc[data[group] == levels[0], value].astype(float)
        b = data.loc[data[group] == levels[1], value].astype(float)
        stat, p = stats.ttest_ind(a, b, equal_var=False)
        return _jsonify({
            "test": "welch_two_sample_t",
            "value": value,
            "group": group,
            "levels": [str(levels[0]), str(levels[1])],
            "n": [int(len(a)), int(len(b))],
            "mean": [a.mean(), b.mean()],
            "t": stat,
            "p": p,
        })
    s = data[value].astype(float)
    stat, p = stats.ttest_1samp(s, popmean=mu)
    return _jsonify({"test": "one_sample_t", "value": value, "mu": mu, "n": len(s), "mean": s.mean(), "t": stat, "p": p})


def r_chisq_test(df: pd.DataFrame, *, row: str, col: str) -> dict:
    tab = pd.crosstab(df[row], df[col])
    chi2, p, dof, expected = stats.chi2_contingency(tab)
    return _jsonify({
        "test": "pearson_chi_square",
        "row": row,
        "col": col,
        "chi2": chi2,
        "p": p,
        "dof": dof,
        "observed": tab.to_dict(),
        "expected": pd.DataFrame(expected, index=tab.index, columns=tab.columns).to_dict(),
    })


def r_aov(df: pd.DataFrame, *, y: str, group: str) -> dict:
    data = df[[y, group]].dropna()
    groups = [g[y].astype(float).to_numpy() for _, g in data.groupby(group)]
    if len(groups) < 2:
        raise ValueError("group must have at least two levels")
    f, p = stats.f_oneway(*groups)
    return _jsonify({
        "test": "one_way_anova",
        "y": y,
        "group": group,
        "k": len(groups),
        "n": int(sum(len(g) for g in groups)),
        "f": f,
        "p": p,
        "means": data.groupby(group)[y].mean().to_dict(),
    })


def r_vif(df: pd.DataFrame, *, columns: list[str] | None = None) -> dict:
    cols = numeric_columns(df, columns)
    data = df[cols].dropna()
    if variance_inflation_factor is None or len(cols) < 2 or len(data) < 3:
        return {"columns": cols, "vif": []}
    X = data.to_numpy(dtype=float)
    out = []
    for i, c in enumerate(cols):
        out.append({"term": c, "vif": variance_inflation_factor(X, i)})
    return _jsonify({"columns": cols, "vif": out})


def r_pca(df: pd.DataFrame, *, columns: list[str] | None = None, n_components: int = 5, scale: bool = True) -> dict:
    cols = numeric_columns(df, columns)
    data = df[cols].dropna()
    if PCA is None or len(cols) < 2 or len(data) < 3:
        return {"columns": cols, "components": []}
    X = data.to_numpy(dtype=float)
    if scale and StandardScaler is not None:
        X = StandardScaler().fit_transform(X)
    k = max(1, min(n_components, len(cols), len(data)))
    model = PCA(n_components=k).fit(X)
    comps = []
    for idx in range(k):
        loadings = {c: model.components_[idx, j] for j, c in enumerate(cols)}
        comps.append({
            "component": idx + 1,
            "explained_variance_ratio": model.explained_variance_ratio_[idx],
            "loadings": loadings,
        })
    return _jsonify({"columns": cols, "scaled": scale, "components": comps})


def analyze_dataframe(
    df: pd.DataFrame,
    *,
    target: str | None = None,
    group: str | None = None,
    corr_method: str = "pearson",
) -> dict:
    """Full quantitative report for a table."""
    report: dict[str, Any] = {
        "summary": r_summary(df),
        "correlation": r_cor(df, method=corr_method),
        "vif": r_vif(df),
        "pca": r_pca(df),
    }
    if target and target in df.columns:
        xs = [c for c in numeric_columns(df) if c != target]
        if xs:
            report["lm_target"] = r_lm(df, y=target, x=xs[:12])
    if target and group and target in df.columns and group in df.columns:
        report["t_test"] = r_t_test(df, value=target, group=group)
        report["anova"] = r_aov(df, y=target, group=group)
    return _jsonify(report)


def analyze_file(path: str | Path, *, target: str | None = None, group: str | None = None, sep: str = ",") -> dict:
    df = load_table(path, sep=sep)
    out = analyze_dataframe(df, target=target, group=group)
    out["source"] = str(_resolve_path(path).relative_to(ROOT)) if ROOT in _resolve_path(path).parents else str(_resolve_path(path))
    return out


def to_markdown(report: dict) -> str:
    """Compact markdown rendering for CLI and docs."""
    summary = report.get("summary", {})
    lines = [
        "# Quant Analysis Report",
        "",
        f"- Rows: {summary.get('n_rows')}",
        f"- Columns: {summary.get('n_cols')}",
        "",
        "## Numeric Summary",
        "",
        "| column | n | missing | mean | sd | min | median | max |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for c, s in summary.get("numeric", {}).items():
        lines.append(
            f"| {c} | {s.get('n')} | {s.get('missing')} | {_fmt(s.get('mean'))} | "
            f"{_fmt(s.get('sd'))} | {_fmt(s.get('min'))} | {_fmt(s.get('median'))} | {_fmt(s.get('max'))} |"
        )
    lines += ["", "## Top Correlations", "", "| x | y | n | r | p | q_bh |", "|---|---|---:|---:|---:|---:|"]
    for row in report.get("correlation", {}).get("pairs", [])[:20]:
        lines.append(
            f"| {row.get('x')} | {row.get('y')} | {row.get('n')} | {_fmt(row.get('r'))} | "
            f"{_fmt(row.get('p'))} | {_fmt(row.get('q_bh'))} |"
        )
    lm = report.get("lm_target")
    if lm:
        lines += ["", "## Linear Model", "", f"- Formula: `{lm.get('formula')}`"]
        metrics = lm.get("metrics", {})
        lines.append(f"- R2: {_fmt(metrics.get('r_squared'))}; RMSE: {_fmt(metrics.get('rmse'))}")
        lines += ["", "| term | estimate | p |", "|---|---:|---:|"]
        for c in lm.get("coefficients", []):
            lines.append(f"| {c.get('term')} | {_fmt(c.get('estimate'))} | {_fmt(c.get('p'))} |")
    return "\n".join(lines) + "\n"


def _fmt(v: Any) -> str:
    if v is None:
        return "-"
    try:
        f = float(v)
    except Exception:
        return str(v)
    if not math.isfinite(f):
        return "-"
    if abs(f) >= 1000 or (abs(f) < 0.001 and f != 0):
        return f"{f:.3e}"
    return f"{f:.4f}"


def dumps(report: dict) -> str:
    return json.dumps(_jsonify(report), indent=2, ensure_ascii=False)
