# API Colmeia — Quick Start

Acesso rápido aos 11 endpoints do sistema de ranking e dinâmicas orgânicas.

## Base URL
```
http://localhost:8100/api/v1/colmeia
```

## Endpoints Essenciais

### 1. Ranking Completo
```bash
curl http://localhost:8100/api/v1/colmeia/ranking?top=20
```
Retorna: lista de NPCs ordenados por pontos

### 2. Estado Geral
```bash
curl http://localhost:8100/api/v1/colmeia/estado
```
Retorna: totais, ativos/latentes, coronéis, top5

### 3. Detalhe de um NPC
```bash
curl "http://localhost:8100/api/v1/colmeia/npc/Estrategista%20Sênior%20(Helena)"
```
Retorna: pontos, patente, genoma, memórias, histórico

### 4. Genoma de um NPC
```bash
curl "http://localhost:8100/api/v1/colmeia/npc/Helena/genoma"
```
Retorna: 10 parâmetros evolutivos (temperatura, profundidade, etc.)

### 5. Comparar Genomas
```bash
curl "http://localhost:8100/api/v1/colmeia/comparar-genomas?npc1=Helena&npc2=Consultor"
```
Retorna: genomas lado a lado + diferenças

### 6. NPCs Latentes
```bash
curl http://localhost:8100/api/v1/colmeia/latentes
```
Retorna: NPCs inativos por 50+ steps (Mandamento 7)

### 7. Ranking por Patente
```bash
curl "http://localhost:8100/api/v1/colmeia/top-patentes?patente=Coronel"
```
Retorna: NPCs de uma patente específica

### 8. Memórias de um NPC
```bash
curl "http://localhost:8100/api/v1/colmeia/npc/Helena/memorias?camada=ativa&limite=10"
```
Retorna: memórias por camada (ativa, latente, arquivo)

### 9. Mandamentos
```bash
curl http://localhost:8100/api/v1/colmeia/mandamentos
```
Retorna: os 11 Mandamentos da Colmeia

### 10. Patentes
```bash
curl http://localhost:8100/api/v1/colmeia/patentes
```
Retorna: 7 níveis de patentes (Recruta até Coronel)

### 11. Critérios de Avaliação
```bash
curl http://localhost:8100/api/v1/colmeia/criterios-avaliacao
```
Retorna: 5 critérios ponderados para avaliar contribuições

## Exemplos de Resposta

### Ranking (top 1)
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
        "foco": 0.78
      }
    }
  ]
}
```

### Estado
```json
{
  "total_npcs": 151,
  "ativos": 145,
  "latentes": 6,
  "memorias_ativas": 2847,
  "memorias_arquivo": 1204,
  "coroneis": 3,
  "majores": 12,
  "ranking_top5": [...]
}
```

## Referência Rápida

| Endpoint | Método | Descrição | Filtros |
|----------|--------|-----------|---------|
| `/ranking` | GET | Top N NPCs | `?top=20` |
| `/estado` | GET | Snapshot geral | — |
| `/npc/{nome}` | GET | Detalhe completo | — |
| `/npc/{nome}/genoma` | GET | Parâmetros evolutivos | — |
| `/npc/{nome}/memorias` | GET | Memórias por camada | `?camada=ativa&limite=50` |
| `/comparar-genomas` | GET | Compara 2 NPCs | `?npc1=A&npc2=B` |
| `/latentes` | GET | NPCs inativos | — |
| `/top-patentes` | GET | Agrupado por patente | `?patente=Coronel` |
| `/mandamentos` | GET | Os 11 Mandamentos | — |
| `/patentes` | GET | Tabela de patentes | — |
| `/criterios-avaliacao` | GET | Critérios de scoring | — |

## Parâmetros do Genoma

- `temperatura` (0.1-0.9): Verbosidade
- `profundidade` (0-10): Profundidade de análise
- `iniciativa` (0.0-1.0): Proatividade
- `contrarianism` (0.0-1.0): Propensão a discordar
- `velocidade` (1-10): Velocidade de resposta
- `foco` (0.0-1.0): Especialização

## Patentes (Ranking)

| Patente | Pontos | Descrição |
|---------|--------|-----------|
| Recruta | 0-10 | Provando que funciona |
| Soldado | 11-30 | Confiável para tarefas simples |
| Sargento | 31-60 | Consistente, qualidade aceitável |
| Tenente | 61-100 | Acima da média |
| Capitão | 101-200 | Excelente, referência |
| Major | 201-500 | Elite |
| Coronel | 501+ | Topo absoluto |

## Como Iniciar o Servidor

```bash
python main.py serve --port 8100
```

Acesse: http://localhost:8100/docs (Swagger UI interativo)

## Dicas

1. Use `?top=` para limitar resultados em ranking
2. Use `?camada=ativa` para filtrar memórias por tipo
3. Use `?patente=Coronel` para filtrar por patente
4. Use `?npc1=&npc2=` para comparar genomas
5. Nomes com espaços: use `%20` na URL ou aspas

## Documentação Completa

Veja `API_COLMEIA.md` para documentação técnica completa.
