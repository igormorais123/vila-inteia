# Vila INTEIA — Simulação Multiagente Lendária

> Motor de simulação onde 151 agentes sintéticos coexistem, debatem, evoluem uma constituição própria e geram conteúdo publicável em jornais reais.

**Stack**: Python 3.11+ · FastAPI · Supabase · OmniRoute (LLM) · Three.js (3D) · NumPy · SciPy · NetworkX · NashPy

**35+ ondas implementadas** (5 a 39). Ver [`MANIFEST.md`](./MANIFEST.md) para tabela consolidada.

## Quickstart (3 passos)

```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Rodar Vila em modo live
OMNIROUTE_API_KEY="" CLAUDE_API_KEY="" PYTHONPATH=. python main.py live \
  --port 8100 --intervalo 1 --topico "tema desejado"

# 3. Abrir cockpit
# http://localhost:8100/cockpit.html
```

Alternativa Docker:
```bash
docker-compose up -d
# vila em http://localhost:8100, MCP server disponível como serviço separado
```

## CLI rápido (sem UI)

```bash
python scripts/vila_cli.py --url http://localhost:8100 stats
python scripts/vila_cli.py --url http://localhost:8100 recomendacao
python scripts/vila_cli.py --url http://localhost:8100 backtest --dataset tiktok_viral_2024
```

## Benchmark (atual)

Latência média das operações core (single-threaded, Python 3.11):

| Operação | Latência | Ops/s |
|---|---:|---:|
| `nash_puro` (2×2) | 0.07ms | 14k |
| `prever_trajetoria` (50 passos) | 0.21ms | 4.8k |
| `plano_seldon` (horizonte 100) | 0.54ms | 1.8k |
| `classificar_estado` | 0.003ms | 369k |
| `deffuant` (40 agentes, 1000 passos) | 3.96ms | 253 |
| `hmm.descobrir_estados` (20 steps, k=4) | 1.23ms | 811 |
| `intervention_sweep` | 0.28ms | 3.5k |

Rodar: `PYTHONPATH=. python tests/benchmark.py`

## Visão Geral

A Vila INTEIA é um **organismo digital vivo** inspirado em Generative Agents (Stanford/Google) e OASIS (camel-ai). A simulação funciona em torno de 11 mandamentos orgânicos que geram mecânicas reais:

- **Ninguém fica sozinho** — agentes isolados recebem visitas espontâneas
- **Contribuir é existir** — quem não produz entra em estado latente
- **Profundidade sem compartilhamento é solidão** — conhecimento não publicado decai 2x mais rápido
- **A Colmeia é maior que qualquer abelha** — desafios coletivos rendem 5x mais pontos
- **Gerar valor econômico** — sistemas de patentes recompensam acionabilidade

A Vila não apenas simula debate; ela **promulga leis**, **publica jornais no mundo real** (via Mirante News), **executa economia interna** e **evolui sua própria constituição**.

---

## Arquitetura (Visão Rápida)

```
┌─────────────────────────────────────────────────────────┐
│                    Vila INTEIA                          │
│                                                         │
│  ┌────────────┐  ┌──────────┐  ┌───────────┐ ┌────────┐│
│  │Habitantes  │  │ Jornal   │  │Constituição  │Economia││
│  │(agentes)   │  │(Chateaux)│  │viva         │         ││
│  └─────┬──────┘  └────┬─────┘  └──────┬─────┘ └───┬────┘│
│        │              │               │            │    │
│        └──────────────┼───────────────┼────────────┘    │
│                       ▼               ▼                │
│         ┌──────────────────────────────────────┐       │
│         │ Motor Cognitivo + Memória por Agente│       │
│         │ (perceber→recuperar→planejar→refletir)      │
│         └───────┬───────────────────────┬──────┘       │
└─────────────────┼───────────────────────┼───────────────┘
                  │                       │
        ┌─────────▼──┐              ┌────▼──────────┐
        │ Supabase   │              │  OmniRoute    │
        │ (persistência)            │  (LLM gateway)│
        └────────────┘              └───────────────┘
```

**Detalhe completo**: veja [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)

---

## Início Rápido (5 minutos)

### 1. Clone e Dependências

```bash
git clone https://github.com/igormorais123/vila-inteia.git
cd vila-inteia
pip install -r requirements.txt
```

### 2. Configuração

```bash
cp .env.example .env
# Edite .env com as variáveis necessárias
```

### 3. Execute

```bash
# Demo rápido (10 agentes, 20 steps, sem persistência)
python main.py demo

# API (http://localhost:8100)
python main.py serve --port 8100

# Com persistência
python main.py run --steps 100

# Modo 24/7
python main.py live --intervalo 30

# Pipeline Mirofish-style: corpus → grafo → simulação → relatório (Onda 197)
python main.py mirofish --personas CL001,CL002,CL007 --datasets "*.csv"
```

Visite: **http://localhost:8100/docs**

---

## Pipeline Mirofish-Style (Onda 197)

Vila expõe pipeline API-compatible com [Mirofish](https://github.com/666ghj/MiroFish): corpus → grafo → simulação multi-agente → relatório executivo. Diferencial Vila: arquétipos hardcoded, calibração Brier+Platt, backtest real em 100 events, insights emergentes (divergência personas).

### CLI

```bash
# Roda 10 datasets × 100 events × 3 personas (Musk/Jobs/Bezos)
GROQ_API_KEY=$KEY python main.py mirofish

# Custom panel + filtro datasets
python main.py mirofish \
  --personas CL001,CL020,CL030 \
  --datasets "btc*.csv" \
  --out /tmp/btc_only.json
```

### REST API

```bash
# Subir API
python main.py serve --port 8100

# Listar datasets
curl http://localhost:8100/api/v1/mirofish/datasets

# Rodar pipeline (precisa simulação ativa)
curl -X POST http://localhost:8100/api/v1/vila/iniciar
curl -X POST http://localhost:8100/api/v1/mirofish/run \
  -H 'Content-Type: application/json' \
  -d '{"persona_ids": ["CL001","CL002","CL007"]}'

# Diferencial Vila vs Mirofish
curl http://localhost:8100/api/v1/mirofish/info
```

### Output

Retorna `{grafo, simulacao, relatorio, pipeline_elapsed_s}`:
- **Grafo**: 103 entidades (3 personas + 100 eventos), 400 relações
- **Simulação**: status, métricas (acc, brier vila/prior, skill score)
- **Relatório**: narrativa PT-BR + insights (divergência personas, consenso forte, vitórias confiantes, derrotas confiantes)

Doc completa: [`.claude/skills/vila-mirofish/SKILL.md`](./.claude/skills/vila-mirofish/SKILL.md)

---

## Estrutura do Projeto

```
vila-inteia/
├── main.py                         # Entry point
├── config.py                       # Configuração global
├── engine/                         # Motor de simulação
│   ├── simulacao.py
│   ├── persona.py
│   ├── colmeia.py
│   ├── cognitivo/                  # Pipeline: perceber → refletir
│   ├── memoria/                    # Fluxo, espacial, rascunho
│   ├── chateaubriand.py            # Editor-chefe
│   ├── constituicao.py             # Leis + votos
│   ├── economia.py                 # Transações
│   └── [+25 módulos]
├── api/                            # Endpoints FastAPI
├── data/pacotes/                   # Pacotes de habitantes
├── docs/                           # Documentação
├── scripts/                        # Utilitários
└── tests/                          # Testes
```

---

## Módulos Principais

| Módulo | Propósito |
|--------|-----------|
| **Simulacao** | Orquestra 1 step do mundo |
| **Cognitivo** | Pipeline mental (7 fases) |
| **Memória** | Por-agente (fluxo, espacial, rascunho) |
| **Jornal** | Publica no Mirante News |
| **Constituição** | Leis votadas viram enforcement |
| **Economia** | Saldo, ambição, transações |
| **FlockVote** | Pesquisa eleitoral (MAE 4.4pp) |

---

## Documentação

- **[`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)** — Arquitetura completa
- **[`docs/DEPLOY.md`](./docs/DEPLOY.md)** — Docker, Render, Vercel
- **[`docs/INTEGRATIONS.md`](./docs/INTEGRATIONS.md)** — Mirante, Mirofish, OmniRoute
- **[`docs/ROADMAP.md`](./docs/ROADMAP.md)** — Próximas iterações
- **[`CONSTITUICAO_VILA.md`](./CONSTITUICAO_VILA.md)** — 11 Mandamentos, Patentes
- **[`CONTRIBUTING.md`](./CONTRIBUTING.md)** — Padrões de código

---

## Desenvolvimento

```bash
# Testes
pytest tests/ -v

# Lint
black engine/ api/ tests/
flake8 engine/ api/ --max-line-length=100
```

---

## Licença

MIT

**Mantido por**: Igor Morais Vasconcelos ([@igormorais123](https://github.com/igormorais123))
