# Estratégia N=100 — Validação Preditiva Vila INTEIA

## 1. CURADORIA DE EVENTOS

Meta: adicionar 91 eventos novos aos 9 legados. Os 9 atuais entram apenas em `tune`, não no claim final.

| Categoria | Eventos | Custo | Leakage | Viabilidade Igor |
|---|---:|---|---|---|
| Jogos NBA/NFL/futebol com spread/over-under fechado | 20 | Baixo, 4-6h | Médio | Alta |
| Eleições municipais BR 2020/2024 com 2º turno | 18 | Médio, 8-12h | Médio-alto | Média-alta |
| Decisões STF/TSE/STJ colegiadas | 10 | Alto, 10-15h | Alto | Média |
| IPOs/listagens: acima do IPO no 30º dia? | 12 | Médio, 6-8h | Médio | Alta |
| Earnings: bateu consenso e ação subiu no dia seguinte? | 12 | Médio-alto, 8-10h | Médio | Média |
| Mercados preditivos resolvidos: Polymarket/Kalshi/Metaculus | 12 | Baixo-médio, 5-7h | Médio | Alta |
| OpenReview: paper aceito em ICLR/NeurIPS? | 7 | Médio, 5-8h | Baixo-médio | Média |

Total: 91 novos. Curar 110 candidatos brutos para aceitar 91 após veto da Helena. Eventos vetados ficam logados.

Regras:
- outcome binário, verificável e não trivial;
- `data_corte_informacao < data_resolucao`;
- fonte de outcome separada da fonte pré-corte;
- pergunta congelada antes da predição;
- excluir eventos de alta saliência pré-2024 do holdout.

## 2. ESQUEMA DE DADOS

Canônico: `data/n100/events_v1.jsonl`. CSV legado é derivado.

```python
class EventoPreditivoV1(BaseModel):
    schema_version: Literal["v1"] = "v1"
    id: str
    dataset: str
    split: Literal["tune", "gate", "holdout", "reserve"]
    categoria: str

    pergunta: str
    outcome_framing: str
    contexto_pre_corte: str
    regra_resolucao: str
    outcome_binario: Literal[0, 1]

    prob_oraculo_humano_se_houver: float | None = Field(None, ge=0, le=1)
    tipo_oraculo_humano: Literal[
        "closing_odds", "polling", "prediction_market",
        "analyst_consensus", "none"
    ]

    data_corte_informacao: date
    data_resolucao: date
    fonte_contexto_pre_corte: list[FonteEvento]
    fonte_outcome: list[FonteEvento]
    fonte_oraculo_humano: list[FonteEvento] = []

    leakage_risk: Literal["baixo", "medio", "alto"]
    leakage_mitigations: list[str] = []
    audit_status: Literal["pendente", "aprovado_helena", "vetado_helena"]
```

Mapeamento legado:
`evento_id=id`, `data=data_corte_informacao`, `contexto=contexto_pre_corte`, `outcome_real=outcome_binario`, `probabilidade_prior=prob_oraculo_humano_se_houver or 0.5`.

## 3. PROTOCOLO ANTI-LEAKAGE

Funciona parcialmente:
- retrieval datado com fontes `<= data_corte_informacao`;
- execução sem web/tools;
- sanitização de prompt;
- masking de datas, times, tickers e nomes quando possível;
- `outcome probe`: se o modelo reconhecer o resultado sem contexto, evento vira alto risco;
- transcripts selados com hash antes de calcular métrica.

Não resolve leakage:
- temperature;
- seed;
- self-consistency;
- debate;
- judge;
- Platt/isotonic;
- system prompt de cutoff sozinho.

Eventos pré-2024 de alta saliência não entram no holdout.

## 4. PROTOCOLO DE HOLDOUT

Split fixo:
- `tune`: 45 eventos, incluindo os 9 legados + 36 novos.
- `gate`: 15 novos.
- `holdout`: 40 novos.

A onda 114 (`cv_holdout`) serve como diagnóstico, mas não como validação final, porque usa shuffle aleatório. Validação final deve ser temporal e estratificada por categoria.

Freeze:
1. AutoResearch só em `tune`.
2. Avaliar config vencedora uma vez em `gate`.
3. Aceitar se `brier_gate <= brier_tune * 1.35` e `brier_gate - brier_tune <= 0.04`.
4. Fit Platt/isotonic final em `tune + gate`.
5. Freeze de config, calibração, hashes de manifesto e split.
6. Só então abrir holdout.

## 5. AUTORESEARCH BUDGET

Budget: 30 iterações principais + 10 contingenciais antes do gate.

Custo: 30 × 50k tokens ≈ 1,5M tokens.

Cronograma:
- 30 eventos novos: baseline apenas.
- 45 eventos `tune`: AutoResearch com `max_iteracoes=30`, `max_sem_melhoria=5`.
- 15 eventos `gate`: avaliação única.
- Freeze.
- 40 eventos holdout: uma execução.

Não adicionar dimensões ao `PROPOSAL_SPACE` durante a campanha. Isso é P1.

## 6. MÉTRICAS DE PARADA

Sucesso forte:
- `N_total_validos >= 100`;
- `N_holdout_validos >= 40`;
- `brier_holdout < 0.10`;
- IC 95% bootstrap superior `<= 0.14`;
- `skill_blend_vs_prior_holdout >= 0.20`.

Sucesso operacional:
- `brier_holdout < 0.12`;
- IC 95% superior `<= 0.16`;
- `brier_N100 <= 0.12`;
- parser failure < 5%.

Drift:
- últimos 50 eventos > 1,30× primeiros 50, ou +0,04 absoluto;
- gate > 1,35× tune;
- holdout > 1,50× tune+gate.

Fracasso:
- AutoResearch melhora tune mas degrada gate/holdout > 50%;
- `brier_holdout >= 0.16` com IC cruzando 0.20;
- Helena encontra leakage provável em >10% do holdout.

## 7. DIVISÃO DE TRABALHO ENTRE AGENTES

Mini:
- curadoria, scraping, geração JSONL/CSV;
- baseline, batch backtest, AutoResearch;
- bootstrap e relatórios.

xhigh:
- schema, split, freeze, métricas;
- mudanças em `PROPOSAL_SPACE`;
- decisão de claim público.

Oracle Gnosis:
- ordem dos testes;
- agregação;
- relatório final com hashes.

Helena:
- auditoria a cada 10 eventos;
- veto por leakage, framing ruim ou viés de seleção;
- validação de exclusões.

Igor:
- aprovar P1: mudar split, remover holdout, trocar métrica, expandir budget, publicar claim externo.

## PRÓXIMOS 3 PASSOS CONCRETOS

1. Mini cria 30 candidatos em `data/n100/candidates_raw.jsonl`: 10 esportes, 5 eleições, 5 IPOs, 5 earnings, 5 mercados preditivos.
2. Mini implementa validador Pydantic e exportador `events_v1.jsonl -> CSV legado`.
3. Oracle Gnosis roda baseline nos 30 aprovados, sem AutoResearch, e entrega tabela para Helena com prob Vila, Brier, leakage risk e transcript hash.