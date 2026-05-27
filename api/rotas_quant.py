"""Quantitative analysis endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engine.quant_analysis import (
    analyze_dataframe,
    load_csv_text,
    r_chisq_test,
    r_cor,
    r_glm_binomial,
    r_lm,
    r_partial_cor,
    r_t_test,
)


router = APIRouter(prefix="/api/v1/quant", tags=["quant"])


class AnalyzeCsvRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)
    sep: str = ","
    target: Optional[str] = None
    group: Optional[str] = None
    corr_method: str = "pearson"


class CorRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)
    sep: str = ","
    columns: Optional[list[str]] = None
    method: str = "pearson"


class PartialCorRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)
    sep: str = ","
    x: str
    y: str
    covar: list[str]
    method: str = "pearson"


class ModelRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)
    sep: str = ","
    formula: Optional[str] = None
    y: Optional[str] = None
    x: Optional[list[str]] = None


class TTestRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)
    sep: str = ","
    value: str
    group: Optional[str] = None
    mu: float = 0.0


class ChiSqRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)
    sep: str = ","
    row: str
    col: str


@router.get("/capabilities")
def capabilities():
    return {
        "style": "R-style Python",
        "libraries": ["pandas", "numpy", "scipy", "statsmodels", "sklearn", "pingouin", "plotnine", "seaborn"],
        "functions": [
            "summary",
            "cor",
            "partial_cor",
            "lm",
            "glm_binomial",
            "t_test",
            "chisq_test",
            "anova",
            "pca",
            "vif",
        ],
    }


@router.post("/analyze")
def analyze(req: AnalyzeCsvRequest):
    try:
        df = load_csv_text(req.csv_text, sep=req.sep)
        return analyze_dataframe(df, target=req.target, group=req.group, corr_method=req.corr_method)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/cor")
def cor(req: CorRequest):
    try:
        df = load_csv_text(req.csv_text, sep=req.sep)
        return r_cor(df, columns=req.columns, method=req.method)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/partial-cor")
def partial_cor(req: PartialCorRequest):
    try:
        df = load_csv_text(req.csv_text, sep=req.sep)
        return r_partial_cor(df, x=req.x, y=req.y, covar=req.covar, method=req.method)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/lm")
def lm(req: ModelRequest):
    try:
        df = load_csv_text(req.csv_text, sep=req.sep)
        return r_lm(df, formula=req.formula, y=req.y, x=req.x)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/glm-binomial")
def glm_binomial(req: ModelRequest):
    try:
        df = load_csv_text(req.csv_text, sep=req.sep)
        return r_glm_binomial(df, formula=req.formula, y=req.y, x=req.x)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/t-test")
def t_test(req: TTestRequest):
    try:
        df = load_csv_text(req.csv_text, sep=req.sep)
        return r_t_test(df, value=req.value, group=req.group, mu=req.mu)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/chisq-test")
def chisq_test(req: ChiSqRequest):
    try:
        df = load_csv_text(req.csv_text, sep=req.sep)
        return r_chisq_test(df, row=req.row, col=req.col)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
