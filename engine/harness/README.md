# engine/harness/ — Camada de Harness da Vila

> Pacote que materializa as **6 dimensões do Harness** (Zhou et al. 2026) sobre a base cognitiva já existente em `engine/cognitivo/` + `engine/memoria/`.
>
> Plano mestre: [`../../docs/HARNESS_VILA.md`](../../docs/HARNESS_VILA.md) (ou `HARNESS_VILA.md` na raiz enquanto não for movido).
> Skill global aplicada: `harness-architect` (v1.1.0, em `~/.claude/skills/harness-architect/`).

---

## Mapa de módulos previstos

| Arquivo | Onda | Responsabilidade | Status |
|---------|------|------------------|--------|
| `observabilidade.py` | 2 | `TraceEvent`, `@trace_fase`, escrita em `vila_traces` | ⏳ planejado |
| `orcamento.py` | 2 | Orçamento de contexto por fase + `caber_ou_resumir` | ⏳ planejado |
| `skill_registry.py` | 3 | Descoberta semântica de oficinas + staged loading | ⏳ planejado |
| `protocolos/` | 3 | Capability cards MCP-like + registry + servidor opcional | ⏳ planejado |
| `policy_engine.py` | 4 | Executor de artigos constitucionais em formato `.toml` | ⏳ planejado |
| `flows.py` | 4 | Os 6 fluxos cross-cutting explícitos | ⏳ planejado |

---

## Princípios de design desta camada

1. **Não quebrar o loop 24/7 de produção.** Toda mudança passa primeiro por *shadow mode* (escreve trace/orçamento mas não altera comportamento) antes de virar load-bearing.
2. **Reutilizar o que já está bom.** `engine/cognitivo/` é o Agent Loop canônico. `constituicao.py` é policy layer. `chateaubriand.py` é approval gate. Não reescrever — embrulhar.
3. **Observabilidade antes de tudo.** Nenhuma otimização sem trace. Nenhum corte de custo sem medir.
4. **Capability cards > adapters ad-hoc.** Integrações externas novas entram via card `.toml`, não via novo `.py`.
5. **Escrever manifest antes do conteúdo.** Toda skill/oficina nova começa por SKILL.md com as 3 camadas (procedimento + heurística + restrição).

---

## Como um novo módulo deve nascer aqui

```bash
# 1. Abra issue com base em HARNESS_VILA.md (Onda X, Gap Y)
# 2. Crie branch harness/<nome>
# 3. Stub em modo shadow:
touch engine/harness/meu_modulo.py  # só coleta, não altera
# 4. Rodar 100+ steps em shadow, comparar métricas
# 5. Promover para load-bearing em PR separado com rollback plan
```

---

## Integração com a skill `harness-architect`

Ao abrir sessão Claude Code neste repositório, a skill `harness-architect` é auto-invocada pelos triggers (`harness`, `arquitetura de agente`, `Vila INTEIA`, etc). Ela carrega:

- `SKILL.md` (manifest + modelo mental)
- `references/05-harness-design.md` (6 dimensões)
- `references/10-use-cases.md` (onde casos 1, 3, 5, 6, 9 se aplicam à Vila)

Em seguida, o agente consulta **este** README + `HARNESS_VILA.md` para contexto específico do projeto e procede com a Onda planejada.

---

## Estado atual

- **Onda 1** (documentação + renomeação): ⏳ em andamento — este README é o primeiro artefato.
- **Onda 2** (observability + orçamento): ❌ não iniciada.
- **Onda 3** (skills + protocolos): ❌ não iniciada.
- **Onda 4** (fundador + constituição policy + fluxos): ❌ não iniciada.
