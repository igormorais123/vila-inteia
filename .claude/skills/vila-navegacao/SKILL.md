# Vila INTEIA — Navegacao do Projeto

> Mapa completo para encontrar qualquer coisa no projeto.

## Arquitetura

```
vila-inteia/
├── main.py                    # Entry point: CLI, API (FastAPI), Demo
├── config.py                  # ConfigSimulacao + ConfigCampus
├── data/
│   └── banco-consultores-lendarios.json  # 151 consultores, 100+ atributos
│
├── engine/                    # Motor de simulacao
│   ├── simulacao.py           # Orquestrador: steps, personas, gatilhos
│   ├── persona.py             # Agente individual (identidade + cognicao)
│   ├── campus.py              # 19 locais com conexoes e horarios
│   ├── rede_social.py         # Feed: posts, comentarios, reacoes, waves
│   ├── gatilhos.py            # 6 triggers + personagens especiais
│   ├── arquetipos.py          # Prompts profundos (6 camadas)
│   ├── ia_client.py           # OmniRoute + Anthropic fallback
│   ├── osa_bridge.py          # OSA (Signal Theory + Web Search)
│   ├── flockvote.py           # Pesquisa eleitoral sintetica
│   ├── cognitivo/             # Pipeline: perceber→recuperar→planejar→refletir→executar→conversar→sintetizar
│   └── memoria/               # fluxo (temporal) + espacial + rascunho
│
├── api/                       # FastAPI endpoints
│   ├── rotas_vila.py          # /api/v1/vila/* (simulacao, agentes, estado)
│   └── rotas_rede_social.py   # /api/v1/rede/* (feed, debate, provocar, parabola)
│
├── frontend/                  # HTML standalone (Three.js + vanilla JS)
│   ├── cidade.html            # Campus 3D (1552 linhas)
│   ├── index.html             # Dashboard principal (1103 linhas)
│   └── rede.html              # Rede social (647 linhas)
│
├── tests/
│   ├── test_bateria.py        # 69 testes (config, campus, memoria, persona, rede, gatilhos)
│   └── test_personagens.py    # 25 personagens + prompts + debates + reacoes
│
└── scripts/
    └── adicionar_lendarios.py # Adiciona consultores ao JSON
```

## Endpoints API

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | /api/v1/vila/iniciar | Inicializar simulacao |
| POST | /api/v1/vila/step | Executar N steps |
| GET | /api/v1/vila/estado | Snapshot do mundo |
| GET | /api/v1/vila/agentes | Listar agentes |
| POST | /api/v1/vila/topico | Injetar tema |
| GET | /api/v1/rede/feed | Feed social |
| POST | /api/v1/rede/tema | Publicar tema (Gatilho 1) |
| POST | /api/v1/rede/debate | Forcar debate rival |
| POST | /api/v1/rede/provocar | Diabob provoca |
| POST | /api/v1/rede/parabola | Jesus posta parabola |
| POST | /api/v1/rede/helena-sintese | Helena sintetiza |
| GET | /api/v1/rede/gatilhos/status | Status do motor |

## Como Rodar

```bash
# Dev local
python main.py serve --port 8100

# CLI
python main.py run --steps 100 --agentes 50

# Demo rapido
python main.py demo

# Testes
python tests/test_bateria.py
python tests/test_personagens.py
```

## Variaveis de Ambiente

| Variavel | Obrigatoria | Descricao |
|----------|-------------|-----------|
| OMNIROUTE_URL | Nao | Gateway LLM gratuito (default: localhost:20128) |
| OMNIROUTE_API_KEY | Nao | Chave OmniRoute |
| CLAUDE_API_KEY | Nao | Fallback Anthropic (custo por token) |
| IA_ALLOW_API_FALLBACK | Nao | Habilitar fallback (default: false) |
