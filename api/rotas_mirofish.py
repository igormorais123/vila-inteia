"""
Onda 197: endpoint Mirofish-style — Vila backtest expõe corpus→grafo→sim→relatório.

API-compatible com fluxo Mirofish:
  POST /api/v1/mirofish/run  — dispara pipeline completo
  GET  /api/v1/mirofish/datasets  — lista datasets disponíveis

Diferente de Mirofish original, que simula rede social, aqui Vila prevê eventos
históricos em N datasets com panel de personas lendárias + calibração.

Segurança: base_dir é validado contra ALLOWED_BASE_DIRS pra evitar path traversal.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/mirofish", tags=["mirofish"])


# Diretórios permitidos pra base_dir (evita path traversal e enum de FS)
_REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWED_BASE_DIRS = {
    str((_REPO_ROOT / "data" / "backtest").resolve()),
}


def _validar_base_dir(base_dir: str) -> Path:
    """Resolve base_dir e checa se está no allowlist. Levanta HTTPException 400 se não."""
    try:
        p = (_REPO_ROOT / base_dir).resolve() if not os.path.isabs(base_dir) else Path(base_dir).resolve()
    except Exception:
        raise HTTPException(400, f"base_dir inválido: {base_dir!r}")
    if str(p) not in ALLOWED_BASE_DIRS:
        raise HTTPException(
            400,
            f"base_dir não permitido. Use 'data/backtest' (allowlist: {sorted(ALLOWED_BASE_DIRS)})",
        )
    return p


class RunRequest(BaseModel):
    dataset_glob: str = Field(default="*.csv", description="glob em data/backtest/")
    persona_ids: list[str] = Field(default=["CL001", "CL002", "CL007"])
    base_dir: str = Field(default="data/backtest")


@router.post("/run")
def endpoint_run(req: RunRequest):
    """Roda Vila pipeline estilo Mirofish: grafo → simulação → relatório."""
    from engine.mirofish_style import pipeline_completo
    from api.rotas_vila import obter_simulacao

    base_path = _validar_base_dir(req.base_dir)

    sim_ativa = obter_simulacao()
    if sim_ativa is None or not getattr(sim_ativa, "personas", None):
        raise HTTPException(503, "Simulação Vila não inicializada. POST /api/v1/vila/iniciar primeiro.")

    faltantes = [pid for pid in req.persona_ids if pid not in sim_ativa.personas]
    if faltantes:
        raise HTTPException(400, f"personas não encontradas: {faltantes}")

    resultado = pipeline_completo(
        base_dir=str(base_path),
        dataset_glob=req.dataset_glob,
        persona_ids=req.persona_ids,
        sim=sim_ativa,
        llm_fn=None,  # usa chamar_llm default (OmniRoute/Groq)
    )
    if "erro" in resultado:
        raise HTTPException(400, resultado["erro"])
    return resultado


@router.get("/datasets")
def endpoint_datasets(base_dir: str = "data/backtest"):
    """Lista datasets disponíveis + n_eventos por arquivo (sem expor path absoluto)."""
    import glob
    from engine.backtest_real import carregar_dataset

    base_path = _validar_base_dir(base_dir)

    out = []
    for f in sorted(glob.glob(f"{base_path}/*.csv")):
        try:
            n = len(carregar_dataset(f))
        except Exception:
            n = None
        # Não expõe path absoluto — só stem (nome) e relative dentro do allowlist
        out.append({"dataset": Path(f).stem, "n_eventos": n})
    return {"n_datasets": len(out), "datasets": out, "base_dir": base_dir}


@router.get("/info")
def endpoint_info():
    """Metadata sobre diferencial Vila vs Mirofish."""
    return {
        "pipeline": "corpus → grafo → simulação → relatório",
        "vila_specialty": [
            "144 arquétipos hardcoded (Jesus, Musk, Sun Tzu, Diabob...)",
            "Brier+Platt+isotonic calibration",
            "backtest real 100 events em 10 domínios",
            "skill score vs prior humano calibrado",
            "persona-diverging insights (potential alpha)",
        ],
        "mirofish_specialty": [
            "1M agentes swarm",
            "grafo conhecimento OASIS",
            "Vue.js dashboard",
            "simulação paralela rede social",
        ],
        "overlap": [
            "pipeline corpus → graph → sim → report",
            "multi-agent simulation",
            "relatório narrativo com insights",
        ],
    }
