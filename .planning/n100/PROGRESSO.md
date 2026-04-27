# Progresso da Campanha N=100

> Atualizado: 2026-04-27
> Estado: **Onda 163 real run em execução** (probe contra LLM)

## Linha do tempo

| Onda | Descrição | Status | Commit |
|---|---|---|---|
| 160 | xhigh STRATEGY.md v1 (5.7KB) | ✅ | 812fd81 |
| Audit | Helena audita v1: 4 P1 + 5 P2 | ✅ | (chat) |
| 160b | xhigh STRATEGY_v2.md (15.8KB) | ✅ | 812fd81 |
| EXEC | Oracle Gnosis EXECUCAO.md | ✅ | 812fd81 |
| 162 | Schema EventoPreditivoV1 + 12 testes + 9 legacy importados | ✅ | 0766b99 |
| 163 | outcome_probe runner + 15 testes + dry-run validado | ✅ | eeba736 |
| 163R | Probe real contra LLM nos 100 legacy | 🔄 em execução | — |
| 164 | Calibração ROC do threshold (estrutura) | ✅ | 37de405 |
| 164R | ROC com dados reais → decisão final do threshold | ⏳ aguarda 163R | — |
| 165 | Curadoria primeiro batch (30 candidatos novos) | ⏸️ aguarda Igor | — |
| 166 | Helena audit checkpoint A | ⏸️ | — |
| 167 | Baseline backtest 30 novos | ⏸️ | — |

## Decisões já tomadas

**Helena P1.1 (calibração)** — Platt/isotonic fitada apenas em `tune`. Implementado no STRATEGY_v2 e respeitado nas próximas ondas.

**Helena P1.2 (probe)** — Threshold 0.65 congelado em `engine/outcome_probe.py:LEAKAGE_THRESHOLD_DEFAULT`. Validação ROC em Onda 164 confirma ou ajusta.

**Helena P1.3 (legacy)** — 9 eventos legacy em `data/n100/legacy_v1.jsonl` com `split=legacy_sanity`. Não entram no AutoResearch nem no claim final.

**Helena P1.4 (gate)** — Critério bootstrap pareado 10k iter, IC 95% < 0.05, p-valor < 0.10. A implementar na Onda 177.

**Oracle (P2.5)** — Métrica primária = `skill_score_blend_vs_prior_holdout`. Brier secundário.

**Oracle (P2.6)** — Split tune=35 / gate=15 / holdout=50. Não 45/15/40.

**Oracle (budget)** — 24M tokens autorizados por Igor (2026-04-27).

## Próximas portas

1. ⏳ Aguardar conclusão da Onda 163R (probe real, ~10 min)
2. Rodar Onda 164R: `python scripts/analisar_probe.py` com dados reais
3. Decisão Oracle: threshold 0.65 mantido ou ajustado
4. Onda 165: curadoria do primeiro batch de 30 eventos novos (esportes 10, eleições 5, IPOs 5, earnings 5, mercados 5)

## Métricas de cota

| Recurso | Estimado | Consumido até agora |
|---|---:|---:|
| Tokens xhigh (estratégia + v2) | 500k | 500k |
| Tokens mini (testes/scripts) | 0 | 0 |
| Tokens probe real (Onda 163R) | 200k | em curso |
| Tokens curadoria + baseline (165-167) | 2M | 0 |
| **Total estimado campanha** | **24M** | **~700k** |

## Status agentes

- **xhigh**: stand-by até Onda 174 (mudanças no PROPOSAL_SPACE) ou Onda 180 (claim final).
- **mini**: stand-by até Onda 165 (curadoria) ou run real do probe (em curso via ia_client).
- **Helena**: stand-by até Onda 166 (checkpoint A do primeiro batch).
- **Oracle Gnosis**: monitorando, decide Onda 164R quando dados reais chegarem.
- **Efesto**: executor — disponível.
