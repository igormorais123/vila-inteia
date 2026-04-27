---
name: vila-mirofish
description: Pipeline Mirofish-style — corpus → grafo → simulação → relatório. Como rodar, debugar, estender.
---

# Vila INTEIA — Pipeline Mirofish-Style (Onda 197)

> Wrapper sobre `engine/backtest_real` que expõe API-compatible com Mirofish.
> Diferencial: Vila adiciona arquétipos hardcoded + Brier+Platt calib + insights emergentes.

## Componentes

| Arquivo | Responsabilidade |
|---|---|
| `engine/mirofish_style.py` | Pipeline core + dataclasses (`GrafoVila`, `SimulacaoVila`, `RelatorioVila`) |
| `api/rotas_mirofish.py` | 3 endpoints REST: `POST /run`, `GET /datasets`, `GET /info` |
| `tests/test_mirofish_style.py` | 24 testes cobrindo dataclasses + pipeline + edge cases |
| `main.py:modo_mirofish` | CLI: `python main.py mirofish` |

## Pipeline (4 fases)

```
[1] construir_grafo()    → corpus → entidades + relações
[2] rodar_simulacao()    → backtest Vila com llm_fn
[3] extrair_insights()   → 4 tipos: divergência, consenso, wins, losses
[4] gerar_relatorio()    → narrativa PT-BR + métricas + insights
```

`pipeline_completo()` orquestra tudo. Retorna dict `{grafo, simulacao, relatorio, pipeline_elapsed_s}`.

## Como rodar

### CLI

```bash
# default: 10 datasets × 100 events × 3 personas (Musk/Jobs/Bezos)
python main.py mirofish

# custom personas + filtro datasets
python main.py mirofish --personas CL001,CL020,CL030 --datasets "btc*.csv" --out /tmp/btc_only.json
```

Requer `GROQ_API_KEY` ou `CLAUDE_API_KEY` configurado pra LLM real. Sem chave, predições retornam None.

### API REST

```bash
# Subir API
python main.py serve --port 8100

# Listar datasets disponíveis
curl http://localhost:8100/api/v1/mirofish/datasets

# Rodar pipeline (requer simulação ativa via /api/v1/vila/iniciar)
curl -X POST http://localhost:8100/api/v1/mirofish/run \
  -H 'Content-Type: application/json' \
  -d '{"persona_ids": ["CL001","CL002","CL007"], "dataset_glob": "*.csv"}'

# Info diferencial vs Mirofish
curl http://localhost:8100/api/v1/mirofish/info
```

### Programático (injetando llm_fn custom)

```python
from engine.mirofish_style import pipeline_completo

def my_llm_fn(mensagens, system_prompt="", **kw):
    return "PROBABILIDADE FINAL: 70%"

class _Sim:
    def __init__(self): self.personas = {...}  # dict de Persona objects

out = pipeline_completo(
    base_dir="data/backtest",
    persona_ids=["CL001", "CL002", "CL007"],
    sim=_Sim(),
    llm_fn=my_llm_fn,
)
```

## Output Schema

```json
{
  "grafo": {
    "graph_id": "vila-1234",
    "total_entidades": 103,
    "total_relacoes": 400,
    "schema": {"nodos": [...], "arestas": [...]},
    "datasets": [...],
    "personas": [...]
  },
  "simulacao": {
    "simulation_id": "sim-1234",
    "status": "concluida",
    "steps_executados": 300,
    "elapsed_s": 0.034,
    "resultado": {
      "acc_total": 0.92,
      "brier_vila_avg": 0.0822,
      "brier_prior_avg": 0.1455,
      "skill_brier_vs_prior": 0.435
    }
  },
  "relatorio": {
    "report_id": "rep-1234",
    "titulo": "Vila INTEIA Predictions — 100 events, 10 datasets",
    "conteudo": "...narrativa PT-BR...",
    "metricas": {...},
    "per_dataset": [...],
    "insights": [
      {"tipo": "divergencia_personas", "items": [...]},
      {"tipo": "consenso_forte", "items": [...]},
      {"tipo": "vitoria_confiante", "items": [...]},
      {"tipo": "derrota_confiante", "items": [...]}
    ]
  },
  "pipeline_elapsed_s": 0.034
}
```

## Diferencial Vila vs Mirofish original

| Feature | Vila | Mirofish |
|---|---|---|
| Pipeline corpus→graph→sim→report | ✓ | ✓ |
| Multi-agent simulation | 144 lendários | 1M swarm |
| Arquétipos hardcoded | ✓ | ✗ |
| Brier+Platt calibration | ✓ | ✗ |
| Backtest real (100 events) | ✓ | ✗ |
| Skill score vs prior humano | ✓ | ✗ |
| Insights emergentes (divergência personas) | ✓ | ✗ |
| Grafo conhecimento OASIS | ✗ | ✓ |
| Vue.js dashboard | ✗ | ✓ |
| Escala 1M agentes | ✗ | ✓ |

Vila ganha em rigor científico. Mirofish ganha em escala + viz.

## Debug comum

**`acc=0/100, brier=None`**: LLM offline. Configure `GROQ_API_KEY` ou injete `llm_fn` custom.

**`SIM_GLOBAL não inicializada`** (endpoint /run): rode `POST /api/v1/vila/iniciar` antes.

**`personas não encontradas`**: IDs devem existir em `data/banco-consultores-lendarios.json`.

**`brier_prior=None`**: dataset sem coluna `probabilidade_prior` ou todos prior=0.

## Estender

- **Novo insight type**: editar `extrair_insights()` em `engine/mirofish_style.py:158-201`
- **Nova fase pipeline**: adicionar função + chamar em `pipeline_completo()`
- **LLM-generated narrativa**: trocar `gerar_relatorio()` heurístico por `chamar_llm()` com prompt do payload
- **Persistir relatórios**: adicionar `save_to_supabase()` salvando em `vila_mirofish_relatorios`

## Testes

```bash
GROQ_API_KEY='' CLAUDE_API_KEY='' python tests/test_mirofish_style.py
```

24 testes cobrindo: dataclasses defaults, construir_grafo counts, rodar_simulacao status, extrair_insights tipos, gerar_relatorio narrativa, pipeline_completo end-to-end, error handling.
