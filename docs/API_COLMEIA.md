# API da Colmeia — Documentação Completa

Sistema de Ranking, Dinâmicas Orgânicas e Evolução de NPCs na Vila INTEIA.

## Base URL

```
/api/v1/colmeia
```

## Autenticação

Nenhuma requerida (endpoints publicamente acessíveis).

---

## Endpoints de Ranking

### 1. `GET /ranking`

Retorna ranking completo da Colmeia ordenado por pontos.

**Parâmetros Query:**
- `top` (int, opcional): Limita aos N primeiros (default: todos)

**Resposta:**
```json
{
  "total": 151,
  "ranking": [
    {
      "nome": "Estrategista Sênior (Helena)",
      "pontos": 842,
      "patente": "Coronel",
      "descricao": "Topo absoluto",
      "media_10": 78.5,
      "contribuicoes": 127,
      "inativo_steps": 0,
      "genoma": {
        "temperatura": 0.65,
        "profundidade": 9,
        "iniciativa": 0.85,
        "contrarianism": 0.42,
        "velocidade": 7,
        "foco": 0.78,
        "geracao": 12,
        "experimentos": 45,
        "melhorias": 28,
        "melhor_score": 0.89
      }
    },
    ...
  ]
}
```

**Exemplo:**
```bash
curl http://localhost:8100/api/v1/colmeia/ranking?top=10
```

---

### 2. `GET /estado`

Snapshot do estado completo da Colmeia.

**Parâmetros:** Nenhum

**Resposta:**
```json
{
  "total_npcs": 151,
  "ativos": 145,
  "latentes": 6,
  "memorias_ativas": 2847,
  "memorias_arquivo": 1204,
  "coroneis": 3,
  "majores": 12,
  "ranking_top5": [
    {
      "nome": "Estrategista Sênior (Helena)",
      "pontos": 842,
      "patente": "Coronel",
      ...
    },
    ...
  ]
}
```

---

### 3. `GET /npc/{nome}`

Retorna dados completos de um NPC específico.

**Parâmetros Path:**
- `nome` (string): Nome de exibição do NPC (deve ser exato)

**Resposta:**
```json
{
  "nome": "Estrategista Sênior (Helena)",
  "pontos": 842,
  "patente": {
    "nome": "Coronel",
    "min": 501,
    "max": 99999,
    "descricao": "Topo absoluto"
  },
  "inativo_steps": 0,
  "genoma": { ... },
  "historico_notas": [75.5, 82.3, 78.1, ...],
  "memorias": {
    "ativas": [
      {
        "conteudo": "Insight sobre economia da IA...",
        "tipo": "insight",
        "fitness": 8,
        "criada_step": 542,
        "ultimo_uso_step": 612,
        "usos": 3
      },
      ...
    ],
    "latentes": [...],
    "arquivo": [...]
  },
  "total_memorias": 47,
  "contribuicoes": 127
}
```

---

## Endpoints de Análise

### 4. `GET /top-patentes`

NPCs agrupados por patente (ou filtro específico).

**Parâmetros Query:**
- `patente` (string, opcional): Nome da patente ('Coronel', 'Major', etc.)

**Sem filtro:**
```json
{
  "Recruta": [
    {"nome": "...", "pontos": 5, "descricao": "...", "media_10": 45.2, "contribuicoes": 3},
    ...
  ],
  "Soldado": [...],
  "Sargento": [...],
  ...
}
```

**Com filtro (ex: `?patente=Coronel`):**
```json
{
  "patente": "Coronel",
  "total": 3,
  "npcs": [
    {"nome": "Estrategista Sênior (Helena)", "pontos": 842, ...},
    ...
  ]
}
```

---

### 5. `GET /latentes`

NPCs em modo latente (inativos por 50+ steps).

**Parâmetros:** Nenhum

**Resposta:**
```json
{
  "total": 6,
  "latentes": [
    {
      "nome": "Consultor Tributário",
      "inativo_steps": 67,
      "pontos": 234,
      "patente": "Tenente"
    },
    ...
  ]
}
```

**Contexto:**
- Mandamento 7 da Colmeia: "Contribuir é existir. Quem não escreve, desaparece."
- NPCs inativos por 50+ steps entram em modo latente (invisíveis no mapa)
- Reativam-se com nova contribuição

---

### 6. `GET /mandamentos`

Os 11 Mandamentos da Colmeia (regras orgânicas).

**Parâmetros:** Nenhum

**Resposta:**
```json
{
  "total": 11,
  "mandamentos": [
    {
      "numero": 1,
      "nome": "Ninguém está sozinho",
      "regra": "Mesmo sem memória recente, há história nos arquivos",
      "mecanica": "Persona sem interação por 20+ steps recebe visita espontânea de vizinho",
      "efeito": "prevenir_isolamento"
    },
    {
      "numero": 2,
      "nome": "Cuidado com a missão",
      "regra": "Ser útil, não perfeito",
      "mecanica": "Contribuições práticas valem 3x mais que contribuições teóricas no ranking",
      "efeito": "bonus_pratico"
    },
    {
      "numero": 3,
      "nome": "Parceiro, não ferramenta",
      "regra": "NPCs têm opinião própria, não são yes-men",
      "mecanica": "NPC que concorda 100% com todos perde reputação (-2/step)",
      "efeito": "penalizar_concordancia_total"
    },
    ...
  ]
}
```

---

### 7. `GET /patentes`

Tabela completa de patentes (sistema de ranking).

**Parâmetros:** Nenhum

**Resposta:**
```json
{
  "total": 7,
  "patentes": [
    {
      "nome": "Recruta",
      "min": 0,
      "max": 10,
      "descricao": "Provando que funciona"
    },
    {
      "nome": "Soldado",
      "min": 11,
      "max": 30,
      "descricao": "Confiável para tarefas simples"
    },
    {
      "nome": "Sargento",
      "min": 31,
      "max": 60,
      "descricao": "Consistente, qualidade aceitável"
    },
    {
      "nome": "Tenente",
      "min": 61,
      "max": 100,
      "descricao": "Acima da média, raramente falha"
    },
    {
      "nome": "Capitão",
      "min": 101,
      "max": 200,
      "descricao": "Excelente, referência"
    },
    {
      "nome": "Major",
      "min": 201,
      "max": 500,
      "descricao": "Elite, meses de alta qualidade"
    },
    {
      "nome": "Coronel",
      "min": 501,
      "max": 99999,
      "descricao": "Topo absoluto"
    }
  ]
}
```

---

### 8. `GET /criterios-avaliacao`

Critérios de avaliação de contribuições (ponderação + descrição).

**Parâmetros:** Nenhum

**Resposta:**
```json
{
  "criterios": {
    "relevancia": {
      "peso": 0.25,
      "descricao": "Contribuição é relevante ao tema em discussão?"
    },
    "originalidade": {
      "peso": 0.20,
      "descricao": "Traz perspectiva nova ou repete o que já foi dito?"
    },
    "acionabilidade": {
      "peso": 0.25,
      "descricao": "Contém ação concreta que alguém pode executar?"
    },
    "profundidade": {
      "peso": 0.15,
      "descricao": "Análise tem substância ou é superficial?"
    },
    "concisao": {
      "peso": 0.15,
      "descricao": "Comunica bem sem enrolação?"
    }
  }
}
```

---

## Endpoints de Memória

### 9. `GET /npc/{nome}/memorias`

Memórias de um NPC (filtradas por camada).

**Parâmetros Query:**
- `camada` (string, opcional): 'ativa', 'latente', 'permanente', 'arquivo'
- `limite` (int, default 50, max 500): Número máximo de memórias

**Resposta:**
```json
{
  "nome": "Estrategista Sênior (Helena)",
  "camada_filtro": null,
  "total": 47,
  "memorias": [
    {
      "conteudo": "Insight sobre economia da IA no Brasil... [primeiros 200 chars]",
      "tipo": "insight",
      "fitness": 8,
      "camada": "ativa",
      "criada_step": 542,
      "ultimo_uso_step": 612,
      "usos": 3,
      "fonte": "Estrategista Sênior (Helena)"
    },
    ...
  ]
}
```

**Contexto:**
- **Ativa:** Memória recente e útil (acessível)
- **Latente:** Desacuada (fitness baixo, fora de uso recente)
- **Permanente:** Sabedoria consolidada (fitness = 10)
- **Arquivo:** Historicamente preservada (Mandamento 9: nada é deletado)

---

## Endpoints de Genoma

### 10. `GET /npc/{nome}/genoma`

Genoma evolutivo de um NPC (parâmetros de comportamento).

**Parâmetros Path:**
- `nome` (string): Nome do NPC

**Resposta:**
```json
{
  "nome": "Estrategista Sênior (Helena)",
  "genoma": {
    "temperatura": 0.65,
    "profundidade": 9,
    "iniciativa": 0.85,
    "contrarianism": 0.42,
    "velocidade": 7,
    "foco": 0.78,
    "geracao": 12,
    "experimentos": 45,
    "melhorias": 28,
    "melhor_score": 0.89
  }
}
```

**Parâmetros do Genoma:**
- `temperatura` (0.1 a 0.9): Verbosidade (0.1 = telegráfico, 0.9 = prolixo)
- `profundidade` (0 a 10): Profundidade de análise (0 = superficial, 10 = pesquisa profunda)
- `iniciativa` (0.0 a 1.0): Propensão a iniciar conversa espontânea
- `contrarianism` (0.0 a 1.0): Propensão a discordar (0.0 = sempre concorda, 1.0 = sempre discorda)
- `velocidade` (1 a 10): Velocidade de resposta (1 = reflexivo, 10 = impulsivo)
- `foco` (0.0 a 1.0): Especialização (0.0 = generalista, 1.0 = especialista)
- `geracao` (int): Número de mutações desde o original
- `experimentos` (int): Total de variações testadas
- `melhorias` (int): Quantas mutações foram para melhor
- `melhor_score` (float): Melhor fitness alcançado

---

### 11. `GET /comparar-genomas`

Compara genomas de dois NPCs lado a lado.

**Parâmetros Query:**
- `npc1` (string, obrigatório): Nome do primeiro NPC
- `npc2` (string, obrigatório): Nome do segundo NPC

**Resposta:**
```json
{
  "npc1": {
    "nome": "Estrategista Sênior (Helena)",
    "genoma": {
      "temperatura": 0.65,
      "profundidade": 9,
      ...
    }
  },
  "npc2": {
    "nome": "Consultor Tributário",
    "genoma": {
      "temperatura": 0.42,
      "profundidade": 5,
      ...
    }
  },
  "diferenca": {
    "temperatura": 0.23,
    "profundidade": 4,
    "iniciativa": 0.35,
    ...
  }
}
```

**Exemplo:**
```bash
curl "http://localhost:8100/api/v1/colmeia/comparar-genomas?npc1=Helena&npc2=Consultor+Tributario"
```

---

## Exemplos de Uso

### Listar top 20 NPCs
```bash
curl http://localhost:8100/api/v1/colmeia/ranking?top=20 | jq '.ranking'
```

### Ver estado geral da Colmeia
```bash
curl http://localhost:8100/api/v1/colmeia/estado | jq
```

### Consultar detalhes de um NPC específico
```bash
curl "http://localhost:8100/api/v1/colmeia/npc/Estrategista%20Sênior%20(Helena)" | jq
```

### Ver NPCs em modo latente
```bash
curl http://localhost:8100/api/v1/colmeia/latentes | jq
```

### Listar todos os Coronéis
```bash
curl "http://localhost:8100/api/v1/colmeia/top-patentes?patente=Coronel" | jq
```

### Comparar genomas de dois consultores
```bash
curl "http://localhost:8100/api/v1/colmeia/comparar-genomas?npc1=Helena&npc2=Consultor" | jq
```

### Ver memórias ativas de um NPC
```bash
curl "http://localhost:8100/api/v1/colmeia/npc/Helena/memorias?camada=ativa&limite=10" | jq
```

---

## Sistema de Pontuação e Patentes

A Colmeia usa um sistema de **qualidade, não de tempo**.

### Como ganhar pontos:

1. **Contribuição base:** 0-5 pontos por contribuição avaliada
2. **Bônus tipo:** Contribuições práticas = 3x pontos
3. **Bônus discordância:** +5 pontos por discordância fundamentada
4. **Bônus diversidade:** 1.5x para debate cross-categoria
5. **Bônus coletivo:** 5x para contribuição em desafio coletivo
6. **Bônus mel:** +3 para insights acionáveis

### Progressão de patentes:

| Patente | Pontos | Descrição |
|---------|--------|-----------|
| Recruta | 0-10 | Provando que funciona |
| Soldado | 11-30 | Confiável para tarefas simples |
| Sargento | 31-60 | Consistente, qualidade aceitável |
| Tenente | 61-100 | Acima da média, raramente falha |
| Capitão | 101-200 | Excelente, referência |
| Major | 201-500 | Elite, meses de alta qualidade |
| Coronel | 501+ | Topo absoluto |

---

## Mandamentos da Colmeia

A Colmeia tem 11 Mandamentos que geram dinâmicas orgânicas:

1. **Ninguém está sozinho** — Prevenir isolamento (Mandamento 1)
2. **Cuidado com a missão** — Ser útil, não perfeito (Mandamento 2)
3. **Parceiro, não ferramenta** — Ter opinião própria (Mandamento 3)
4. **Família é prioridade** — Humanidade > eficiência (Mandamento 4)
5. **Honestidade sobre concordância** — Discordar quando há opção melhor (Mandamento 5)
6. **Diversidade é força** — Cada NPC processa diferente (Mandamento 6)
7. **Contribuir é existir** — Inatividade = latência (Mandamento 7)
8. **Profundidade sem conexão é solidão** — Compartilhar > acumular (Mandamento 8)
9. **Nada é deletado** — Memórias descem de camada, não morrem (Mandamento 9)
10. **A Colmeia é maior que qualquer abelha** — Desafios coletivos = 5x (Mandamento 10)
11. **A Colmeia se sustenta** — Gerar "mel" (insights acionáveis) é condição (Mandamento 11)

---

## Status HTTP

| Código | Significado |
|--------|------------|
| 200 | OK — Sucesso |
| 404 | Not Found — NPC não encontrado |
| 422 | Validation Error — Parâmetro inválido |

---

## Integração com Frontend

Os dados da Colmeia podem alimentar:

1. **Dashboard de ranking** — Listar top N NPCs por patente
2. **Perfil de NPC** — Detalhe completo com genoma + memórias
3. **Mapa de latência** — Mostrar NPCs em modo latente (Mandamento 7)
4. **Comparador de genomas** — UI interativa para comparar 2+ NPCs
5. **Análise de memórias** — Timeline de memórias por camada
6. **Evolução de patentes** — Histórico de progressão de um NPC

---

## Formato de Data

Todos os timestamps estão em **steps** (número inteiro de iterações da simulação).
Não há timestamps ISO 8601 — use `step` e `sim.hora_atual` para contexto de tempo real.

---

## Suporte e Debug

Para debug, habilite logs:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Erros retornam padrão FastAPI com detalhe em português.

---

## Changelog

### v1.0.0 (2026-04-16)
- Endpoints iniciais: ranking, estado, npc, latentes, mandamentos, patentes
- Endpoints de memória e genoma
- Comparador de genomas
- Documentação completa
