# AutoResearch Program — Vila INTEIA accuracy optimization

**Inspired by**: [Karpathy/autoresearch](https://github.com/karpathy/autoresearch) (2026-03).

## Objective

Minimize `brier_blend_final_avg` aggregate over ≥3 datasets. Lower is better.

Baseline (Onda 158): ~0.10-0.12 brier_blend over impeachment + crypto + eleicao_pres (9 events, llama-4-scout real).

## Constraints

- Cannot change prompt structure pre-Onda 134 (outcome_framing, CoT, anchor_scale are baseline features).
- Cannot recalibrate `calibracao_platt.json` mid-loop (invalidates comparisons).
- Each experiment = backtest_acc run, costs ~2k tokens per event × 3 personas × 3 events per dataset = ~18k/dataset.

## Proposal Space (engine/autoresearch_accuracy.py:PROPOSAL_SPACE)

Flags:
- `usar_debate` (Onda 124) — quality up, cost 3x
- `usar_peso_adaptativo` (Onda 137) — Aumann-based peso_vila
- `usar_blend_ensemble` (Onda 147) — mediana de pesos
- `chain_of_thought` — CoT structured
- `aplicar_platt` — calibracao runtime
- `usar_self_consistency` (Onda 129) — multi-sample, cost 3x
- `temp_por_persona` (Onda 158) — arquétipo temps
- `aplicar_calib_por_persona` (Onda 156)

Ranges:
- `peso_vila` [0.5, 0.9] step 0.05
- `prob_floor` [0.0, 0.15] step 0.025
- `prob_ceiling` [0.85, 1.0] step 0.025
- `recency_decay` [0.7, 1.0] step 0.05

Choices:
- `few_shot_k` {0, 1, 2, 3}
- `n_samples_sc` {2, 3, 5}

## Research Directions (for human-curated proposals)

1. **Prior humano já bate Vila em crypto**. Raise `peso_vila < 0.5` em dataset crypto? Dataset-conditional peso.
2. **imp03 solved via outcome_framing**. Validar que manter flag ativa não regride outros datasets.
3. **peso_adaptativo + blend_ensemble** interage. Testar OFF vs ambos ON.
4. **temp_por_persona** não testado empiricamente. Priority proposal.
5. **Self-consistency** custa 3x — só considerar se Δbrier > 10%.

## Workflow

```bash
# 2 datasets, 10 iter, seed 42
python scripts/autoresearch_vila.py --iter 10 --seed 42

# Trace: data/autoresearch_trace.jsonl (append-only)
# Best config: stdout + última linha kept=true no trace
```

## Success criteria

- Find config with brier_blend < 0.08 on 3+ datasets, OR
- Beat baseline by ≥10% sustained across 3+ datasets, OR
- Document that current baseline is near-optimal for this stack.

## Stop conditions

- `max_iteracoes` reached (default 10)
- `max_sem_melhoria` consecutive reverts (default 5)
- Manual Ctrl-C (trace preserved, resumable)
