# Plano de Implementacao — Vila INTEIA v1.1

> Revisado 2026-03-30 com aprendizados das 3 sessoes de desenvolvimento.

## Estado Atual: PRONTO PARA DEPLOY

### O que existe e funciona

| Componente | Status | Arquivos |
|-----------|--------|----------|
| Motor de Simulacao | Completo | engine/simulacao.py |
| 151 Consultores Lendarios | Completo | data/banco-consultores-lendarios.json |
| Pipeline Cognitivo (7 modulos) | Completo | engine/cognitivo/*.py |
| Sistema de Memoria (3 tipos) | Completo | engine/memoria/*.py |
| Campus 3D (19 locais) | Completo | engine/campus.py + frontend/cidade.html |
| Rede Social (feed, comentarios) | Completo | engine/rede_social.py |
| Motor de Gatilhos (6 triggers) | Completo | engine/gatilhos.py |
| Prompts Profundos (6 camadas) | Completo | engine/arquetipos.py |
| 20 Pares Rivais | Completo | engine/gatilhos.py |
| 15 Regras Especiais | Completo | engine/arquetipos.py |
| API REST (25+ endpoints) | Completo | api/*.py |
| Frontend (3 paginas HTML) | Completo | frontend/*.html |
| Testes (69 + 25) | Completo | tests/*.py |
| 6 Skills Claude Code | Completo | .claude/skills/* |
| Infra Deploy (Docker+Render) | Completo | Dockerfile, render.yaml, requirements.txt |

### Aprendizados incorporados

1. **Imports dual-mode**: todo modulo funciona como package (vila_inteia.X) E standalone (X)
2. **Especiais automaticos**: personagens-chave sempre carregados independente de max_agentes
3. **Fallback total**: sistema funciona 100% sem LLM (heuristicos para tudo)
4. **Cadencia negativa**: ultimo_*_step inicia negativo para primeiro uso imediato
5. **Wave resiliente**: se IA falha, cai para heuristico (nunca perde conteudo)
6. **Helena auto**: intervem automaticamente apos 5+ comentarios acumulados
7. **Cap diario**: 75 posts/dia maximo, reseta automaticamente ao mudar de dia
8. **JSON de consultores no repo**: 151 consultores versionados no git

---

## Fase 1: Deploy Basico (PRONTO)

**Objetivo**: Vila INTEIA acessivel online.

- [x] requirements.txt
- [x] Dockerfile com healthcheck
- [x] render.yaml para Render.com
- [x] .env.example com variaveis documentadas
- [x] main.py aceita PORT do ambiente
- [x] main.py inclui router da rede social
- [x] Imports dual-mode em todos os modulos criticos

**Deploy**:
```bash
# Render: push para main e configurar no dashboard
# Docker: docker build -t vila-inteia . && docker run -p 8100:8100 vila-inteia
```

---

## Fase 2: Conectar OmniRoute (proxima)

**Objetivo**: Rede social com conteudo gerado por IA real.

- [ ] Configurar OMNIROUTE_URL e OMNIROUTE_API_KEY no Render
- [ ] Testar endpoint POST /api/v1/rede/tema com IA ligada
- [ ] Testar debate POST /api/v1/rede/debate com IA
- [ ] Testar POST /api/v1/rede/provocar (Diabob com IA)
- [ ] Verificar custos: ~300-500 chamadas/dia in-game via OmniRoute (gratis)

---

## Fase 3: Frontend Interativo (futura)

**Objetivo**: Experiencia de usuario no browser.

- [ ] Compose box na rede.html para injetar temas
- [ ] Feed em tempo real com SSE ou polling
- [ ] Cidade 3D mostra agentes se movendo em real-time
- [ ] Clique no agente abre perfil + historico
- [ ] Barra lateral com trending tags e debates ativos

---

## Fase 4: Memoria Persistente (futura)

**Objetivo**: Consultores lembram de sessoes anteriores.

- [ ] Salvar/carregar estado da simulacao completo
- [ ] Salvar/carregar rede social (posts + comentarios)
- [ ] Historico de debates entre pares rivais
- [ ] Evolucao de relacionamentos ao longo do tempo
- [ ] Helena sinteses acumulativas (insights cruzados entre dias)

---

## Fase 5: Integracao INTEIA (futura)

**Objetivo**: Vila como produto da INTEIA.

- [ ] Login com auth do sistema principal
- [ ] Integrar FlockVote com pesquisa eleitoral
- [ ] Helena gera relatorios formatados INTEIA
- [ ] API de webhook para injetar eventos do mundo real
- [ ] Dashboard analytics: metricas de engajamento, temas quentes

---

## Metricas de Sucesso

| Metrica | Meta | Como medir |
|---------|------|------------|
| Uptime | 99% | Healthcheck Render |
| Posts/dia in-game | 45-75 | GET /api/v1/rede/gatilhos/status |
| Comentarios/dia | 200-400 | GET /api/v1/rede/stats |
| Debates/dia | 2-3 | Motor de Gatilhos |
| Tempo de resposta API | <500ms | Logs Render |
| Testes passando | 94/94 | python tests/test_bateria.py + test_personagens.py |
