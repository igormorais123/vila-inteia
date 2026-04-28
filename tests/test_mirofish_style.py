"""Teste pipeline Mirofish-style (Onda 197)."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["GROQ_API_KEY"] = ""
os.environ["CLAUDE_API_KEY"] = ""
os.environ["OMNIROUTE_URL"] = ""

from engine.mirofish_style import (
    GrafoVila, SimulacaoVila, RelatorioVila,
    construir_grafo, rodar_simulacao, extrair_insights, gerar_relatorio,
    pipeline_completo,
)
from engine.persona import Persona
from engine.persona_chat import resetar_historico
from engine.backtest_real import carregar_dataset
import glob

REPO = str(Path(__file__).resolve().parent.parent)
PANEL = ["CL001", "CL002", "CL007"]

ok = fail = 0
def check(cond, msg):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {msg}")
    else: fail += 1; print(f"  FAIL {msg}")


def _load_sim():
    banco = json.load(open(f"{REPO}/data/banco-consultores-lendarios.json"))
    personas = {p["id"]: Persona(dados_consultor=p) for p in banco if p["id"] in PANEL}
    class _S:
        def __init__(self): self.personas = personas
    return _S()


def _make_llm_fn():
    """llm_fn determinístico: retorna 70% para quaisquer prompts."""
    contexto_to_ev = {}
    for f in sorted(glob.glob(f"{REPO}/data/backtest/*.csv")):
        for ev in carregar_dataset(f):
            contexto_to_ev[ev["contexto"]] = ev

    def fn(mensagens, system_prompt="", **kw):
        return "PROBABILIDADE FINAL: 70%"
    return fn


print("=== test_mirofish_style ===")
print("\n[1] Dataclasses iniciam com campos default")
g = GrafoVila(graph_id="g1")
check(g.total_entidades == 0, "GrafoVila default total_entidades=0")
check(g.status == "pronto", "GrafoVila default status=pronto")
s = SimulacaoVila(simulation_id="s1", graph_id="g1")
check(s.progresso == 0.0, "SimulacaoVila default progresso=0.0")
r = RelatorioVila(report_id="r1", graph_id="g1", simulation_id="s1")
check(r.insights == [], "RelatorioVila default insights=[]")

print("\n[2] construir_grafo conta entidades/relações corretamente")
sim = _load_sim()
paths = sorted(glob.glob(f"{REPO}/data/backtest/*.csv"))[:2]  # 2 datasets só
nomes = {pid: sim.personas[pid].nome_exibicao for pid in PANEL}
grafo = construir_grafo(paths, PANEL, nomes)
# 2 datasets × 10 eventos = 20, + 3 personas = 23 entidades
check(grafo.total_entidades == 23, f"grafo entidades=23 got {grafo.total_entidades}")
# 20 eventos × 3 personas + 20 event-dataset = 80
check(grafo.total_relacoes == 80, f"grafo relacoes=80 got {grafo.total_relacoes}")
check(len(grafo.datasets) == 2, "grafo.datasets len=2")
check(grafo.personas[0]["nome"] == "Elon Musk", "persona[0] nome Musk")

print("\n[3] rodar_simulacao retorna status concluida + métricas")
resetar_historico()
simulacao, per_event, per_dataset = rodar_simulacao(
    grafo, paths, PANEL, sim, llm_fn=_make_llm_fn()
)
check(simulacao.status == "concluida", "sim status=concluida")
check(simulacao.steps_executados == 20 * 3, "steps = 60")
check(len(per_event) == 20, "per_event len=20")
check(len(per_dataset) == 2, "per_dataset len=2")
check(simulacao.resultado["brier_vila_avg"] is not None, "brier_vila_avg != None")

print("\n[4] extrair_insights produz 4 tipos")
insights = extrair_insights(per_event, top_k=3)
check(len(insights) == 4, f"4 tipos, got {len(insights)}")
tipos = {i["tipo"] for i in insights}
esperado = {"divergencia_personas", "consenso_forte", "vitoria_confiante", "derrota_confiante"}
check(tipos == esperado, f"tipos corretos: {tipos == esperado}")

print("\n[5] gerar_relatorio produz narrativa + metricas")
rel = gerar_relatorio(grafo, simulacao, per_event, per_dataset, insights, nomes, PANEL)
check(len(rel.conteudo) > 200, f"narrativa > 200 chars (got {len(rel.conteudo)})")
check("Vila INTEIA" in rel.conteudo, "narrativa menciona Vila INTEIA")
check("skill score" in rel.conteudo.lower(), "narrativa menciona skill score")
check(rel.metricas == simulacao.resultado, "metricas == sim.resultado")

print("\n[6] pipeline_completo end-to-end")
resetar_historico()
out = pipeline_completo(
    base_dir=f"{REPO}/data/backtest", dataset_glob="*.csv",
    persona_ids=PANEL, sim=sim, llm_fn=_make_llm_fn(),
)
check("grafo" in out and "simulacao" in out and "relatorio" in out,
      "out tem 3 sections")
check(out["simulacao"]["steps_executados"] == 120 * 3, "120 events × 3 personas = 360 steps (Onda 231 post-cutoff v1+v2)")
check(out["pipeline_elapsed_s"] > 0, "elapsed > 0")
check("insights" in out["relatorio"], "relatorio tem insights")

print("\n[7] pipeline_completo handles missing sim")
out_err = pipeline_completo(base_dir="/nope", dataset_glob="*.csv", persona_ids=PANEL, sim=None)
check("erro" in out_err, "sim=None retorna erro")

print(f"\n{ok} ok, {fail} fail")
sys.exit(0 if fail == 0 else 1)
