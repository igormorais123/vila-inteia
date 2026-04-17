# Vila INTEIA

Motor de simulação multiagente onde centenas de agentes sintéticos vivem,
debatem, publicam matérias no jornal externo (Mirante News), evoluem uma
constituição própria e operam uma economia interna. Inspirado em Generative
Agents (Stanford/Google) e OASIS (camel-ai).

**Stack**: Python 3.11+ · FastAPI · Supabase · OmniRoute (LLM) · Three.js (3D)

---

## Start rápido (5 minutos)

```bash
# 1. clone + deps
git clone https://github.com/igormorais123/vila-inteia.git
cd vila-inteia
pip install -r requirements.txt     # fastapi, uvicorn, requests

# 2. config
cp .env.example .env
# edite .env — preencha OMNIROUTE_URL + SUPABASE_VILA_URL + SUPABASE_VILA_KEY
#               + MIRANTE_API_URL + MIRANTE_API_TOKEN (se for publicar no Mirante)

# 3. sobe
python main.py serve --port 8100
# → http://localhost:8100/docs  (API FastAPI)
# → http://localhost:8100/       (frontend estático)

# 4. smoke test
python main.py demo               # 10 agentes, 20 steps, sem banco
```

---

## O que o sistema faz

| Capacidade | Módulo | Descrição |
|-----------|--------|-----------|
| **Simulação cognitiva** | `engine/cognitivo/` | perceber → recuperar → planejar → refletir → executar → conversar → sintetizar |
| **Memória por agente** | `engine/memoria/` | fluxo (eventos), espacial (onde esteve), rascunho (plano ativo) |
| **Economia viva** | `engine/economia.py` | saldo, ambição financeira, precificação de trabalho, transações |
| **Constituição viva** | `engine/constituicao.py` + `constituinte.py` + `executor_constitucional.py` | regras votadas viram enforcement automático; estruturais viram ticket pro dev |
| **Jornal da Vila** | `engine/chateaubriand.py` + `engine/mirante_client.py` | editor-chefe avalia/reescreve/publica no Mirante News |
| **Simulação de rede social** | `engine/mirofish_bridge.py` | delega grafos + simulação para o serviço Mirofish |
| **Save/Load de vilas** | `engine/save_load.py` | snapshot completo em Supabase, retomável depois |
| **Pacotes de habitantes** | `engine/pacotes_habitantes.py` + `data/pacotes/` | escolher que tipo de agente povoa a vila (eleitores, consultores, magistrados, …) |
| **Auto-research (Karpathy)** | `engine/autoresearch.py` | ciclo: gerar → avaliar → criticar → refinar → sintetizar |
| **Problem solving (27 técnicas)** | `engine/oficinas.py` | Van Aken & Berends — 6 fases, 27 técnicas |
| **FlockVote** | `engine/flockvote.py` | pesquisa eleitoral sintética; benchmark MAE 4.4pp no DF/2022 |

---

## Arquitetura (visão rápida)

```
┌──────────────────────────────────────────────────────────┐
│                      Vila INTEIA                         │
│                                                          │
│  ┌─────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Habitantes│  │ Jornal    │  │ Constitu-│  │ Economia │  │
│  │ (agentes) │  │ da Vila   │  │ ição viva│  │          │  │
│  └────┬────┘  └─────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │             │             │        │
│       ▼              ▼             ▼             ▼        │
│  ┌───────────────────────────────────────────────────┐   │
│  │          Motor cognitivo + memória                │   │
│  └────┬──────────────────────┬───────────────────────┘   │
│       │                       │                          │
│       │ (persistência)        │ (LLM)                    │
│       ▼                       ▼                          │
└───┬────────────────────┬──────────────────────────┬──────┘
    │                    │                          │
    ▼                    ▼                          ▼
┌────────┐         ┌──────────┐             ┌─────────────┐
│Supabase│         │OmniRoute │             │  Mirofish   │
│(dados) │         │ (LLM gtw)│             │ (rede social)
└────────┘         └──────────┘             └─────────────┘
                         │
                         ▼
                  ┌────────────────┐
                  │ Mirante News   │  ← Chateaubriand publica via
                  │ (mundo real)   │     POST /api/vila/submissoes
                  └────────────────┘
```

Detalhe por módulo em [`ARCHITECTURE.md`](./ARCHITECTURE.md).
Contratos com sistemas externos em [`INTEGRATIONS.md`](./INTEGRATIONS.md).

---

## Modos de execução

```bash
python main.py demo                 # 10 agentes, 20 steps, não persiste
python main.py run --steps 100      # CLI, persiste no Supabase
python main.py serve --port 8100    # API REST + frontend
python main.py live --intervalo 30  # 24/7: API + simulação contínua (1 step a cada 30s)
```

---

## Criar uma vila

Via API:

```bash
curl -X POST http://localhost:8100/api/v1/vila/instancias \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Simulação eleição DF 2026",
    "pacote_base": "eleitores-df-2015",
    "qtd_habitantes": 300,
    "objetivo": "Intenção de voto para governador"
  }'
```

Lista de pacotes disponíveis em [`data/pacotes/MANIFEST.md`](./data/pacotes/MANIFEST.md).

---

## Documentação

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — módulos por dentro
- [`INTEGRATIONS.md`](./INTEGRATIONS.md) — Mirante, Mirofish, OmniRoute, Supabase
- [`DEPLOY.md`](./DEPLOY.md) — Docker, Render, Vercel
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — padrões de código e commit
- [`ROADMAP.md`](./ROADMAP.md) — features Camada 2 (próximas iterações)
- [`FRAMEWORK_INTERACOES.md`](./FRAMEWORK_INTERACOES.md) — design das interações entre agentes
- [`docs/produto/`](./docs/produto/) — constituição, jornal, oficinas, etc.

---

## Licença

MIT.
