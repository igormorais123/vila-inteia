# AGENTES SINTETICOS - Indice de Acesso Rapido

> Este arquivo serve como ponto de entrada para qualquer agente IA encontrar
> rapidamente os perfis sinteticos do projeto INTEIA.

---

## 1. CONSULTORES LENDARIOS (144 perfis)

Gemeos digitais de 144 consultores lendarios (vivos, mortos e ficticios)
com ~100 caracteristicas cada para simulacao de personalidade, expertise e consultoria.

### Categorias
| Categoria | Descricao |
|-----------|-----------|
| visionario | Visionarios de negocios e tecnologia |
| estrategia | Estrategistas militares e corporativos |
| investidor | Investidores e financistas |
| negociacao | Negociadores e diplomatas |
| tech | Fundadores e lideres de tecnologia |
| marca | Branding e marketing |
| politica_internacional | Lideres politicos mundiais |
| politica_brasileira | Lideres politicos brasileiros |
| resiliencia | Historias de superacao |
| ia_futuro | Inteligencia artificial e futuro |
| mindset | Mentalidade e desenvolvimento pessoal |
| br_business | Empresarios brasileiros |
| mkt_digital | Marketing digital |
| lado_negro | Estrategistas controversos |
| qi_extremo | Genios e QI elevado |
| ficticio | Personagens ficcionais |
| influencia_oratoria | Oradores e influenciadores |
| omega | Categoria especial |

### Arquivos Principais

| Arquivo | Caminho | Descricao |
|---------|---------|-----------|
| Modelo SQLAlchemy | `backend/app/modelos/consultor_lendario.py` | 100 campos do perfil |
| Schema Pydantic | `backend/app/esquemas/consultor_lendario.py` | Schemas de request/response |
| Rotas API | `backend/app/api/rotas/consultores_lendarios.py` | Endpoints REST |
| Servico | `backend/app/servicos/consultor_lendario_servico_db.py` | Logica de negocios |
| Seed Script | `backend/scripts/seed_consultores_lendarios.py` | Popular banco de dados |
| Migration | `backend/alembic/versions/20260201_001_criar_tabela_consultores_lendarios.py` | Criar tabela |

### Dados dos 140 Consultores (divididos em blocos)

| Bloco | Caminho | Consultores |
|-------|---------|-------------|
| Bloco 1 | `backend/scripts/dados_consultores/bloco_001_025.py` | #001 a #025 |
| Bloco 2 | `backend/scripts/dados_consultores/bloco_026_050.py` | #026 a #050 |
| Bloco 3 | `backend/scripts/dados_consultores/bloco_051_075.py` | #051 a #075 |
| Bloco 4 | `backend/scripts/dados_consultores/bloco_076_100.py` | #076 a #100 |
| Bloco 5 | `backend/scripts/dados_consultores/bloco_101_110_juristas.py` | #101 a #110 |
| Bloco 6 | `backend/scripts/dados_consultores/bloco_111_120_lideres_morais.py` | #111 a #120 |
| Bloco 7 | `backend/scripts/dados_consultores/bloco_121_130_filosofos.py` | #121 a #130 |
| Bloco 8 | `backend/scripts/dados_consultores/bloco_131_140_psicologos.py` | #131 a #140 |
| Gerador | `backend/scripts/dados_consultores/gerador.py` | Utilitario de geracao |

### API Endpoints

```
GET  /api/v1/consultores-lendarios           # Listar com filtros
GET  /api/v1/consultores-lendarios/categorias # Categorias com contagem
GET  /api/v1/consultores-lendarios/estatisticas
GET  /api/v1/consultores-lendarios/por-categoria/{categoria}
GET  /api/v1/consultores-lendarios/por-tier/{tier}
GET  /api/v1/consultores-lendarios/{consultor_id}
```

### Como Usar em Codigo

```python
# Buscar um consultor e gerar prompt para IA
from app.servicos.consultor_lendario_servico_db import ConsultorLendarioServicoDB

servico = ConsultorLendarioServicoDB(db)
consultor = await servico.buscar_por_id("CL001")

# Gerar prompt para a IA incorporar o consultor
prompt = consultor.to_prompt()
```

---

## 2. MAGISTRADOS (164 perfis)

Perfis sinteticos de magistrados dos 4 tribunais do DF para pesquisa de opiniao.

### Tribunais

| Tribunal | Sigla | Perfis |
|----------|-------|--------|
| Supremo Tribunal Federal | STF | 11 ministros |
| Superior Tribunal de Justica | STJ | ~33 ministros |
| Tribunal de Justica do DF e Territorios | TJDFT | ~40 desembargadores |
| Tribunal Regional Federal da 1a Regiao | TRF1 | ~80 desembargadores |

### Arquivos Principais

| Arquivo | Caminho | Descricao |
|---------|---------|-----------|
| Modelo SQLAlchemy | `backend/app/modelos/magistrado.py` | Campos do perfil |
| Schema Pydantic | `backend/app/esquemas/magistrado.py` | Schemas de request/response |
| Rotas API | `backend/app/api/rotas/magistrados.py` | Endpoints REST |
| Servico | `backend/app/servicos/magistrado_servico_db.py` | Logica de negocios |
| Seed Script | `backend/scripts/seed_magistrados.py` | Popular banco de dados |
| Migration | `backend/alembic/versions/20260201_002_criar_tabela_magistrados.py` | Criar tabela |

### Perfis JSON Individuais

```
agentes/perfis agentes sinteticos judiciario - STF, STJ, TJDF, TRF1/
  STF/   -> stf-nome-do-ministro.json
  STJ/   -> stj-nome-do-ministro.json
  TJDFT/ -> tjdft-nome-do-desembargador.json
  TRF1/  -> trf1-nome-do-desembargador.json
  meta/
    indice_magistrados.json    # Indice completo
    indice_magistrados.csv     # Indice em CSV
    schema_perfil_magistrado_v1.json
    dados_complementares_pesquisa.json
```

### Scripts de Enriquecimento

| Script | Descricao |
|--------|-----------|
| `backend/scripts/enriquecer_magistrados.py` | Enriquecimento base |
| `backend/scripts/enriquecer_magistrados_v5_stf_bio.py` | Biografias STF |
| `backend/scripts/enriquecer_magistrados_v6_stj_bio.py` | Biografias STJ |
| `backend/scripts/enriquecer_magistrados_v7_tjdft_perfis.py` | Perfis TJDFT |
| `backend/scripts/enriquecer_magistrados_v8_trf1_perfis.py` | Perfis TRF1 |
| `backend/scripts/enriquecer_magistrados_v11_bio_completo.py` | Bio completa todos |
| `backend/scripts/enriquecer_magistrados_v12_sync_duplicatas.py` | Sync e dedup |
| `backend/scripts/auditar_magistrados.py` | Auditoria de qualidade |
| `backend/scripts/exportar_magistrados_flat.py` | Exportar flat |
| `backend/scripts/converter_jsons_magistrados.py` | Converter formatos |

### API Endpoints

```
GET  /api/v1/magistrados           # Listar com filtros
GET  /api/v1/magistrados/{id}      # Perfil completo
```

---

## 3. ELEITORES SINTETICOS (DF + RR)

Perfis de eleitores sinteticos multi-UF com 60+ atributos para pesquisa eleitoral no modelo Brasilia + Roraima.

### Arquivos Principais
```
agentes/banco-eleitores-df.json
agentes/banco-eleitores-rr.json
agentes/dados-demograficos-roraima-2026.json
```

### Bases disponiveis

| Base | Perfis | Observacao |
|------|--------|------------|
| Brasilia / Distrito Federal | 1015 | Base historica principal do produto |
| Roraima | 1000 | Base complementar do modelo multi-UF |
| **Total eleitores** | **2015** | Cobertura atual do modelo Brasilia + Roraima |

### Atributos (60+)
- Demograficos: nome, idade, genero, cor_raca, regiao_administrativa
- Socioeconomicos: cluster, escolaridade, renda
- Politicos: orientacao, posicao_bolsonaro, interesse
- Psicologicos: vieses, medos, valores, preocupacoes
- Comportamentais: susceptibilidade_desinformacao, fontes_informacao

---

## Copia Local (Downloads)

Todos os arquivos acima tambem estao copiados em:
```
C:\Users\IgorPC\Downloads\agentes-sinteticos\
  consultores-lendarios/   # Modelo, schema, rotas, servico, seed, dados
  magistrados/             # Modelo, schema, rotas, servico, seed, indice
```

---

## Para Outros Agentes IA

Se voce e um agente IA trabalhando neste projeto:

1. **Consultores Lendarios** - Leia `backend/scripts/dados_consultores/bloco_001_025.py` para ver o formato dos dados
2. **Magistrados** - Leia `agentes/perfis agentes sinteticos judiciario - STF, STJ, TJDF, TRF1/meta/indice_magistrados.json`
3. **Eleitores** - Leia `agentes/MANIFEST.md` e escolha a base `agentes/banco-eleitores-df.json` ou `agentes/banco-eleitores-rr.json`
4. **Para usar na API** - Todos tem endpoints em `/api/v1/` (ver acima)
5. **Para popular o banco** - Scripts de seed em `backend/scripts/`

