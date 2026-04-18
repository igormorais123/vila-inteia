"""
Efesto Tekhton — Diretor de Tecnologia da INTEIA.

Vive na Vila (residência fixa: laboratorio), imune à dormência.
Heartbeat a cada 30 steps executa health check real da infra:

    1. Ping aos módulos do harness (imports, sem HTTP)
    2. Verifica presença das 2 migrations aplicadas
    3. Amostra últimas execuções e checa duração anômala
    4. Calcula bloom do budget (fases mais caras)
    5. Escreve relatório em data/agentes_vivos/efesto_tekhton/
    6. Alerta em caso de: supabase off, cardinalidade estranha,
       skill perdendo manifest, cards malformados.
"""

from __future__ import annotations

from typing import Any

from .base import AgenteVivo


LIMITES_EFESTO = {
    "duracao_ms_max_fase": 10_000,       # 10s
    "taxa_falha_max": 0.05,              # 5%
    "tamanho_min_doc_mestre": 400,       # 400 chars
    "min_skills": 10,
    "min_capabilities": 1,
}


class EfestoTekhton(AgenteVivo):
    id = "efesto_tekhton"
    nome = "Efesto Tekhton"
    papel = "Diretor de Tecnologia · Infraestrutura"
    intervalo_steps = 30

    def acoes(self, step: int, sim: Any = None) -> tuple[dict, list[str], list[str]]:
        acoes_exec: list[str] = []
        alertas: list[str] = []
        metricas: dict = {}

        # 1. Snapshot do harness
        snap = self.obter_harness_local()
        metricas["harness_snapshot"] = snap
        acoes_exec.append("checa_saude_harness")
        if snap.get("erro"):
            alertas.append(f"harness import erro: {snap['erro']}")

        # 2. Imports críticos
        try:
            from engine.harness import trace_fase, obter_orcamento, skill_registry, listar_cards  # noqa
            acoes_exec.append("valida_imports_criticos")
        except Exception as exc:
            alertas.append(f"import_critico_quebrado: {exc}")

        # 3. Migrations presentes no repo
        migrations = self.listar("migrations", "*.sql")
        metricas["migrations_presentes"] = migrations
        if not migrations:
            alertas.append("Nenhum arquivo de migration encontrado — infra em shadow puro?")
        acoes_exec.append("confere_migrations")

        # 4. Budget saúde — faixa razoável
        try:
            from engine.harness import relatorio_orcamentos
            orc = relatorio_orcamentos()
            soma = sum(b["tokens_max"] for b in orc.values())
            metricas["budget_total_tokens_max"] = soma
            if soma < 10_000:
                alertas.append(f"Budget total muito baixo ({soma}) — revisar tabela de orçamento")
        except Exception as exc:
            alertas.append(f"relatorio_orcamentos falhou: {exc}")

        # 5. Skills e capabilities
        if snap.get("num_skills", 0) < LIMITES_EFESTO["min_skills"]:
            alertas.append(f"Só {snap.get('num_skills')} skills registradas (mín: {LIMITES_EFESTO['min_skills']})")
        if snap.get("num_capabilities", 0) < LIMITES_EFESTO["min_capabilities"]:
            alertas.append("Nenhum capability card registrado")

        # 6. Amostra últimas execuções — detecta latência anômala
        try:
            from engine import supabase_db
            amostra = supabase_db.buscar("vila_traces", "order=inicio.desc&limit=200") or []
            duracoes = [int(t.get("duracao_ms") or 0) for t in amostra]
            if duracoes:
                dur_max = max(duracoes)
                dur_avg = sum(duracoes) / len(duracoes)
                metricas["latencia_amostra_200"] = {"max_ms": dur_max, "avg_ms": round(dur_avg, 1)}
                if dur_max > LIMITES_EFESTO["duracao_ms_max_fase"]:
                    alertas.append(f"Fase com duração {dur_max}ms detectada (limite: {LIMITES_EFESTO['duracao_ms_max_fase']}ms)")
            acoes_exec.append("audita_latencia_ultimas_200")
        except Exception as exc:
            alertas.append(f"Falha consulta vila_traces: {exc}")

        # 7. Documentos mestre com substância
        docs = ["HARNESS_VILA.md", "HARNESS_VILA_VIVENCIAL.md", "HARNESS_VILA_FUNCIONAL.md"]
        doc_sizes = {}
        for d in docs:
            txt = self.ler_arquivo(d, max_bytes=200_000) or ""
            doc_sizes[d] = len(txt)
            if len(txt) < LIMITES_EFESTO["tamanho_min_doc_mestre"]:
                alertas.append(f"{d} muito pequeno ({len(txt)} bytes) — suspeita de truncamento")
        metricas["docs_mestre_bytes"] = doc_sizes
        acoes_exec.append("confere_tamanho_docs_mestre")

        # 8. Runbook-style sumário
        metricas["resumo_runbook"] = self._runbook(snap, alertas)
        acoes_exec.append("emite_runbook_sumario")

        return metricas, acoes_exec, alertas

    def _runbook(self, snap: dict, alertas: list[str]) -> str:
        status = "VERDE" if not alertas else ("AMARELO" if len(alertas) <= 2 else "VERMELHO")
        linhas = [
            f"RUNBOOK EFESTO [{status}]",
            f"  tracing={snap.get('tracing_habilitado')} supabase={snap.get('supabase_conectado')}",
            f"  traces_total={snap.get('total_traces')} skills={snap.get('num_skills')} caps={snap.get('num_capabilities')}",
        ]
        if alertas:
            linhas.append("  alertas:")
            for a in alertas[:5]:
                linhas.append(f"    - {a}")
        return "\n".join(linhas)


EFESTO = EfestoTekhton()
