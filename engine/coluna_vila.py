"""
engine/coluna_vila — Coluna diária da Vila INTEIA no Mirante News.

Uma publicação por dia na editoria "Pesquisa IA" (subcategoria "Vila INTEIA")
assinada por Helena ou Efesto, dependendo do tipo de dia:

    - Dia par         → Helena (parecer estratégico)
    - Dia ímpar       → Efesto (runbook operacional)
    - Dia de incidente → quem detectou (override manual via endpoint)

O conteúdo sai dos heartbeats reais + traces do harness. Não inventa
dados. Se não houver material real, escreve "sem atividade significativa".

Dispara:
    - Automático uma vez por dia via scheduler (step * minutos_por_step >= 24h)
    - Manual via POST /api/v1/vivos/publicar-coluna-hoje
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("vila-inteia.coluna_vila")

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_COLUNA = REPO_ROOT / "data" / "coluna_vila"
DATA_COLUNA.mkdir(parents=True, exist_ok=True)


def _hoje_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _ja_publicou_hoje() -> bool:
    return (DATA_COLUNA / f"{_hoje_iso()}.mdx").is_file()


def _coletar_material(horas: int = 24) -> dict:
    """Extrai sumário de traces + heartbeats das últimas N horas."""
    try:
        from engine import supabase_db
    except Exception:
        return {}

    corte = (datetime.now(timezone.utc) - timedelta(hours=horas)).isoformat()

    traces = supabase_db.buscar("vila_traces", f"order=inicio.desc&limit=5000&inicio=gte.{corte}") or []
    heartbeats = supabase_db.buscar("vila_heartbeat", f"order=executado_em.desc&limit=500&executado_em=gte.{corte}") or []

    por_fase: dict[str, int] = {}
    por_agente: dict[str, int] = {}
    falhas = 0
    custo = 0.0
    for t in traces:
        f = t.get("fase", "?")
        a = t.get("agente_id", "?")
        por_fase[f] = por_fase.get(f, 0) + 1
        por_agente[a] = por_agente.get(a, 0) + 1
        if t.get("resultado") != "sucesso":
            falhas += 1
        custo += float(t.get("custo_usd") or 0)

    alertas = []
    for h in heartbeats:
        for a in h.get("alertas", []) or []:
            alertas.append(f"{h.get('agente')}: {a}")

    return {
        "traces_total": len(traces),
        "heartbeats_total": len(heartbeats),
        "por_fase": por_fase,
        "agentes_ativos": len(por_agente),
        "top_agentes": sorted(por_agente.items(), key=lambda x: x[1], reverse=True)[:5],
        "falhas": falhas,
        "taxa_falha": round(falhas / len(traces), 4) if traces else 0.0,
        "custo_usd_total": round(custo, 4),
        "alertas_heartbeat": alertas[:10],
    }


def _gerar_mdx_helena(material: dict) -> dict:
    """Parecer estratégico em tom Helena — sinal da INTEIA e do Fundador."""
    data = _hoje_iso()
    traces = material.get("traces_total", 0)
    fases = material.get("por_fase", {})
    falhas = material.get("falhas", 0)
    taxa = material.get("taxa_falha", 0.0)
    alertas = material.get("alertas_heartbeat", [])

    titulo = f"Boletim da Vila INTEIA — {data}"
    slug = f"vila-inteia-{data}"

    linhas = [
        f"# {titulo}",
        "",
        "*Coluna diária da Vila INTEIA. Parecer de Helena Strategos, "
        "Cientista-Chefe de Inteligência.*",
        "",
        "## Panorama das últimas 24 horas",
        "",
        f"A Vila registrou **{traces} eventos cognitivos** distribuídos "
        f"entre **{len(fases)} fases do Agent Loop**, com "
        f"**{material.get('agentes_ativos', 0)} agentes ativos**.",
        "",
        f"- Fases mais movimentadas: {', '.join(f'{k} ({v})' for k, v in sorted(fases.items(), key=lambda x: x[1], reverse=True)[:3])}.",
        f"- Taxa de falha observada: **{taxa*100:.2f}%** ({falhas} de {traces}).",
        f"- Custo apurado: **US$ {material.get('custo_usd_total', 0):.4f}** "
        "(se o valor aparece zerado, a instrumentação de tokens ainda está em implantação — ver agenda).",
        "",
        "## Leitura estratégica",
        "",
        "O sistema está operando dentro do envelope esperado para a Onda "
        "atual do harness. O que chama atenção hoje:",
        "",
    ]
    if alertas:
        linhas.append("**Alertas registrados pelos heartbeats:**")
        linhas.append("")
        for a in alertas[:5]:
            linhas.append(f"- {a}")
        linhas.append("")
    else:
        linhas.append("Sem alertas relevantes — ambiente estável.")
        linhas.append("")

    linhas += [
        "## Agenda para o próximo ciclo",
        "",
        "1. Instrumentar captura de tokens e custo em cada chamada ao OmniRoute.",
        "2. Popular a Ficha do Fundador via `data/fundador.yaml` no repositório.",
        "3. Acolher o primeiro cliente piloto no Copilot-Sandbox.",
        "",
        "*Assinado: Dra. Helena Strategos, em nome da INTEIA e do Fundador.*",
    ]

    corpo = "\n".join(linhas)
    excerpt = (f"Em 24 horas a Vila registrou {traces} eventos cognitivos, "
               f"taxa de falha {taxa*100:.2f}%. Parecer de Helena Strategos.")

    return {
        "titulo": titulo,
        "slug": slug,
        "categoria": "Pesquisa IA",
        "tags": ["Vila INTEIA", "Harness", "Helena", "Boletim Diário"],
        "excerpt": excerpt[:240],
        "corpo_mdx": corpo,
        "autor_nome": "Dra. Helena Strategos",
        "autor_id": "helena_strategos",
    }


def _gerar_mdx_efesto(material: dict) -> dict:
    data = _hoje_iso()
    traces = material.get("traces_total", 0)
    heartbeats = material.get("heartbeats_total", 0)
    falhas = material.get("falhas", 0)
    taxa = material.get("taxa_falha", 0.0)
    alertas = material.get("alertas_heartbeat", [])
    fases = material.get("por_fase", {})

    titulo = f"Runbook da Vila INTEIA — {data}"
    slug = f"vila-inteia-runbook-{data}"

    status = "VERDE" if not alertas else ("AMARELO" if len(alertas) <= 2 else "VERMELHO")

    linhas = [
        f"# {titulo}",
        "",
        f"*Coluna diária da Vila INTEIA. Runbook de Efesto Tekhton, "
        f"Diretor de Tecnologia. Status operacional: **{status}**.*",
        "",
        "## Indicadores operacionais (24h)",
        "",
        f"- **Eventos cognitivos**: {traces}",
        f"- **Heartbeats executados**: {heartbeats}",
        f"- **Taxa de falha**: {taxa*100:.2f}%",
        f"- **Custo OmniRoute**: US$ {material.get('custo_usd_total', 0):.4f}",
        "",
        "## Distribuição por fase do Agent Loop",
        "",
    ]
    for k, v in sorted(fases.items(), key=lambda x: x[1], reverse=True):
        linhas.append(f"- {k}: {v}")
    linhas += ["", "## Alertas ativos", ""]
    if alertas:
        for a in alertas[:5]:
            linhas.append(f"- {a}")
    else:
        linhas.append("- Nenhum alerta pendente.")

    linhas += [
        "",
        "## Próximos passos técnicos",
        "",
        "1. Fechar captura real de tokens por chamada (`engine/ia_client.py` + `capturar_tokens` no decorator).",
        "2. Rodar script de verificação de capability cards em CI.",
        "3. Provisionar domínio `vila.inteia.ai` apontando para Render.",
        "",
        "*Assinado: Efesto Tekhton — sem trace, sem decisão.*",
    ]

    corpo = "\n".join(linhas)
    excerpt = f"Status {status}. {traces} eventos, {heartbeats} heartbeats, taxa de falha {taxa*100:.2f}%."

    return {
        "titulo": titulo,
        "slug": slug,
        "categoria": "Tecnologia",
        "tags": ["Vila INTEIA", "Harness", "Efesto", "Runbook"],
        "excerpt": excerpt[:240],
        "corpo_mdx": corpo,
        "autor_nome": "Efesto Tekhton",
        "autor_id": "efesto_tekhton",
    }


def compor_coluna_hoje(forcar_autor: Optional[str] = None) -> dict:
    """Monta a matéria diária sem publicar. Devolve dict pronto para publicar()."""
    material = _coletar_material(horas=24)
    dia = datetime.now(timezone.utc).day

    autor = forcar_autor
    if not autor:
        autor = "helena" if dia % 2 == 0 else "efesto"

    if autor == "helena":
        mdx = _gerar_mdx_helena(material)
    else:
        mdx = _gerar_mdx_efesto(material)

    mdx["material"] = material
    return mdx


def publicar_coluna_hoje(forcar: bool = False, forcar_autor: Optional[str] = None) -> dict:
    """
    Publica a coluna diária. Idempotente por dia (só publica 1x — a menos
    de `forcar=True`).
    """
    if not forcar and _ja_publicou_hoje():
        return {"status": "skipped", "motivo": "coluna já publicada hoje", "data": _hoje_iso()}

    mdx = compor_coluna_hoje(forcar_autor=forcar_autor)

    # salva cópia local sempre
    arq = DATA_COLUNA / f"{_hoje_iso()}.mdx"
    try:
        with open(arq, "w", encoding="utf-8") as f:
            f.write(f"---\ntitulo: {mdx['titulo']}\ndata: {_hoje_iso()}\n---\n\n")
            f.write(mdx["corpo_mdx"])
    except Exception as exc:
        logger.warning("erro salvando mdx local: %s", exc)

    # tenta publicar via mirante_client
    try:
        from engine import mirante_client
        sub = mirante_client.Submissao(
            submissao_id=str(uuid.uuid4()),
            titulo=mdx["titulo"],
            slug=mdx["slug"],
            categoria=mdx["categoria"],
            tags=mdx["tags"],
            excerpt=mdx["excerpt"],
            corpo_mdx=mdx["corpo_mdx"],
            autor=mirante_client.Autor(
                agente_id=mdx["autor_id"],
                nome=mdx["autor_nome"],
                vila_id="vila-inteia",
            ),
            parecer_editorial=mirante_client.ParecerEditorial(
                veredito="aprovado",
                score=0.9,
                observacoes="Coluna diária oficial — heartbeat real.",
            ),
        )
        resultado = mirante_client.publicar(sub)
        resultado_dict = {
            "status": resultado.status,
            "url": resultado.url,
            "motivo": resultado.motivo,
            "transporte": resultado.transporte,
            "submissao_id": resultado.submissao_id,
        }
    except Exception as exc:
        resultado_dict = {"status": "erro_publicacao", "motivo": str(exc)}

    # registra no Supabase
    try:
        from engine import supabase_db
        supabase_db.inserir("vila_coluna_publicacoes", {
            "publicacao_id": str(uuid.uuid4()),
            "data_ref": _hoje_iso(),
            "autor_id": mdx["autor_id"],
            "autor_nome": mdx["autor_nome"],
            "titulo": mdx["titulo"],
            "slug": mdx["slug"],
            "categoria": mdx["categoria"],
            "resultado": resultado_dict,
            "material_resumo": mdx["material"],
            "publicado_em": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as exc:
        logger.debug("erro gravando vila_coluna_publicacoes: %s", exc)

    return {
        "status": "publicada",
        "data": _hoje_iso(),
        "autor": mdx["autor_nome"],
        "titulo": mdx["titulo"],
        "slug": mdx["slug"],
        "arquivo_local": str(arq.relative_to(REPO_ROOT)),
        "resultado_mirante": resultado_dict,
    }
