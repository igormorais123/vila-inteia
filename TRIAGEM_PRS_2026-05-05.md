# Triagem de PRs Abertos — vila-inteia (onda 289)
Data: 2026-05-05

## Resumo Executivo

Total de PRs abertos: **25**

| Classificação | Qtde | Ação |
|---|---|---|
| **STALE** | 24 | Fechar sem merge (superadas ou descontinuadas) |
| **REVISITAR** | 0 | Decisão técnica pendente |
| **MERGEAR** | 1 | Merge imediato (já feito) |

---

## Detalhamento por Onda

### STALE — Bloco 1: Ondas 115-191 (22 PRs)

Padrão: linha de experimento paralela abandonada após onda 196. Ondas 197-289 (exceto 281-282) representam continuação diferente mergeada em main.

| PR# | Onda | Branch | Razão |
|---|---|---|---|
| #69 | 115 | feat/onda115-persona-skill-endpoint | Onda nunca mergeada; superseded 197+ |
| #113 | 157 | feat/onda157-platt-iso-20ev | Onda nunca mergeada; calibração pulada |
| #114 | 160 | feat/onda160-autoresearch-resume | Onda nunca mergeada; autoresearch descontinuada |
| #115 | 161 | feat/onda161-autoresearch-resume | Onda nunca mergeada; versão old |
| #116 | 162 | feat/onda162-conformal | Onda nunca mergeada; conformal pulado |
| #117 | 164 | feat/onda164-multi-model-ensemble | Onda nunca mergeada; superseded por 216-217 |
| #118 | 165 | feat/onda165-prompt-variant-ensemble | Onda nunca mergeada; descontinuada |
| #119 | 166 | feat/onda166-multi-model-wire | Onda nunca mergeada; descontinuada |
| #120 | 167 | feat/onda167-paper-update | Onda nunca mergeada; artigo reescrito |
| #121 | 168 | feat/onda168-autoresearch-sa | Onda nunca mergeada; SA descontinuado |
| #122 | 170 | feat/onda170-compare-backtests | Onda nunca mergeada; CLI superado |
| #123 | 171 | feat/onda171-karpathy-full | Onda nunca mergeada; Karpathy pulado |
| #124 | 172 | feat/onda172-timing-overnight | Onda nunca mergeada; timing superado |
| #125 | 173 | feat/onda173-autoresearch-run1-results | Onda nunca mergeada; trace descontinuado |
| #126 | 175 | feat/onda175-meta-autoresearch | Onda nunca mergeada; meta-learning pulado |
| #127 | 182 | feat/onda182-scout2-trace | Onda nunca mergeada; scout descontinuado |
| #128 | 183 | feat/onda183-120b-trace | Onda nunca mergeada; baseline superseded |
| #129 | 184 | feat/onda184-fix-circuit-breaker | Onda nunca mergeada; fix descontinuado |
| #130 | 184 | feat/onda184b-fix-validated | Onda nunca mergeada; validação descontinuada |
| #131 | 190 | feat/onda190-6ev-trace | Onda nunca mergeada; 6-event pulado |
| #132 | 191 | feat/onda191-model-rotation | Onda nunca mergeada; rotation descontinuado |
| #133 | 191 | feat/onda191c-rotate-trace | Onda nunca mergeada; rotation pulado |

### STALE — Bloco 2: Ondas 281-282 (2 PRs)

Padrão: experimento recente descontinuado. Ondas 284-285-289 foram mergeadas, 281-282 não.

| PR# | Onda | Branch | Razão |
|---|---|---|---|
| #214 | 281 | feat/onda281-vila-llm-hybrid | Hybrid LLM pulado; 284+ levou adiante |
| #215 | 282 | feat/onda282-llm-coordinator | LLM-coordinator descontinuado; 284+ diferente |

### MERGEADO — 1 PR

| PR# | Onda | Branch | Razão |
|---|---|---|---|
| #217 | 284 | feat/onda284-btc-cohort | MERGEADO em 2026-05-04, commit 352e06a |

---

## Critério de Classificação Aplicado

- **STALE**: onda referenciada não mergeada em main E (>14 dias sem update OU onda foi descontinuada em favor de posterior)
- **REVISITAR**: onda não mergeada mas <14 dias sem update E tema ainda aberto
- **MERGEAR**: onda mergeada ou válido para merge imediato

---

## Recomendação

Fechar todas as 24 PRs STALE sem merge. Não há decisão técnica pendente — todas foram abandonadas por razões de design (linha paralela descontinuada ou experimento curto que evoluiu diferente em versão posterior).
