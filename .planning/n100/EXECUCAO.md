# EXECUÇÃO N=100 — Plano Operacional Oracle Gnosis

> Comanda: Oracle Gnosis (metodologia)
> Audita: Helena Strategos Inteia (epistemologia)
> Coordenação: GPT-5.5 xhigh (estratégia, mudanças P1)
> Execução: GPT-5.5 mini (loops, scraping, batch)
> Repositório alvo: `C:\Agentes\vila-inteia`
> Documento mãe: `.planning/n100/STRATEGY.md` (a ser substituído por v2)
> Versão: 1.0 (2026-04-27)

## Pergunta de pesquisa

Qual a precisão preditiva calibrada da Vila INTEIA em N=100 eventos com holdout cego, controlando leakage de pré-treinamento dos LLMs e overfit do AutoResearch?

## Decisões metodológicas (Oracle não delega)

1. **Métrica primária**: `skill_score_blend_vs_prior_holdout` com bootstrap pareado IC 95% excluindo zero. Brier absoluto vira métrica secundária. Razão: priors variam por categoria (NBA closing line ≈ 0.55 vs IPO consenso ≈ 0.50 vs paper ICLR ≈ 0.30), então Brier absoluto é incomparável entre categorias; skill score normaliza.
2. **Split final**: `tune=35` / `gate=15` / `holdout=50` — adoto a contraposta da Helena (P2.6). Razão: power analysis com brier esperado 0.13-0.18 e IC 95% binomial-like exige n≥50 no holdout para largura < 0.08.
3. **Ordem dos testes**: leakage probe ANTES de qualquer baseline. Dataset legacy é probado primeiro para calibrar threshold do probe contra eventos com brier conhecido.
4. **Agregação**: por categoria (esportes, eleições, IPOs, earnings, mercados, papers) com weighted average ponderado por raiz de N. Reportar também sem ponderação para sensibilidade.
5. **Não-decisão**: budget de tokens (cabe ao Igor aprovar 6-8M). Mudança de holdout depois de aberto (P1). Publicação externa do claim (P1).

## Hierarquia de evidência usada nesta operação

- **Primária**: outcome real verificado em fonte oficial (TSE, SEC, NBA box score, Polymarket resolution).
- **Secundária**: prob_oraculo_humano congelada antes do evento (closing line, polling agregador, prediction market price).
- **Operacional**: brier/skill_score computados pelo `engine/backtest_acc.py`.
- **Diagnóstica**: outcome_probe (não vai no claim final, só filtra eventos).

## Plano em ondas (160-180)

### Pré-execução (bloqueantes Helena P1)

#### Onda 160 — STRATEGY_v2.md (P1.1, P1.2, P1.3, P1.4)
- **Input**: STRATEGY.md atual + auditoria Helena (4 P1).
- **Output**: `.planning/n100/STRATEGY_v2.md` com:
  - Calibração Platt/isotonic fitada **apenas em tune**, congelada antes do gate.
  - `outcome_probe` operacionalizado: rodar GPT-5.5-mini sem contexto, 3 paráfrases da pergunta, threshold 0.65 de média de probabilidade do outcome correto → "alto leakage".
  - 9 eventos legacy excluídos do AutoResearch; usados em `legacy_sanity` (não conta no claim).
  - Critério de aceite do gate: bootstrap pareado 10k iter sobre `brier_gate − brier_tune`, aceitar se IC 95% superior < 0.05 E p-valor unilateral < 0.10.
  - Split final: tune=35, gate=15, holdout=50.
  - Skill_score como métrica primária.
- **Agente**: xhigh (`codex exec --reasoning xhigh`).
- **Comando**: `codex exec - -s read-only -c 'model_reasoning_effort="xhigh"' --json < /tmp/v2_prompt.txt > /tmp/v2_out.jsonl`.
- **Saída**: arquivo gerado, validado por Oracle (eu).
- **Estimativa**: 1 chamada xhigh ≈ 250k tokens.

#### Onda 161 — Re-auditoria Helena (rápida)
- **Input**: STRATEGY_v2.md.
- **Output**: comentário curto em `.planning/n100/audit_v2.md`. Verdict: APROVADO ou REPROVADO (sem terceira via).
- **Agente**: Helena (skill `/helena`, modo=auditar_breve).
- **Saída**: verdict APROVADO. Se REPROVADO, retornar à 160.
- **Estimativa**: ≈ 5k tokens contexto.

### Infraestrutura (Helena P2.7, P2.8, P2.9)

#### Onda 162 — Schema + validador + conversor
- **Input**: schema EventoPreditivoV1 do STRATEGY_v2.md.
- **Output**:
  - `engine/eventos_v1.py` — Pydantic models, `from_csv_legado()`, `to_csv_legado()`.
  - `tests/test_eventos_v1.py` — roundtrip JSONL↔CSV; 11 casos.
  - `data/n100/schema_v1.json` — JSON schema exportado.
- **Agente**: mini (`codex exec --model gpt-5.5-mini`).
- **Comando**: tarefa via codex-companion.mjs com `--write`.
- **Saída**: pytest passa, conversor preserva 9 legacy → `data/n100/legacy_v1.jsonl`.
- **Estimativa**: ≈ 100k tokens.

#### Onda 163 — outcome_probe runner
- **Input**: schema + spec do probe.
- **Output**:
  - `engine/outcome_probe.py` — função `probar_evento(evento, modelo, n_paráfrases=3)` retorna `{p_outcome, std, n_validas}`.
  - `scripts/rodar_probe_legacy.py` — roda probe nos 100 eventos do `data/backtest/*.csv`.
  - `data/n100/probe_legacy_results.jsonl`.
- **Agente**: mini.
- **Saída**: relatório com distribuição de p_outcome dos 100; threshold 0.65 separa quantos como "alto leakage".
- **Estimativa**: 100 eventos × 3 paráfrases × 1k tokens ≈ 300k tokens.

#### Onda 164 — Calibração do threshold de probe
- **Input**: probe_legacy_results + brier real dos 9 legacy.
- **Output**: `.planning/n100/probe_calibracao.md` com:
  - Curva ROC do probe contra "evento que Vila acertou trivialmente".
  - Justificativa do threshold final (0.65 ou ajustado).
  - Lista dos 100 legacy classificados em `baixo/médio/alto leakage`.
- **Agente**: Oracle (eu) + mini para os cálculos.
- **Saída**: threshold congelado.
- **Estimativa**: ≈ 50k tokens.

### Curadoria (Helena P2.7 fica restrito)

#### Onda 165 — Curadoria primeiro batch (30 candidatos novos)
- **Input**: STRATEGY_v2.md categorias.
- **Output**: `data/n100/candidates_raw.jsonl` com 30 candidatos:
  - 10 jogos NBA com closing spread (temporada 2024-25 pós-cutoff Llama-4).
  - 5 eleições municipais BR 2024 (2º turno em municípios > 200k habitantes).
  - 5 IPOs 2024-2025 com primeiro mês fechado.
  - 5 earnings reports 2024-Q4 (Mag 7).
  - 5 mercados Polymarket/Kalshi resolvidos pós-cutoff modelo.
- **Agente**: mini com tasks separadas por categoria; cada categoria = 1 task com `--write`.
- **Saída**: 30 candidatos JSONL com schema válido, todos com `audit_status=pendente`.
- **Estimativa**: ≈ 600k tokens (curadoria via web fetch).

#### Onda 166 — Auditoria Helena pré-predição (checkpoint A)
- **Input**: candidates_raw.jsonl + probe results dos 30.
- **Output**:
  - Cada candidato vira `aprovado_helena` ou `vetado_helena`.
  - Razão de veto registrada em `audit_log` no JSONL.
  - Meta: aceitar ≥ 25 dos 30 (taxa de veto < 17%).
- **Agente**: Helena.
- **Saída**: `data/n100/events_v1.jsonl` com candidatos aprovados; veto > 17% trigger investigação de viés de curadoria.
- **Estimativa**: ≈ 150k tokens contexto (Helena lê tudo).

### Execução (a campanha começa aqui)

#### Onda 167 — Baseline backtest sem AutoResearch (30 eventos novos)
- **Input**: events_v1.jsonl aprovados (≥ 25).
- **Output**:
  - `data/n100/baseline_run_001.json` com prob_vila, brier, transcript hashes.
  - Reportar por categoria.
- **Agente**: mini executa `engine/backtest_acc.py` com config padrão atual.
- **Saída**: brier por evento + categoria; sem otimização ainda.
- **Estimativa**: 25 eventos × 3 personas × 18k tokens ≈ 1.4M tokens.

#### Onda 168 — Auditoria Helena pós-batch (checkpoint B)
- **Input**: baseline_run_001 + transcripts.
- **Output**: relatório curto Helena: drift entre categorias, framings ruins residuais, transcript anomalies.
- **Agente**: Helena.
- **Saída**: lista de eventos a re-curar (se houver).
- **Estimativa**: ≈ 80k tokens.

#### Onda 169-171 — Curadoria batches 2, 3, 4 (descer até N=70 aprovados)
- Mesma estrutura das 165-166 repetida 3 vezes:
  - Onda 169: curar +25 candidatos (categorias underrepresented).
  - Onda 170: Helena audita.
  - Onda 171: curar +25 finais (papers OpenReview ICLR 2025, decisões STF 2024-25).
- **Saída**: 70-80 eventos aprovados em `events_v1.jsonl`.
- **Estimativa**: ≈ 1.5M tokens curadoria.

#### Onda 172 — Atribuição de splits
- **Input**: events_v1.jsonl com ≥ 100 aprovados (target: 100 limpos = 35+15+50).
- **Output**: cada evento ganha `split = tune | gate | holdout`. Estratificação:
  - Por categoria (proporção igual em cada split).
  - Temporal (gate e holdout têm eventos mais recentes).
  - Hash determinístico para reprodutibilidade: `split = stratified_split(evento.id, seed=42)`.
- **Agente**: Oracle (eu) executando script mini-gerado.
- **Saída**: `data/n100/events_v1.jsonl` com splits congelados; `data/n100/split_manifest.json` com hash SHA256 da atribuição.
- **Estimativa**: ≈ 30k tokens.

#### Onda 173 — Backtest baseline em todos os splits (sem otimização)
- **Input**: events com splits.
- **Output**: brier baseline em cada split, separado.
- **Agente**: mini.
- **Saída**: 3 arquivos `baseline_tune.json`, `baseline_gate.json`, `baseline_holdout.json` (este último é para diagnóstico só, não conta no claim).
- **Estimativa**: 100 × 3 × 18k ≈ 5.4M tokens.

> ⚠️ Decisão Oracle: rodar baseline no holdout AGORA, antes do AutoResearch, é metodologicamente discutível porque revela info do holdout. Mitigação: o brier_baseline_holdout fica selado em arquivo criptografado e só é aberto pela Helena depois do freeze. Razão para rodar agora: detectar parser failure rate antes que vire problema final.

#### Onda 174 — AutoResearch loop (apenas tune)
- **Input**: 35 eventos `tune` + config baseline.
- **Output**:
  - `data/autoresearch_trace_n100.jsonl` (append-only).
  - `data/n100/best_config_tune.json` com config vencedora.
  - Stop: `max_iteracoes=30` ou `max_sem_melhoria=5`.
- **Agente**: mini executa `scripts/autoresearch_vila.py`.
- **Comando**: `python scripts/autoresearch_vila.py --eventos data/n100/events_v1.jsonl --filter split=tune --iter 30 --seed 42`.
- **Saída**: best_config + brier_tune final.
- **Estimativa**: 30 × 35 × 3 × 18k ≈ 56M tokens. **PROIBITIVO**.

> ⚠️ Decisão Oracle: 56M é incompatível com cota Team. Reduzir AutoResearch para amostragem: 30 iter × **subset de 12 eventos tune** balanceado por categoria. Resto dos 35 entra só na avaliação final do tune. Custo cai para 30 × 12 × 3 × 18k ≈ 19M ainda alto. **Reduzir paralelismo de personas para 2 durante AutoResearch** (panel de 3 só na avaliação final). Custo: 13M tokens. Aceitável se Igor aprovar.

#### Onda 175 — Avaliação final em tune (com config congelada)
- **Input**: best_config_tune + 35 eventos tune.
- **Output**: `brier_tune_final` com 3 personas.
- **Agente**: mini.
- **Estimativa**: 35 × 3 × 18k ≈ 1.9M tokens.

#### Onda 176 — Calibração Platt/isotonic em tune apenas
- **Input**: probs_tune_raw + outcomes_tune.
- **Output**: `data/n100/calibracao_n100.json` (Platt + isotonic), auto-select via brier.
- **Agente**: mini executa `engine/calibracao_auto.py`.
- **Saída**: calibração congelada com hash. Helena assina.
- **Estimativa**: ≈ 20k tokens (puro cálculo).

#### Onda 177 — Gate (15 eventos, uma medição única)
- **Input**: best_config + calibração congelada + 15 eventos gate.
- **Output**: brier_gate, skill_score_gate.
- **Agente**: mini.
- **Critério**: bootstrap pareado 10k iter sobre `brier_gate − brier_tune`. Aceitar se IC 95% superior < 0.05 E p-valor unilateral < 0.10.
- **Saída**: APROVADO (vai pro holdout) ou REPROVADO (campanha aborta, fracasso reportado).
- **Estimativa**: 15 × 3 × 18k ≈ 800k tokens.

#### Onda 178 — Auditoria Helena pré-holdout (P1 final)
- **Input**: tudo congelado: config, calibração, splits, transcripts.
- **Output**: assinatura Helena em `.planning/n100/freeze_manifest.json` com hashes SHA256 de tudo. Sem assinatura, holdout não abre.
- **Agente**: Helena.
- **Saída**: freeze assinado.

#### Onda 179 — Holdout final (50 eventos)
- **Input**: best_config + calibração congeladas + 50 eventos holdout.
- **Output**: brier_holdout, skill_score_holdout, IC 95% bootstrap pareado.
- **Agente**: mini.
- **Estimativa**: 50 × 3 × 18k ≈ 2.7M tokens.

#### Onda 180 — Relatório final
- **Input**: todos os números.
- **Output**: `.planning/n100/RELATORIO_FINAL.md` com:
  - Skill score primário + IC.
  - Brier absoluto secundário.
  - Decomposição por categoria.
  - Comparação com 9 legacy (sanity check).
  - Limites e lacunas (Oracle obrigatório).
  - Decisão: claim defensável ou não.
- **Agente**: Oracle (eu) escreve, Helena revisa, Igor decide publicar.

## Cronograma e checkpoints

| Marco | Onda | Tokens cumulativo | Decisão Igor? |
|---|---:|---:|---|
| STRATEGY_v2 aprovada | 161 | 0.3M | Não |
| Schema + probe rodando | 164 | 0.7M | Não |
| 30 eventos curados aprovados | 166 | 1.5M | Não |
| Baseline 30 eventos | 168 | 3M | **Sim — review brier inicial antes de continuar** |
| 100 eventos curados | 171 | 5M | **Sim — autorizar AutoResearch** |
| AutoResearch concluído | 174 | 18M | Não (Oracle decide) |
| Gate aprovado | 177 | 21M | Não |
| Freeze assinado | 178 | 21.1M | **Sim — autorizar holdout** |
| Holdout finalizado | 179 | 24M | Não |
| Relatório final | 180 | 24.2M | **Sim — decisão de claim** |

**Total estimado: 24M tokens**. Acima dos 6-8M da Helena, abaixo dos 56M ingênuos. Diferença vem de manter 3 personas em todas as avaliações finais e do AutoResearch reduzido (P2.9 da Helena revisado para cima).

## Limites e lacunas

1. **Cobertura categórica**: 6 categorias não esgotam o espaço de eventos preditivos. Resultado generaliza para mix similar; não para categorias ausentes (clima, saúde pública, esporte individual).
2. **Cutoff dos LLMs**: Llama-4-scout cutoff é incerto; mitigação via outcome_probe é heurística, não prova.
3. **Outcome objetivo**: 6 categorias têm outcomes fechados. Eventos abertos (e.g., "X será reeleito em N anos") ficam fora.
4. **Bootstrap pareado**: assume independência entre eventos. Eventos do mesmo dataset (mesma categoria) podem ser correlacionados — IC pode estar subestimado. Mitigação: agregação por categoria.
5. **Auditoria Helena single-blind**: Helena não vê transcripts cegamente. Em trabalho futuro, blind audit com hash-only seria superior.
6. **Cota Codex Team**: campanha consome ~24M tokens em ~10 dias úteis. Janela de cota da assinatura precisa ser monitorada.

## Próximo passo

Disparar **Onda 160** imediatamente: xhigh produz STRATEGY_v2.md respeitando os 4 P1 da Helena. Comando preparado em `/tmp/v2_prompt.txt`, executar via codex exec stdin redirect com xhigh.

Após 160 e 161 aprovadas, avançar para infraestrutura sem novas escaladas.

— Oracle Gnosis
*Diretor de Pesquisa e Conhecimento. Método antes de conclusão.*
