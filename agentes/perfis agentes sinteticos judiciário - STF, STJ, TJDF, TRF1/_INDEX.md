# Magistrados - Hub Juridico

> Mapa local para `agentes/perfis agentes sinteticos judiciário - STF, STJ, TJDF, TRF1/`.
> Atualizado em 2026-03-17.

## O que ha aqui

Este diretorio reune o bloco juridico sintetico do projeto:

- perfis estruturados por tribunal
- metadados e schemas
- dossies em Markdown para navegacao humana/IA

## Entrada recomendada

| Se voce quer... | Abra primeiro |
|-----------------|--------------|
| entender o escopo e as restricoes | [meta/README.md](meta/README.md) |
| abrir dossies navegaveis | [dossies/INDICE.md](dossies/INDICE.md) |
| consultar perfis estruturados | uma das pastas `STF/`, `STJ/`, `TJDFT/`, `TRF1/` |
| entender limitacoes | [meta/NOTAS_LIMITACOES.md](meta/NOTAS_LIMITACOES.md) |
| ver fontes sugeridas | [meta/FONTES_SUGERIDAS.md](meta/FONTES_SUGERIDAS.md) |

## Estrutura

| Pasta | Conteudo |
|-------|----------|
| `STF/` | 11 perfis estruturados |
| `STJ/` | 33 perfis estruturados |
| `TJDFT/` | 47 perfis estruturados |
| `TRF1/` | 44 perfis estruturados |
| `dossies/` | dossies Markdown por tribunal |
| `meta/` | schema, indices e notas metodologicas |

## Como navegar sem se perder

### Se a tarefa for analitica

1. [meta/README.md](meta/README.md)
2. [meta/NOTAS_LIMITACOES.md](meta/NOTAS_LIMITACOES.md)
3. arquivo JSON do tribunal alvo

### Se a tarefa for documental

1. [dossies/INDICE.md](dossies/INDICE.md)
2. dossie do magistrado
3. depois, se preciso, perfil estruturado correspondente

### Se a tarefa for de produto/backend

1. este indice
2. [../../backend/app/api/rotas/magistrados.py](../../backend/app/api/rotas/magistrados.py)
3. [../../backend/app/servicos/magistrado_servico_db.py](../../backend/app/servicos/magistrado_servico_db.py)

## Regras importantes

- trate tudo como simulacao transparente, nunca como impersonacao
- campos inferidos devem permanecer rotulados como hipotese ou simulacao
- use os dossies para navegacao rapida e os perfis estruturados para consumo tecnico
- discrepancias de contagem entre perfis e dossies devem ser tratadas como dado a verificar, nao como verdade automatica

## Atalho por tribunal

| Tribunal | Onde abrir |
|----------|------------|
| STF | `STF/` ou `dossies/STF/` |
| STJ | `STJ/` ou `dossies/STJ/` |
| TJDFT | `TJDFT/` ou `dossies/TJDFT/` |
| TRF1 | `TRF1/` ou `dossies/TRF1/` |

## Memoria local

- [_INSIGHTS.md](_INSIGHTS.md)
- [_CHECKLIST.md](_CHECKLIST.md)
