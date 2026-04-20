# Rodando Vila com LLM real

A Vila detecta automaticamente o provider de LLM via variáveis de ambiente e
escolhe o primeiro disponível nesta ordem:

1. **OmniRoute** (grátis, gateway interno) — `OMNIROUTE_API_KEY` + `OMNIROUTE_URL`
2. **Google AI Studio — Gemini** (free tier) — `GEMINI_API_KEY`
3. **Anthropic Claude** (pago) — `CLAUDE_API_KEY` + `IA_ALLOW_API_FALLBACK=true`
4. **Heurístico** (sem LLM) se nenhum configurado

## Gemini (Google AI Studio)

Obter chave em <https://aistudio.google.com/>.

Guardar em arquivo local (não commitar):

```bash
echo "GEMINI_API_KEY=..." >> ~/.vila_env
chmod 600 ~/.vila_env
```

Rodar com Gemini:

```bash
set -a; . ~/.vila_env; set +a
export GEMINI_MODEL="gemini-2.5-flash-lite"   # único com free tier
export SUPABASE_VILA_URL=""                    # desativa supabase
export PYTHONPATH=.
python main.py live --port 8700 --intervalo 5 --topico "tema desejado"
```

### Modelos disponíveis

| Modelo | Free tier | Uso |
|---|---|---|
| `gemini-2.5-flash-lite` | ✓ | padrão recomendado |
| `gemini-2.5-flash` | ✗ (conta paga) | análise mais rica |
| `gemini-2.0-flash` | ✗ (quota=0 free) | — |
| `gemini-1.5-flash` | ✗ (deprecated) | — |

Override via `GEMINI_MODEL` env var.

### Rate limits free tier

- ~10 requests por minuto por projeto
- Usar `--intervalo 5+` para ficar dentro da quota
- Circuit breaker abre após 5 falhas (pausa 120s)

## OmniRoute

Configuração INTEIA interna:

```bash
export OMNIROUTE_API_KEY="..."
export OMNIROUTE_URL="http://..."
```

Custo zero, roteia automaticamente entre Opus/Sonnet/Gemma/Grok/Llama.

## Anthropic (fallback)

```bash
export CLAUDE_API_KEY="sk-ant-..."
export IA_ALLOW_API_FALLBACK=true
```

## Verificar provider ativo

```bash
curl http://localhost:8700/api/v1/harness/saude | jq .ia_client
```

Ou em Python:

```python
from engine.ia_client import _detectar_provider
from engine import ia_client as m
_detectar_provider()
print(m._provider)  # "omniroute" | "gemini" | "nenhum"
```
