# Deploy — Vila INTEIA

## Opções

| Alvo | Quando | Complexidade |
|------|--------|--------------|
| Local (dev) | Desenvolvimento | Baixa |
| Docker | Dev paritário + homologação | Baixa |
| Render (Web Service) | Produção single-node | Média |
| VPS (Docker + nginx) | Produção com controle total | Alta |

---

## 1. Local

```bash
pip install -r requirements.txt
cp .env.example .env
# preencha .env
python main.py serve --port 8100
```

Pré-requisitos:
- Python 3.11+
- Supabase acessível (URL + anon key no .env)
- OmniRoute rodando OU `CLAUDE_API_KEY` + `IA_ALLOW_API_FALLBACK=true`

---

## 2. Docker

Dockerfile já incluso. Build + run:

```bash
docker build -t vila-inteia:latest .
docker run -d \
  --name vila-inteia \
  -p 8100:8100 \
  --env-file .env \
  -v vila-data:/app/data \
  vila-inteia:latest
```

Ou `docker-compose`:

```yaml
version: "3"
services:
  vila:
    build: .
    ports: ["8100:8100"]
    env_file: .env
    volumes:
      - vila-data:/app/data
    restart: unless-stopped
volumes:
  vila-data:
```

---

## 3. Render

**Web Service** (Python):

1. Conecta o repo `github.com/<org>/vila-inteia`
2. Runtime: Python 3.11
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py live --intervalo 30`
5. Environment variables: copia do `.env` (NÃO subir `.env` no repo)
6. Health check: `/api/v1/vila/live`

Render reinicia o container quando deploya — por isso o estado vai todo para
Supabase. Nada crítico em memória.

---

## 4. VPS (Docker Compose)

Para rodar 24/7 com reverse proxy TLS:

```bash
# SSH no VPS
git clone https://github.com/<org>/vila-inteia.git
cd vila-inteia
cp .env.example .env && vim .env     # preenche
docker-compose up -d
```

Exemplo de nginx virtual host:
```nginx
server {
    server_name vila.<seu-dominio>.com.br;
    location / {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
    listen 443 ssl http2;
    # certificados Let's Encrypt...
}
```

---

## 5. Endpoint Mirante (no repo do Mirante)

A route `POST /api/vila/submissoes` **não fica neste repo**. Fica no repo do
site Mirante News (que usa Next.js 14 na Vercel). O arquivo de referência já
está commitado lá em `src/app/api/vila/submissoes/route.ts` e tem Supabase +
GitHub API como dependência.

**Env que o Mirante precisa** (Vercel Environment Variables):

```
VILA_MIRANTE_TOKEN=<gerado_pelo_dev>      # mesmo valor do MIRANTE_API_TOKEN na Vila
GITHUB_TOKEN=<PAT_com_escopo_repo>
GITHUB_REPO=<org>/<repo_do_mirante>
GITHUB_BRANCH=main
MIRANTE_CONTENT_PATH=frontend/content/mirante
NEXT_PUBLIC_SUPABASE_URL=<url_projeto_mirante>
SUPABASE_SERVICE_ROLE_KEY=<service_role>
```

O `VILA_MIRANTE_TOKEN` é um shared secret. Gere com
`python -c "import secrets; print(secrets.token_urlsafe(32))"` e salve nos
dois lados.

---

## 6. Mirofish (no repo do Mirofish)

Motor Flask que roda em container separado. A Vila só precisa da URL:

```
MIROFISH_API_URL=http://<host_do_mirofish>:5001
```

Se Mirofish estiver no mesmo VPS que a Vila, use rede Docker interna.

---

## Checklist de produção

- [ ] `.env` preenchido com valores reais
- [ ] `.env` no `.gitignore` (já está)
- [ ] Credenciais Supabase rotacionadas se vazaram em commits antigos
- [ ] `VILA_MIRANTE_TOKEN` gerado e configurado em ambos os lados
- [ ] Supabase RLS endurecido se for multi-tenant
- [ ] Logs centralizados (stderr → container logs)
- [ ] Health check configurado
- [ ] Backup periódico de `vila_snapshots` (Supabase já faz PITR)
- [ ] Rate limit testado na rota Mirante
- [ ] Smoke test: `python main.py demo` roda sem exceção
