# Plano: Supera-MiroFish — 5 Ondas de Evolução

**Objetivo**: Posicionar Vila INTEIA como simulação multi-agente superior ao MiroFish (benchmark open-source: OASIS + Zep + GraphRAG, 33k stars, 1M agent interactions) em dimensões onde Vila já é diferenciada, e atacar gaps onde MiroFish ganha.

**Criado em**: 2026-04-20
**Status**: proposta, aguarda aprovação do Fundador

---

## 0. Premissas

- Vila já domina: personas lendárias nomeadas, governança constitucional executável, economia interna, publicação editorial real (Mirante), sintetizar com detecção de echo, trace/causal chain.
- Gaps vs MiroFish: escala (140 vs 1M), GraphRAG nativo, multi-plataforma, backtest/calibração preditiva, memória federada.
- Harness (Zhou 2026) já prevê 4 ondas — este plano estende como Ondas 5–9.
- Restrição: custo zero de LLM (OmniRoute + fallback Anthropic só em produção).

---

## 1. Onda 5 — Proveniência Pública + Backtest Seed (2 semanas)

**Meta**: quick win. Diferencial imediato de venda ("jornalismo auditável"). Primeiro dataset preditivo.

### Entregas

1. **Endpoint de proveniência cognitiva**
   - Novo arquivo: `api/rotas_proveniencia.py`
   - Rota: `GET /api/v1/materia/{id}/proveniencia` → JSON com trace_hash, lista personagens, custo token, causal chain recursiva
   - Rota: `GET /materia/{id}/proveniencia.html` → template read-only (extensão de `frontend/`)
   - Consome `engine/harness/observabilidade.py` (já existe) + `vila_publicacoes_mirante` + `vila_traces`
   - Mount em `main.py:serve/live`

2. **Publicação automática do trace_hash**
   - Editar `engine/publicar_mirante.py` → incluir `trace_hash = hash(causal_chain)` no payload Mirante
   - Editar `engine/mirante_client.py` → aceitar campo `proveniencia_url` no POST
   - Migration: `sql/migrations/2026-04-21_proveniencia.sql` adiciona coluna `trace_hash TEXT` em `vila_publicacoes_mirante`

3. **Backtest harness seed**
   - Novo diretório: `engine/backtest/`
   - `engine/backtest/dataset.py` — loader de CSV histórico (formato: `evento_id, data, contexto, outcome_real`)
   - `engine/backtest/runner.py` — reset sim com `t=T0`, roda N steps, compara output vs `outcome_real`
   - `engine/backtest/metricas.py` — Brier score, log-loss, accuracy binária
   - Seed dataset: `data/backtest/eleicao_municipal_sp_2024.csv` (10 eventos, outcome conhecido)
   - CLI: `python -m engine.backtest.runner --dataset eleicao_municipal_sp_2024 --n 5`

4. **Dashboard de proveniência**
   - HTML vanilla em `frontend/proveniencia.html`
   - Renderiza causal chain via Three.js (já disponível) como DAG
   - Mostra: personagens envolvidos, custo token, tempo, fase por fase

### Critério de aceite

- [ ] Publicar 1 matéria real no Mirante com trace_hash
- [ ] URL pública `/materia/{id}/proveniencia` renderiza causal chain
- [ ] Backtest seed roda e imprime Brier score em CI
- [ ] README.md atualizado com claim "jornalismo com proveniência cognitiva auditável"

### Arquivos novos/modificados

```
CRIAR: api/rotas_proveniencia.py
CRIAR: engine/backtest/{__init__.py, dataset.py, runner.py, metricas.py}
CRIAR: data/backtest/eleicao_municipal_sp_2024.csv
CRIAR: frontend/proveniencia.html
CRIAR: sql/migrations/2026-04-21_proveniencia.sql
MODIF: main.py                      (mount router)
MODIF: engine/publicar_mirante.py   (inclui trace_hash)
MODIF: engine/mirante_client.py     (payload)
MODIF: README.md                    (claim)
```

### Riscos

- Mirante pode rejeitar campo `proveniencia_url` → mitigar com feature flag, fallback p/ URL INTEIA.
- Seed dataset pequeno → Brier ruidoso, usar só como smoke test.

---

## 2. Onda 6 — Knowledge Graph Nativo (3 semanas)

**Meta**: fechar gap GraphRAG. Fundação para Ondas 7-8.

### Entregas

1. **Schema SQL do grafo**
   - Tabelas: `vila_grafo_nos` (id, tipo, rotulo, props JSONB, vila_id, criado_em), `vila_grafo_arestas` (origem_id, destino_id, relacao, peso, props JSONB)
   - Índices: BTREE em (vila_id, tipo), GIN em props
   - Migration: `sql/migrations/2026-04-25_grafo.sql`
   - Opção B (futuro): migrar para Neo4j dedicado se escala exigir

2. **Extrator de entidades+relações**
   - Novo: `engine/memoria/grafo.py`
   - `extrair_entidades(texto: str) -> list[Entidade]` usa `ia_client` modelo `sintese` + prompt few-shot
   - `extrair_relacoes(texto: str, entidades: list) -> list[Relacao]`
   - Hook: após cada `conversar.py` / `sintetizar.py` / publicação Mirante → enfileira extração
   - Worker assíncrono (thread) consome fila, escreve em `vila_grafo_*`

3. **Query grafo em recuperar**
   - Modificar `engine/cognitivo/recuperar.py:22-113`
   - Adicionar `recuperar_subgrafo(entidade, hops=2) -> list[NoGrafo]`
   - Score híbrido: `0.5 * relevancia_tripla + 0.3 * proximidade_grafo + 0.2 * recencia`
   - Grounding: resposta cita `no_id` do grafo → rastreável

4. **Visualização**
   - Endpoint `GET /api/v1/vila/grafo?filtro=X` → JSON node-link D3
   - Frontend: aba nova em `cidade.html` ou `frontend/grafo.html` com D3.js force graph

### Critério de aceite

- [ ] 10k nós + 30k arestas extraídos de 100 steps de simulação
- [ ] `recuperar` usa subgrafo 2-hops em debates — redução de 30%+ em alucinação (medido via eval set)
- [ ] Visualização interativa zoom/pan
- [ ] Benchmark: query grafo < 100ms p95

### Arquivos novos/modificados

```
CRIAR: engine/memoria/grafo.py
CRIAR: sql/migrations/2026-04-25_grafo.sql
CRIAR: frontend/grafo.html
MODIF: engine/cognitivo/recuperar.py     (query híbrida)
MODIF: engine/cognitivo/conversar.py     (hook extração)
MODIF: engine/cognitivo/sintetizar.py    (hook extração)
MODIF: engine/publicar_mirante.py        (hook extração)
MODIF: api/rotas_vila.py                 (endpoint grafo)
```

### Riscos

- Custo de LLM p/ extração → usar modelo `sintese` (osa-specialist), batch de 50 docs por chamada.
- Qualidade extração ruim → começar com entidades PER/ORG/LOC spaCy + só relações via LLM.

---

## 3. Onda 7 — Multi-Plataforma Social Paralela (4 semanas)

**Meta**: simular propagação cross-platform. MiroFish faz Twitter+Reddit; Vila faz 4.

### Entregas

1. **Abstração `PlataformaSocial`**
   - Novo: `engine/plataformas/base.py` — interface `PlataformaSocial` com métodos `postar/engajar/ranking_feed/amplificar`
   - Mover lógica atual de `engine/rede_social.py` para `engine/plataformas/twitter_like.py` (mantém compat)

2. **Implementações**
   - `twitter_like.py` — feed temporal + virality score (já ~100% pronto via `rede_social.py`)
   - `reddit_like.py` — threaded deep discussion, upvote/downvote, subreddits = oficinas
   - `linkedin_like.py` — corporate tone, endorsement mecânico, algoritmo prioriza peer connections
   - `tiktok_like.py` — video/short-form, algoritmo For You = pure engagement-maximizing
   - Cada plataforma = algoritmo ranking próprio

3. **Personas multi-perfil**
   - Expandir `engine/persona.py:23-943`
   - Campo `perfis_plataforma: dict[str, PerfilPlataforma]` — Steve Jobs Twitter ≠ Steve Jobs LinkedIn
   - `arquetipos.py` ganha variantes por plataforma (`gerar_prompt_plataforma(consultor, plataforma)`)

4. **Cross-posting + viralização inter-plataforma**
   - Motor: post viral no Twitter → spillover 20% p/ LinkedIn, 10% p/ TikTok
   - Rastreado em `vila_cross_platform_flow`

5. **UI multi-plataforma**
   - `frontend/plataformas.html` com 4 abas
   - API: `GET /api/v1/plataformas/{nome}/feed`

### Critério de aceite

- [ ] Simulação roda 4 plataformas simultâneas sem degradar TPS
- [ ] Métricas de spillover entre plataformas logadas em `vila_traces`
- [ ] Caso de uso: lançar tema "IA generativa em jurídico", medir viralização diferencial por plataforma

### Arquivos novos/modificados

```
CRIAR: engine/plataformas/{__init__.py, base.py, twitter_like.py, reddit_like.py, linkedin_like.py, tiktok_like.py}
CRIAR: frontend/plataformas.html
CRIAR: sql/migrations/2026-05-15_plataformas.sql (vila_cross_platform_flow, perfis_plataforma)
MODIF: engine/persona.py                  (perfis_plataforma)
MODIF: engine/arquetipos.py               (prompts por plataforma)
MODIF: engine/rede_social.py              (delegar p/ PlataformaSocial)
MODIF: api/rotas_rede_social.py           (roteamento por plataforma)
DEPRECAR: nada (compat mantida via twitter_like default)
```

### Riscos

- 4x carga de LLM → priorizar heurístico puro em plataformas "cold" (LinkedIn/TikTok), LLM só Twitter+Reddit.
- Fragmentação de personas → manter núcleo (arquétipo) imutável, variar só tom/registro.

---

## 4. Onda 8 — MCP Server + Calibração Preditiva (3 semanas)

**Meta**: expor Vila como tool externa (Colmeia chama Vila). Calibrar backtest contra múltiplos datasets.

### Entregas

1. **MCP Server**
   - Novo: `engine/mcp_server/` (servidor stdio/HTTP compatível com Model Context Protocol spec)
   - Converte `engine/harness/protocolos/cards/*.toml` em tool schemas MCP automáticos
   - Tools expostas: `vila.simular_cenario`, `vila.consultar_habitante`, `vila.injetar_topico`, `vila.obter_proveniencia`, `vila.extrair_grafo`
   - CLI: `python -m engine.mcp_server --port 3000`

2. **Calibração**
   - Novo: `engine/backtest/calibracao.py`
   - Loop: para cada dataset histórico, rode N sims estocásticas, meça Brier, ajuste params do genoma via grid search (6 dims) ou Bayesian optim (`scikit-optimize`)
   - Output: `data/calibracao/genoma_otimo_{dataset}.json`
   - A/B: roda nova sim com genoma calibrado vs default, mede melhora

3. **Datasets ampliados**
   - 5 datasets seed:
     - Eleição municipal SP 2024
     - Lançamento produto tech (Apple Vision Pro feedback público)
     - Escândalo corporate (caso Americanas)
     - Crise política (impeachment 2016)
     - Movimento social viral (XP de TikTok)
   - `data/backtest/*.csv` + docs em `docs/BACKTEST_DATASETS.md`

4. **Dashboard preditivo**
   - Página pública `mirantenews.com.br/previsoes` com Brier atualizado diariamente
   - Credibilidade crescente (track record pública)

### Critério de aceite

- [ ] Claude Desktop consegue conectar via `claude mcp add vila ...` e chamar `vila.simular_cenario`
- [ ] Calibração reduz Brier médio ≥20% vs genoma default em 3 dos 5 datasets
- [ ] Dashboard público online

### Arquivos novos/modificados

```
CRIAR: engine/mcp_server/{__init__.py, server.py, tool_registry.py}
CRIAR: engine/backtest/calibracao.py
CRIAR: data/backtest/{lancamento_apple_vpro.csv, americanas_2022.csv, impeachment_2016.csv, tiktok_viral.csv}
CRIAR: data/calibracao/                 (gerado runtime)
CRIAR: docs/BACKTEST_DATASETS.md
MODIF: engine/colmeia.py                (aceitar genoma_base calibrado)
```

### Riscos

- MCP spec em mudança → pinar versão 2026-04 atual, docs em `docs/MCP_INTEGRATION.md`.
- Calibração overfitting → train/test split 70/30, reportar test Brier.

---

## 5. Onda 9 — Escala 100x (6-10 semanas, opcional se demanda exigir)

**Meta**: ordem OASIS (10k-100k agentes) sem depender de OASIS.

### Entregas

1. **Arquitetura distribuída**
   - Migrar `SimulacaoVila` para Ray Actors (`pip install ray`)
   - Cada persona = actor isolado, step coordinator central
   - Hot/cold tiers: 95% agentes cold (heurístico puro sem LLM), 5% hot (LLM-backed rotacional)
   - Partitioning por categoria (engenheiro_futurista em 1 node, jurista em outro)

2. **Inference local self-hosted**
   - Servidor vLLM com Llama 3.3 70B 4-bit quantizado em GPU (RTX 4090 dev, A100 prod)
   - `ia_client.py` detecta endpoint local em `VLLM_URL`, rota `modelo_rapido` p/ local
   - Custo marginal zero após infra

3. **Observabilidade distribuída**
   - `vila_traces` com `node_id` coluna
   - Dashboards Grafana: TPS, latência por fase, custo por node

4. **Governança em escala**
   - Flockvote (`engine/flockvote.py`) → paralelizar votação 100k em 2s (já modelo boids)
   - Constituinte detecta padrões emergentes só em sample 1% (estatístico)

### Critério de aceite

- [ ] 10k agentes ativos 24/7 em 1 node, 100k em cluster 10 nodes
- [ ] Custo operacional < R$ 500/mês em modo local
- [ ] TPS ≥ 50 steps/min com 10k agentes

### Riscos

- Complexidade infra enorme → ondas 5-8 primeiro. Onda 9 só se pipeline comercial exigir.

---

## 6. Roadmap Visual

```
Abr/20 ──── Mai/5 ───── Mai/25 ──── Jun/20 ──── Jul/12 ──── Set/20
   │           │           │           │           │           │
  [Onda 5]  [Onda 6]    [Onda 7]   [Onda 8]    (caps)      (Onda 9)
  Provenien. GraphRAG   4 Plataform MCP + Calib             Scale 100x
  + Backtest            paralelas                           (se demanda)
  seed
   ↓           ↓           ↓           ↓
  MVP       Fundação     Produto    Produto
  público   técnica      vendável   B2B plug-in
```

---

## 7. KPIs por Onda

| Onda | KPI primário | Meta |
|---|---|---|
| 5 | Matéria publicada c/ proveniência | 1 viralizar |
| 6 | Redução alucinação via grounding | -30% em eval set |
| 7 | Spillover cross-platform medido | ≥1 caso público |
| 8 | Brier vs baseline | -20% em 3/5 datasets |
| 9 | Agentes simultâneos | 10k no lab, 100k prod |

---

## 8. Dependências Externas

- Supabase pgvector (Onda 6): ativar extensão
- Neo4j dedicado (Onda 6+, opcional): avaliar custo vs Supabase
- GPU A100 (Onda 9): Hetzner ou Lambda Cloud, R$800-2000/mês
- MCP spec: pinar versão (Onda 8)
- Mirante API v2 (Onda 5): negociar aceitar `proveniencia_url` field

---

## 9. Decisões em Aberto (requer Fundador)

1. Manter Supabase ou migrar grafo p/ Neo4j?
2. Open-source Vila (match MiroFish 33k stars) ou manter privado?
3. Onda 9 agora (infra upfront) ou sob demanda?
4. Prioridade: BR-only (eleições/política BR) ou global (inglês + datasets globais)?
5. Comercializar MCP server como produto B2B ou só interno Colmeia?

---

## 10. Primeiro Passo Executável (esta semana)

Começar **Onda 5 — Proveniência Pública** pois:
- Zero dependência externa
- Código já existe (vila_traces), só falta expor
- Diferencial imediato de venda
- Valida pipeline de publicação Mirante ponta-a-ponta

**Tarefas imediatas** (2-3 dias):

1. Criar `api/rotas_proveniencia.py` com 2 endpoints
2. Migration `sql/migrations/2026-04-21_proveniencia.sql` adicionando `trace_hash`
3. Modificar `engine/publicar_mirante.py` para gerar hash
4. Frontend `frontend/proveniencia.html` usando Three.js já instalado
5. Publicar 1 matéria teste + URL pública ao vivo
6. Atualizar `README.md` com claim

Após validação, avançar Onda 6.
