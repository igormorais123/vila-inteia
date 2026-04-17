# Roadmap — Vila INTEIA (Camada 2)

Features prontas em Camada 1 (base arquitetural):
- ✅ Chateaubriand (editor-chefe)
- ✅ Cliente Mirante + endpoint `/api/vila/submissoes`
- ✅ Save/Load de vilas (Supabase)
- ✅ Pacotes de habitantes
- ✅ Constituição viva (3 tipos + enforcement)
- ✅ Economia base (ambição + precificação + transações)
- ✅ Mirofish bridge
- ✅ 27 técnicas Problem Solving
- ✅ Auto-research (Karpathy loop)

Abaixo o que ainda precisa de aprofundamento.

---

## 1. Escalabilidade de habitantes (200 → 1000+)

**Problema**: hoje todos os habitantes são processados a cada step. Com 1000
agentes e intervalo de 30s, cada step passa de 5min.

**Solução proposta**:
- Classificar habitantes em `ativo | dormente | raramente_ativo`
- Por default: 20% ativos, 60% dormentes, 20% raramente_ativos
- Dormentes só "acordam" por gatilho: conversa, menção, convocação, evento de rede social
- Worker pool (ThreadPoolExecutor ou asyncio) para paralelizar chamadas LLM

**Onde mexer**: `engine/simulacao.py` → loop de step + scheduler de dormência.

---

## 2. Constituição — enforcement semântico

Hoje o `executor_constitucional.py` faz parsing por keyword (regex). Limitado.

**Melhorar**:
- LLM-as-validator: antes de cada ação crítica, pergunta "esta ação viola
  algum artigo vigente?"
- Embeddings: indexar artigos, verificar similaridade semântica com a
  ação proposta
- Metadados estruturados no artigo: `handler: "nome_funcao"` para regras que
  o dev codificou explicitamente

---

## 3. Economia — mercado de colaboração

Hoje: habitantes são creditados por ação unilateral. Falta:

- **Contratação**: habitante A contrata B por R$ X para colaborar numa matéria
- **Co-autoria**: split de recompensa por contribuição
- **Patrocínio**: habitante rico patrocina coluna de outro
- **Reputação**: score que altera preço aceitável de trabalhos
- **Inflação**: saldo perde valor ao longo do tempo, forçando ação

**Onde mexer**: `engine/economia.py` → novos métodos + novas colunas em
`vila_economia_perfis` (reputacao, nivel_especialista).

---

## 4. Mirofish — ida e volta

Hoje: Vila envia dados → Mirofish processa → Vila recebe. One-shot.

**Evoluir para**:
- Mirofish importa habitantes Vila via `/api/v1/vila/habitantes`
- Vila consome insights Mirofish em tempo real via webhook
- Dashboard unificado: grafo Mirofish renderizado dentro do frontend Vila

---

## 5. Frontend — unificar 3 HTMLs

Hoje existem `cidade.html` (3D), `index.html` (dashboard) e `rede.html` (feed).
Não conversam entre si.

**Objetivo**: SPA Next.js ou Vite que:
- Tela inicial = galeria de vilas salvas (save/load visual)
- Menu lateral com: Campus 3D, Rede Social, Jornal da Vila, Economia, Constituinte, Oficinas, Desafios
- Realtime via Supabase channels (updates de matérias, votos, transações)

---

## 6. Editor-chefe — aprendizado

Chateaubriand hoje aplica critérios estáticos. Pode:

- Logar quais matérias viraram capa no Mirante
- Ajustar score de avaliação baseado no resultado real
- Fine-tuning de prompt com base no histórico de aprovação/rejeição Mirante

---

## 7. Constituinte — detecção mais rica

Hoje `detectar_problemas_reais` usa 3 heurísticas. Ampliar para:

- Conflitos interpessoais recorrentes na rede social
- Temas que aparecem em 20%+ das matérias rejeitadas
- Oficinas que ninguém completou
- Propostas que foram rejeitadas 3x no mesmo mês

---

## 8. Audit trail

Adicionar tabela `vila_auditoria` que registra toda decisão automatizada:
quem decidiu (sistema/agente), qual artigo aplicado, input, output. Útil para
provar que o sistema agiu conforme a constituição.

---

## 9. Multi-vila paralela

Hoje: 1 processo = 1 vila. Executar múltiplas vilas no mesmo backend
(isolamento por `vila_id` em todas as queries, o que já está no schema).

---

## 10. Comparações entre vilas

UI que compara:
- Vila A (eleitores DF) vs Vila B (eleitores RR) sobre o mesmo tópico
- Vila hoje vs snapshot de 3 semanas atrás
- Diferentes constituições sobre a mesma população

---

## 11. Exportar como biblioteca

Hoje: monolito FastAPI. Transformar `engine/` em pacote pip-instalável
(`pip install vila-inteia-engine`) para que outros projetos possam embutir a
simulação sem subir servidor inteiro.

---

## Priorização sugerida

1. Escalabilidade (bloqueia casos reais com 1000 agentes)
2. Frontend unificado (UX atual é fragmentada)
3. Economia — mercado de colaboração (dá vida ao dinheiro)
4. Constituição — enforcement semântico (dá força real às regras)
5. Mirofish — ida e volta (amplia o laboratório)
6. Resto conforme demanda

---

## Tickets executivos gerados pela Vila

A Vila pode ela mesma pedir features via artigos constitucionais estruturais.
Esses pedidos vão parar em `vila_tickets_executivo` no Supabase. O dev deve
revisar essa tabela periodicamente:

```sql
SELECT * FROM vila_tickets_executivo
WHERE status = 'aberto'
ORDER BY urgencia DESC, criado_em ASC;
```

Respondendo um ticket:
```sql
UPDATE vila_tickets_executivo
SET status = 'implementado',
    resposta_executivo = 'PR #XYZ mergeado, deploy em prod.',
    respondido_em = now()
WHERE id = '<uuid>';
```
