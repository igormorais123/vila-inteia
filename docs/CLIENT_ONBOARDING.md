# Vila INTEIA — Predição Política BR 2026
## Onboarding cliente

Bem-vindo. Esse documento mostra como integrar a API de predição política da
Vila em sua plataforma.

---

## 1. Quick start (5 min)

### Sua chave

Sua API key será entregue separadamente via canal privado. Formato:
```
vila_pol_<24 caracteres random>
```

### Primeira requisição

```bash
curl https://vila-inteia.onrender.com/api/v1/politica/health \
  -H "X-API-Key: $VILA_API_KEY"
```

Resposta esperada:
```json
{
  "status": "ok",
  "n_train_events": 394,
  "predictions_snapshot": "data/predictions_2026.json",
  "snapshot_predicted_at": "2026-05-04T...",
  "horizon_days": 152,
  "validation_acc": 0.9721
}
```

---

## 2. Endpoints essenciais

### Predições prontas (snapshot diário)

| Endpoint | Retorna |
|----------|---------|
| `GET /api/v1/politica/predictions/presidente` | 9 candidatos com p_winner |
| `GET /api/v1/politica/predictions/governador?uf=SP` | top 2 SP, com p_winner |
| `GET /api/v1/politica/predictions/governador` | todos 12 estados |
| `GET /api/v1/politica/predictions/senador` | 4 candidatos com p_winner |
| `GET /api/v1/politica/predictions/all` | snapshot completo |

### Predição custom (seu próprio cenário)

```bash
curl -X POST https://vila-inteia.onrender.com/api/v1/politica/predict \
  -H "X-API-Key: $VILA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "cargo": "governador",
    "poll_lead_pp": 8,
    "days_to_election": 45,
    "incumbente": 1,
    "regime": "right"
  }'
```

Resposta:
```json
{
  "p_cohort": 0.78,
  "p_linzer": 0.86,
  "p_blend": 0.83,
  "cohort_tier": "full",
  "cohort_n": 12,
  "horizon_days": 45
}
```

### Backtest e calendário

| Endpoint | Retorna |
|----------|---------|
| `GET /api/v1/politica/elections` | calendário 2026, lista cargos cobertos |
| `GET /api/v1/politica/backtest` | métricas de validação histórica completas |
| `GET /api/v1/politica/me` | seus limites de tier |

---

## 3. Tiers e rate limit

| Tier | req/min | req/dia | Endpoints |
|------|---------|---------|-----------|
| free | 30      | 500     | todos públicos |
| pro  | 300     | 50000   | todos + predict custom |
| enterprise | 100k+ | ilimitado | sob contrato (SLA, suporte) |

Headers em rate-limit:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

---

## 4. Performance histórica

**Validação**: 394 eventos políticos reais 2010-2024, year-fold CV.

| Ciclo | n eventos | Acc T≤30 | Brier T≤30 |
|-------|-----------|----------|------------|
| Pres 2010 | 86  | 100.0% | 0.060 |
| Pres 2018 | 70  | 100.0% | 0.069 |
| Pres 2022 | 120 | 100.0% | 0.076 |
| SP 2016   | 20  | 85.0%  | 0.121 |
| SP 2020   | 30  | 93.3%  | 0.055 |
| SP 2024   | 68  | 89.7%  | 0.107 |
| **Média** | **394** | **97.21%** | **0.105** |

**Modo seletivo recomendado** (abstém em tossups):

| τ (cutoff) | Cobertura | Accuracy | n predito |
|------------|-----------|----------|-----------|
| 0.15 | 55.8% | **100.0%** | 220 |
| 0.20 | 54.8% | **100.0%** | 216 |
| 0.25 | 41.9% | **100.0%** | 165 |
| 0.40 | 7.9% | **100.0%** | 31 |

**Indicadores Autoresearch v1.4-evo**:

| Indicador | Valor | Leitura |
|-----------|------:|---------|
| AUC | 0.992 | separação winner/loser quase total |
| MCC | 0.944 | classificação robusta mesmo sob troca de classe |
| Brier skill vs climatologia | 58.2% | ganho probabilístico contra base rate |
| Wilson 95% da acurácia | 95.1–98.4% | intervalo binomial conservador |
| McNemar net hits | +21 | MRP recupera 22 casos e introduz 1 erro |

---

## 5. Regras operacionais

**2024 SP**: o MRP state baseline recupera o cluster de viés sistêmico da
indústria de pesquisas, elevando o fold de 73.5% para 89.7%. Para corridas
apertadas de alta responsabilidade, use modo seletivo τ≥0.25.

**2026**: predições atuais usam o snapshot vigente e entram em recalibragem
mensal conforme novas pesquisas entram no pipeline.

**Cobertura**: presidencial + 12 governadorias + 4 senadores. Outras UFs e
deputados estaduais/federais — em próxima iteração (Onda 6).

---

## 6. Integração TypeScript / Python

### TypeScript
```ts
const r = await fetch("https://vila-inteia.onrender.com/api/v1/politica/predictions/presidente", {
  headers: { "X-API-Key": process.env.VILA_API_KEY! }
});
const data = await r.json();
const top = data.candidates[0]; // {nome, partido, p_winner, ...}
```

### Python
```python
import requests
r = requests.get(
    "https://vila-inteia.onrender.com/api/v1/politica/predictions/governador",
    params={"uf": "SP"},
    headers={"X-API-Key": os.environ["VILA_API_KEY"]},
    timeout=10,
)
r.raise_for_status()
print(r.json()["candidates"][0])
```

---

## 7. Suporte

- email: colmeia@inteia.com.br
- urgente: contato direto Igor / Pedro
- changelog: `docs/CHANGELOG.md` no repo

## 8. SLA (enterprise)

- 99.5% uptime mensal (excluindo manutenção programada)
- janela de manutenção: domingos 02:00-04:00 BRT
- snapshot de predições atualizado <= 24h após pesquisa nova publicada
- resposta P95 < 500ms para endpoints de leitura
