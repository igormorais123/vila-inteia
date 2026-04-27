"""
Onda 120: feature comparison Vila vs outros multi-agent simulators.

Referências (publicados):
- Generative Agents (Park et al 2023 UIST): smallville, 25 NPCs
- OASIS (CAMEL-AI 2024): 1M agents social network
- MiroFish (Mar 2026): swarm intelligence, 1M target

Matrix de features booleanos + counts + citações.
"""

from __future__ import annotations


SIMULADORES = {
    "vila_inteia": {
        "nome": "Vila INTEIA",
        "publicacao": "Malheiros & Vasconcelos 2026",
        "ref": "github.com/igormorais123/vila-inteia",
        "n_agentes_max": 144,
        "agentes_lendarios_nomeados": True,
        "regras_arqueotipicas_hardcoded": True,
        "markov_psicohistoria": True,
        "calibracao_online_platt": True,
        "pearl_do_calculus": True,
        "louvain_communities": True,
        "game_theory_nash_nashpy": True,
        "opinion_dynamics_degroot_deffuant": True,
        "shapley_banzhaf": True,
        "backtest_real_events": True,
        "n_datasets_backtest": 10,
        "n_eventos_backtest": 100,
        "skill_score_positivo_vs_prior_humano": True,
        "reliability_diagram": True,
        "mirofish_style_pipeline_api": True,  # Onda 197
        "insights_emergentes_divergencia_personas": True,
        "relatorio_narrativo_executivo": True,
        "persona_chat_direto_user": True,
        "panel_chat_paralelo": True,
        "dashboard_d3_forcegraph": True,
        "sse_realtime_stream": True,
        "webhook_alerts": True,
        "auth_rate_limit": True,
        "mobile_responsive": True,
        "pdf_export": True,
        "supabase_persist": True,
        "deploy_render_docker_compose": True,
        "tour_onboarding": True,
        "cross_validation_holdout": True,
        "brier_score_decomposition_murphy": True,
        "bootstrap_ci": True,
        "vs_baselines_arima_markov_expsmooth": True,
        "codigo_fonte_aberto": True,
        "testes_ci_count": 700,
    },
    "generative_agents": {
        "nome": "Generative Agents",
        "publicacao": "Park et al 2023 UIST",
        "ref": "arxiv.org/abs/2304.03442",
        "n_agentes_max": 25,
        "agentes_lendarios_nomeados": False,
        "regras_arqueotipicas_hardcoded": False,
        "markov_psicohistoria": False,
        "calibracao_online_platt": False,
        "pearl_do_calculus": False,
        "louvain_communities": False,
        "game_theory_nash_nashpy": False,
        "opinion_dynamics_degroot_deffuant": False,
        "backtest_real_events": False,
        "persona_chat_direto_user": True,
        "dashboard_d3_forcegraph": False,
        "sse_realtime_stream": False,
        "codigo_fonte_aberto": True,
        "testes_ci_count": None,
    },
    "oasis": {
        "nome": "OASIS (CAMEL-AI)",
        "publicacao": "2024",
        "ref": "github.com/camel-ai/oasis",
        "n_agentes_max": 1_000_000,
        "agentes_lendarios_nomeados": False,
        "regras_arqueotipicas_hardcoded": False,
        "markov_psicohistoria": False,
        "calibracao_online_platt": False,
        "pearl_do_calculus": False,
        "louvain_communities": False,
        "backtest_real_events": False,
        "persona_chat_direto_user": False,
        "dashboard_d3_forcegraph": False,
        "codigo_fonte_aberto": True,
    },
    "mirofish": {
        "nome": "MiroFish",
        "publicacao": "2026-03",
        "ref": "github.com/666ghj/MiroFish",
        "n_agentes_max": 1_000_000,
        "agentes_lendarios_nomeados": False,
        "regras_arqueotipicas_hardcoded": False,
        "markov_psicohistoria": False,
        "calibracao_online_platt": False,
        "pearl_do_calculus": False,
        "louvain_communities": False,
        "backtest_real_events": False,
        "persona_chat_direto_user": True,  # post-sim chat
        "dashboard_d3_forcegraph": False,  # Vue.js
        "codigo_fonte_aberto": True,
    },
}


FEATURES_KEY = [
    "n_agentes_max",
    "agentes_lendarios_nomeados",
    "regras_arqueotipicas_hardcoded",
    "markov_psicohistoria",
    "calibracao_online_platt",
    "pearl_do_calculus",
    "louvain_communities",
    "game_theory_nash_nashpy",
    "opinion_dynamics_degroot_deffuant",
    "shapley_banzhaf",
    "backtest_real_events",
    "n_datasets_backtest",
    "n_eventos_backtest",
    "reliability_diagram",
    "mirofish_style_pipeline_api",
    "insights_emergentes_divergencia_personas",
    "relatorio_narrativo_executivo",
    "persona_chat_direto_user",
    "panel_chat_paralelo",
    "dashboard_d3_forcegraph",
    "sse_realtime_stream",
    "webhook_alerts",
    "auth_rate_limit",
    "mobile_responsive",
    "pdf_export",
    "supabase_persist",
    "deploy_render_docker_compose",
    "tour_onboarding",
    "cross_validation_holdout",
    "brier_score_decomposition_murphy",
    "bootstrap_ci",
    "vs_baselines_arima_markov_expsmooth",
    "codigo_fonte_aberto",
    "testes_ci_count",
]


def build_comparison() -> dict:
    """Retorna dict com matriz {simulador: {feature: value}} + diffs."""
    matriz = {}
    for sid, sim in SIMULADORES.items():
        matriz[sid] = {"nome": sim["nome"], "ref": sim["ref"]}
        for f in FEATURES_KEY:
            matriz[sid][f] = sim.get(f)

    # Count features exclusivas Vila
    vila = SIMULADORES["vila_inteia"]
    outros = ["generative_agents", "oasis", "mirofish"]
    exclusivas_vila = []
    for f in FEATURES_KEY:
        if not isinstance(vila.get(f), bool):
            continue
        if vila.get(f) is True:
            if all(not SIMULADORES[o].get(f, False) for o in outros):
                exclusivas_vila.append(f)

    return {
        "simuladores": matriz,
        "features_ordem": FEATURES_KEY,
        "features_exclusivas_vila": exclusivas_vila,
        "n_features_exclusivas": len(exclusivas_vila),
    }
