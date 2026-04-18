# HARNESS VILA FUNCIONAL — Cidade a Serviço da INTEIA

> Correção do risco contido em `HARNESS_VILA_VIVENCIAL.md`: **ideias soltas e decorativas não entram**. Cada elemento da Vila precisa ter função backend real, gerar inteligência utilizável e se integrar ao harness. A Vila não é demo — é **fábrica de inteligência** que a INTEIA consome, cobra e entrega.

---

## 0. Tese corrigida

> **A Vila é uma cidade-máquina: cada rua, prédio, luz, partícula e sino corresponde a uma função operacional. Nenhum elemento existe para parecer bonito. Tudo que se vê, se opera. Tudo que se opera, gera inteligência. Toda inteligência gerada vira produto da INTEIA.**

Regra de filtro aplicada a todo elemento:

```
Elemento entra na Vila SE E SOMENTE SE:
  (1) corresponde a uma função backend executável — OU será criada na Onda X
  (2) produz um output que alguém da Colmeia ou cliente consome
  (3) o output é mensurável (tokens, decisão, relatório, artefato, matéria)
  (4) existe rota HTTP, tabela Supabase ou skill backing-up
```

Se falha em qualquer um dos 4, não entra. Este documento retira o que falha e promove o que passa.

---

## 1. Auditoria de todo elemento proposto — funcional ou fora

Cada linha é julgada. Onde estava "decorativo", foi transformado em "funcional" ou removido.

### 1.1 Mapeamento revisado: visível ↔ função ↔ produto

| Elemento visível | Função backend real | Output mensurável | Consumidor | Onda |
|------------------|---------------------|-------------------|------------|------|
| **Esfera pulsante na Ágora** | LED pulsa na frequência real do `ia_client.completar()`; cor = modelo OmniRoute ativo | Latência média por modelo (ms) visível em tooltip | Igor (ops), Efesto (tech) | 2 |
| **Partículas douradas como traces** | Cada partícula = 1 `TraceEvent` real do `vila_traces` | Count de traces/s = throughput cognitivo | Observabilidade / dashboard Grafana | 2 |
| **Linhas neon de causal chain** | `SELECT * FROM vila_traces WHERE causal_parent = X` recursivo | Grafo causal exportável como JSON para post-mortem | Efesto em debug / Oracle Gnosis em pesquisa | 2 |
| **Céu muda de cor conforme carga** | Baseline vs atual do `orcamento_consumido_step_atual / orcamento_total` | Indicador operacional visível à distância | Igor (glanceable) | 2 |
| **Biblioteca, Sala 1 (rascunho)** | Lê `engine/memoria/rascunho.py` | Top-10 rascunhos ativos ranqueados por agente | Debug de memória quente | 1-2 |
| **Biblioteca, Sala 2 (episódios)** | Lê `engine/memoria/fluxo.py` com filtro por relevância decaída | Top-N episódios acessados na última hora | Autoresearch para destilação | 3 |
| **Biblioteca, Sala 3 (saberes)** | Interface sobre o RAG já existente (Supabase + embeddings) | Query UI em linguagem natural → snippets retornados | Cliente / Helena / pesquisador | 3 |
| **Biblioteca, Sala 4 (Fundador)** | `GET /api/memoria/fundador` devolve ficha do `FichaFundador` | Vista consolidada das preferências + histórico de decisões | Qualquer agente que interage com Igor | 4 |
| **Rua das Oficinas (27 ateliês)** | Cada edifício = 1 skill em `engine/skills_oficinas/<nome>/` com manifest | Skill invocável via `POST /api/skill/<nome>` streamando trace | Cliente externo (produto) + Colmeia | 3 |
| **Torre do Observatório** | Vista do `vila_traces` com filtros (agente, fase, período, resultado) | Relatório operacional em tempo real | Ops diária do Igor | 2 |
| **Mercado da Atenção** | View sobre `vila_orcamento_historico` (tabela nova) agregada por agente/fase | Top-N agentes mais caros; sugestão automática de oficinas a cortar | Controle de custo LLM | 2 |
| **Sino da Torre** | Emite evento `step.tick` real via webhook | Canal de integração para scheduler externo (Colmeia, Hookify) | Automação Colmeia | 2 |
| **Praça dos Ágoras** | Renderiza `engine/conversar.py` log + próximos eventos A2A | Transcrições + intent classification por par agente-agente | Cícero (retórica), Diana (comunicação) | 3 |
| **Portal do Mercado (capability cards)** | Lê `engine/harness/protocolos/cards/*.toml` | Lista JSON de capabilities discoveráveis via MCP | Colmeia inteira (clientes do harness) | 3 |
| **Portões da cidade (permissão)** | Middleware em `api/` que valida reputação + constituição antes de aceitar submissão | Log de rejeições/aprovações por regra | Auditoria de governança | 4 |
| **Basílica da Constituição** | Lê `engine/constituicao/artigos/*.toml`; pedras têm hash do artigo | Histórico constitucional exportável; diff entre versões | Themis (compliance) + Igor (governance) | 4 |
| **Laboratório Alquímico (Autoresearch)** | `engine/autoresearch.py` já existente + log de destilações | Novas skills candidatas + score de validação | Promoção automática para produção | 4 |
| **Hall dos Insights** | Lê `vila_publicacoes_mirante` | Top-10 matérias publicadas + métricas de tráfego | Venda / portfólio / Mirante News | 1 |
| **Modo adote um habitante** | `GET /api/agente/<id>/trace-live` com SSE | Feed do loop cognitivo de 1 agente em 1ª pessoa | Pedagogia / apresentação comercial | 3 |
| **Tour Chateaubriand (TTS)** | Rota narrativa que chama endpoints reais; script gerado de `HARNESS_VILA.md` | Onboarding de 6 min para visitante novo | Venda, captação, doutorado | 1 |
| **Modo doutorado (Igor)** | Painel completo com queries livres sobre `vila_traces` + `vila_constituicao` | Export de datasets para pesquisa acadêmica | Tese do Igor / artigos | 4 |

### 1.2 Removido do Vivencial por falha no filtro

| Elemento removido | Razão | Substituto funcional |
|-------------------|-------|----------------------|
| "Áudio ambiente diferente por zona" | Decorativo puro, não produz output | Mantido apenas como **sinalização operacional**: som de erro na Torre quando loop detectado, sino quando step avança, alerta no Mercado se budget > 90% |
| "Easter eggs constitucionais" | Diversão sem output | Removido |
| "Aura do Fundador brilha quando Igor logado" | Só se o brilho = métrica | Reformulado: o busto mostra sempre **quantos agentes consultaram a ficha nos últimos N minutos** (contador visível) |
| "Página vira quando alguém consulta" | Animação gratuita | Só se cada virada corresponder a 1 hit real e o total aparecer como métrica |
| "Cada zona tem cor própria" | Mantido porque a cor é canônica do módulo (azul/verde/rosa/dourado/violeta) — ajuda diagnóstico | Mantido |

---

## 2. Os 5 produtos de inteligência que a Vila gera para a INTEIA

A Vila existe para gerar 5 outputs vendáveis/usáveis. Tudo converge para eles.

### Produto 1 — **Simulação Decisional** (para Helena / Colmeia)

**O que é**: dada uma pergunta estratégica ("aceitar cliente X?", "entrar em mercado Y?", "contratar Z?"), a Vila instancia N agentes relevantes, roda M steps, devolve relatório estruturado.

**Rota**: `POST /api/vila/simular-decisao`

**Input**:
```json
{
  "contexto": "proposta comercial cliente Zeta",
  "agentes": ["themis", "midas", "chateaubriand", "cicero", "oracle-gnosis"],
  "steps": 30,
  "restricoes": ["sem dados sensíveis reais", "orçamento 50k tokens"]
}
```

**Output**:
```json
{
  "relatorio_id": "...",
  "decisao_recomendada": "aceitar com ressalvas",
  "confianca": 0.76,
  "votos_por_agente": {...},
  "riscos_detectados": [...],
  "margem_projetada_usd": 12400,
  "trace_completo_url": "/api/traces/..."
}
```

**Valor comercial**: Helena cobra R$ 2k por simulação estratégica executiva.

### Produto 2 — **Copilot-Sandbox** (para clientes Paixão Cortes, Elexion, etc.)

**O que é**: cliente logado na Vila tem acesso a um sub-conjunto de agentes (ex: copilot jurídico = Themis + Cícero + pesquisador acadêmico). Pergunta, recebe resposta com trace auditável.

**Rota**: `POST /api/vila/cliente/<cliente_id>/perguntar`

**Diferencial**: cliente **vê** o agent loop acontecendo. Confiança > chatbot opaco. Diferencial de venda.

**Valor comercial**: inclui mensalidade; aumenta retenção.

### Produto 3 — **Feed Editorial Mirante** (já funciona, agora instrumentado)

**O que é**: Chateaubriand + habitantes produzem matérias publicadas em mirantenews.com.br. Já existe.

**Incremento do harness**: cada matéria publicada traz **rastro completo** (quais memórias, quais oficinas, quais votos). Jornalismo auditável → diferencial competitivo em jornalismo.

**Valor comercial**: Mirante News vira referência de "jornalismo com proveniência cognitiva".

### Produto 4 — **Dataset Acadêmico** (doutorado Igor + artigos)

**O que é**: `vila_traces` + `vila_constituicao` + `vila_economia` exportáveis como dataset anonimizado.

**Rota**: `GET /api/vila/dataset/v1/<ano-mes>`

**Valor acadêmico**: material base para tese + 3-5 artigos submissíveis (IJCAI, NeurIPS, EMNLP).

**Valor comercial**: licenciamento de dataset para laboratórios de IA.

### Produto 5 — **Showcase Vivo** (captação + venda)

**O que é**: URL `vila.inteia.ai` acessível a investidores, clientes, imprensa. Tour de 6 minutos.

**Diferencial**: ninguém mais no Brasil tem harness visitável funcionando.

**Valor comercial**: acelera ciclo de venda; encurta pitch.

---

## 3. Integração com a Colmeia — cada agente consome Vila de um jeito

Cada diretor/agente da Colmeia usa a Vila como infraestrutura, não como decoração. Contrato funcional explícito:

| Agente Colmeia | Endpoint que ele chama | O que obtém |
|----------------|------------------------|-------------|
| **Helena** (estratégia) | `POST /api/vila/simular-decisao` | Relatório de decisão com N agentes + trace |
| **Iris** (executiva) | `GET /api/vila/agenda-fundador` | Próximas obrigações do Igor + restrições da ficha |
| **Diana** (comunicação) | `GET /api/vila/conversas?categoria=retorica` | Exemplares A2A para análise de estilo |
| **Efesto** (tech) | `GET /api/traces` + `GET /api/vila/saude` | Métricas operacionais + causal chain |
| **Cícero** (jurídico orador) | `POST /api/skill/<tecnica-retorica>` | Skill invocada em contexto |
| **Themis** (jurídico compliance) | `GET /api/vila/constituicao/artigos/<id>/check` | Validação de compliance |
| **Midas** (negócios) | `GET /api/vila/economia/precificacao?cenario=X` | Sugestão de preço baseado em simulação interna |
| **Oracle Gnosis** (pesquisa) | `GET /api/vila/dataset/v1/...` | Dados para pesquisa |
| **Mel** (comercial) | `POST /api/vila/demo?cliente_id=X` | Sessão demo customizada para prospect |
| **ONIR** (este Claude Code) | `GET /api/skill/*` + `POST /api/vila/refletir` | Skills reutilizáveis + capacidade de propor mudanças |

Cada integração vira capability card em `engine/harness/protocolos/cards/` (Onda 3). A Colmeia, quando faltar informação, **consulta a Vila** em vez de chutar.

---

## 4. Nada decorativo — redefinição dos elementos mantidos

Revisão explícita dos elementos da versão vivencial, agora todos funcionais:

### 4.1 Os 9 lugares, cada um com função backend

1. **Ágora + Esfera pulsante** = painel de saúde do OmniRoute (modelo ativo, latência, tokens/s)
2. **Biblioteca (4 salas)** = 4 endpoints de memória (`/memoria/rascunho`, `/memoria/fluxo`, `/memoria/semantica`, `/memoria/fundador`)
3. **Rua das Oficinas** = skill registry navegável + invocável
4. **Praça dos Ágoras** = histórico + live stream de A2A conversations
5. **Torre do Observatório** = dashboard operacional (equivalente ao `/api/traces`)
6. **Mercado da Atenção** = controle de custo (`/api/orcamento`)
7. **Sino da Torre** = scheduler tick + webhook externo
8. **Portões da cidade** = middleware de permissão + log de rejeições
9. **Basílica** = CRUD de artigos constitucionais + diff histórico

### 4.2 Os 5 efeitos visuais mantidos (todos funcionais)

| Efeito | O que indica | Como é calculado |
|--------|--------------|------------------|
| Partícula dourada | 1 trace event real | `vila_traces` INSERT |
| Linha neon (causal chain) | 1 aresta causal | `causal_parent` recursivo |
| Cor da luz da oficina | Skill está carregada no contexto agora | `vila_skill_loading` state |
| Cor do céu | Carga operacional | `SUM(tokens_consumidos) / ORCAMENTO_GLOBAL` |
| Cor da bolsa do agente | Porcentagem de orçamento pessoal gasto | Por agente na view do Mercado |

Tudo o mais que era só "bonito" foi cortado ou transformado em métrica.

---

## 5. Roadmap funcional revisado — o que fazer quando

### Onda 1 Funcional (1 semana) — Visibilidade mínima viável

- [ ] `docs/HARNESS_VILA.md` + `HARNESS_VILA_VIVENCIAL.md` + **este** documento commitados
- [ ] `engine/harness/` pacote criado com README
- [ ] Landing `vila.inteia.ai/sobre` explicando a proposta de valor (5 produtos)
- [ ] Tour guiado MVP (link percorre endpoints reais em sequência)
- [ ] Skill `.claude/skills/harness-vila` ativada

**Entregável funcional**: visitante entra e entende em 5 min que a Vila **faz** coisas, não apenas anima.

### Onda 2 Funcional (2 semanas) — Observabilidade como produto

- [ ] `engine/harness/observabilidade.py` + tabela `vila_traces`
- [ ] `engine/harness/orcamento.py` + tabela `vila_orcamento_historico`
- [ ] Torre do Observatório (frontend) conectada a `/api/traces`
- [ ] Mercado da Atenção (frontend) conectado a `/api/orcamento`
- [ ] Esfera da Ágora conectada a métricas OmniRoute
- [ ] Produto 1 (Simulação Decisional) no ar em MVP
- [ ] Helena chama `POST /api/vila/simular-decisao` pela primeira vez

**Entregável funcional**: Helena gera 1ª inteligência executiva real usando a Vila. Custo LLM mensurável. Debug em < 5s.

### Onda 3 Funcional (3 semanas) — Skills + Protocolos = Produto escalável

- [ ] 27 oficinas viram skills com `SKILL.md` formal
- [ ] `POST /api/skill/<nome>` invocável externamente
- [ ] Capability cards para as 10 integrações Colmeia
- [ ] Produto 2 (Copilot-Sandbox) ativo para 1º cliente piloto
- [ ] Produto 5 (Showcase) no ar em `vila.inteia.ai`
- [ ] Rua das Oficinas + Praça dos Ágoras renderizadas

**Entregável funcional**: 1º cliente paga pelo Copilot-Sandbox. Showcase fecha 1º investidor/cliente novo.

### Onda 4 Funcional (2 semanas) — Governança + Pesquisa = Ativos de longo prazo

- [ ] `engine/memoria/fundador.py` implementada + Sala 4 renderizada
- [ ] Constituição migrada para `.toml` + policy engine
- [ ] Basílica interativa com diff de versões
- [ ] Produto 4 (Dataset Acadêmico) exportável
- [ ] Laboratório Alquímico visível com destilações em tempo real
- [ ] Modo doutorado para Igor

**Entregável funcional**: Igor submete 1º artigo acadêmico usando dataset da Vila. INTEIA licencia dataset.

---

## 6. Métricas de sucesso funcional (OKRs da Vila)

Ao final da Onda 4, os números que importam:

| Métrica | Meta mínima | Meta ambiciosa |
|---------|-------------|----------------|
| Simulações Decisionais executadas/mês | 10 | 50 |
| Receita direta gerada pela Vila/mês | R$ 5k | R$ 30k |
| Clientes ativos no Copilot-Sandbox | 1 | 5 |
| Traces/dia em produção | 10 000 | 200 000 |
| Custo LLM/step médio | -30% vs baseline pré-harness | -60% |
| Artigos acadêmicos submetidos | 1 | 3 |
| Matérias Mirante com proveniência cognitiva | 100% das novas | 100% do backlog |
| Uptime do harness | 99% | 99.9% |
| Tempo de onboarding de visitante novo | 6 min | 3 min |

Se a Vila não estiver mexendo estes ponteiros, **a arquitetura falhou** — por mais bonita que esteja.

---

## 7. Princípios não-negociáveis (reforçados)

1. **Proibido ornamento sem função**. Todo pixel corresponde a métrica ou ação.
2. **Proibido feature sem consumidor identificado**. Cada endpoint tem ≥1 agente Colmeia ou cliente que o usa.
3. **Proibido protocolo sem contrato**. Capability card `.toml` obrigatório para toda integração nova.
4. **Proibido skill sem manifest**. 3 camadas (procedimento + heurística + restrição) ou não é skill.
5. **Proibido artigo constitucional sem `evento_origem`**. Constituição é lei sobre fato, nunca sobre hipótese.
6. **Proibido memória sem política de retenção**. TTL, consolidação, esquecimento explícitos.
7. **Proibido trace sem causal chain**. Nada é evento órfão.
8. **Proibido LLM call sem orçamento declarado**. Ninguém estoura budget sem consentimento.
9. **A Vila serve ao Fundador + INTEIA + Colmeia + Cliente — nessa ordem de prioridade**. Qualquer conflito resolve-se pela hierarquia.
10. **Toda inteligência gerada fica registrada, reutilizável e monetizável**. Nada se perde no vento.

---

## 8. Leitura obrigatória para todo contribuidor

Antes de tocar a Vila:

1. [`HARNESS_VILA.md`](./HARNESS_VILA.md) — diagnóstico técnico + 4 ondas
2. [`HARNESS_VILA_VIVENCIAL.md`](./HARNESS_VILA_VIVENCIAL.md) — camada experiencial (lido em 2º lugar para entender metáfora)
3. **Este documento** (`HARNESS_VILA_FUNCIONAL.md`) — filtro funcional que prevalece sobre os dois anteriores
4. Skill global `harness-architect` — framework teórico

**Regra de prevalência em conflito**: se o Vivencial propõe algo bonito mas o Funcional diz que é decorativo → vence o Funcional. Se o técnico propõe algo austero mas o Vivencial torna pedagógico sem custo extra → vale adicionar. **Nada entra na Vila sem passar pelo crivo dos 4 critérios da §0.**

---

## 9. Próximo passo imediato

Escrever o primeiro **manifesto funcional** traduzindo este documento em tickets executáveis:

```bash
# 1. Criar issues no GitHub — uma por linha da tabela §1.1
# 2. Priorizar pela Onda (2 > 3 > 1 > 4, ROI decrescente)
# 3. Abrir PR da Onda 1 Funcional hoje (só docs + skill local)
# 4. Agendar kickoff da Onda 2 (observabilidade) com Efesto
```

---

> *"A Vila é um organismo. Este documento garante que o organismo tem músculos, não só figurino."*

**Skill aplicada**: `harness-architect` v1.1.0 + `harness-vila` v1.0.0.
**Artefatos desta iteração**: `HARNESS_VILA.md` (técnico) + `HARNESS_VILA_VIVENCIAL.md` (experiencial) + `HARNESS_VILA_FUNCIONAL.md` (este, filtro final).
**Trinca inviolável**: técnico → experiencial → funcional. Pensados juntos, filtrados no final pela utilidade.
