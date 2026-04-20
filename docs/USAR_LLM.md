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

## OmniRoute (custo zero, gateway INTEIA)

OmniRoute é gateway LLM interno INTEIA que roteia entre múltiplos providers
(Opus, Sonnet, Gemma, Grok, Llama) agregando quotas grátis de cada um.
**Sem custo para INTEIA** quando configurado.

### Setup

```bash
# Em ~/.vila_env (chmod 600):
OMNIROUTE_API_KEY=sk-or-...
OMNIROUTE_URL=http://omniroute.inteia.com.br
# OU http://localhost:20128 se rodando local
```

Rodar Vila:

```bash
set -a; . ~/.vila_env; set +a
export PYTHONPATH=.
python main.py live --port 8100 --intervalo 3 --topico "seu tema"
```

### Modelos aliases (resolvidos pelo OmniRoute)

| Alias | Modelo real roteado | Uso |
|---|---|---|
| `BestFREE` | Melhor grátis disponível no momento | diálogos, volume alto |
| `osa-elite` | Opus/Sonnet high-end | sínteses estratégicas 8+ perspectivas |
| `osa-specialist` | Haiku/Gemini-flash | resumo tático, compressão |

No código Vila:

```python
from engine.ia_client import chamar_llm_conversa

resp = chamar_llm_conversa(
    system_prompt="Instrução sistema...",
    user_prompt="Pergunta usuário...",
    modelo="rapido",   # alias → BestFREE
    max_tokens=300,
)
```

### Verificar que OmniRoute está ativo

```bash
curl -s http://localhost:8100/api/v1/harness/saude | jq .ia_client
```

Output esperado:
```json
{"provider": "omniroute", "client_ok": true, "circuito_aberto": false}
```

Ou Python REPL:

```python
from engine.ia_client import _detectar_provider
from engine import ia_client as m
_detectar_provider()
print(m._provider)  # deve imprimir 'omniroute'
```

### Troubleshooting

**Circuit breaker abriu** (log: `Circuit breaker ABERTO — provider omniroute`)
- OmniRoute falhou 5× consecutivas
- Vila pausa chamadas por 120s
- Fix: checar servidor OmniRoute (`curl $OMNIROUTE_URL/health`)

**Rate limit upstream**
- Alguns modelos no OmniRoute têm quota agregada (Gemma, Llama grátis têm rpm)
- Reduzir `VILA_LLM_RPM` env (default 50, tentar 20)
- Ou usar `GEMINI_MODEL=osa-specialist` (roteado p/ modelo menor)

**`openai SDK não instalado`**
- `pip install openai>=1.0.0`

**Vila usa heurístico apesar de OmniRoute configurado**
- Verificar `echo $OMNIROUTE_API_KEY` não vazio
- Checar log inicial: "Vila IA: OmniRoute (...) — custo zero"
- Se não aparece, env não está exportado (use `set -a; . ~/.vila_env; set +a`)

### Fluxo de fallback

```
request → OmniRoute (c/ circuit breaker)
            ↓ falha
         Gemini (se GEMINI_API_KEY definido)
            ↓ falha
         Anthropic (se IA_ALLOW_API_FALLBACK=true)
            ↓ falha
         heurístico (sem LLM, Vila continua rodando)
```

A Vila nunca para por falha LLM — sempre degrada gracefully para heurístico.

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
