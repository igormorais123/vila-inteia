# 🏛️ Juristas Lendários Brasileiros (CL101-CL110)

## Consultores Adicionados

| # | ID | Nome | Título | Tier |
|---|-----|------|--------|------|
| 101 | CL101 | **Rui Barbosa** | A Águia de Haia | S |
| 102 | CL102 | **Miguel Reale** | O Filósofo do Direito Brasileiro | S |
| 103 | CL103 | **Pontes de Miranda** | O Tratadista Supremo | S |
| 104 | CL104 | **Sobral Pinto** | O Defensor Intransigente | S |
| 105 | CL105 | **San Tiago Dantas** | O Estadista Jurista | A |
| 106 | CL106 | **Clóvis Beviláqua** | O Arquiteto do Código Civil | S |
| 107 | CL107 | **Evandro Lins e Silva** | O Príncipe da Advocacia Criminal | S |
| 108 | CL108 | **Nelson Hungria** | O Codificador Penal | A |
| 109 | CL109 | **Teixeira de Freitas** | O Precursor Genial | A |
| 110 | CL110 | **Tobias Barreto** | O Condor da Escola do Recife | A |

## Perfis Ultra-Detalhados

Cada jurista tem ~60 campos preenchidos, incluindo:

- **Dados básicos:** nome, título, subtítulo, nacionalidade, anos
- **Biografia:** origem, momento definidor, conquistas, fracassos, legado
- **Personalidade:** traços dominantes, sombra, valores, medos, vieses
- **Expertise:** áreas, frameworks mentais, princípios, estilo de pensamento
- **Comunicação:** tom de voz, estilo de escrita, vocabulário típico, frases célebres
- **Liderança:** estilo, delegação, como trata diferentes pessoas
- **Visões:** política, ética, poder, dinheiro, pessoas, futuro
- **Consultoria:** quando consultar, perguntas típicas, abordagem
- **Rede:** mentores, rivais, influenciadores, influenciados

## Campos Especiais por Jurista

- **Rui Barbosa:** `citacoes_juridicas`, `casos_emblematicos`, `tecnicas_argumentativas`
- **Miguel Reale:** `teoria_explicada` (tridimensionalidade explicada)
- **Pontes de Miranda:** `planos_explicados` (existência/validade/eficácia)
- **Sobral Pinto:** `casos_emblematicos`
- **E mais...**

## Para Inserir no Banco

```bash
cd C:\Agentes\backend
.venv\Scripts\python.exe -m scripts.seed_consultores_lendarios
```

## Arquivos Modificados

1. `backend/scripts/dados_consultores/bloco_101_110_juristas.py` - **NOVO** (63KB)
2. `backend/scripts/dados_consultores/__init__.py` - Atualizado
3. `backend/scripts/seed_consultores_lendarios.py` - Importa novo bloco
4. `backend/app/modelos/consultor_lendario.py` - Nova categoria JURISTA
5. `backend/app/esquemas/consultor_lendario.py` - Nova categoria
6. `frontend/src/types/index.ts` - Nova categoria
7. `frontend/src/components/consultores/ConsultorCard.tsx` - Label da categoria
8. `frontend/src/components/consultores/ConsultoresFilters.tsx` - Label da categoria

---
*Criado em 2025-02-04 por NEXO*
