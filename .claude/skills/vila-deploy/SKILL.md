# Vila INTEIA — Deploy

> Como colocar em producao: Render (backend) ou Docker (qualquer cloud).

## Stack de Producao

- **Backend**: FastAPI + Uvicorn (Python 3.11+)
- **Frontend**: HTML estatico (Three.js) — servido pelo FastAPI
- **LLM**: OmniRoute (custo zero) + Anthropic fallback
- **Dados**: JSON (banco-consultores-lendarios.json, 1.2MB)
- **Banco**: Nenhum (estado em memoria, JSON para persistencia)

## Deploy via Render

```yaml
# render.yaml
services:
  - type: web
    name: vila-inteia
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py serve --port $PORT
    envVars:
      - key: OMNIROUTE_URL
        sync: false
      - key: OMNIROUTE_API_KEY
        sync: false
```

## Deploy via Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8100
CMD ["python", "main.py", "serve", "--port", "8100"]
```

## Variaveis de Ambiente

| Variavel | Obrigatoria | Default |
|----------|-------------|---------|
| PORT | Sim (Render) | 8100 |
| OMNIROUTE_URL | Nao | localhost:20128 |
| OMNIROUTE_API_KEY | Nao | (vazio = heuristicos) |
| CLAUDE_API_KEY | Nao | (vazio) |
| IA_ALLOW_API_FALLBACK | Nao | false |

## Healthcheck

```
GET /api/v1/vila/estado
→ 200 OK com JSON do estado da simulacao
```

## requirements.txt

```
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
pydantic>=2.0.0
openai>=1.0.0
anthropic>=0.25.0
```

## Passos para Deploy

1. `pip freeze > requirements.txt` (ou usar lista minima acima)
2. Criar Dockerfile ou render.yaml
3. Configurar env vars no painel
4. Push para branch de deploy
5. Verificar /docs (Swagger) e /api/v1/vila/estado

## Sem LLM (modo heuristico)

O sistema funciona 100% sem OmniRoute ou Claude API:
- Comentarios gerados por templates + personalidade
- Posts espontaneos com conceitos do consultor
- Debates com fallback minimalista
- Waves processam normalmente
