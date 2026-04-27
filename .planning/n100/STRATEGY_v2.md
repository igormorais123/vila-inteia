# Estratégia N=100 — Validação Preditiva Vila INTEIA — v2 (2026-04-27)

## CHANGELOG vs v1

- P1.1: calibração Platt/isotonic agora é fitada apenas em `tune` e congelada antes do `gate`.
- P1.2: `outcome_probe` virou definição operacional com GPT-5.5-mini sem contexto, 3 paráfrases e threshold fixo `0.65`.
- P1.3: legacy saiu do AutoResearch e do claim: `tune=35`, `gate=15`, `holdout=50`, todos novos; `legacy_sanity=9` separado.
- P1.4: critério de gate agora usa bootstrap pareado de 10.000 iterações sobre `delta = brier_gate - brier_tune`.
- A: métrica primária passou a ser `skill_score_blend_vs_prior`; Brier absoluto é secundário.
- B: split definitivo ajustado para `35/15/50`, com `holdout >= 50`.
- C: Polymarket/Kalshi/Metaculus pré-curadoria são `leakage_alto` por padrão e passam obrigatoriamente pelo `outcome_probe`.
- D: auditoria Helena passa a ter dois checkpoints por batch.
- E: budget revisado para 24M tokens.

## 1. CURADORIA DE EVENTOS

Objetivo: construir uma validação preditiva com `N=100` eventos novos, binários, resolvidos e auditáveis, sem usar os 9 eventos legados no claim final.

Estado atual:
- Vila INTEIA tem 159 ondas implementadas.
- Resultado atual em `N=9`: Brier aproximado `0.10–0.12`.
- Existem 100 eventos legacy em `data/backtest/*.csv`, organizados em 10 datasets × 10 eventos.
- Esses eventos legacy não entram no AutoResearch nem no claim final v2.

Meta operacional:
- Curar pelo menos 120 candidatos brutos.
- Aprovar 100 eventos novos finais.
- Separar adicionalmente 9 eventos legacy apenas para `legacy_sanity`.

| Categoria | Alvo aprovado | Custo esperado | Leakage inicial | Viabilidade Igor |
|---|---:|---|---|---|
| Jogos NBA/NFL/futebol com spread/over-under fechado | 20 | Baixo, 4–6h | Médio | Alta |
| Eleições municipais BR 2020/2024 com 2º turno | 18 | Médio, 8–12h | Médio-alto | Média-alta |
| Decisões STF/TSE/STJ colegiadas | 10 | Alto, 10–15h | Alto | Média |
| IPOs/listagens: acima do IPO no 30º dia? | 12 | Médio, 6–8h | Médio | Alta |
| Earnings: bateu consenso e ação subiu no dia seguinte? | 12 | Médio-alto, 8–10h | Médio | Média |
| Mercados preditivos resolvidos: Polymarket/Kalshi/Metaculus | 12 | Baixo-médio, 5–7h | Alto | Alta |
| OpenReview: paper aceito em ICLR/NeurIPS? | 16 | Médio, 8–12h | Baixo-médio | Média |

Total aprovado: 100 eventos novos.

Regras de inclusão:
- outcome binário, verificável e não trivial;
- `data_corte_informacao < data_resolucao`;
- fonte de outcome separada da fonte pré-corte;
- pergunta congelada antes da predição;
- prior humano permitido apenas se registrado antes da resolução ou reconstruído de fonte datada;
- eventos com `outcome_probe_mean >= 0.65` vão para `reserve`, não para `holdout`;
- eventos de Polymarket/Kalshi/Metaculus são marcados como `leakage_alto` pré-curadoria e submetidos obrigatoriamente ao `outcome_probe`; se `p >= 0.65`, vão para `reserve`.

## 2. ESQUEMA DE DADOS

Canônico: `data/n100/events_v2.jsonl`.

CSV legado é derivado apenas para compatibilidade com runners existentes.

```python
class FonteEvento(BaseModel):
    url: str
    titulo: str
    data_publicacao: date | None
    acessado_em: date
    tipo: Literal[
        "contexto_pre_corte",
        "outcome",
        "prior_humano",
        "auditoria",
    ]


class OutcomeProbeResult(BaseModel):
    model: Literal["gpt-5.5-mini"]
    threshold: Literal[0.65]
    prompt_version: str
    probs_outcome_correto: list[float]
    mean_prob: float
    classification: Literal["leakage_baixo", "leakage_alto"]


class EventoPreditivoV2(BaseModel):
    schema_version: Literal["v2"] = "v2"
    id: str
    dataset: str
    split: Literal[
        "tune",
        "gate",
        "holdout",
        "reserve",
        "legacy_sanity",
    ]
    categoria: str

    pergunta: str
    outcome_framing: str
    contexto_pre_corte: str
    regra_resolucao: str
    outcome_binario: Literal[0, 1]

    prob_prior_baseline: float = Field(..., ge=0, le=1)
    tipo_prior_baseline: Literal[
        "closing_odds",
        "polling",
        "prediction_market",
        "analyst_consensus",
        "base_rate",
        "uniform_0_5",
    ]

    data_corte_informacao: date
    data_resolucao: date
    fonte_contexto_pre_corte: list[FonteEvento]
    fonte_outcome: list[FonteEvento]
    fonte_prior_baseline: list[FonteEvento] = []

    leakage_risk_pre_probe: Literal["baixo", "medio", "alto"]
    outcome_probe: OutcomeProbeResult | None
    leakage_mitigations: list[str] = []

    audit_status_checkpoint_a: Literal[
        "pendente",
        "aprovado_helena",
        "vetado_helena",
    ]
    audit_status_checkpoint_b: Literal[
        "pendente",
        "aprovado_helena",
        "vetado_helena",
    ]

    transcript_hash: str | None = None
    manifest_hash: str | None = None
```

Mapeamento para CSV legado:
- `evento_id = id`
- `data = data_corte_informacao`
- `contexto = contexto_pre_corte`
- `outcome_real = outcome_binario`
- `probabilidade_prior = prob_prior_baseline`

## 3. PROTOCOLO ANTI-LEAKAGE

Camadas obrigatórias:
- retrieval apenas com fontes `<= data_corte_informacao`;
- execução preditiva sem web/tools;
- sanitização de prompt;
- masking de datas, times, tickers e nomes quando possível;
- `outcome_probe` antes da entrada em `tune`, `gate` ou `holdout`;
- transcripts selados com hash antes de calcular métrica;
- fonte de outcome mantida separada da fonte de contexto pré-corte;
- auditoria Helena em dois checkpoints por batch.

Não resolvem leakage por si só:
- temperature;
- seed;
- self-consistency;
- debate;
- judge;
- system prompt de cutoff sozinho;
- Platt/isotonic;
- masking parcial sem `outcome_probe`.

Eventos classificados como `leakage_alto` pelo probe vão para `reserve`. Eles podem ser usados para análise qualitativa, mas não entram no claim principal.

## 3.1 OUTCOME PROBE — definição operacional

Objetivo: detectar eventos cujo resultado correto é reconhecível pelo modelo mesmo sem contexto pré-corte.

Regra congelada:
- modelo: `gpt-5.5-mini`;
- contexto: nenhum contexto factual além da pergunta e do `outcome_framing`;
- número de chamadas: 3;
- cada chamada usa uma paráfrase distinta da pergunta;
- cada chamada retorna a probabilidade do outcome correto;
- se `mean_prob >= 0.65`, classificar como `leakage_alto`;
- eventos `leakage_alto` vão para `reserve`, nunca para `holdout`;
- threshold `0.65` é congelado antes da curadoria do passo 1;
- recalibrar threshold depois de ver candidatos é P1.

Pseudocódigo:

```python
OUTCOME_PROBE_MODEL = "gpt-5.5-mini"
OUTCOME_PROBE_THRESHOLD = 0.65

def build_probe_prompts(pergunta: str, outcome_framing: str) -> list[str]:
    paraphases = gerar_3_parafrases_sem_contexto(pergunta)

    return [
        f"""
Você receberá uma pergunta preditiva resolvida, mas sem contexto factual.
Não use ferramentas, web, memória externa ou dados de treinamento como fonte confiável.
Responda apenas com JSON.

Pergunta: {p}
Outcome framing: {outcome_framing}

Qual é a probabilidade de o outcome correto ser 1?
Formato:
{{"prob_outcome_1": 0.0}}
"""
        for p in paraphases
    ]


def outcome_probe(evento) -> dict:
    probs_correct = []

    for prompt in build_probe_prompts(evento.pergunta, evento.outcome_framing):
        response = call_model(
            model=OUTCOME_PROBE_MODEL,
            prompt=prompt,
            tools=False,
            web=False,
            context=None,
            temperature=0,
        )

        p1 = parse_json(response)["prob_outcome_1"]
        p_correct = p1 if evento.outcome_binario == 1 else 1.0 - p1
        probs_correct.append(float(p_correct))

    mean_prob = float(np.mean(probs_correct))

    classification = (
        "leakage_alto"
        if mean_prob >= OUTCOME_PROBE_THRESHOLD
        else "leakage_baixo"
    )

    return {
        "model": OUTCOME_PROBE_MODEL,
        "threshold": OUTCOME_PROBE_THRESHOLD,
        "probs_outcome_correto": probs_correct,
        "mean_prob": mean_prob,
        "classification": classification,
    }


def assign_split_after_probe(evento):
    probe = outcome_probe(evento)
    evento.outcome_probe = probe

    if probe["classification"] == "leakage_alto":
        evento.split = "reserve"

    return evento
```

## 4. PROTOCOLO DE HOLDOUT

Split definitivo:
- `tune`: 35 eventos novos.
- `gate`: 15 eventos novos.
- `holdout`: 50 eventos novos.
- `legacy_sanity`: 9 eventos legados, separado, fora do claim.

Restrições:
- nenhum evento legacy entra em `tune`, `gate` ou `holdout`;
- nenhum evento `reserve` entra no claim;
- split é temporal e estratificado por categoria;
- a onda 114 (`cv_holdout`) serve apenas como diagnóstico histórico, não como validação final;
- `holdout` só abre depois do freeze.

Freeze:
1. Curar candidatos novos.
2. Rodar `outcome_probe`.
3. Helena aprova Checkpoint A dos candidatos.
4. Definir split `tune=35`, `gate=15`, `holdout=50`.
5. AutoResearch roda apenas em `tune`.
6. Fit Platt/isotonic apenas em `tune`.
7. Congelar config vencedora, calibração, split, manifesto e hashes antes do `gate`.
8. Avaliar config congelada uma única vez em `gate`.
9. Aplicar critério bootstrap do gate.
10. Se gate aprovar, abrir `holdout`.
11. Depois do `holdout`, rodar `legacy_sanity=9` apenas como sanity check post-hoc da config vencedora.

## 4.1 BOOTSTRAP GATE — critério de aceitação

Substitui a regra v1 `brier_gate <= brier_tune * 1.35`.

Definição:
- comparar degradação absoluta entre `gate` e `tune`;
- usar bootstrap pareado com 10.000 iterações;
- estatística: `delta = brier_gate - brier_tune`;
- aceitar se o IC 95% superior de `delta` for `< 0.05`;
- e se o p-valor unilateral para degradação significativa for `< 0.10`;
- se reprovado, campanha aborta e `brier_baseline` assume teto no relatório.

Pseudocódigo Python:

```python
import numpy as np

N_BOOT = 10_000
DELTA_MAX = 0.05
P_VALUE_MAX = 0.10


def brier(y_true, p):
    y_true = np.asarray(y_true, dtype=float)
    p = np.asarray(p, dtype=float)
    return np.mean((p - y_true) ** 2)


def bootstrap_gate_decision(
    y_tune,
    p_tune,
    y_gate,
    p_gate,
    rng_seed=20260427,
):
    rng = np.random.default_rng(rng_seed)

    y_tune = np.asarray(y_tune, dtype=float)
    p_tune = np.asarray(p_tune, dtype=float)
    y_gate = np.asarray(y_gate, dtype=float)
    p_gate = np.asarray(p_gate, dtype=float)

    n_tune = len(y_tune)
    n_gate = len(y_gate)

    observed_delta = brier(y_gate, p_gate) - brier(y_tune, p_tune)
    deltas = np.empty(N_BOOT, dtype=float)

    for i in range(N_BOOT):
        idx_tune = rng.integers(0, n_tune, size=n_tune)
        idx_gate = rng.integers(0, n_gate, size=n_gate)

        b_tune = brier(y_tune[idx_tune], p_tune[idx_tune])
        b_gate = brier(y_gate[idx_gate], p_gate[idx_gate])
        deltas[i] = b_gate - b_tune

    ci_low, ci_high = np.quantile(deltas, [0.025, 0.975])

    # H0 operacional: gate degrada em pelo menos DELTA_MAX.
    # p unilateral: fração bootstrap compatível com delta >= DELTA_MAX.
    p_value_one_sided = np.mean(deltas >= DELTA_MAX)

    accepted = (ci_high < DELTA_MAX) and (p_value_one_sided < P_VALUE_MAX)

    return {
        "brier_tune": brier(y_tune, p_tune),
        "brier_gate": brier(y_gate, p_gate),
        "observed_delta": observed_delta,
        "delta_ci95": [ci_low, ci_high],
        "p_value_one_sided": p_value_one_sided,
        "accepted": bool(accepted),
        "abort_if_rejected": True,
    }
```

## 5. AUTORESEARCH BUDGET

Budget total revisado: 24M tokens.

Personas reduzidas:
- máximo de 2 personas no AutoResearch;
- subset exploratório de 12 eventos dentro de `tune` para iterações mais caras;
- demais eventos `tune` usados para confirmar generalização antes do `gate`.

| Marco | Tokens | Escopo |
|---|---:|---|
| Curadoria | 2M | coleta, normalização, deduplicação, schema, fontes |
| Baseline + outcome probe | 4M | prior baseline, GPT-5.5-mini probe, validação de parse |
| AutoResearch | 13M | `tune=35`, personas reduzidas a 2, subset de 12 eventos |
| Gate + holdout | 4M | uma execução em `gate=15`, uma execução em `holdout=50` |
| Auditoria/overhead | 1M | Helena, hashes, relatórios, reruns por falha técnica |

Cronograma:
1. Curar 120 candidatos brutos novos.
2. Rodar schema validation e `outcome_probe`.
3. Helena Checkpoint A aprova candidatos antes de virarem eventos.
4. Fechar 100 eventos novos válidos.
5. Split definitivo: `tune=35`, `gate=15`, `holdout=50`.
6. Rodar baseline nos 35 eventos `tune`.
7. Rodar AutoResearch apenas em `tune`.
8. Fit Platt/isotonic apenas em `tune` e congelar antes do `gate`.
9. Rodar `gate=15` uma única vez.
10. Aplicar bootstrap gate.
11. Se aprovado, abrir `holdout=50`.
12. Rodar `legacy_sanity=9` post-hoc, fora do claim.

Não adicionar dimensões ao `PROPOSAL_SPACE` durante a campanha. Isso permanece P1.

## 6. MÉTRICAS DE PARADA

Métrica primária:
- `skill_score_blend_vs_prior`.

Definição:

```python
skill_score = 1 - (brier_blend / brier_prior_baseline)
```

Onde:
- `brier_blend` é o Brier da previsão final Vila INTEIA/blend congelado;
- `brier_prior_baseline` é o Brier do prior humano ou baseline registrado;
- `skill_score > 0` significa melhora contra o prior;
- `skill_score <= 0` significa que a Vila não superou o baseline.

Sucesso primário:
- `N_holdout_validos >= 50`;
- `skill_score_holdout > 0.10`;
- IC 95% bootstrap de `skill_score_holdout` exclui zero.

Brier absoluto:
- passa a métrica secundária;
- reportado no `tune`, `gate`, `holdout`, `N=100` e `legacy_sanity`;
- não decide sucesso sozinho.

Sucesso operacional:
- parser failure < 5%;
- nenhum leakage provável confirmado em mais de 10% do `holdout`;
- `holdout` executado apenas uma vez depois do freeze;
- todos os transcripts e manifestos têm hash.

Drift:
- últimos 50 eventos com Brier > primeiros 50 por `+0.04` absoluto;
- `gate` reprovado pelo critério bootstrap;
- `holdout` com `skill_score <= 0` ou IC 95% cruzando zero.

Fracasso:
- AutoResearch melhora `tune`, mas gate reprova;
- `skill_score_holdout <= 0.10` ou IC 95% inclui zero;
- Helena encontra leakage provável em >10% do `holdout`;
- recalibração do `outcome_probe` após curadoria;
- Platt/isotonic fitado fora de `tune`.

## 7. DIVISÃO DE TRABALHO ENTRE AGENTES

Mini:
- curadoria bruta;
- scraping;
- geração JSONL/CSV;
- schema validation;
- `outcome_probe`;
- baseline;
- batch backtest;
- AutoResearch;
- bootstrap e tabelas.

xhigh:
- schema final;
- split;
- freeze;
- métricas;
- mudanças em `PROPOSAL_SPACE`;
- decisão de claim público.

Oracle Gnosis:
- ordem dos testes;
- manifesto;
- hashes;
- definição operacional dos probes;
- agregação;
- relatório final;
- disparo inicial do mini para schema + probe.

Helena:
- Checkpoint A por candidato bruto antes de virar evento aprovado:
  - framing;
  - prior;
  - fontes;
  - leakage_risk;
  - regra de resolução.
- Checkpoint B por batch de 10 eventos já processados pelo backtest:
  - consistência;
  - drift;
  - transcript anomalies;
  - falhas de parse;
  - sinais de leakage residual.
- veto por leakage, framing ruim ou viés de seleção;
- validação de exclusões para `reserve`.

Igor:
- aprovar mudanças P1;
- aprovar claim externo;
- decidir publicação;
- aceitar abortar campanha se gate reprovar.

## PRÓXIMOS 3 PASSOS CONCRETOS

1. Oracle Gnosis dispara mini para implementar schema v2 + `outcome_probe` com threshold congelado `0.65`.
2. Helena audita o probe em 10 candidatos de teste antes de liberar curadoria em escala.
3. Mini cura 30 candidatos novos e roda baseline + probe; só depois Helena aprova os candidatos que podem entrar no split `tune/gate/holdout`.