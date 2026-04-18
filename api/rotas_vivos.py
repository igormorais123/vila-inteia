"""
api/rotas_vivos — Endpoints dos agentes vivos da INTEIA na Vila.

Helena Strategos (cientista-chefe) e Efesto Tekhton (CTO) estão vivos:
heartbeats executam auditoria real, publicam coluna diária no Mirante,
e podem ser consultados em tempo real.

Rotas:
    GET  /api/v1/vivos/status
    POST /api/v1/vivos/heartbeat/{agente}
    GET  /api/v1/vivos/{agente}/ultimos
    POST /api/v1/vivos/publicar-coluna-hoje
    GET  /api/v1/vivos/coluna/historico
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger("vila-inteia.api.vivos")

router = APIRouter(prefix="/api/v1/vivos", tags=["Agentes Vivos"])


@router.get("/status")
def status_vivos() -> dict:
    """Status do scheduler e dos agentes vivos."""
    from engine.agentes_vivos import scheduler, HELENA, EFESTO
    ult_helena = HELENA.ultimos_relatorios(limit=1)
    ult_efesto = EFESTO.ultimos_relatorios(limit=1)
    return {
        "scheduler": scheduler.status(),
        "ultimo_helena": ult_helena[0] if ult_helena else None,
        "ultimo_efesto": ult_efesto[0] if ult_efesto else None,
    }


@router.post("/heartbeat/{agente}")
def disparar_heartbeat(agente: str, step: int = 0) -> dict:
    """Dispara manualmente um heartbeat de um agente."""
    from engine.agentes_vivos import HELENA, EFESTO
    mapa = {"helena": HELENA, "helena_strategos": HELENA,
            "efesto": EFESTO, "efesto_tekhton": EFESTO}
    a = mapa.get(agente.lower())
    if not a:
        raise HTTPException(status_code=404, detail=f"Agente '{agente}' desconhecido. Opções: helena, efesto.")
    hb = a.executar_heartbeat(step=step or 1, sim=None)
    return hb.as_dict()


@router.get("/{agente}/ultimos")
def ultimos_heartbeats(
    agente: str,
    limit: int = Query(5, ge=1, le=50),
) -> dict:
    """Últimos relatórios de heartbeat de um agente."""
    from engine.agentes_vivos import HELENA, EFESTO
    mapa = {"helena": HELENA, "helena_strategos": HELENA,
            "efesto": EFESTO, "efesto_tekhton": EFESTO}
    a = mapa.get(agente.lower())
    if not a:
        raise HTTPException(status_code=404, detail=f"Agente '{agente}' desconhecido")
    return {"agente": a.id, "relatorios": a.ultimos_relatorios(limit=limit)}


@router.post("/publicar-coluna-hoje")
def publicar_coluna(
    forcar: bool = Query(False, description="republica mesmo se já existe matéria hoje"),
    autor: Optional[str] = Query(None, description="helena | efesto (override)"),
) -> dict:
    """Publica a coluna diária da Vila no Mirante News."""
    from engine.coluna_vila import publicar_coluna_hoje
    r = publicar_coluna_hoje(forcar=forcar, forcar_autor=autor)
    return r


@router.get("/coluna/previa")
def previa_coluna(autor: Optional[str] = None) -> dict:
    """Mostra como ficaria a coluna de hoje sem publicar (dry-run)."""
    from engine.coluna_vila import compor_coluna_hoje
    mdx = compor_coluna_hoje(forcar_autor=autor)
    return mdx


@router.get("/coluna/historico")
def historico_coluna(limit: int = Query(30, ge=1, le=365)) -> dict:
    """Histórico das colunas publicadas (persistido em vila_coluna_publicacoes)."""
    try:
        from engine import supabase_db
        rows = supabase_db.buscar("vila_coluna_publicacoes", f"order=publicado_em.desc&limit={limit}") or []
        return {"total": len(rows), "colunas": rows}
    except Exception as exc:
        logger.warning("historico coluna falhou: %s", exc)
        return {"total": 0, "colunas": [], "erro": str(exc)}


# =====================================================================
# Coluna pública — visível em HTML no navegador
# =====================================================================

from fastapi.responses import HTMLResponse, PlainTextResponse


def _render_html_coluna(coluna: dict) -> str:
    titulo = coluna.get("titulo") or "Coluna Vila INTEIA"
    autor = coluna.get("autor_nome") or coluna.get("autor") or "Vila INTEIA"
    data = coluna.get("data_ref") or coluna.get("data") or ""
    # o corpo pode vir como corpo_mdx (preview) ou precisar reconstruir do Supabase
    corpo_mdx = coluna.get("corpo_mdx") or ""
    if not corpo_mdx and coluna.get("material_resumo"):
        # veio do histórico — puxa o mdx do arquivo local se existir, senão remonta resumo
        try:
            from engine.coluna_vila import DATA_COLUNA
            arq = DATA_COLUNA / f"{data}.mdx"
            if arq.is_file():
                corpo_mdx = arq.read_text(encoding="utf-8")
        except Exception:
            pass
    if not corpo_mdx:
        corpo_mdx = "*Conteúdo não disponível para esta data.*"
    # Converter markdown-lite para HTML
    import re
    html_body = corpo_mdx
    html_body = re.sub(r"^###\s+(.*)$", r"<h3>\1</h3>", html_body, flags=re.M)
    html_body = re.sub(r"^##\s+(.*)$",  r"<h2>\1</h2>", html_body, flags=re.M)
    html_body = re.sub(r"^#\s+(.*)$",   r"<h1>\1</h1>", html_body, flags=re.M)
    html_body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html_body)
    html_body = re.sub(r"\*(.+?)\*",     r"<em>\1</em>", html_body)
    html_body = re.sub(r"^-\s+(.*)$", r"<li>\1</li>", html_body, flags=re.M)
    html_body = re.sub(r"(<li>.*?</li>(\s*<li>.*?</li>)+)", r"<ul>\1</ul>", html_body, flags=re.S)
    html_body = html_body.replace("\n\n", "</p><p>")
    html_body = f"<p>{html_body}</p>"
    html_body = html_body.replace("<p><h", "<h").replace("</h1></p>", "</h1>").replace("</h2></p>", "</h2>").replace("</h3></p>", "</h3>").replace("<p><ul>", "<ul>").replace("</ul></p>", "</ul>")

    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo} · Vila INTEIA no Mirante News</title>
<style>
  body {{ background: #0b1020; color: #e8ecf5; font-family: ui-sans-serif,system-ui,Inter,sans-serif; line-height:1.7; margin:0; padding:48px 28px; }}
  .wrap {{ max-width: 880px; margin: 0 auto; }}
  h1,h2,h3 {{ font-family: "Cormorant Garamond", Georgia, serif; color:#e7b84a; }}
  h1 {{ font-size: 2.6rem; line-height:1.1; }}
  h2 {{ font-size: 1.6rem; margin-top:2rem; }}
  .kicker {{ color:#c9952a; letter-spacing:.2em; text-transform:uppercase; font-size:.8rem; font-weight:600; margin-bottom:6px; }}
  .meta {{ color:#9aa4bf; font-size:.9rem; margin-bottom:36px; border-bottom:1px solid #2a3558; padding-bottom:14px; }}
  em {{ color:#cbd3eb; }}
  strong {{ color:#fff; }}
  a {{ color:#7fd8ff; }}
  ul li {{ margin:4px 0; }}
  footer {{ margin-top:60px; padding-top:20px; border-top:1px solid #2a3558; color:#9aa4bf; font-size:.85rem; }}
</style></head><body><div class="wrap">
<div class="kicker">Vila INTEIA · Coluna Diária · {data}</div>
<div class="meta">Assinado por <strong>{autor}</strong> · Publicado em parceria com Mirante News</div>
{html_body}
<footer>
  <p>Esta coluna é gerada automaticamente pelos agentes vivos <strong>Helena Strategos</strong> e <strong>Efesto Tekhton</strong> a partir dos heartbeats e traces reais da Vila INTEIA nas últimas 24 horas. Ver <a href="/api/v1/harness/saude">/api/v1/harness/saude</a> e <a href="/api/v1/vivos/status">/api/v1/vivos/status</a>.</p>
  <p>© INTEIA · <a href="/api/v1/vivos/coluna/historico">Histórico completo</a></p>
</footer>
</div></body></html>"""


@router.get("/coluna/hoje", response_class=HTMLResponse, include_in_schema=False)
def coluna_hoje_html():
    """Renderiza a coluna de hoje em HTML (pública)."""
    from datetime import datetime, timezone
    from engine import supabase_db
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = supabase_db.buscar("vila_coluna_publicacoes", f"data_ref=eq.{hoje}&limit=1") or []
    if rows:
        return _render_html_coluna(rows[0])
    # fallback: compõe prévia
    from engine.coluna_vila import compor_coluna_hoje
    return _render_html_coluna(compor_coluna_hoje())


@router.get("/coluna/{data}", response_class=HTMLResponse, include_in_schema=False)
def coluna_por_data_html(data: str):
    """Renderiza coluna de data específica (YYYY-MM-DD)."""
    from engine import supabase_db
    rows = supabase_db.buscar("vila_coluna_publicacoes", f"data_ref=eq.{data}&limit=1") or []
    if not rows:
        raise HTTPException(status_code=404, detail=f"Sem coluna publicada em {data}")
    return _render_html_coluna(rows[0])


@router.get("/coluna/{data}/mdx", response_class=PlainTextResponse, include_in_schema=False)
def coluna_mdx(data: str):
    """MDX bruto da coluna — para consumo pelo Mirante ou outros."""
    from engine.coluna_vila import DATA_COLUNA
    arq = DATA_COLUNA / f"{data}.mdx"
    if not arq.is_file():
        raise HTTPException(status_code=404, detail=f"MDX de {data} não encontrado")
    return arq.read_text(encoding="utf-8")
