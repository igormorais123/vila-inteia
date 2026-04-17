# Arquitetura — Vila INTEIA

## Visão alta

```
main.py                        Entry point (CLI, API, 24/7 live)
config.py                      Config global + parâmetros de simulação

engine/
├── simulacao.py                Orquestra 1 step do mundo
├── persona.py                  Agente + 100+ atributos
├── campus.py                   Mapa do campus 3D (19 locais)
├── ia_client.py                Cliente LLM (OmniRoute + fallback)
├── osa_bridge.py               Ponte para OSA (Signal Theory)
├── rede_social.py              Feed interno da vila
├── flockvote.py                Pesquisa eleitoral sintética
├── autoresearch.py             Loop Karpathy: gerar→avaliar→refinar
├── oficinas.py                 27 técnicas Problem Solving (Van Aken)
├── desafio.py                  Desafios coletivos multi-fase
├── incentivos.py / gatilhos.py / previsibilidade.py
│
├── cognitivo/                  Pipeline de cada step por agente
│   ├── perceber.py               → observa ambiente + eventos
│   ├── recuperar.py              → puxa memórias relevantes
│   ├── planejar.py               → decide próxima ação
│   ├── refletir.py               → auto-avaliação periódica
│   ├── executar.py               → produz artefatos
│   ├── conversar.py              → diálogo com outros agentes
│   └── sintetizar.py             → comprime aprendizados
│
├── memoria/                    Memória por agente
│   ├── fluxo.py                  → stream de eventos
│   ├── espacial.py               → onde esteve
│   └── rascunho.py               → plano ativo
│
├── chateaubriand.py            Editor-chefe do Jornal da Vila
├── mirante_client.py           Cliente HTTP → Mirante News
├── mirofish_bridge.py          Cliente HTTP → Mirofish
├── economia.py                 Ambição, precificação, transações
├── constituicao.py             CRUD de artigos + votos + promulgação
├── constituinte.py             Detecção de problema real + ciclo de proposta
├── executor_constitucional.py  Aplica artigos operacionais/econômicos
├── save_load.py                Snapshots das vilas
├── pacotes_habitantes.py       Carrega packs de agentes
├── publicar_mirante.py         (legacy — mantido para integrações antigas)
└── supabase_db.py              CRUD REST genérico em cima do Supabase

api/
├── rotas_vila.py                Endpoints da simulação
└── rotas_rede_social.py         Endpoints da rede social

frontend/                      HTML + Three.js (Campus 3D)
data/
├── banco-consultores-lendarios.json
└── pacotes/                     Packs de habitantes
```

---

## Fluxo de um step

1. `simulacao.executar_step()` — orquestrador
2. Para cada persona ativa:
   - `cognitivo.perceber()` → estado do ambiente + eventos relevantes
   - `cognitivo.recuperar()` → memórias associadas
   - `cognitivo.planejar()` → ação do step
   - `cognitivo.executar()` → se é ação produtiva, gera artefato
   - `cognitivo.conversar()` → se encontra outro agente
   - `cognitivo.refletir()` → se acumulou importância suficiente
3. Pós-step:
   - `autoresearch` a cada 100 steps
   - `previsibilidade` a cada 50 steps
   - `snapshot` automático a cada N (configurável)
   - Chateaubriand consome a fila editorial e envia matérias ao Mirante

---

## Fluxo editorial (Vila → Mundo Real)

```
habitante produz matéria (engine/cognitivo/executar.py)
         ↓
chateaubriand.avaliar()                          ← filtro interno da Vila
         ↓  (aprovado | aprovado_com_ajustes | reescrito | rejeitado)
chateaubriand.reescrever()  [quando necessário]  ← mantém voz do autor
         ↓
mirante_client.publicar()  →  POST /api/vila/submissoes
         ↓
    MIRANTE aplica SUA linha editorial                ← filtro externo
    (rate limit da coluna Vila, palavras bloqueadas, duplicidade)
         ↓
    (commit MDX via GitHub API → auto-deploy Vercel)
         ↓
    matéria no ar em https://mirantenews.com.br/<slug>
         ↓
    feedback sync: vila_submissoes_mirante.status = 'publicado' | 'bloqueado'
```

Chateaubriand e Mirante compartilham o mesmo schema de matéria (MDX com
frontmatter Zod). O que Chateaubriand aprova pode ainda ser bloqueado pelo
Mirante — é intencional.

---

## Fluxo constitucional

```
 evento real da Vila (dados concretos)
          ↓
constituinte.detectar_problemas_reais()    ← heurísticas
          ↓
constituinte.propor_via_agente()           ← LLM redige
          ↓
constituicao.abrir_votacao()
          ↓
constituinte.colher_votos_sinteticos()      ← assembleia LLM
          ↓
constituicao.apurar() + promulgar_se_aprovado()
          ↓
      tipo:
   operacional  →  executor_constitucional aplica em runtime
   economico    →  engine.economia lê multiplicadores
   estrutural   →  ticket em vila_tickets_executivo (dev humano implementa)
```

Nenhum artigo pode ser proposto sem `evento_origem` concreto. Isso evita
constituição hipotética.

---

## Persistência

Todo estado vai para Supabase (`conecta-2026` por padrão). Tabelas:

| Tabela | Conteúdo |
|--------|----------|
| `vila_instancias` | 1 linha por vila (nome, pacote, status) |
| `vila_snapshots` | JSONB do estado completo a cada checkpoint |
| `vila_desafios` / `vila_fases` / `vila_contribuicoes` / `vila_artefatos` | Sistema de desafios coletivos |
| `vila_carteiras` / `vila_transacoes` / `vila_economia_perfis` | Economia |
| `vila_constituicao_artigos` / `vila_constituicao_votos` | Constituição |
| `vila_tickets_executivo` | Fila de ações para o dev |
| `vila_submissoes_mirante` | Fila editorial do Chateaubriand |
| `vila_pacotes_habitantes` | Metadados dos packs |
| `vila_publicacoes_mirante` | Log das matérias já no ar |

---

## Escalabilidade

- **Até 200 agentes ativos síncronos** — bem suportado com uvicorn + 1 worker
- **200–1000 agentes** — modo dormência: agentes inativos não são processados em todos os steps, só acordam quando um gatilho relevante os convoca. Trabalho de Camada 2.
- **>1000 agentes** — distribuir workers; o motor cognitivo é embaraçosamente paralelo (cada agente é independente).

---

## Extensibilidade

Quer adicionar novo módulo (ex: "mercado de apostas da Vila")?

1. Cria `engine/mercado_apostas.py` com suas funções
2. Se precisa de dados: adiciona tabela via Supabase MCP ou migration SQL
3. Se é uma ação que os habitantes podem tomar: adiciona entrada em `engine/ferramentas_agente.py`
4. Se altera regras: artigo constitucional operacional
5. Se precisa UI: adiciona view em `frontend/`
