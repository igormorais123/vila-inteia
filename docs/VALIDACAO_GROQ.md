# Validação Vila INTEIA com LLM real Groq

Documento registra run de validação end-to-end com Groq como provider LLM.

## Configuração

| Env | Valor |
|---|---|
| `GROQ_API_KEY` | configurada (~/.vila_env, chmod 600) |
| `VILA_LLM_RPM` | 25 |
| `VILA_LLM_MAX_POR_STEP` | 3 |
| `VILA_LLM_TIMEOUT_S` | 8 |
| `VILA_LLM_TIER` | on |
| `VILA_HOT_FRACTION` | 0.02 (3 personas de 151) |
| `SUPABASE_VILA_URL` | "" (desativado) |
| `--intervalo` | 15 |
| `--port` | 8900 |
| Modelo | `llama-3.1-8b-instant` (rapido), `llama-3.3-70b-versatile` (analise) |

## Resultados observados (primeiros 60s)

### Steps
Steps 2, 3, 4, 5 (e 8 em progresso no monitor) completados sem `TIMEOUT step`.
75-90 conversas/step (heurísticas + LLM quando tier hot ativo).

### LLM (Groq)
- Provider ativo: **groq**
- Circuit breaker: fechado (nenhuma falha)
- Chamadas LLM: **24 em 50s** (~0.5 req/s)
- Tokens in: **2,898 delta** (coleta 50s)
- Tokens out: **796 delta**
- Custo: **$0.000000** (Groq free tier absorve)

### Tier gate
- 3 de 151 personas ativas no hot tier (2%)
- Rotação a cada 20 steps

### Trajetória psico-histórica
- Estado observado: `expansao` (100%)
- Consistente com runs heurísticas anteriores

## Baseline heurístico comparativo

Sim sem LLM (pra provar pipeline não-LLM-dependente):
- 14 steps rastreados em ~30s
- 70-91 conv/step
- Estado `expansao` (100%)

Pipeline cognitivo saudável independente de LLM.

## Como reproduzir

```bash
# 1. Configurar chave
echo "GROQ_API_KEY=gsk_..." >> ~/.vila_env
chmod 600 ~/.vila_env

# 2. Script de launch
cat > /tmp/start_groq.sh <<'EOF'
#!/usr/bin/env bash
cd /home/pedroafonso/vila-inteia
set -a; . ~/.vila_env; set +a
export OMNIROUTE_API_KEY=""
export GEMINI_API_KEY=""
export CLAUDE_API_KEY=""
export SUPABASE_VILA_URL=""
export SUPABASE_VILA_KEY=""
export VILA_LLM_RPM="25"
export VILA_LLM_MAX_POR_STEP="3"
export VILA_LLM_TIMEOUT_S="8"
export VILA_LLM_TIER="on"
export VILA_HOT_FRACTION="0.02"
export PYTHONPATH=.
exec python main.py live --port 8900 --intervalo 15 --topico "..."
EOF
chmod +x /tmp/start_groq.sh

# 3. Rodar
/tmp/start_groq.sh &

# 4. Coletar dados
python scripts/coletar_dados_real.py \
  --url http://localhost:8900 --intervalo 10 --duracao 60 \
  --out /tmp/dados.jsonl

# 5. Gerar relatório
python scripts/gerar_relatorio_coleta.py \
  --in /tmp/dados.jsonl \
  --out ~/Downloads/vila_groq_relatorio.md
```

## Bugs resolvidos durante validação

| Onda | Problema | Fix |
|---|---|---|
| 68 | `TIMEOUT step 1` com 151 personas | cap `VILA_LLM_MAX_POR_STEP=10` |
| 70 | Timeout LLM individual 30s | env `VILA_LLM_TIMEOUT_S=10` (default) |
| 66 | Tier gate sem inicializar | `TIER_GATE_GLOBAL.inicializar(ids)` no boot |

## Próximo

- Rodar 100+ steps Groq pra coletar trajetória significativa (além de expansao)
- Validar auto-calibrador dispara (a cada 50 steps)
- Testar detector de Mule em sim longa
