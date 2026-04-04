<div align="center">

# 🏛️ Vila INTEIA — Campus 3D

### Think Tank Vivo com 144 Consultores Lendários Simulados por IA

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Three.js](https://img.shields.io/badge/Three.js-r128-000000?style=flat-square&logo=three.js&logoColor=white)](https://threejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-d69e2e?style=flat-square)](LICENSE)

*Um campus virtual onde as maiores mentes da história debatem, colaboram e geram inteligência coletiva em tempo real.*

[Campus 3D](#campus-3d) · [Arquitetura](#arquitetura) · [Como Rodar](#como-rodar) · [Documentação](#documentação)

</div>

---

## O que é

A **Vila INTEIA** é um motor de simulação social onde **144 consultores lendários** — estrategistas, juristas, tecnólogos, visionários — vivem em um campus virtual 3D. Cada agente possui:

- **Memória** (fluxo, espacial, rascunho) — lembram conversas, locais e planos
- **Pipeline cognitivo** — perceber → recuperar → planejar → refletir → executar → conversar
- **Personalidade** — 100+ atributos extraídos de figuras históricas reais
- **Rotina diária** — acordam, trabalham, almoçam, debatem e dormem

Os agentes interagem entre si usando Large Language Models via [OmniRoute](https://github.com/igormorais123/Vila-INTEIA) (custo zero), gerando conversas, debates, reflexões e insights coletivos emergentes.

## Campus 3D

O frontend renderiza o campus completo em **Three.js** com 19 edifícios interativos:

| Edifício | Função |
|----------|--------|
| Torre de Estratégia | Planejamento e análise de cenários |
| Laboratório de Ideias | Pesquisa e prototipação |
| Arena de Debates | Confronto de ideias e argumentação |
| Tribunal da Razão | Análise jurídica e ética |
| Ágora Central | Encontros espontâneos e networking |
| Biblioteca Infinita | Pesquisa e reflexão profunda |
| Observatório do Futuro | Projeções e cenários de longo prazo |
| Ateliê dos Artesãos | Criação de narrativas e marcas |
| Café dos Filósofos | Conversas informais e insights |
| Sala de Guerra | Simulações táticas |
| Auditório INTEIA | Apresentações e palestras |
| Refeitório Central | Encontros obrigatórios, almoço e jantar |
| Jardim dos Visionários | Contemplação e ideação |
| Terraço Panorâmico | Networking ao fim do dia |
| Residências (4 blocos) | Norte, Sul, Leste, Oeste |

**Controles da câmera:**
- `Arrastar` — Rotacionar
- `Scroll` — Zoom
- `Shift+Arrastar` — Pan
- `W/A/S/D` — Mover câmera
- `R` — Reset
- `Espaço` — Pausar/retomar simulação
- `Duplo-clique` — Voar até edifício

## Arquitetura

```
vila-inteia/
├── main.py                    # Entry point (CLI, API, Demo)
├── config.py                  # Configuração da simulação
│
├── engine/                    # Motor de simulação
│   ├── simulacao.py           # Orquestrador principal
│   ├── persona.py             # Agente inteligente (100+ atributos)
│   ├── campus.py              # Mapa do campus (19 locais)
│   ├── ia_client.py           # Cliente LLM via OmniRoute
│   ├── osa_bridge.py          # Integração OSA (Signal Theory)
│   ├── flockvote.py           # Pesquisa eleitoral sintética
│   ├── rede_social.py         # Rede social entre agentes
│   │
│   ├── cognitivo/             # Pipeline cognitivo do agente
│   │   ├── perceber.py        # Percepção do ambiente
│   │   ├── recuperar.py       # Recuperação de memória
│   │   ├── planejar.py        # Planejamento de ações
│   │   ├── refletir.py        # Auto-reflexão
│   │   ├── executar.py        # Execução de ações
│   │   ├── conversar.py       # Diálogos entre agentes
│   │   └── sintetizar.py      # Síntese de insights
│   │
│   └── memoria/               # Sistema de memória
│       ├── fluxo.py           # Memória de fluxo (eventos)
│       ├── espacial.py        # Memória espacial (onde esteve)
│       └── rascunho.py        # Scratchpad (planos ativos)
│
├── api/                       # API REST
│   ├── rotas_vila.py          # Endpoints da simulação
│   └── rotas_rede_social.py   # Endpoints da rede social
│
├── frontend/                  # Interface web
│   ├── cidade.html            # Campus 3D (Three.js)
│   ├── index.html             # Dashboard principal
│   └── rede.html              # Visualização da rede social
│
├── data/                      # Dados persistidos
└── FRAMEWORK_INTERACOES.md    # Design doc do sistema de interações
```

## Como Rodar

### Requisitos

- Python 3.11+
- OmniRoute rodando (ou qualquer endpoint OpenAI-compatible)

### Instalação

```bash
git clone https://github.com/igormorais123/Vila-INTEIA.git
cd vila-inteia
pip install -r requirements.txt  # se existir, ou instale dependências manualmente
```

### Modos de Execução

```bash
# CLI — roda simulação no terminal
python -m vila-inteia.main --steps 100

# CLI com tópico injetado
python -m vila-inteia.main --steps 50 --topico "Impacto da IA no mercado jurídico"

# API — sobe servidor REST
python -m vila-inteia.main --serve

# Demo — roda demonstração rápida
python -m vila-inteia.main --demo
```

### Frontend

Abra `frontend/cidade.html` diretamente no navegador para o Campus 3D, ou `frontend/index.html` para o dashboard de simulação.

### Configuração

Edite `config.py` ou use variáveis de ambiente:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OMNIROUTE_URL` | `http://localhost:20128` | Endpoint do gateway LLM |
| `OMNIROUTE_API_KEY` | — | Chave de API |
| `OSA_URL` | `http://localhost:8089` | Endpoint do OSA |

## FlockVote Lite

Módulo integrado de **pesquisa eleitoral sintética** baseado nos papers FlockVote (ICAIS 2025) e "Donald Trumps in Virtual Polls" (Wuhan University).

- 1015 eleitores sintéticos do DF com 38 atributos demográficos
- Calibração: `resultado_final = h × histórico + (1-h) × LLM`
- **Benchmark 2022 DF:** MAE 4.4pp — previu corretamente Ibaneis e Grass
- Custo zero via OmniRoute

## Inspiração

Baseado nos conceitos de [Generative Agents](https://arxiv.org/abs/2304.03442) (Stanford/Google) e [OASIS](https://github.com/camel-ai/oasis), adaptado para o contexto brasileiro de simulação político-eleitoral e consultoria estratégica.

## Sobre a INTEIA

A [INTEIA](https://inteia.com.br) é um think tank de inteligência artificial aplicada a estratégia, política e direito. A Vila INTEIA é o laboratório vivo onde agentes sintéticos debatem cenários reais.

---

<div align="center">

**Desenvolvido por [Igor Morais Vasconcelos](https://github.com/igormorais123)**

*INTEIA — Inteligência Artificial Estratégica*

</div>
