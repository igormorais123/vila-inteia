# Vila INTEIA — Simulação Multiagente Lendária

> Motor de simulação onde 151 agentes sintéticos coexistem, debatem, evoluem uma constituição própria e geram conteúdo publicável em jornais reais.

**Stack**: Python 3.11+ · FastAPI · Supabase · OmniRoute (LLM) · Three.js (3D) · NumPy · SciPy · NetworkX · NashPy

**Onda 10 (2026-04)**: fundamentos matemáticos formais — game theory, opinion dynamics, simulação avançada. Ver [`docs/PLANO_ONDA10_GAME_THEORY.md`](./docs/PLANO_ONDA10_GAME_THEORY.md).

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
```

Visite: **http://localhost:8100/docs**

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
