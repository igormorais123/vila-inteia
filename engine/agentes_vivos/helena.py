"""
Helena Strategos — Cientista-Chefe de Inteligência da INTEIA.

Vive na Vila (residência fixa: torre_estrategia), imune à dormência.
Heartbeat a cada 50 steps executa auditoria estratégica real:

    1. Coleta métricas do harness (saúde, traces, custo, falhas)
    2. Compara com OKRs declarados em HARNESS_VILA_FUNCIONAL §6
    3. Lê fragmentos do código-fonte quando precisa entender mudança
    4. Consulta Ficha do Fundador para alinhar prioridades
    5. Gera relatório estratégico em data/agentes_vivos/helena_strategos/
    6. Emite alertas se algum OKR estiver em risco
"""

from __future__ import annotations

from typing import Any

from .base import AgenteVivo


# OKRs declarados em HARNESS_VILA_FUNCIONAL.md §6 (mínimos)
OKRS_MINIMOS = {
    "traces_diarios": 10_000,
    "reducao_custo_llm_pct": 30,
    "clientes_copilot_ativos": 1,
    "simulacoes_decisionais_mes": 10,
    "artigos_academicos_submetidos": 1,
    "uptime_pct": 99.0,
}


class HelenaStrategos(AgenteVivo):
    id = "helena_strategos"
    nome = "Dra. Helena Strategos"
    papel = "Cientista-Chefe · Representa INTEIA e Fundador"
    intervalo_steps = 50

    def acoes(self, step: int, sim: Any = None) -> tuple[dict, list[str], list[str]]:
        acoes_exec: list[str] = []
        alertas: list[str] = []
        metricas: dict = {}

        # 1. Snapshot do harness
        harness = self.obter_harness_local()
        acoes_exec.append("audita_metricas_harness")
        metricas["harness"] = harness

        # 2. Ficha do Fundador
        ficha = self.obter_ficha_fundador()
        acoes_exec.append("consulta_ficha_fundador")
        metricas["fundador_carregado"] = bool(ficha.get("identificacao"))

        # 3. OKR tracking — só o que conseguimos medir agora
        okrs_estado = {}
        okrs_estado["traces_total"] = harness.get("total_traces", 0)
        okrs_estado["skills_registradas"] = harness.get("num_skills", 0)
        okrs_estado["capabilities_publicadas"] = harness.get("num_capabilities", 0)
        metricas["okrs"] = okrs_estado
        acoes_exec.append("verifica_okrs_funcional")

        # 4. Verifica presença de documentos-mestre (trinca HARNESS_VILA)
        docs = {
            "HARNESS_VILA.md": bool(self.ler_arquivo("HARNESS_VILA.md", 500)),
            "HARNESS_VILA_VIVENCIAL.md": bool(self.ler_arquivo("HARNESS_VILA_VIVENCIAL.md", 500)),
            "HARNESS_VILA_FUNCIONAL.md": bool(self.ler_arquivo("HARNESS_VILA_FUNCIONAL.md", 500)),
        }
        metricas["docs_mestre"] = docs
        acoes_exec.append("verifica_trinca_documentos")
        if not all(docs.values()):
            alertas.append("Falta pelo menos um dos 3 documentos-mestre do harness")

        # 5. Sanidade: tracing tem que estar on em produção
        if not harness.get("tracing_habilitado"):
            alertas.append("VILA_TRACE_ENABLED não está ligado — observabilidade comprometida")
        if not harness.get("supabase_conectado"):
            alertas.append("Supabase não conectado — traces e heartbeats não persistirão")

        # 6. Vigilância estratégica: custos e taxa de falha (via metricas supabase)
        try:
            from engine import supabase_db
            amostra = supabase_db.buscar("vila_traces", "order=inicio.desc&limit=500") or []
            falhas = [t for t in amostra if t.get("resultado") != "sucesso"]
            custo = sum(float(t.get("custo_usd") or 0) for t in amostra)
            taxa_falha = round(len(falhas) / len(amostra), 4) if amostra else 0.0
            metricas["ultimos_500_traces"] = {
                "amostra": len(amostra),
                "falhas": len(falhas),
                "taxa_falha": taxa_falha,
                "custo_usd_total": round(custo, 4),
            }
            acoes_exec.append("analisa_ultimos_500_traces")
            if taxa_falha > 0.05:
                alertas.append(f"Taxa de falha {taxa_falha*100:.1f}% nas últimas 500 execuções (limite: 5%)")
            if custo > 0 and custo < 0.0001:
                alertas.append("Custo reportado = 0 em 500 traces — captura de tokens/USD não instrumentada (E3 do audit)")
        except Exception as exc:
            alertas.append(f"Falha ao consultar vila_traces: {exc}")

        # 7. Gera parecer textual curto
        parecer = self._gerar_parecer(harness, okrs_estado, alertas)
        metricas["parecer"] = parecer
        acoes_exec.append("gera_parecer_estrategico")

        # 8. Onda 16: consulta Plano de Seldon para recomendação estratégica
        try:
            from engine.psicohistoria.decision_helper import relatorio_estrategico_helena
            rel_psico = relatorio_estrategico_helena()
            metricas["psico_historia"] = rel_psico
            acoes_exec.append("consulta_plano_seldon")
            if rel_psico.get("urgencia") in ("alta", "crítica"):
                alertas.append(
                    f"PSICO-HISTÓRIA {rel_psico['urgencia'].upper()}: "
                    f"{rel_psico['recomendacao']} (estado={rel_psico['estado']}, "
                    f"destino={rel_psico['destino']})"
                )
        except Exception as e:
            metricas["psico_historia_erro"] = str(e)

        return metricas, acoes_exec, alertas

    def _gerar_parecer(self, harness: dict, okrs: dict, alertas: list[str]) -> str:
        linhas = []
        linhas.append("PARECER HELENA — auditoria de heartbeat")
        traces = okrs.get("traces_total", 0)
        skills = okrs.get("skills_registradas", 0)
        caps = okrs.get("capabilities_publicadas", 0)
        linhas.append(f"  Inventário: {traces} traces, {skills} skills, {caps} capabilities.")
        if alertas:
            linhas.append("  ALERTAS:")
            for a in alertas:
                linhas.append(f"    - {a}")
        else:
            linhas.append("  Sem alertas estratégicos.")
        linhas.append("  Recomendação: priorizar gap de tokens/custo real e 1º cliente piloto (HARNESS_VILA_FUNCIONAL §6).")
        return "\n".join(linhas)


HELENA = HelenaStrategos()
