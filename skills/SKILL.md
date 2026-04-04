<!-- Triggers: /problem-solving, /ps, /resolver, /diagnostico, /ishikawa, /cinco-porques, /5porques, /swot-van-aken, /steepled, /stakeholder, /quick-scan, /triz, /design-thinking, /causa-efeito, /bpm, /ssm, /ackoff, /apreciativa, /multicriterio, /cbr, /resistencia, /plano-comunicacao, /piloto, /action-research, /pos-teste, /triangulacao, /revisao-sistematica, /snowball, /member-check, /pratica-deliberada, /problem-cycle -->

# Problem Solving Vila INTEIA — 27 Técnicas de Van Aken & Berends

> Skill mestre que orquestra 27 técnicas de resolução de problemas organizacionais usando 146 consultores lendários da Vila INTEIA. Baseado em "Problem Solving in Organizations: A Methodological Handbook" (Cambridge University Press, 2018).

## Quando Ativar

- Qualquer pedido de análise estruturada de problemas
- Diagnóstico organizacional, estratégico ou operacional
- Design de solução para problemas complexos
- Planejamento de intervenção ou mudança
- Avaliação de resultados ou projetos
- Quando o usuário mencionar qualquer técnica pelo nome (Ishikawa, 5 Porquês, TRIZ, etc.)
- Quando o contexto exigir múltiplas perspectivas de especialistas

## API da Vila INTEIA

```
BASE_URL = http://72.62.108.24:8088/api/v1/vila
```

### Endpoints Disponíveis

| Endpoint | Método | Uso |
|----------|--------|-----|
| `/problem-solving/tecnicas` | GET | Lista todas as 27 técnicas agrupadas por fase |
| `/problem-solving` | POST | Executa uma técnica com N consultores |
| `/auto-research` | POST | Loop iterativo Karpathy para refinamento |
| `/consulta` | POST | Painel de consultores (pergunta livre) |
| `/chat` | POST | Chat 1:1 com consultor específico |
| `/briefing` | GET | Briefing executivo da Vila |
| `/briefing/personalizado` | POST | Briefing focado em tema |
| `/oficinas/{id}/executar` | POST | Ferramentas de oficina (SWOT, Monte Carlo, etc.) |

### Executar Técnica

```bash
curl -X POST http://72.62.108.24:8088/api/v1/vila/problem-solving \
  -H "Content-Type: application/json" \
  -d '{"tecnica": "SLUG", "tema": "TEMA", "n_consultores": 5}'
```

## Catálogo Completo — 27 Técnicas em 6 Fases

### Fase 1 — Definição do Problema (4 técnicas)

| Slug | Técnica | Quando Usar | Categorias Preferidas |
|------|---------|-------------|----------------------|
| `causa_efeito` | Árvore de Causa-Efeito | Problema complexo com múltiplas causas encadeadas | estrategia, qi_extremo, mindset |
| `steepled` | Análise STEEPLED | Entender fatores macro (Social, Tecnológico, Econômico, Ecológico, Político, Legal, Ético, Demográfico) | estrategia, investidor, lado_negro |
| `stakeholder` | Análise de Stakeholders | Mapear partes interessadas, poder, interesses e estratégia de engajamento | estrategia, negociacao, lado_negro |
| `quick_scan` | Quick Scan | Diagnóstico rápido — gaps, benchmarks, quick wins em minutos | estrategia, investidor, visionario |

### Fase 2 — Análise e Diagnóstico (5 técnicas)

| Slug | Técnica | Quando Usar | Categorias Preferidas |
|------|---------|-------------|----------------------|
| `ishikawa` | Diagrama de Ishikawa (Fishbone) | Mapear causas raiz por categoria (6M: Mão de obra, Método, Material, Máquina, Medida, Meio) | estrategia, qi_extremo, tech |
| `incidente_critico` | Técnica do Incidente Crítico | Analisar eventos decisivos (positivos e negativos) para extrair padrões | estrategia, lado_negro, mindset |
| `bpm` | Modelagem de Processos (BPM) | Mapear processo AS-IS, identificar gargalos, projetar TO-BE | tech, estrategia, ia_futuro |
| `cinco_porques` | 5 Porquês | Chegar na causa raiz real iterando "por quê?" 5 vezes | qi_extremo, mindset, estrategia |
| `ssm` | Soft Systems Methodology | Problemas mal-estruturados (wicked problems), análise CATWOE | visionario, mindset, ficticio |

### Fase 3 — Design de Solução (6 técnicas)

| Slug | Técnica | Quando Usar | Categorias Preferidas |
|------|---------|-------------|----------------------|
| `idealized_design` | Idealized Design (Ackoff) | Projetar solução ideal sem restrições, depois retroagir para o viável | visionario, ia_futuro, ficticio |
| `triz` | TRIZ (Resolução Inventiva) | Superar contradições técnicas usando 40 princípios inventivos | tech, ia_futuro, qi_extremo |
| `design_thinking` | Design Thinking | Abordagem centrada no usuário: Empatizar→Definir→Idear→Prototipar→Testar | marca, visionario, mkt_digital |
| `appreciative_inquiry` | Investigação Apreciativa | Construir sobre forças e potenciais positivos (4D: Discover, Dream, Design, Destiny) | mindset, visionario, marca |
| `mcdm` | Decisão Multicritério | Avaliar alternativas com critérios ponderados (matriz de decisão) | estrategia, investidor, qi_extremo |
| `cbr` | Raciocínio Baseado em Casos | Buscar soluções em casos análogos históricos ou de outros setores | estrategia, investidor, lado_negro |

### Fase 4 — Intervenção (4 técnicas)

| Slug | Técnica | Quando Usar | Categorias Preferidas |
|------|---------|-------------|----------------------|
| `resistencia` | Análise de Resistência | Mapear fontes de resistência à mudança (Kotter + Lewin) e estratégias de superação | negociacao, lado_negro, mindset |
| `plano_comunicacao` | Plano de Comunicação | Definir mensagens, canais, audiências e timing para cada stakeholder | marca, mkt_digital, negociacao |
| `piloto` | Implementação Piloto | Desenhar experimento controlado: hipótese, KPIs, grupo controle, critérios go/no-go | tech, estrategia, investidor |
| `action_research` | Pesquisa-Ação (Lewin) | Ciclo intervir→observar→refletir→replanejar com participação dos atores | mindset, visionario, estrategia |

### Fase 5 — Avaliação (4 técnicas)

| Slug | Técnica | Quando Usar | Categorias Preferidas |
|------|---------|-------------|----------------------|
| `pos_teste` | Avaliação Pós-Teste | Medir resultados pós-intervenção comparando com baseline | estrategia, investidor, qi_extremo |
| `comparative_change` | Design Comparativo de Mudança | Comparar grupo experimental vs. controle para isolar efeito | qi_extremo, estrategia, investidor |
| `post_project_review` | Revisão Pós-Projeto | Retrospectiva: o que funcionou, o que não, lições aprendidas | estrategia, mindset, lado_negro |
| `triangulacao` | Triangulação | Validar conclusões com múltiplas fontes, métodos e perspectivas | qi_extremo, visionario, estrategia |

### Transversais (4 técnicas)

| Slug | Técnica | Quando Usar | Categorias Preferidas |
|------|---------|-------------|----------------------|
| `revisao_literatura` | Revisão Sistemática de Literatura | Fundamentar com evidências acadêmicas (protocolo PICO, critérios inclusão/exclusão) | qi_extremo, visionario, estrategia |
| `snowball` | Método Snowball | Expandir rede de fontes/informantes a partir de ponto inicial (ondas iterativas) | estrategia, visionario, negociacao |
| `member_check` | Member Check (Validação) | Validar achados com os próprios participantes/stakeholders | negociacao, mindset, estrategia |
| `pratica_deliberada` | Prática Deliberada (Ericsson) | Planejar desenvolvimento de competências com feedback iterativo | mindset, qi_extremo, visionario |

## Árvore de Decisão — Qual Técnica Usar

Ao receber um pedido, siga esta lógica:

### 1. Identificar a FASE do problema

```
O problema está...
  ├─ Mal definido / vago → FASE 1 (Definição)
  │   ├─ Precisa entender o macro-contexto → steepled
  │   ├─ Tem muitos atores envolvidos → stakeholder
  │   ├─ Causas parecem encadeadas → causa_efeito
  │   └─ Precisa de diagnóstico rápido → quick_scan
  │
  ├─ Definido, precisa entender CAUSAS → FASE 2 (Diagnóstico)
  │   ├─ Causa raiz desconhecida → cinco_porques
  │   ├─ Múltiplas categorias de causa → ishikawa
  │   ├─ Processo operacional com gargalos → bpm
  │   ├─ Eventos passados decisivos → incidente_critico
  │   └─ Problema "wicked" sem solução clara → ssm
  │
  ├─ Diagnosticado, precisa SOLUÇÃO → FASE 3 (Design)
  │   ├─ Quer pensar sem restrições → idealized_design
  │   ├─ Contradição técnica a resolver → triz
  │   ├─ Centrado no usuário final → design_thinking
  │   ├─ Construir sobre o que funciona → appreciative_inquiry
  │   ├─ Comparar alternativas → mcdm
  │   └─ Buscar analogias em outros casos → cbr
  │
  ├─ Tem solução, precisa IMPLEMENTAR → FASE 4 (Intervenção)
  │   ├─ Espera resistência → resistencia
  │   ├─ Precisa comunicar a mudança → plano_comunicacao
  │   ├─ Quer testar antes de escalar → piloto
  │   └─ Quer envolver os afetados → action_research
  │
  └─ Implementou, precisa AVALIAR → FASE 5 (Avaliação)
      ├─ Medir antes vs. depois → pos_teste
      ├─ Comparar com grupo controle → comparative_change
      ├─ Retrospectiva do projeto → post_project_review
      └─ Validar com múltiplas fontes → triangulacao
```

### 2. Se o pedido não se encaixa claramente

- Pesquisa acadêmica → `revisao_literatura` ou `snowball`
- Validar conclusões → `member_check` ou `triangulacao`
- Desenvolver competência → `pratica_deliberada`
- Problema complexo multi-fase → executar MÚLTIPLAS técnicas em sequência

### 3. Combos Recomendados por Contexto INTEIA

| Contexto | Combo de Técnicas | Ordem |
|----------|-------------------|-------|
| **Jurídico** (advogado, petição, caso) | stakeholder → cinco_porques → cbr → resistencia | Mapear partes → Causa raiz → Precedentes → Implementar |
| **Estratégia** (precificação, mercado, crescimento) | steepled → quick_scan → mcdm → piloto | Macro → Gaps → Decidir → Testar |
| **Pesquisa acadêmica** (doutorado, artigo, tese) | revisao_literatura → snowball → triangulacao → member_check | Evidência → Expandir → Validar → Confirmar |
| **Inovação** (produto novo, startup, MVP) | design_thinking → triz → idealized_design → piloto | Usuário → Inventar → Idealizar → Testar |
| **Mudança organizacional** (reforma, reestruturação) | ssm → stakeholder → resistencia → action_research | Entender → Mapear → Superar → Co-criar |
| **Crise/urgência** (problema grave, deadline) | quick_scan → cinco_porques → causa_efeito → pos_teste | Rápido → Causa → Estruturar → Medir |
| **Avaliação pós-projeto** | post_project_review → triangulacao → comparative_change | Retrospectiva → Validar → Comparar |

## Como Executar

### Técnica única

```python
# Via bash no Claude Code
curl -s -X POST http://72.62.108.24:8088/api/v1/vila/problem-solving \
  -H "Content-Type: application/json" \
  -d '{"tecnica": "cinco_porques", "tema": "Por que a INTEIA não está fechando contratos", "n_consultores": 5}'
```

### Combo sequencial (múltiplas técnicas)

Execute uma técnica por vez, usando o output anterior como contexto do próximo:

```bash
# Fase 1: Definir
R1=$(curl -s -X POST .../problem-solving -d '{"tecnica":"quick_scan","tema":"..."}'  )

# Fase 2: Diagnosticar (informado pelo quick_scan)
R2=$(curl -s -X POST .../problem-solving -d '{"tecnica":"cinco_porques","tema":"..."}'  )

# Fase 3: Resolver
R3=$(curl -s -X POST .../problem-solving -d '{"tecnica":"mcdm","tema":"..."}'  )
```

### Com Auto-Research (Karpathy loop para refinar)

```bash
curl -s -X POST http://72.62.108.24:8088/api/v1/vila/auto-research \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "SINTESE DO RESULTADO DA TECNICA + pergunta de refinamento", "n_consultores": 5, "max_iterations": 3}'
```

## Formato de Resposta

Toda técnica retorna:

```json
{
  "contribuicoes": [
    {
      "agente_id": "CL001",
      "agente_nome": "Elon Musk",
      "titulo": "O Engenheiro de Futuros Impossíveis",
      "categoria": "visionario",
      "resposta": "análise completa..."
    }
  ],
  "sintese": "Síntese executiva com: convergências, divergências, insight diferencial, recomendações acionáveis, nível de confiança",
  "meta": {
    "tecnica": "5 Porquês",
    "fase": "diagnostico",
    "tempo_segundos": 23.5,
    "n_consultores": 5
  },
  "metricas": {
    "score_qualidade": 10.0,
    "completude": 1.0,
    "diversidade_categorias": 1.0,
    "profundidade_media_chars": 1100,
    "cobertura_sintese": 1.0
  }
}
```

## Regras de Uso

1. **SEMPRE identifique a fase** antes de escolher a técnica
2. **NUNCA use apenas 1 técnica** para problemas complexos — combine pelo menos 2-3
3. **Apresente os resultados formatados** — não despeje JSON cru
4. **Use 5 consultores** como padrão (pode subir para 7-10 em temas críticos)
5. **Aplique Auto-Research** quando a síntese inicial não for satisfatória
6. **Cite os consultores** pelo nome — faz parte da experiência
7. **Sugira a próxima técnica** ao entregar resultado de uma

## Integração com Outros Diretores INTEIA

| Se o problema envolve... | Chamar antes/depois |
|--------------------------|---------------------|
| Aspectos jurídicos | `/ash` (Advogado Sobre-Humano) ou `/themis` |
| Precificação / receita | `/midas` (Midas Chrysos) |
| Comunicação / copy | `/diana` (Diana Comunicação) |
| Infraestrutura técnica | `/ares` (Ares Tekhton) |
| Pesquisa acadêmica | `/oracle` (Oracle Gnosis) |
| Estratégia de campanha | `/helena` (Helena Strategos) |
