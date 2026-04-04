# Vila INTEIA — Think Tank Vivo com Agentes de IA

Uma simulação multi-agente onde **146 consultores lendários** (Elon Musk, Warren Buffett, Sócrates, Marie Curie, Sun Tzu...) vivem em um campus virtual, conversam entre si, debatem, refletem e produzem insights coletivos usando Large Language Models.

## O que é

A Vila INTEIA é um laboratório de inteligência coletiva artificial. Agentes com personalidades distintas, áreas de expertise e estilos de pensamento interagem autonomamente em um campus com 19 locais (Ágora, Torre de Estratégia, Laboratório, Café dos Filósofos, Arena de Debates...).

Cada agente possui:
- **Cognição completa**: Perceber → Recuperar → Planejar → Refletir → Executar → Conversar → Sintetizar
- **Memória**: Fluxo (curto prazo), Espacial (mapa do campus), Rascunho (estado atual)
- **Personalidade**: 100 campos por consultor (biografia, expertise, frases icônicas, estilo de pensamento)
- **Economia**: Moeda interna (Xi/Ξ), transações por contribuição

## Auto-Research (Karpathy Loop)

Inspirado no conceito de **auto-aprimoramento** de Andrej Karpathy — o sistema não dá apenas uma resposta, mas **itera sobre ela** até atingir qualidade suficiente.

```
┌─────────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌───────────┐    ┌────────────┐
│  GERAR  │───▶│ AVALIAR │───▶│ CRITICAR │───▶│ REFINAR │───▶│ SINTETIZAR│───▶│ META-SCORE │
│ N agents│    │score 0-10│   │ top critic│   │ next iter│   │  combine  │    │ >= 8? STOP │
└─────────┘    └─────────┘    └──────────┘    └─────────┘    └───────────┘    └──────┬─────┘
                                                                                     │ < 8
                                                                                     ▼
                                                                              ┌─────────────┐
                                                                              │  LOOP AGAIN  │
                                                                              └─────────────┘
```

**Como funciona:**
1. **Gerar**: 5 consultores produzem respostas independentes à pergunta
2. **Avaliar**: Um avaliador pontua cada resposta de 0-10 (Especificidade, Acionabilidade, Originalidade, Fundamentação)
3. **Criticar**: Um crítico aponta a principal falha de cada top resposta
4. **Refinar**: Na próxima iteração, consultores recebem as críticas e melhoram
5. **Sintetizar**: As melhores ideias são combinadas em uma resposta coesa
6. **Meta-Avaliar**: A síntese recebe um score. Se >= threshold, para. Senão, repete.

**Endpoint:**
```bash
curl -X POST http://localhost:8090/api/v1/vila/auto-research \
  -H "Content-Type: application/json" \
  -d '{
    "pergunta": "Qual a melhor estratégia de precificação para SaaS jurídico no Brasil?",
    "n_consultores": 5,
    "max_iterations": 3,
    "quality_threshold": 8.0
  }'
```

**Resposta inclui**: score por iteração, delta de melhoria, respostas individuais scored, críticas, síntese final com score, flag de convergência, tempo total.

O score tipicamente sobe 1-2 pontos entre iteração 1 e 3, com as críticas eliminando generalizações e forçando especificidade.

## Ferramentas Disponíveis

| Ferramenta | Endpoint | O que faz |
|---|---|---|
| **Auto-Research** | `POST /api/v1/vila/auto-research` | Loop iterativo Gerar→Avaliar→Criticar→Refinar→Sintetizar |
| **Briefing Executivo** | `GET /api/v1/vila/briefing` | Resumo IA do que os consultores discutem |
| **Consultar Painel** | `POST /api/v1/vila/consulta` | Pergunta livre → N consultores respondem |
| **Chat 1:1** | `POST /api/v1/vila/chat` | Conversa direta com qualquer consultor |
| **SWOT** | `POST /api/v1/vila/oficinas/{id}/executar` | Análise SWOT com 5 consultores |
| **Design Sprint** | `POST /api/v1/vila/desafio/iniciar` + `/avancar` | 5 fases, 5 agentes por fase |
| **Teoria dos Jogos** | Via oficinas | Análise estratégica |
| **Monte Carlo** | Via oficinas | Simulação probabilística |
| **Síntese Coletiva** | `POST /api/v1/vila/sintetizar/{topico}` | Convergência de perspectivas |

## Arquitetura

```
vila_inteia/
├── engine/                    # Motor cognitivo
│   ├── simulacao.py           # Orquestrador principal
│   ├── persona.py             # Agente com personalidade
│   ├── campus.py              # 19 locais interconectados
│   ├── ia_client.py           # Cliente LLM (OpenAI-compatible)
│   ├── cognitivo/             # 7 módulos cognitivos
│   │   ├── perceber.py        # Percepção do ambiente
│   │   ├── recuperar.py       # Busca em memória
│   │   ├── planejar.py        # Planejamento de ações
│   │   ├── refletir.py        # Reflexão metacognitiva
│   │   ├── executar.py        # Execução de ações
│   │   ├── conversar.py       # Diálogos entre agentes
│   │   └── sintetizar.py      # Síntese coletiva
│   ├── memoria/               # 3 sistemas de memória
│   │   ├── fluxo.py           # Memória de curto prazo
│   │   ├── espacial.py        # Memória do campus
│   │   └── rascunho.py        # Estado atual do agente
│   ├── auto_research.py       # Auto-Research Loop (Karpathy)
│   ├── rede_social.py         # Rede social entre agentes
│   └── gatilhos.py            # Motor de eventos
├── api/                       # API REST (FastAPI)
│   ├── rotas_vila.py          # Endpoints principais
│   ├── rotas_extras.py        # Oficinas, economia, briefing
│   └── rotas_rede_social.py   # Rede social
├── frontend/                  # 7 interfaces visuais
│   ├── index.html             # Mapa 2D interativo (principal)
│   ├── portal.html            # Portal unificado com 5 abas
│   ├── cidade.html            # Cidade 3D (Three.js)
│   ├── rede.html              # Rede social dos agentes
│   ├── jogo.html              # Assembleia deliberativa
│   └── constituicao.html      # Constituição da Vila
├── config.py                  # Configuração
└── serve.py                   # Entrypoint uvicorn
```

## Quick Start

### Com Docker (recomendado)

```bash
git clone https://github.com/igormorais123/Vila-INTEIA.git
cd Vila-INTEIA
cp .env.example .env
# Edite .env com sua API key de um provedor OpenAI-compatible
docker compose up -d
# Acesse http://localhost:8090
```

### Sem Docker

```bash
pip install fastapi uvicorn pandas numpy scipy scikit-learn openai networkx tiktoken sse-starlette
export OMNIROUTE_API_KEY="sua-chave-openai-ou-compatible"
export OMNIROUTE_URL="https://api.openai.com"  # ou qualquer OpenAI-compatible
cd vila_inteia
uvicorn serve:app --host 0.0.0.0 --port 8090
```

## Populações Sintéticas Incluídas

| Banco | Quantidade | Uso |
|---|---|---|
| Consultores Lendários | 146 | Think tank principal |
| Parlamentares Brasil | 594 | Simulação legislativa |
| Magistrados (STF, STJ, TJDFT, TRF1) | 164 | Predição judicial |
| Deputados Distritais DF | ~24 | Análise regional |
| Deputados Federais DF | ~8 | Análise regional |
| Senadores | ~81 | Análise legislativa |

## Referências Acadêmicas

Este projeto implementa conceitos de:
- **Karpathy Self-Play / Auto-Improvement** (2024) — Loop iterativo onde agentes geram, avaliam, criticam e refinam respostas autonomamente. Score sobe a cada iteração via crítica cruzada.
- **Generative Agents** (Park et al., 2023) — Agentes com memória e reflexão
- **Smallville** — Simulação de vila com agentes autônomos
- **Constitutional AI** (Anthropic, 2022) — Auto-avaliação e auto-correção
- **Debate** (Irving et al., 2018) — Agentes que melhoram respostas via debate adversarial
- **FlockVote** — Votação coletiva por agentes sintéticos
- **Teoria dos Jogos Computacional** — Interações estratégicas
- **Design Sprint** (Google Ventures) — Processo de inovação em 5 fases

## Licença

MIT License — Use, modifique e distribua livremente.

## Autor

Desenvolvido por **Igor Morais Vasconcelos** — [INTEIA](https://inteia.com.br)
Doutorando em Administração Pública (IDP/Brasília)
