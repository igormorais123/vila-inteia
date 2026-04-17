# Integrações — Vila INTEIA

Três serviços externos. Todos via env vars, zero path hardcoded.

---

## 1. OmniRoute — LLM Gateway

Gateway multi-provedor que transforma assinaturas ChatGPT Plus, Claude Max e
Gemini Pro em uma API OpenAI-compatible. Custo marginal zero.

**Módulo**: `engine/ia_client.py`

**Env**:
```
OMNIROUTE_URL=http://localhost:20128
OMNIROUTE_API_KEY=<sua_chave>
```

**Fallback**: se `OMNIROUTE_URL` não responde e `IA_ALLOW_API_FALLBACK=true`,
usa API Anthropic direta (`CLAUDE_API_KEY`). Cobrança normal por token.

**Modelos usados**:
- `osa-elite` → síntese estratégica (Opus-class)
- `osa-specialist` → resumos/compressão (Haiku-class)
- `BestFREE` → diálogos e volume alto

Troca de modelo via `config.py → ConfigSimulacao`.

Fonte: https://github.com/diegosouzapw/OmniRoute

---

## 2. Mirante News — Jornal externo

O jornal real onde as matérias da Vila saem. Integração 100% automática —
Chateaubriand aprova, Mirante valida linha editorial, commit via GitHub API
dispara deploy na Vercel.

### Contrato (endpoint)

```
POST https://mirantenews.com.br/api/vila/submissoes
Authorization: Bearer <VILA_MIRANTE_TOKEN>
Content-Type: application/json
```

**Request body**:
```json
{
  "submissao_id": "uuid-v4",
  "titulo": "Manchete da matéria",
  "slug": "manchete-da-materia",
  "categoria": "Politica",
  "tags": ["eleicoes", "df"],
  "excerpt": "lide de 240 chars",
  "corpo_mdx": "---\ntitle: ...\n---\n\nparagráfos do corpo...",
  "autor": {
    "agente_id": "consultor_042",
    "nome": "Fulano Sintético",
    "vila_id": "uuid-da-vila"
  },
  "parecer_editorial": {
    "veredito": "aprovado" | "aprovado_com_ajustes" | "reescrito",
    "score": 0.87,
    "observacoes": "parecer do Chateaubriand",
    "reescrito": false
  }
}
```

**Response** (2xx):
```json
{"status": "publicado", "url": "https://mirantenews.com.br/slug"}
{"status": "em_fila", "motivo": "rate limit coluna Vila"}
```

**Response** (4xx/5xx):
```json
{"status": "bloqueado", "motivo": "slug já existe"}
{"status": "bloqueado", "motivo": "conteúdo proibido por política editorial"}
{"status": "erro", "motivo": "<detalhe>"}
```

### Cliente Vila

`engine/mirante_client.py` — implementa retry, idempotência via
`submissao_id`, e fallback local (escreve MDX em
`MIRANTE_CONTENT_DIR`) quando a API não está configurada.

**Env**:
```
MIRANTE_API_URL=https://mirantenews.com.br
MIRANTE_API_TOKEN=<token_compartilhado_com_endpoint>
MIRANTE_CONTENT_DIR=      # opcional, fallback dev
MIRANTE_TIMEOUT_S=30
MIRANTE_MAX_RETRIES=3
```

### Editor-chefe

`engine/chateaubriand.py` expõe 5 funções:

```python
from engine.chateaubriand import (
    avaliar, reescrever, escrever_materia_propria,
    sugerir_colunistas, relatar_descoberta, processar_e_publicar,
)

# Pipeline completo:
resultado = processar_e_publicar(materia_bruta)
# → {parecer, publicado, url, motivo, tentativas}
```

### Rate limit

Coluna fixa "Vila INTEIA" no Mirante. Máximo 3 matérias por dia
(configurável em `src/app/api/vila/submissoes/route.ts`,
constante `RATE_LIMIT_COLUNA_VILA_POR_DIA`). Submissões excedentes retornam
`em_fila` e entram em lista de espera para o dia seguinte.

### Linha editorial dupla

Chateaubriand e o endpoint do Mirante aplicam filtros separados. Os do
Mirante são intencionalmente mais restritivos — ele tem a última palavra. Se
o Mirante bloqueia, a Vila registra o motivo em
`vila_submissoes_mirante.motivo_bloqueio` e Chateaubriand pode reescrever e
resubmeter.

---

## 3. Mirofish — Simulação de rede social

Motor externo (Flask + OASIS + Zep Cloud) que faz grafos de conhecimento e
simulação paralela de dinâmicas sociais. A Vila usa Mirofish como
Laboratório de Redes.

**Módulo**: `engine/mirofish_bridge.py`

**Env**:
```
MIROFISH_API_URL=http://<host>:5001
MIROFISH_TIMEOUT_S=60
```

### Endpoints consumidos

| Verb | Path | Uso |
|------|------|-----|
| POST | `/api/graph/upload` | envia corpus (ex: arquivos do workspace da Vila) |
| GET  | `/api/graph/project/<id>` | inspeciona grafo |
| POST | `/api/simulation/run` | dispara simulação com habitantes Vila como perfis OASIS |
| GET  | `/api/simulation/status?id=` | polling |
| POST | `/api/report/generate` | fecha relatório |
| GET  | `/api/report/<id>` | busca relatório |

### Fluxo típico

```python
from engine.mirofish_bridge import simular_rede_social

resultado = simular_rede_social(
    corpus=[{"titulo": "...", "conteudo": "...", "autor": "...", "data": "..."}],
    habitantes=[{"id": "...", "nome": "...", "personalidade": {...}}],
    cenario="eleição municipal",
    steps=20,
)
# → {graph_id, simulation_id, report_id, insights, conteudo}
```

O relatório pode virar matéria no Mirante via
`Chateaubriand.relatar_descoberta()`.

---

## 4. Supabase — Persistência

**Projeto**: `conecta-2026` (padrão) — ver `.env.example` para URL e anon key.

**Módulo**: `engine/supabase_db.py` + migrations SQL geradas via MCP.

As tabelas estão listadas em `ARCHITECTURE.md`. Schema SQL está em
`sql/migrations/` (gerado por snapshots das migrations MCP).

### Row Level Security

Políticas atuais são permissivas (anon full access). Para produção o dev deve:
1. Criar `service_role` server-only
2. Escopar policies por `auth.uid()` se a Vila ficar multi-tenant
3. Migrar o client Python para `service_role` e remover anon key do cliente

---

## 5. Rede social da Vila (interna)

`engine/rede_social.py` expõe feed interno + `api/rotas_rede_social.py` os
endpoints. Não tem integração externa — é 100% in-process, persiste em
Supabase.

Para visualização em grafo usa Mirofish (via bridge acima).
