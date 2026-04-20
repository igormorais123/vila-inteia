# Onda 10 — Game Theory + Opinion Dynamics + Simulação Avançada

**Branch**: `onda-game-theory-sim-upgrade`
**Criado**: 2026-04-20
**Status**: skeleton proposto, aguarda aprovação

## 1. Motivação

Vila INTEIA atualmente usa heurísticas + LLM para comportamento dos agentes. Falta fundamentação matemática em três áreas clássicas de modelagem social/estratégica:

1. **Game Theory**: agentes tomam decisões estratégicas sem modelar payoff/equilíbrio formalmente
2. **Opinion Dynamics**: convergência/divergência de crenças é só emergente de LLM, sem modelo analítico
3. **Simulação avançada**: campus é grafo simples de locais, sem física, sem coalizões formais, sem segregação espacial

Esta Onda adiciona fundamentos formais que coexistem com o pipeline cognitivo existente — agentes passam a consultar solvers matemáticos em fases críticas (planejamento estratégico, conversa com atualização bayesiana de crença, formação de aliança).

Benefício: decisões auditáveis, reprodutíveis, e comparáveis contra literatura acadêmica. Fecha gap de credibilidade vs MiroFish (que usa OASIS/CAMEL-AI publicado em peer review).

## 2. Escopo

### 2.1 Game Theory (`engine/game_theory/`)

| Módulo | Conteúdo | Uso na Vila |
|---|---|---|
| `equilibrio.py` | Nash eq (mixed+pure), best response, Stackelberg | Tribunal decide consenso; Helena avalia stacks estratégicos |
| `mecanismos.py` | VCG, leilão Vickrey, 2nd price, allocation design | Distribuição de cargos (relator, moderador); alocação de oficinas lotadas |
| `jogos_repetidos.py` | Tit-for-tat, trigger strategies, folk theorem, Axelrod tournament | Confiança/traição entre rivais ao longo de steps |
| `evolutivo.py` | Replicator dynamics, ESS, hawk-dove | Evolução do genoma populacional (estende `colmeia.py`) |
| `coordenacao.py` | Schelling focal points, stag hunt, coordination games | Sincronização de desafios coletivos, escolha de tema |
| `bem_comum.py` | Public goods game, tragedy of commons, Ostrom design principles | Orçamento compartilhado, contribuição ao desafio coletivo |

### 2.2 Opinion Dynamics (`engine/opinion_dynamics/`)

| Módulo | Conteúdo | Uso na Vila |
|---|---|---|
| `degroot.py` | DeGroot linear consensus; matrix W convergence | Debate onde crenças ponderadas por reputação convergem |
| `bounded_confidence.py` | Deffuant-Weisbuch; Hegselmann-Krause | Agentes só atualizam se opinião alheia estiver dentro de threshold (modelagem polarização) |
| `cascatas.py` | Bikhchandani-Hirshleifer-Welch info cascade; Bayesian updating | Modela viralização de temas independente de LLM |
| `bayesiano.py` | Bayesian agent belief update sobre mundo | Cada persona mantém prior/posterior sobre outras personas e temas |
| `social_impact.py` | Nowak-Latane social impact theory | Quantifica influência = strength × immediacy² × #sources |

### 2.3 Simulação Avançada (`engine/simulacao_avancada/`)

| Módulo | Conteúdo | Uso na Vila |
|---|---|---|
| `campus_fisica.py` | A* pathfinding, weighted edges, collision avoidance, congestion cost | Movimentação realista no campus 19 locais; fila em oficinas |
| `coalizoes.py` | Shapley value, core, Banzhaf, coalitional form games | Distribuição justa de pontos em desafios coletivos multi-agente |
| `schelling.py` | Schelling segregation model 2D | Emergência de clusters por categoria/tier no campus |
| `voter_espacial.py` | Hotelling/Downs spatial voter; median voter theorem | Posicionamento ideológico em debates; ponto médio ganha |
| `redes.py` | Small-world (Watts-Strogatz), preferential attachment (Barabási-Albert), community detection (Louvain) | Topologia da rede social; hubs; detectar câmaras de eco |
| `informacao_imperfeita.py` | Signaling games, cheap talk, reputation models | Agente pode mentir; filtros de credibilidade |

## 3. Dependências Externas

Adicionar em `requirements.txt`:

```
nashpy>=0.0.38       # Nash equilibrium solver (Python pure)
numpy>=1.24
scipy>=1.11
networkx>=3.1        # grafos + community detection
axelrod>=4.13        # iterated prisoner's dilemma lib (opcional)
```

Nenhuma dep requer GPU ou licença paga.

## 4. Integração com Pipeline Cognitivo

### 4.1 `engine/cognitivo/planejar.py`
- Antes de escolher ação, se contexto é estratégico (`desafio_ativo` OR `debate_formal`), consulta `game_theory.equilibrio.nash(payoff_matrix)` para decisão
- `payoff_matrix` montado a partir de preferências da persona (já em `dados_consultor`)
- Resultado da NE vira input do prompt LLM como "sua análise game-teórica sugere X"

### 4.2 `engine/cognitivo/conversar.py`
- Após cada turno, chama `opinion_dynamics.degroot.atualizar(crencas, matriz_influencia)` para atualizar crença da persona sobre tema
- `matriz_influencia` derivada de: mentor(+0.45), rival(-0.35), reputação, overlap de frameworks mentais

### 4.3 `engine/cognitivo/executar.py`
- Se ação envolve escolher local saturado (oficina lotada), roda `mecanismos.vcg_alocacao(bidders, slots)` — persona "paga" coins pelo slot
- Movimento pelo campus usa `simulacao_avancada.campus_fisica.rota_otima(origem, destino)` em vez de teleporte

### 4.4 `engine/colmeia.py`
- `GenomaNPC` evolução atualizada via `game_theory.evolutivo.replicator_step(populacao, payoffs)` em vez de mutação aleatória
- Dominated strategies caem na população; ESS emerge

### 4.5 `engine/desafio.py`
- Distribuição de pontos finais do desafio usa `coalizoes.shapley_value(contribuicoes)` — justiça cooperativa formal
- Formação de subgrupos usa `coalizoes.core_stable(preferencias)`

### 4.6 `engine/rede_social.py`
- Topologia da rede (quem segue quem) gerada via `redes.preferential_attachment()` no bootstrap
- Propagação de post usa `cascatas.bikhchandani(rede, post, prior)` antes de LLM reagir

## 5. Métricas Novas

Adicionar em `vila_traces` (coluna `tags_game_theory JSONB`):

- `ne_found`: bool — equilíbrio foi atingido?
- `shapley_gini`: 0-1 — desigualdade da distribuição Shapley
- `polarization_index`: -1 a 1 — dispersão de crenças pós-Deffuant
- `cascade_depth`: int — profundidade da cascata informacional
- `coordination_success_rate`: % de jogos de coordenação resolvidos sem NE mixto

## 6. Arquivos Criados

```
CRIAR:
docs/PLANO_ONDA10_GAME_THEORY.md

engine/game_theory/__init__.py
engine/game_theory/equilibrio.py
engine/game_theory/mecanismos.py
engine/game_theory/jogos_repetidos.py
engine/game_theory/evolutivo.py
engine/game_theory/coordenacao.py
engine/game_theory/bem_comum.py

engine/opinion_dynamics/__init__.py
engine/opinion_dynamics/degroot.py
engine/opinion_dynamics/bounded_confidence.py
engine/opinion_dynamics/cascatas.py
engine/opinion_dynamics/bayesiano.py
engine/opinion_dynamics/social_impact.py

engine/simulacao_avancada/__init__.py
engine/simulacao_avancada/campus_fisica.py
engine/simulacao_avancada/coalizoes.py
engine/simulacao_avancada/schelling.py
engine/simulacao_avancada/voter_espacial.py
engine/simulacao_avancada/redes.py
engine/simulacao_avancada/informacao_imperfeita.py

tests/test_game_theory.py
tests/test_opinion_dynamics.py
tests/test_simulacao_avancada.py

MODIF:
requirements.txt
```

Integrações em `persona.py`, `cognitivo/*.py`, `colmeia.py`, `desafio.py`, `rede_social.py` ficam em PR separado (Onda 10.2) — esta branch só cria fundações + testes.

## 7. Ordem de Implementação

1. ✅ Branch + plano doc
2. Skeleton de todos os módulos com classes + docstrings + stubs + NotImplementedError
3. Testes unitários contra casos clássicos da literatura:
   - Prisoner's Dilemma → defect/defect NE único
   - Public Goods (n=4, MPCR=0.5) → 0 contribuição NE, ESS cooperação com tit-for-tat
   - DeGroot com W estocástica → converge em <100 iter
   - Deffuant threshold 0.3 → polariza, 0.5 → consenso
   - Schelling tipping point → 33% threshold
   - Shapley(3-agent voting game) → (1/3, 1/3, 1/3)
4. Implementação real por módulo (em PR subsequentes — Onda 10.2+)
5. Integração no ciclo cognitivo (Onda 10.3)
6. Benchmark comparativo antes/depois (Onda 10.4)

## 8. Critério de Aceite (desta branch)

- [ ] Todos arquivos de skeleton criados
- [ ] Testes unitários rodando (mesmo que contra stubs com `pytest.skip`)
- [ ] `python -c "from engine import game_theory, opinion_dynamics, simulacao_avancada"` executa sem erro
- [ ] Plano doc aprovado pelo Fundador antes de implementação real

## 9. Decisões em Aberto

1. **NashPy vs Gambit**: NashPy é Python puro, Gambit é C++ com wrapper mais poderoso. Decisão: começar NashPy, migrar se gargalo.
2. **Axelrod library**: adicionar como dep ou implementar iterated games à mão? Axelrod tem 200+ strategies prontas; vale a pena.
3. **GPU para replicator dynamics em 100k agentes**: adiar — só relevante na Onda 9 (scale).
4. **Integração com LLM**: game-theory output vai no prompt ("seu cálculo sugere X") ou substitui LLM em decisões triviais? Proposta: híbrido, LLM decide só se diff de payoff < threshold 0.1.

## 9.5 UI — Aprimoramento Paralelo

Nesta mesma branch, aprimorar frontend existente (vanilla JS + CSS3 + Three.js). Manter filosofia **minimalista** — sem shimmer, sem boxed-card excessivo, sem emojis, sem em-dashes. Dark theme amber (--amber #d69e2e) preservado.

### 9.5.1 Fundações compartilhadas

| Arquivo | Propósito |
|---|---|
| `frontend/css/tokens.css` | Design tokens: cores, espaçamento, tipografia, z-index, radius, easing |
| `frontend/css/base.css` | Reset + typography + utilitários (flex, grid) |
| `frontend/css/components.css` | Componentes reutilizáveis: button, input, badge, list-row |
| `frontend/js/core.js` | fetch wrapper, WebSocket/SSE client, event bus, toast |
| `frontend/js/api.js` | Wrapper típico p/ `/api/v1/*` endpoints |
| `frontend/components/` | Web Components nativos sem framework |

### 9.5.2 Web Components (nativos — sem build step)

- `<vila-agent-card>` — card compacto de habitante (avatar inicial + nome + tier + patente)
- `<vila-trace-view>` — renderiza causal chain como árvore minimalista
- `<vila-payoff-matrix>` — tabela interativa de payoffs para game theory
- `<vila-feed-post>` — item de feed com reações + threaded comments
- `<vila-graph-canvas>` — D3.js force-graph (grafo conhecimento + rede social)
- `<vila-metric-line>` — sparkline sem bordas, 1 linha 1 número

### 9.5.3 Páginas novas (Onda 10)

- `frontend/gametheory.html` — visualizador de equilíbrios (payoff matrix, NE highlight, Shapley bars)
- `frontend/opinioes.html` — evolução de crenças ao longo do tempo (line chart Deffuant, clusters emergentes)
- `frontend/coalizoes.html` — grafo de alianças formadas, Shapley pie, core membership

### 9.5.4 Refatoração das páginas existentes

- `index.html`: extrair CSS inline → tokens.css. Sidebar colapsável em mobile. Removed duplicado CSS.
- `cidade.html`: manter Three.js; adicionar legend minimalista; heatmap de congestão (usa `campus_fisica.congestion_cost`)
- `jogo.html`: adicionar coluna de payoff em tempo real; NE current
- `rede.html`: integrar `<vila-graph-canvas>` para visualizar cascata informacional

### 9.5.5 Responsividade + Acessibilidade

- Breakpoints: 480 / 768 / 1024 / 1440
- Prefers-reduced-motion: desativar animações fadeSlide
- ARIA: `role="feed"`, `aria-live="polite"` em updates SSE
- Contrast ratio 4.5:1 mínimo (tokens.css garante)
- Keyboard navigation: todos os controles reachable via Tab

### 9.5.6 Ordem de trabalho UI

1. Criar tokens.css + base.css (zero dep, rápido)
2. Extrair CSS inline das 4 páginas atuais → arquivos compartilhados
3. Criar 6 Web Components (stub + 1 de cada)
4. Implementar `gametheory.html` como primeira prova do stack novo
5. Medir bundle: meta ≤ 40KB CSS + 60KB JS sem frameworks
6. Mostrar screenshot antes de merge (CLAUDE.md regra)

### 9.5.7 Critério de aceite UI

- [ ] Tokens centralizados, nenhum valor hardcoded em HTML inline
- [ ] 6 Web Components funcionando em página demo
- [ ] Zero framework (React/Vue/Svelte) adicionado
- [ ] Bundle ≤ 100KB total (CSS + JS)
- [ ] Lighthouse score ≥ 90 (performance, accessibility)
- [ ] Screenshot aprovado pelo Fundador antes de merge

## 10. Impacto Esperado

- **Rigor acadêmico**: resultados da Vila ficam comparáveis contra literatura (Axelrod 1984, Nowak 2006, Ostrom 1990, Schelling 1971)
- **Reprodutibilidade**: mesmo seed + mesmos params → mesma trajetória (LLM é estocástico, mas game-theory solver é determinístico dado matriz de payoff)
- **Novos produtos**: "Vila como laboratório de mechanism design" — clientes que querem testar novos sistemas de recompensa antes de rollout real
- **Papers possíveis**: (a) emergence of cooperation em 144 LLM agents, (b) comparação LLM-heuristic vs game-theoretic agents em public goods
