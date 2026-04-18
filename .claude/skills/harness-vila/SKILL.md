---
name: harness-vila
description: "Aplica a skill global harness-architect especificamente ao projeto Vila INTEIA. Traz o diagnóstico + plano de 4 ondas (observability, orçamento de contexto, skills canônicas, protocolos unificados) descrito em HARNESS_VILA.md. Use sempre que mexer em engine/cognitivo/, engine/memoria/, engine/oficinas.py, engine/chateaubriand.py, engine/constituicao.py, engine/ia_client.py, ou ao discutir arquitetura, refatoração, observabilidade, custo, integração externa ou ligação com a Colmeia."
triggers:
  - harness vila
  - refatorar vila
  - arquitetura vila
  - observability vila
  - orçamento de contexto vila
  - oficinas como skills
  - capability card vila
  - policy engine constituição
  - ficha do fundador
  - integrar colmeia vila
  - vila como harness
  - banho técnico vila
  - onda 1 vila
  - onda 2 vila
  - onda 3 vila
  - onda 4 vila
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
version: 1.0.0
---

# harness-vila — Aplicação do Harness Architect na Vila INTEIA

Skill local que é **filha** da skill global `harness-architect`. Traz o plano específico da Vila sem precisar carregar toda a teoria de novo.

## O que carregar e em que ordem

1. **Sempre primeiro**: `C:\Agentes\vila-inteia\HARNESS_VILA.md` (ou `docs/HARNESS_VILA.md` após Onda 1) — este é o documento mestre com diagnóstico + 4 ondas.
2. **Se implementando código**: `C:\Agentes\vila-inteia\engine\harness\README.md` — mapa de módulos + princípios.
3. **Se precisar de teoria canônica**: skill global `harness-architect` em `~/.claude/skills/harness-architect/` (carregar referência apropriada, ex: `02-memory-architectures.md` para Gap #5).

## Mapa rápido — trigger → ação

| Usuário fala em… | Carregue e abra |
|------------------|-----------------|
| "custo LLM alto", "tokens", "prompt gigante" | HARNESS_VILA.md §3.2 (Gap #2, orçamento) |
| "debug agente", "porque o X fez Y", "trace" | HARNESS_VILA.md §3.1 (Gap #1, observability) |
| "oficinas", "técnica de problem solving", "Van Aken" | HARNESS_VILA.md §3.3 (Gap #3, skills canônicas) |
| "integrar Helena", "chamar Mirante", "adapter novo" | HARNESS_VILA.md §3.4 (Gap #4, protocolos) |
| "Igor esqueceu", "fundador", "CLAUDE.md na Vila" | HARNESS_VILA.md §3.5 (Gap #5, ficha do fundador) |
| "artigo constitucional", "testar constituição" | HARNESS_VILA.md §3.6 (Gap #6, policy) |
| "autoresearch", "evolução de skill", "cross-cutting" | HARNESS_VILA.md §3.7 (Gap #7, 6 fluxos) |
| "Colmeia usa Vila", "Helena simular cenário" | HARNESS_VILA.md §6 (Colmeia como harness distribuído) |

## Regra de ouro

Nunca editar `engine/cognitivo/`, `engine/memoria/`, `engine/oficinas.py`, `engine/chateaubriand.py`, `engine/constituicao.py` ou `engine/ia_client.py` **sem primeiro responder em qual Onda/Gap a mudança se enquadra** segundo HARNESS_VILA.md. Se não enquadrar em nenhum, pergunte ao Igor se é trabalho fora do plano ou se é gap novo a documentar.

## Anti-padrões que a Vila evita

- Adicionar novo `_client.py` ad-hoc em vez de capability card
- Injetar prompt grande em fase cognitiva sem declarar orçamento
- Criar oficina nova sem manifest (nível 1 ≤50 tokens)
- Alterar artigo constitucional sem registrar `evento_origem`
- Fazer chamada LLM sem emitir `TraceEvent`

Todos esses são bloqueios de revisão.
