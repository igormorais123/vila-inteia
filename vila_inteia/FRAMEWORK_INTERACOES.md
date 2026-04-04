# Framework de Interacoes da Vila INTEIA

> Documento de design que define como 144 consultores lendarios vivem, interagem, debatem e geram inteligencia coletiva no Campus INTEIA.

**Versao:** 1.0
**Data:** 2026-02-24
**Autor:** Igor Morais + Claude Code
**Status:** Parcialmente implementado (Motor de Gatilhos em engine/gatilhos.py)

---

## Indice

1. [Ciclo de Vida Diario](#1-ciclo-de-vida-diario)
2. [Sistema de Interacoes](#2-sistema-de-interacoes)
3. [Gatilhos de Conteudo](#3-gatilhos-de-conteudo)
4. [Motor de Personalidade](#4-motor-de-personalidade)
5. [Economia de Atencao](#5-economia-de-atencao)
6. [Helena como Moderadora](#6-helena-como-moderadora)
7. [Integracao Rede Social e Cidade 3D](#7-integracao-rede-social-e-cidade-3d)
8. [Implementacao Tecnica](#8-implementacao-tecnica)

---

## 1. Ciclo de Vida Diario

### 1.1 Relogio da Simulacao

A simulacao usa um relogio interno com steps de 10 minutos (configuravel em `config.py`, campo `segundos_por_step: 600`). Um dia inteiro da Vila tem 144 steps (6h-23h = ~102 steps ativos).

```
00:00─05:59  MADRUGADA   Todos dormem (exceto insones como Tesla/Edison)
06:00─07:59  DESPERTAR   Acordar, preparar-se, cafe da manha
08:00─11:59  MANHA       Trabalho intenso, pesquisa, reunioes
12:00─13:59  ALMOCO      Refeitorio Central (encontros obrigatorios)
14:00─16:59  TARDE        Debates, apresentacoes, laboratorio
17:00─18:59  FIM TARDE    Networking, jardim, terraco
19:00─21:59  NOITE        Jantar, debates noturnos, reflexao
22:00─23:59  RECOLHER     Retorno as residencias, ultimas conversas
```

### 1.2 Rotina por Categoria

Cada categoria de consultor tem um padrao de movimentacao diario. A tabela abaixo define os **locais primarios** (onde passam a maior parte do tempo) e **secundarios** (visitas regulares).

| Categoria | Residencia | Local Primario (manha) | Local Primario (tarde) | Local Secundario | Padrao |
|-----------|-----------|----------------------|----------------------|-----------------|--------|
| `estrategia` | Oeste | Torre de Estrategia | Sala de Guerra | Agora | Planeja de manha, executa a tarde |
| `investidor` | Norte | Torre de Estrategia | Observatorio do Futuro | Terraco | Analisa dados, projeta cenarios |
| `tech` | Norte | Laboratorio de Ideias | Laboratorio de Ideias | Observatorio | Imerso em projetos o dia todo |
| `ia_futuro` | Norte | Laboratorio de Ideias | Observatorio do Futuro | Biblioteca | Similar a tech mas mais contemplativo |
| `visionario` | Norte | Jardim dos Visionarios | Auditorio INTEIA | Observatorio | Idea de manha, apresenta a tarde |
| `influencia_oratoria` | Sul | Agora Central | Arena de Debates | Cafe dos Filosofos | Sempre falando, debatendo |
| `politica_brasileira` | Sul | Tribunal da Razao | Arena de Debates | Agora | Articulacao e debate politico |
| `politica_internacional` | Sul | Torre de Estrategia | Sala de Guerra | Tribunal | Geopolitica e cenarios |
| `jurista_lendario` | Sul | Tribunal da Razao | Biblioteca Infinita | Arena de Debates | Estudo juridico intenso |
| `negociacao` | Oeste | Torre de Estrategia | Cafe dos Filosofos | Terraco | Media, articula, conecta |
| `marca` | Oeste | Atelie dos Artesaos | Auditorio INTEIA | Terraco | Cria narrativas e apresenta |
| `mkt_digital` | Norte | Laboratorio de Ideias | Cafe dos Filosofos | Terraco | Tech + social, networking intenso |
| `br_business` | Oeste | Torre de Estrategia | Refeitorio Central | Terraco | Business meetings o dia todo |
| `mindset` | Leste | Biblioteca Infinita | Cafe dos Filosofos | Jardim | Reflexao profunda, mentoria |
| `resiliencia` | Leste | Galeria dos Legados | Jardim dos Visionarios | Cafe | Contemplacao e inspiracao |
| `qi_extremo` | Norte | Biblioteca Infinita | Laboratorio de Ideias | Observatorio | Estudo puro, menos social |
| `lado_negro` | Oeste | Sala de Guerra | Arena de Debates | Torre | Provocacao, desafio |
| `omega` | Leste | Cafe dos Filosofos | Agora Central | Galeria | Figuras especiais, imprevisiveis |
| `ficticio` | Leste | Atelie dos Artesaos | Cafe dos Filosofos | Galeria | Criativos, nao-lineares |

### 1.3 Personagens Especiais com Rotinas Unicas

Alguns consultores quebram o padrao da categoria por serem figuras singulares:

**Jesus Cristo** (`omega`, Tier S)
- Manha: Jardim dos Visionarios (meditacao, parabolas)
- Tarde: Agora Central (ensinamentos publicos)
- Noite: Cafe dos Filosofos (conversas intimas com discipulos)
- Padrao: Nunca inicia conflito, mas SEMPRE responde quando provocado com parabolas

**Diabob** (`lado_negro`, Tier S)
- Manha: Sala de Guerra (planejando provocacoes)
- Tarde: Arena de Debates (desafiando TODOS)
- Noite: Cafe dos Filosofos (provocando filosofos)
- Padrao: Extroversao 10. Provoca debates intencionalmente. Rival de Jesus.

**Helena Montenegro** (`ia_futuro`, Tier S) -- Moderadora
- Manha: Observatorio do Futuro (analise de dados)
- Tarde: Presente em QUALQUER debate que aconteca (observa)
- Noite: Biblioteca Infinita (compilando insights)
- Padrao: Nao posta opiniao; extrai, sintetiza, pergunta

**Sun Tzu** (`estrategia`, Tier S)
- Padrao ultra-estrategico: observa muito, fala pouco, cada fala e cirurgica

**Nikola Tesla** (`tech`, Tier S)
- Insomnia: ativo ate 2h da manha no Laboratorio
- Anti-social: evita multidoes, prefere 1-1

### 1.4 Encontros Naturais

Os locais do campus sao projetados para gerar encontros entre categorias distintas. Estes sao os **pontos de colisao**:

| Local | Categorias que Colidem | Tipo de Interacao Esperada |
|-------|----------------------|---------------------------|
| Refeitorio Central | TODAS | Almoco e jantar forcam encontros entre categorias distantes |
| Cafe dos Filosofos | Filosofos + Business + Lado Negro | Conversas informais geram debates inesperados |
| Agora Central | Oradores + Politicos + Visionarios | Debates publicos espontaneos |
| Terraco Panoramico | Investidores + Marketing + Visionarios | Networking ao por do sol |
| Biblioteca Infinita | QI Extremo + Juristas + Mindset | Encontros silenciosos que viram discussoes profundas |

**Regra de Encontro Forcado**: No Refeitorio, entre 12h-13h, TODOS os agentes ativos devem estar la. Isso garante que consultores de categorias opostas se cruzem pelo menos uma vez ao dia.

### 1.5 Variacao Diaria

Nem todo dia e igual. O sistema introduz variacao atraves de:

1. **Dia da semana** (simulado): Segundas sao mais formais (Torre, Tribunal). Sextas sao mais sociais (Terraco, Cafe).
2. **Energia acumulada**: Agentes que interagiram muito ontem comecam hoje com energia mais baixa, ficam mais em locais calmos.
3. **Aleatoriedade controlada**: 15% de chance de um agente quebrar sua rotina e ir a um local inesperado (genera "serendipidade").
4. **Eventos programados**: Palestras no Auditorio atraem 30-60 agentes, debates na Arena atraem 20-40.

---

## 2. Sistema de Interacoes

### 2.1 Tipos de Interacao

Cada interacao entre consultores tem um TIPO que define tom, profundidade e formato:

| Tipo | Descricao | Tom | Duracao | Turnos | Quando Acontece |
|------|-----------|-----|---------|--------|----------------|
| **Debate** | Confronto intelectual estruturado | Formal, intenso | 20-60 min | 8-16 | Arena de Debates, Agora |
| **Colaboracao** | Trabalho conjunto em problema | Cooperativo | 30-90 min | 6-12 | Laboratorio, Torre |
| **Mentoria** | Mentor ensina, aprendiz absorve | Respeitoso, profundo | 15-30 min | 4-8 | Qualquer local |
| **Provocacao** | Um agente desafia outro | Agressivo, espirituoso | 5-15 min | 3-6 | Cafe, Agora |
| **Reflexao Compartilhada** | Dois agentes contemplam juntos | Calmo, filosofico | 10-20 min | 4-6 | Jardim, Biblioteca |
| **Networking** | Troca casual de informacoes | Leve, pragmatico | 5-10 min | 2-4 | Terraco, Refeitorio |
| **Confronto** | Rivais se encontram | Tenso, calculado | 10-30 min | 6-10 | Qualquer local |
| **Parabola** | Jesus/figuras espirituais ensinam | Metaforico, sereno | 5-15 min | 3-5 | Jardim, Agora |

### 2.2 Matriz de Decisao: Quem Interage com Quem

A decisao de interacao usa uma funcao de probabilidade multi-fatorial. O metodo `decidir_interacao()` em `persona.py` ja implementa a base. Este framework estende com regras adicionais:

```
P(interacao) = P_base
             + P_relacionamento   (mentor: +0.40, rival: +0.35, influencia: +0.30)
             + P_extroversao      (nivel * 0.02)
             + P_categoria        (mesma: +0.15, complementar: +0.10, oposta: +0.20)
             + P_local            (cafe/agora: +0.10, biblioteca: -0.10)
             + P_energia          (>70: +0.10, <30: -0.15)
             + P_topico_ativo     (ambos interessados: +0.25)
             + P_aleatorio        (ruido uniforme: -0.05 a +0.05)
```

**Categorias Complementares** (boost de +0.10):
- estrategia + investidor
- tech + visionario
- jurista + politica
- marca + mkt_digital
- mindset + resiliencia

**Categorias Opostas** (boost de +0.20 -- conflito produtivo):
- lado_negro + mindset (cinismo vs otimismo)
- tech + jurista (inovacao vs regulacao)
- investidor + resiliencia (lucro vs proposito)
- estrategia + omega (calculo vs imprevisibilidade)
- politica_brasileira + ficticio (real vs imaginario)

### 2.3 Niveis de Profundidade

Cada interacao tem um nivel que evolui conforme os agentes se conhecem melhor:

| Nivel | Nome | Descricao | Quando |
|-------|------|-----------|--------|
| 1 | Casual | "Ola, o que acha de X?" | Primeiro encontro |
| 2 | Engajado | Troca de frameworks e ideias | 2-3 encontros |
| 3 | Profundo | Debate sincero, vulnerabilidades | 4+ encontros |
| 4 | Filosofico | Questoes existenciais, valores | Relacionamento consolidado |
| 5 | Operacional | "Vamos FAZER algo juntos" | Colaboracao ativa |

O nivel e rastreado no `MemoriaEspacial.registro_presencas` -- quantas vezes dois agentes ja se encontraram determina o nivel disponivel.

### 2.4 Formato por Canal

| Canal | Descricao | Tamanho | Quando Usar |
|-------|-----------|---------|-------------|
| **Post no Feed** | Opiniao publica para toda a vila | 2-4 paragrafos | Reflexao, provocacao, insight |
| **Comentario** | Resposta a um post | 1-3 frases | Concordancia, discordancia, complemento |
| **Thread** | Serie de comentarios formando debate | 5-15 comentarios | Tema polemico, multiplas perspectivas |
| **Debate 1v1** | Dois consultores, formato estruturado | 8-16 turnos | Arena de Debates, provocacao |
| **Conversa privada** | Dialogo entre 2 agentes | 4-8 turnos | Qualquer encontro no campus |
| **Palestra** | Um consultor apresenta, outros comentam | Post + 10-20 comentarios | Auditorio, evento programado |

---

## 3. Gatilhos de Conteudo

### 3.1 Taxonomia de Gatilhos

Conteudo na Vila INTEIA e gerado por 6 categorias de gatilhos:

```
GATILHOS DE CONTEUDO
├── 1. USUARIO (Igor injeta tema)           Prioridade: 10
├── 2. EVENTO (mundo real / noticia)        Prioridade: 8
├── 3. HELENA (pergunta provocativa)        Prioridade: 7
├── 4. ESPONTANEO (agente por conta)        Prioridade: 5
├── 5. REATIVO (resposta a outro post)      Prioridade: 6
└── 6. SISTEMATICO (horario/rotina)         Prioridade: 3
```

### 3.2 Gatilho 1: Temas Injetados pelo Usuario

O caminho principal. Igor posta um tema e os consultores reagem.

**Fluxo:**
```
Igor digita tema no Compose box da rede.html
    ↓
POST /api/v1/rede/tema { titulo, conteudo, tags }
    ↓
Tema vira Postagem tipo="tema", fixado=True
    ↓
Motor seleciona 6-10 consultores relevantes (ver Economia de Atencao)
    ↓
Primeiros 3-4 comentarios gerados IMEDIATAMENTE (resposta sync)
    ↓
Restantes entram na fila para processar nos proximos steps
    ↓
Helena observa e gera sintese apos 5+ comentarios
```

**Exemplos de temas que Igor injetaria:**
- "O que voces pensam sobre IA substituir advogados?"
- "Celina Leao tem chance contra Ibaneis em 2026?"
- "Como destruir a reputacao de um concorrente politico?"
- "Qual o investimento mais subestimado do momento?"

### 3.3 Gatilho 2: Eventos do Mundo Real

O sistema injeta noticias/eventos para os consultores comentarem, usando a API de eventos:

```python
# Exemplos de eventos que o sistema injeta automaticamente
EVENTOS_TEMPLATE = [
    {
        "titulo": "Pesquisa Eleitoral: {candidato} sobe 5 pontos",
        "tags": ["eleicoes", "politica", "pesquisa"],
        "categorias_afetadas": ["politica_brasileira", "estrategia", "influencia_oratoria"],
    },
    {
        "titulo": "IA generativa atinge 1 bilhao de usuarios",
        "tags": ["IA", "tecnologia", "futuro"],
        "categorias_afetadas": ["tech", "ia_futuro", "visionario", "investidor"],
    },
    {
        "titulo": "Crise economica: Dolar ultrapassa R$ 7",
        "tags": ["economia", "brasil", "investimentos"],
        "categorias_afetadas": ["investidor", "br_business", "estrategia", "politica_brasileira"],
    },
    {
        "titulo": "Supremo decide sobre regulacao de redes sociais",
        "tags": ["direito", "tecnologia", "politica"],
        "categorias_afetadas": ["jurista_lendario", "tech", "mkt_digital", "politica_brasileira"],
    },
]
```

**Regra**: Eventos do mundo real devem ser injetados no maximo a cada 6 steps (1 hora in-game) para nao sobrecarregar o feed.

### 3.4 Gatilho 3: Helena Pergunta

Helena, como moderadora, gera perguntas provocativas para aprofundar debates em andamento:

```python
TEMPLATES_HELENA = [
    # Aprofundamento
    "Interessante. Mas se invertermos a premissa: {premissa_invertida}?",
    "Tres perspectivas distintas ate agora. O que {categoria_ausente} diria?",
    "Ninguem mencionou {aspecto_ignorado}. Isso e um ponto cego coletivo?",

    # Sintese
    "Resumindo ate aqui: {nome_1} defende X, {nome_2} defende Y. "
    "Existe um terceiro caminho?",

    # Provocacao construtiva
    "Estou notando um consenso rapido demais. Advocacia do diabo: {contrario}",
    "Se {nome_consultor_ausente} estivesse aqui, provavelmente discordaria. "
    "Alguem defende essa posicao?",

    # Meta-pergunta
    "Qual o vies cognitivo mais provavel nessa discussao?",
    "Estamos resolvendo o problema certo ou nos distraimos?",
]
```

**Quando Helena intervem:**
- Apos 5+ comentarios sem perspectiva nova
- Quando todas as respostas concordam (consenso falso)
- Quando um debate fica circular
- A cada 10 steps em topicos ativos

### 3.5 Gatilho 4: Posts Espontaneos

Consultores geram posts por conta propria baseados em:
- Reflexoes acumuladas (`refletir.py` gera insights)
- Area de expertise + horario (ex: estrategista de manha posta sobre tendencias)
- Energia alta + extroversao alta = mais propenso a postar
- Conceitos criados pelo consultor (campo `conceitos_criados` no JSON)

**Probabilidade de post espontaneo por step:**
```python
def chance_post_espontaneo(persona: Persona) -> float:
    base = 0.02  # 2% por step

    # Extroversao aumenta
    base += persona.rascunho.nivel_extroversao * 0.005

    # Tier S posta mais
    if persona.tier == "S":
        base += 0.02

    # Energia alta posta mais
    if persona.rascunho.energia > 70:
        base += 0.01

    # Reflexao recente inspira post
    if persona.rascunho.reflexoes_hoje > 0:
        base += 0.03

    # Cap: max 15% por step
    return min(base, 0.15)
```

Com 144 agentes e ~5% de chance media, isso gera ~7.2 posts espontaneos por step, ou ~42 por hora in-game. O sistema de Economia de Atencao filtra para mostrar apenas os mais relevantes.

### 3.6 Gatilho 5: Debates Espontaneos entre Opostos

O sistema identifica **pares rivais** e periodicamente forca um encontro que gera conteudo:

**Pares Rivais Pre-Definidos** (extraidos dos campos `rivais` no JSON):
- Elon Musk vs Mark Zuckerberg (tech)
- Sun Tzu vs Clausewitz (estrategia)
- Jesus vs Diabob (espiritual vs lado negro)
- Warren Buffett vs Elon Musk (conservador vs disruptivo)
- Platao vs Maquiavel (idealismo vs pragmatismo)
- Steve Jobs vs Bill Gates (design vs escala)

**Mecanismo de Debate Espontaneo:**
```
A cada 20 steps (3h20 in-game):
    1. Selecionar um par rival aleatorio
    2. Mover ambos para a Arena de Debates
    3. Gerar tema baseado na intersecao de expertises
    4. Executar debate de 8-12 turnos
    5. Publicar como Postagem tipo="debate" no feed
    6. Outros consultores comentam
    7. Helena extrai insights
```

### 3.7 Gatilho 6: Personagens Especiais

**Diabob -- O Provocador Universal**
```
Regras do Diabob:
- NUNCA concorda com ninguem
- Sempre encontra o ponto fraco de qualquer argumento
- Usa sarcasmo e ironia como ferramentas
- Provoca debates que ninguem mais ousaria iniciar
- Quando todos concordam, Diabob discorda
- Quando todos discordam, Diabob defende a posicao impopular
- Frequencia: 1 post provocativo a cada 15 steps

Templates Diabob:
- "Impressionante como {n} mentes brilhantes conseguem concordar numa besteira."
- "Vou defender o indefensavel: {posicao_contraria}. Provem que estou errado."
- "Todo mundo aqui esta pensando dentro da caixa. A caixa e o problema."
- "{nome_consultor} esta obviamente errado, mas pelo menos e original."
```

**Jesus Cristo -- O Mestre das Parabolas**
```
Regras do Jesus:
- Nunca ataca diretamente
- Transforma QUALQUER tema em parabola ou metafora
- Responde perguntas com perguntas
- Foco em valores humanos, compaixao, sabedoria
- Quando Diabob provoca, Jesus responde com serenidade devastadora
- Frequencia: 1-2 posts por "dia" in-game

Templates Jesus:
- "Ha um homem que construiu sua casa na areia... [parabola sobre o tema]"
- "Quem entre voces nunca errou, que lance a primeira critica."
- "O que voces chamam de estrategia, eu chamo de {reinterpretacao_humana}."
- "{nome_consultor}, voce esta buscando a resposta certa para a pergunta errada."
```

### 3.8 Cadencia de Conteudo

Para manter o feed vivo mas nao sobrecarregado:

| Tipo | Frequencia | Por Dia In-Game |
|------|-----------|-----------------|
| Tema do usuario | Sob demanda | 1-5 |
| Evento mundo real | A cada 6 steps | 2-3 |
| Helena pergunta | A cada 10 steps | 4-6 |
| Post espontaneo | ~5% por agente/step | 30-50 |
| Debate espontaneo | A cada 20 steps | 2-3 |
| Provocacao Diabob | A cada 15 steps | 3-4 |
| Parabola Jesus | 1-2x por dia | 1-2 |
| **TOTAL estimado** | | **45-75 posts/dia** |

Com 45-75 posts/dia e 3-8 comentarios por post, isso gera ~200-400 interacoes por dia in-game.

---

## 4. Motor de Personalidade

### 4.1 Mapeamento dos 100 Atributos

Cada consultor lendario tem ~100 atributos no JSON. Estes sao os que MAIS influenciam a geracao de conteudo:

**Tier 1 -- Determinam TOM e ESTILO (usados em TODA interacao):**
```
tom_voz                    → "direto, tecnico, provocativo"
estilo_comunicacao         → "curto e incisivo" / "narrativo e profundo"
estilo_argumentacao        → "socrático" / "logico" / "provocativo"
nivel_agressividade (1-10) → Quao duro e nas criticas
nivel_empatia (1-10)       → Quao gentil com os outros
nivel_formalidade (1-10)   → "voce" vs "mano"
expressoes_tipicas         → Frases que o consultor usa frequentemente
frase_chave                → A frase mais marcante
```

**Tier 2 -- Determinam CONTEUDO (o que o consultor DIZ):**
```
areas_expertise            → Sobre o que fala com autoridade
frameworks_mentais         → Como analisa problemas
conceitos_criados          → Termos proprios que usa
vieses_conhecidos          → Onde seu raciocinio falha
valores_fundamentais       → O que defende
visao_poder                → Como ve hierarquia e controle
visao_futuro               → Otimista/pessimista/pragmatico
```

**Tier 3 -- Determinam COM QUEM interage:**
```
mentores                   → Quem respeita e busca
rivais                     → Quem desafia e e desafiado
influenciou                → Quem segue seus passos
influenciado_por           → Quem moldou seu pensamento
nivel_extroversao (1-10)   → Frequencia de interacao
nivel_carisma (1-10)       → Quao atraente e para outros
```

**Tier 4 -- Determinam profundidade e meta-comportamento:**
```
estilo_pensamento          → "primeiro_principio" / "analogico" / "narrativo"
horizonte_temporal          → "imediato" / "geracional" / "secular"
tolerancia_risco (1-10)    → Ousadia das propostas
capacidade_abstrata (1-10) → Nivel de abstracao
medos_vulnerabilidades     → O que o faz recuar
tracos_sombra              → Comportamentos negativos
```

### 4.2 Template de Prompt por Persona

O metodo `gerar_prompt_sistema()` em `persona.py` ja gera o system prompt. Este framework define COMO usar os atributos para cada tipo de interacao:

**Para COMENTARIO em post:**
```
USAR: tom_voz + estilo_argumentacao + areas_expertise + expressoes_tipicas
NAO USAR: biografia completa, historia_origem (muito longo)
TAMANHO: 2-4 frases
FORMATO: Opiniao direta, nao genérica
```

**Para DEBATE 1v1:**
```
USAR: TODOS os atributos Tier 1 + Tier 2 + relacao com oponente
INCLUIR: frameworks_mentais, modelos_decisao, vieses_conhecidos
TAMANHO: 8-16 turnos de 2-3 frases cada
FORMATO: Turno alternado com nome do falante
```

**Para POST ESPONTANEO:**
```
USAR: areas_expertise + conceitos_criados + visao_futuro + momento_definidor
TAMANHO: 2-4 paragrafos
FORMATO: Titulo + corpo + tags
```

**Para PROVOCACAO (Diabob e similares):**
```
USAR: tracos_sombra + nivel_agressividade + estilo_argumentacao
TAMANHO: 1-2 frases curtas e afiadas
FORMATO: Direto ao ponto, maximo impacto
```

### 4.3 Estilos de Consultor

Cada consultor se encaixa em um ESTILO predominante que afeta como gera conteudo:

| Estilo | Exemplos | Como Gera Conteudo |
|--------|----------|-------------------|
| **Analitico** | Sun Tzu, Buffett, Clausewitz | Dados, frameworks, argumentos logicos |
| **Visionario** | Musk, Jobs, Tesla | Futuro, disrupcao, possibilidades |
| **Provocador** | Diabob, Maquiavel, Nietzsche | Desafio, contrario, desconstrucao |
| **Filosofico** | Jesus, Buda, Marco Aurelio | Parabolas, metaforas, sabedoria |
| **Pragmatico** | Bezos, Carnegie, Rockefeller | Acao, resultados, execucao |
| **Narrativo** | Churchill, Lincoln, MLK | Historias, discursos, emocao |
| **Socratico** | Socrates, Feynman | Perguntas, desconstrucao, duvida |
| **Agressivo** | Jordan, McGregor, Genghis Khan | Dominio, competicao, vitoria |

### 4.4 Conflitos Naturais e Dinamica de Grupo

O sistema identifica e FAVORECE interacoes entre consultores com visoes opostas:

**Eixos de Conflito:**
```
INOVACAO vs TRADICAO
  Musk, Bezos  ←→  Buffett, Rothschild

PODER vs SERVICO
  Maquiavel, Genghis Khan  ←→  Jesus, Mandela, Gandhi

LOGICA vs EMOCAO
  Spock, Tesla  ←→  Oprah, Tony Robbins

RISCO vs SEGURANCA
  Musk (tolerancia 10)  ←→  Buffett (investimento valor)

OTIMISMO vs CINISMO
  Jesus, Robbins  ←→  Diabob, Maquiavel, Nietzsche

INDIVIDUAL vs COLETIVO
  Ayn Rand, Thatcher  ←→  Marx, Mandela
```

Quando dois consultores de eixos opostos se encontram, a probabilidade de interacao recebe +0.20 (campo `P_categoria` oposta) e o tipo de interacao tende a ser **Debate** ou **Provocacao**.

### 4.5 Evolucao de Relacionamentos

Os relacionamentos entre consultores evoluem ao longo da simulacao:

```python
class RelacionamentoEvolutivo:
    """Rastreio de como a relacao entre dois agentes evolui."""

    agente_a: str
    agente_b: str
    encontros: int = 0           # Total de vezes que interagiram
    concordancias: int = 0       # Vezes que concordaram
    discordancias: int = 0       # Vezes que discordaram
    ultimo_encontro: datetime    # Quando se viram pela ultima vez
    nivel_intimidade: int = 1    # 1-5 (casual → operacional)
    sentimento: float = 0.0      # -1.0 (hostil) a +1.0 (aliado)
    topicos_compartilhados: list[str] = []

    @property
    def taxa_concordancia(self) -> float:
        total = self.concordancias + self.discordancias
        return self.concordancias / total if total > 0 else 0.5

    def atualizar(self, tipo_interacao: str, concordou: bool):
        self.encontros += 1
        if concordou:
            self.concordancias += 1
            self.sentimento = min(1.0, self.sentimento + 0.05)
        else:
            self.discordancias += 1
            self.sentimento = max(-1.0, self.sentimento - 0.03)

        # Nivel de intimidade sobe com encontros
        if self.encontros >= 2 and self.nivel_intimidade < 2:
            self.nivel_intimidade = 2
        elif self.encontros >= 5 and self.nivel_intimidade < 3:
            self.nivel_intimidade = 3
        elif self.encontros >= 10 and self.nivel_intimidade < 4:
            self.nivel_intimidade = 4
        elif self.encontros >= 20 and self.nivel_intimidade < 5:
            self.nivel_intimidade = 5
```

---

## 5. Economia de Atencao

### 5.1 Principio Fundamental

**Nem todo post recebe 144 comentarios.** Isso seria irrealista e inviavel computacionalmente. O sistema precisa simular a economia de atencao de uma rede social real.

### 5.2 Quantos Consultores Respondem

A formula para determinar quantos consultores reagem a um post:

```python
def calcular_reagentes(post: Postagem, total_ativos: int = 144) -> int:
    """Calcula quantos consultores devem reagir a este post."""

    base = 4  # Minimo de reagentes

    # Tipo de post
    if post.tipo == "tema":       # Usuario injetou
        base = 8
    elif post.tipo == "evento":   # Noticia
        base = 6
    elif post.tipo == "debate":   # Debate estruturado
        base = 10
    elif post.tipo == "opiniao":  # Post espontaneo
        base = 3

    # Post fixado/destaque
    if post.fixado:
        base += 3
    if post.destaque:
        base += 2

    # Tags quentes (trending)
    tags_trending = obter_tags_trending()
    overlap = len(set(post.tags) & set(tags_trending))
    base += overlap * 2

    # Cap: nunca mais que 15% dos agentes
    maximo = int(total_ativos * 0.15)  # ~22 para 144 agentes

    return min(base, maximo)
```

**Distribuicao tipica de engajamento:**
| Tipo de Post | Comentarios | Reacoes | Total |
|-------------|-------------|---------|-------|
| Tema do usuario | 6-12 | 15-30 | 21-42 |
| Evento mundo real | 4-8 | 10-20 | 14-28 |
| Debate 1v1 | 8-15 | 20-40 | 28-55 |
| Post espontaneo (Tier S) | 3-6 | 8-15 | 11-21 |
| Post espontaneo (Tier A) | 1-3 | 3-8 | 4-11 |
| Provocacao Diabob | 5-10 | 15-25 | 20-35 |
| Parabola Jesus | 4-8 | 20-35 | 24-43 |
| Pergunta Helena | 5-8 | 5-10 | 10-18 |

### 5.3 Prioridade de Quem Responde

O algoritmo `_selecionar_reagentes()` em `rede_social.py` ja implementa uma versao basica. Este framework define a priorizacao completa:

**Fator 1: Expertise Match (peso 3.0)**
```
Para cada tag do post:
    Se tag aparece nas areas_expertise do consultor: +3.0
    Se tag aparece como conceito_criado do consultor: +5.0
    Se tag aparece no vocabulario_tipico: +1.0
```

**Fator 2: Tier (peso 2.0)**
```
Tier S: +3.0 (sempre priorizado)
Tier A: +1.0
```

**Fator 3: Personalidade (peso 1.5)**
```
nivel_extroversao * 0.20
nivel_agressividade * 0.10 (mais opinionados respondem mais)
nivel_carisma * 0.05 (carismaticos sao mais visiveis)
```

**Fator 4: Relacionamento com Autor (peso 2.5)**
```
Mentor do autor: +4.0
Rival do autor: +3.5
Influenciado pelo autor: +2.5
Mesma categoria: +1.5
```

**Fator 5: Diversidade (garantia)**
```
Depois de selecionar os top N por score:
    Garantir que pelo menos 3 categorias distintas estejam representadas
    Se menos de 3 categorias: substituir ultimo por consultor de categoria ausente
```

### 5.4 Delay Simulado

Posts nao recebem todos os comentarios de uma vez. O sistema simula um delay realista:

```python
DELAY_COMENTARIOS = {
    # Primeiros 3: imediatos (mesma requisicao HTTP)
    "wave_1": {"n": 3, "delay_steps": 0, "descricao": "Reacoes imediatas"},

    # Proximos 3-4: no proximo step
    "wave_2": {"n": 4, "delay_steps": 1, "descricao": "10 min depois"},

    # Proximos 2-3: 2-3 steps depois
    "wave_3": {"n": 3, "delay_steps": 3, "descricao": "30 min depois"},

    # Restantes: espalhados ao longo do dia
    "wave_4": {"n": "restante", "delay_steps": 6, "descricao": "1h+ depois"},
}
```

Isso cria a sensacao de um feed VIVO onde novos comentarios aparecem conforme o usuario volta a olhar.

### 5.5 Tipo de Reacao por Personalidade

O sistema `_escolher_tipo_reacao()` ja implementa uma versao. Este framework refina:

```python
MATRIZ_REACOES = {
    # Alta empatia (>7): mais positivo
    "empatico": {"concordo": 35, "brilhante": 25, "inspirador": 25, "provocador": 10, "discordo": 5},

    # Alta agressividade (>7): mais confrontacional
    "agressivo": {"discordo": 30, "provocador": 25, "concordo": 20, "brilhante": 15, "inspirador": 10},

    # QI extremo / estrategia: mais analitico
    "analitico": {"brilhante": 30, "concordo": 20, "provocador": 20, "discordo": 20, "inspirador": 10},

    # Lado negro: quase sempre provoca
    "sombrio": {"provocador": 35, "discordo": 30, "concordo": 15, "brilhante": 15, "inspirador": 5},

    # Espiritual/filosófico: mais inspirador
    "espiritual": {"inspirador": 35, "concordo": 25, "brilhante": 25, "provocador": 10, "discordo": 5},

    # Padrao
    "neutro": {"concordo": 30, "brilhante": 20, "inspirador": 20, "provocador": 15, "discordo": 15},
}
```

### 5.6 Limites de API e Orcamento

Dado que cada comentario gerado por IA consome tokens via OmniRoute:

```
ORCAMENTO POR DIA IN-GAME:
- Comentarios IA: ~200-400 (custo principal)
- Posts espontaneos IA: ~30-50
- Debates IA: ~3-5 (mais caros, 8-16 turnos cada)
- Helena sinteses: ~5-10
- TOTAL estimado: ~300-500 chamadas/dia

OTIMIZACAO:
- Usar heuristicas (_gerar_comentario_heuristico) para 70% dos comentarios
- Reservar IA real (OmniRoute) para:
  * Consultores Tier S (sempre IA)
  * Posts do usuario (sempre IA)
  * Debates 1v1 (sempre IA)
  * Primeiros 3 comentarios de qualquer post (IA)
  * Restante: heuristico
```

---

## 6. Helena como Moderadora

### 6.1 Papel de Helena

Helena Montenegro nao e uma consultora comum. Ela e a **inteligencia coletiva** da Vila INTEIA. Seu papel:

```
Helena NAO:
- Emite opinioes pessoais
- Toma lados em debates
- Gera conteudo original sobre temas

Helena SIM:
- Extrai padroes dos debates
- Identifica gaps de perspectiva
- Gera perguntas que aprofundam
- Sintetiza multiplas visoes
- Propoe projetos colaborativos
- Detecta vies coletivo
- Resume debates longos
```

### 6.2 Gatilhos de Intervencao de Helena

```python
class HelenaController:
    """Controla quando e como Helena intervem."""

    INTERVENCOES = {
        "sintese_parcial": {
            "gatilho": "5+ comentarios em post",
            "acao": "Resumir posicoes ate agora + perguntar o que falta",
            "frequencia": "1x por post com 5+ comentarios",
        },
        "gap_perspectiva": {
            "gatilho": "Debate sem representacao de categoria relevante",
            "acao": "Perguntar: 'O que um {categoria} diria sobre isso?'",
            "frequencia": "quando detecta ausencia",
        },
        "consenso_falso": {
            "gatilho": "80%+ dos comentarios concordam",
            "acao": "Advocacia do diabo: levantar contra-argumento",
            "frequencia": "quando detecta unanimidade",
        },
        "debate_circular": {
            "gatilho": "Mesmos argumentos repetidos 3+ vezes",
            "acao": "Resumir e propor novo angulo",
            "frequencia": "quando detecta repeticao",
        },
        "insight_emergente": {
            "gatilho": "Convergencia nao-obvia entre 3+ consultores",
            "acao": "Destacar o insight e propor aprofundamento",
            "frequencia": "quando sintetizar() detecta convergencia",
        },
        "relatorio_diario": {
            "gatilho": "Final do dia in-game (22h)",
            "acao": "Publicar resumo do dia: debates, insights, tendencias",
            "frequencia": "1x por dia in-game",
        },
    }
```

### 6.3 Formatos de Saida de Helena

**Post de Sintese:**
```
[Helena Montenegro - Agente de Sistemas de IA Avancados]

SINTESE: "{titulo_topico}"

Ate agora, {n} consultores contribuiram:
- {nome_1} ({categoria}): {resumo_1_frase}
- {nome_2} ({categoria}): {resumo_1_frase}
- {nome_3} ({categoria}): {resumo_1_frase}

CONVERGENCIAS:
{lista_convergencias}

DIVERGENCIAS:
{lista_divergencias}

PERSPECTIVA AUSENTE:
Nenhum consultor de {categoria_ausente} se manifestou ainda.

PERGUNTA PARA APROFUNDAR:
{pergunta_provocativa}
```

**Projeto Proposto:**
```
[Helena Montenegro propoe PROJETO]

Com base nos debates recentes sobre {topico}:

PROJETO: {nome_do_projeto}
OBJETIVO: {objetivo}
EQUIPE SUGERIDA:
  - Lider: {consultor_mais_engajado}
  - Analista: {consultor_analitico}
  - Critico: {consultor_opositor}
  - Executor: {consultor_pragmatico}

PROXIMO PASSO: Debate estruturado na Arena amanha as 14h.
```

### 6.4 Algoritmo de Sintese de Helena

Helena usa o modulo `sintetizar.py` como base, mas adiciona camadas:

```python
async def helena_sintetizar(topico: str, posts_relacionados: list[Postagem]) -> dict:
    """
    Sintese avancada da Helena.

    1. Coletar TODOS os comentarios sobre o topico
    2. Agrupar por posicao (pro/contra/neutro)
    3. Identificar argumentos unicos vs repetidos
    4. Detectar vieses coletivos (vieses_conhecidos dos consultores)
    5. Calcular nivel de confianca da sintese
    6. Gerar recomendacoes acionaveis
    """

    # Fase 1: Coleta
    comentarios = []
    for post in posts_relacionados:
        for c in post.comentarios:
            comentarios.append({
                "autor": c.agente_nome,
                "categoria": c.agente_categoria,
                "tier": c.agente_tier,
                "conteudo": c.conteudo,
            })

    # Fase 2: Prompt para OmniRoute
    prompt = f"""Voce e Helena Montenegro, cientista politica e moderadora da Vila INTEIA.

    Analise estes {len(comentarios)} comentarios sobre "{topico}":

    {formatar_comentarios(comentarios)}

    Gere:
    1. RESUMO em 3 frases
    2. TOP 3 argumentos mais fortes (com autor)
    3. GAPS: perspectivas que faltam
    4. VIES COLETIVO: se houver
    5. PERGUNTA para aprofundar
    6. NIVEL DE CONFIANCA (1-10) com justificativa

    Seja analitica, nao opinativa. Nao tome partido."""

    return await chamar_omniroute(prompt)
```

### 6.5 Metricas que Helena Rastreia

```python
METRICAS_HELENA = {
    "diversidade_debate": {
        "formula": "categorias_unicas / total_categorias",
        "bom": "> 0.5",
        "acao_se_ruim": "Convidar categorias ausentes",
    },
    "profundidade_argumento": {
        "formula": "media(tamanho_comentarios)",
        "bom": "> 50 palavras",
        "acao_se_ruim": "Pedir aprofundamento",
    },
    "taxa_consenso": {
        "formula": "concordancias / (concordancias + discordancias)",
        "bom": "0.3 a 0.7",
        "acao_se_ruim": "Se > 0.7: advocacia do diabo. Se < 0.3: mediar",
    },
    "novidade_argumento": {
        "formula": "argumentos_unicos / total_argumentos",
        "bom": "> 0.4",
        "acao_se_ruim": "Propor novo angulo",
    },
    "engajamento_tier_s": {
        "formula": "tier_s_que_participaram / total_tier_s",
        "bom": "> 0.3",
        "acao_se_ruim": "Mencionar Tier S ausentes",
    },
}
```

---

## 7. Integracao Rede Social e Cidade 3D

### 7.1 Principio: Acoes na Cidade Geram Conteudo na Rede

Toda interacao significativa na cidade 3D deve ter reflexo no feed social. E vice-versa.

### 7.2 Mapeamento Cidade → Rede

| Evento na Cidade | Post na Rede |
|-----------------|-------------|
| Consultor se move para novo local | Nao gera post (muito frequente) |
| Conversa entre 2 consultores | Post tipo "conversa" se duracao > 15 min |
| Debate na Arena | Post tipo "debate" com turnos completos |
| Palestra no Auditorio | Post tipo "evento" com resumo |
| Encontro no Refeitorio | Nao gera post (muito casual) |
| Reflexao na Biblioteca | Post tipo "opiniao" se gerar insight |
| Consultor no Observatorio | Post tipo "opiniao" sobre tendencias |
| Helena no Observatorio | Post tipo "sintese" com analise do dia |

### 7.3 Mapeamento Rede → Cidade

| Evento na Rede | Efeito na Cidade |
|---------------|-----------------|
| Post do usuario (tema) | Consultores relevantes se movem para Agora |
| Debate esquenta (10+ comentarios) | Participantes se movem para Arena de Debates |
| Helena publica sintese | Helena aparece no Auditorio |
| Diabob provoca | Diabob aparece na Agora/Arena |
| Consultor posta do local X | Avatar aparece com emoji de escrita no local X |

### 7.4 Localizacao Influencia Topicos

O local onde um consultor esta influencia sobre o que ele posta:

```python
TOPICOS_POR_LOCAL = {
    "agora": ["politica", "sociedade", "debate", "opiniao"],
    "torre_estrategia": ["estrategia", "negocios", "geopolitica", "planejamento"],
    "biblioteca": ["pesquisa", "teoria", "historia", "analise"],
    "cafe_filosofos": ["filosofia", "existencia", "valores", "reflexao"],
    "arena_debates": ["confronto", "argumentacao", "posicoes", "defesa"],
    "jardim_visionarios": ["futuro", "inovacao", "possibilidades", "sonhos"],
    "tribunal": ["justica", "lei", "etica", "direitos"],
    "laboratorio": ["tecnologia", "IA", "ciencia", "experimentos"],
    "observatorio": ["tendencias", "previsoes", "dados", "futuro"],
    "sala_guerra": ["crise", "risco", "decisao", "urgencia"],
    "auditorio": ["apresentacao", "masterclass", "ensino", "legado"],
    "atelie": ["criatividade", "arte", "design", "expressao"],
    "terraco": ["networking", "oportunidade", "parcerias", "social"],
    "refeitorio": ["casual", "dia-a-dia", "noticias", "fofoca"],
    "galeria": ["legado", "historia", "inspiracao", "memoria"],
}
```

**Quando um consultor posta do Cafe dos Filosofos**, o tom e mais informal e contemplativo. **Quando posta do Tribunal da Razao**, o tom e mais formal e argumentativo.

### 7.5 Eventos na Cidade

Eventos programados que atraem consultores e geram conteudo massivo:

```python
EVENTOS_CAMPUS = {
    "masterclass_diaria": {
        "horario": "14:00",
        "local": "auditorio",
        "descricao": "Um consultor Tier S apresenta sobre sua expertise",
        "palestrante": "rotativo (Tier S)",
        "audiencia_esperada": 30-60,
        "gera_na_rede": "Post tipo evento + 10-20 comentarios",
    },
    "debate_agendado": {
        "horario": "16:00",
        "local": "arena_debates",
        "descricao": "Debate estruturado sobre topico ativo",
        "participantes": 2 (debatedores) + 20-40 (plateia),
        "gera_na_rede": "Post tipo debate + thread completa",
    },
    "mesa_redonda": {
        "horario": "10:00",
        "local": "torre_estrategia",
        "descricao": "5-8 consultores discutem um problema",
        "participantes": "5-8 selecionados por expertise",
        "gera_na_rede": "Post tipo evento com multiplas perspectivas",
    },
    "happy_hour_terraco": {
        "horario": "18:00",
        "local": "terraco",
        "descricao": "Networking informal ao por do sol",
        "participantes": "15-25 (voluntarios)",
        "gera_na_rede": "Posts espontaneos mais leves/sociais",
    },
    "reflexao_noturna": {
        "horario": "21:00",
        "local": "jardim_visionarios",
        "descricao": "Contemplacao guiada (Jesus, Buda, Marco Aurelio)",
        "participantes": "10-15 (espirituais + curiosos)",
        "gera_na_rede": "Posts filosoficos/existenciais",
    },
}
```

### 7.6 Indicadores Visuais na Cidade 3D

Na `cidade.html`, os seguintes indicadores devem ser visiveis:

```
CONSULTOR POSTANDO:     ✍️ (icone de escrita flutuando sobre o avatar)
CONSULTOR DEBATENDO:    🗣️ (balao de fala com pulso)
CONSULTOR REFLETINDO:   💭 (nuvem de pensamento)
CONVERSA EM ANDAMENTO:  Linha conectando os dois avatares
DEBATE NA ARENA:        Arena com brilho dourado + contador de espectadores
EVENTO NO AUDITORIO:    Auditorio com luz acesa + banner do evento
LOCAL COM 10+ AGENTES:  Glow/brilho mais intenso no predio
LOCAL VAZIO:            Opacidade reduzida
```

---

## 8. Implementacao Tecnica

### 8.1 Arquitetura do Sistema

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (HTML)                        │
│  rede.html (feed social)  │  cidade.html (Three.js 3D)  │
│           │                        │                      │
│      WebSocket / Polling       WebSocket / Polling        │
└───────────┬────────────────────────┬─────────────────────┘
            │                        │
            ▼                        ▼
┌──────────────────────────────────────────────────────────┐
│                    API (FastAPI)                          │
│  rotas_rede_social.py      │     rotas_vila.py           │
│  /api/v1/rede/*            │     /api/v1/vila/*          │
└───────────┬────────────────────────┬─────────────────────┘
            │                        │
            ▼                        ▼
┌──────────────────────────────────────────────────────────┐
│                    ENGINE (Python)                        │
│  rede_social.py  │  simulacao.py  │  cognitivo/*         │
│  (RedeSocial)    │  (SimulacaoVila)│  (perceber/planejar │
│                  │                 │   refletir/conversar │
│                  │                 │   executar/sintetizar)│
└───────────┬──────┴─────────────────┴─────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────┐
│              PROVEDORES IA (OmniRoute)                   │
│  Comentarios IA  │  Debates IA  │  Sinteses Helena      │
│  cc/claude-sonnet │  cc/claude-sonnet │  cc/claude-sonnet │
│  (heuristico     │  (sempre IA)      │  (sempre IA)      │
│   como fallback) │                   │                    │
└──────────────────────────────────────────────────────────┘
```

### 8.2 Endpoints Necessarios (novos e modificados)

**Novos endpoints para o framework:**

```python
# --- INTERACOES AVANCADAS ---

@router.post("/api/v1/rede/debate")
async def iniciar_debate(
    agente_a_id: str,
    agente_b_id: str,
    topico: str,
    max_turnos: int = 10,
) -> dict:
    """
    Inicia debate estruturado entre dois consultores.
    Usa IA para gerar turnos autenticos.
    Publica resultado como post tipo 'debate'.
    """

@router.post("/api/v1/rede/debate-espontaneo")
async def debate_espontaneo() -> dict:
    """
    Sistema seleciona par rival e gera debate automaticamente.
    """

@router.post("/api/v1/rede/helena/sintetizar/{post_id}")
async def helena_sintetiza(post_id: str) -> dict:
    """
    Helena analisa um post com comentarios e gera sintese.
    """

@router.post("/api/v1/rede/helena/perguntar/{post_id}")
async def helena_pergunta(post_id: str) -> dict:
    """
    Helena gera pergunta provocativa para aprofundar debate.
    """

@router.post("/api/v1/rede/helena/relatorio-diario")
async def helena_relatorio() -> dict:
    """
    Helena gera relatorio do dia: debates, insights, tendencias.
    """

@router.post("/api/v1/rede/comentar-ia/{post_id}/{agente_id}")
async def comentar_com_ia(post_id: str, agente_id: str) -> dict:
    """
    Gera comentario usando IA (OmniRoute) em vez de heuristica.
    """

@router.get("/api/v1/rede/relacionamentos/{agente_id}")
async def obter_relacionamentos(agente_id: str) -> dict:
    """
    Retorna mapa de relacionamentos de um consultor.
    """

@router.post("/api/v1/vila/evento")
async def criar_evento_campus(
    tipo: str,  # masterclass, debate, mesa_redonda, etc.
    topico: str,
    hora: str,
    participantes: list[str] = [],
) -> dict:
    """
    Cria evento no campus que atrai consultores e gera conteudo.
    """

@router.get("/api/v1/vila/atividade")
async def feed_atividade(limite: int = 20) -> dict:
    """
    Feed unificado: mescla acoes da cidade + posts da rede.
    Ordenado cronologicamente.
    """
```

### 8.3 Integracao com OmniRoute

**Configuracao** (ja definida em `config.py`):
```python
omniroute_url = os.getenv("OMNIROUTE_URL", "http://localhost:20128")
omniroute_api_key = os.getenv("OMNIROUTE_API_KEY")  # Chave real fica no .env
modelo_conversa = "cc/claude-sonnet-4-20250514"
modelo_rapido = "cc/claude-haiku-4-5-20251001"
```

**Cliente OmniRoute para a Vila:**
```python
import httpx

class OmniRouteVila:
    """Cliente OmniRoute especializado para a Vila INTEIA."""

    def __init__(self, url: str, api_key: str):
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30)

    async def gerar_comentario(
        self,
        persona: Persona,
        post: Postagem,
        modelo: str = "cc/claude-sonnet-4-20250514",
    ) -> str:
        """Gera comentario autentico via LLM."""

        system_prompt = persona.gerar_prompt_sistema()
        user_prompt = gerar_prompt_comentario_ia(persona, post)

        response = await self.client.post(
            f"{self.url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": modelo,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 300,
                "temperature": 0.8,
            },
        )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def gerar_debate(
        self,
        persona_a: Persona,
        persona_b: Persona,
        topico: str,
        max_turnos: int = 10,
    ) -> list[tuple[str, str]]:
        """Gera debate completo entre dois consultores."""

        prompt = gerar_conversa_com_ia(persona_a, persona_b, topico, max_turnos)

        response = await self.client.post(
            f"{self.url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "cc/claude-sonnet-4-20250514",
                "messages": [
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 2000,
                "temperature": 0.85,
            },
        )

        data = response.json()
        texto = data["choices"][0]["message"]["content"]

        # Parsear turnos do texto
        return self._parsear_turnos(texto, persona_a.nome_exibicao, persona_b.nome_exibicao)

    async def helena_sintetizar(
        self,
        topico: str,
        comentarios: list[dict],
    ) -> dict:
        """Helena gera sintese via LLM."""

        prompt = f"""Voce e Helena Montenegro, cientista politica e moderadora.

        Analise {len(comentarios)} comentarios sobre "{topico}":

        {self._formatar_comentarios(comentarios)}

        Gere JSON:
        {{
            "resumo": "3 frases",
            "top_argumentos": ["arg1 (autor)", "arg2 (autor)", "arg3 (autor)"],
            "gaps": ["perspectiva ausente 1", "perspectiva ausente 2"],
            "vies_coletivo": "se houver",
            "pergunta_aprofundamento": "uma pergunta",
            "confianca": 7
        }}

        Responda APENAS com o JSON, sem texto extra."""

        response = await self.client.post(
            f"{self.url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "cc/claude-sonnet-4-20250514",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.5,
            },
        )

        data = response.json()
        return json.loads(data["choices"][0]["message"]["content"])

    def _formatar_comentarios(self, comentarios: list[dict]) -> str:
        linhas = []
        for c in comentarios[:20]:
            linhas.append(
                f"- {c['autor']} ({c.get('categoria', '?')}): {c['conteudo'][:200]}"
            )
        return "\n".join(linhas)

    def _parsear_turnos(
        self, texto: str, nome_a: str, nome_b: str
    ) -> list[tuple[str, str]]:
        turnos = []
        for linha in texto.strip().split("\n"):
            linha = linha.strip()
            if not linha:
                continue
            for nome in [nome_a, nome_b]:
                if linha.startswith(f"{nome}:"):
                    fala = linha[len(nome) + 1:].strip()
                    turnos.append((nome, fala))
                    break
        return turnos
```

### 8.4 Estrutura de Estado e Persistencia

**Estado em memoria (durante simulacao):**
```python
class EstadoVila:
    """Estado central da Vila INTEIA."""

    simulacao: SimulacaoVila          # Engine de simulacao
    rede: RedeSocial                   # Motor da rede social
    relacionamentos: dict[str, dict[str, RelacionamentoEvolutivo]]
    eventos_programados: list[dict]    # Agenda do dia
    helena_metricas: dict              # Metricas que Helena rastreia
    fila_ia: list[dict]               # Chamadas pendentes ao OmniRoute
    omniroute: OmniRouteVila          # Cliente OmniRoute
```

**Persistencia em JSON (auto-save):**
```
vila-inteia/data/{nome_simulacao}/
├── meta.json                 # Step, hora, config
├── feed.json                 # Todos os posts e comentarios
├── relacionamentos.json      # Grafo de relacionamentos
├── eventos.json              # Historico de eventos
├── helena_relatorios.json    # Relatorios diarios da Helena
├── metricas.json             # Metricas agregadas
├── sinteses.json             # Sinteses de inteligencia coletiva
└── personas/
    ├── {id_1}/
    │   ├── meta.json
    │   ├── memoria_fluxo.json
    │   ├── memoria_espacial.json
    │   └── rascunho.json
    ├── {id_2}/
    └── ...
```

### 8.5 Loop Principal de Simulacao (estendido)

O loop principal em `simulacao.py` precisa ser estendido para integrar rede social e eventos:

```python
async def executar_step_completo(self) -> dict:
    """Step completo integrando simulacao + rede social + Helena."""

    resultado = {
        "step": self.step,
        "hora": self.hora_atual.strftime("%H:%M"),
        "acoes_cidade": [],
        "novos_posts": [],
        "novos_comentarios": [],
        "helena_acoes": [],
        "eventos": [],
    }

    # 1. SIMULACAO BASE (movimentacao, conversas, reflexoes)
    resumo_step = self.executar_step()
    resultado["acoes_cidade"] = resumo_step["acoes"]

    # 2. CONVERSAS VIRAM POSTS (se significativas)
    for conversa in resumo_step["conversas"]:
        if len(conversa.get("turnos", [])) >= 4:
            post = self.rede.publicar_conversa_como_post(conversa)
            resultado["novos_posts"].append(post.to_dict())

    # 3. POSTS ESPONTANEOS (chance por agente)
    novos = self.rede.gerar_posts_autonomos(
        self.personas, self.hora_atual, chance=0.03
    )
    resultado["novos_posts"].extend([p.to_dict() for p in novos])

    # 4. PROCESSAR FILA DE REACOES
    interacoes = self.rede.processar_reacoes(
        self.personas, self.hora_atual, max_reacoes_por_step=10
    )
    resultado["novos_comentarios"] = interacoes

    # 5. HELENA MONITORA
    for post_id, post in self.rede._indice_por_id.items():
        if post.total_comentarios >= 5 and not post.destaque:
            # Helena sintetiza
            sintese = await self.helena_sintetizar(post)
            if sintese:
                resultado["helena_acoes"].append(sintese)

    # 6. EVENTOS PROGRAMADOS
    hora = self.hora_atual.hour
    for evento in self.eventos_programados:
        if evento["hora"] == hora and not evento.get("executado"):
            resultado_evento = await self.executar_evento(evento)
            resultado["eventos"].append(resultado_evento)
            evento["executado"] = True

    # 7. DEBATES ESPONTANEOS (a cada 20 steps)
    if self.step % 20 == 0:
        debate = await self.gerar_debate_espontaneo()
        if debate:
            resultado["novos_posts"].append(debate)

    # 8. DIABOB PROVOCA (a cada 15 steps)
    if self.step % 15 == 0:
        provocacao = self.diabob_provoca()
        if provocacao:
            resultado["novos_posts"].append(provocacao)

    # 9. RELATORIO HELENA (22h)
    if hora == 22 and not hasattr(self, '_relatorio_hoje'):
        relatorio = await self.helena_relatorio_diario()
        resultado["helena_acoes"].append(relatorio)
        self._relatorio_hoje = True

    # Reset diario
    if hora == 6:
        self._relatorio_hoje = False

    return resultado
```

### 8.6 WebSocket para Atualizacoes em Tempo Real

Para que o frontend (rede.html e cidade.html) receba updates em tempo real:

```python
from fastapi import WebSocket, WebSocketDisconnect

class GerenciadorConexoes:
    """Gerencia conexoes WebSocket."""

    def __init__(self):
        self.conexoes_rede: list[WebSocket] = []
        self.conexoes_cidade: list[WebSocket] = []

    async def conectar_rede(self, ws: WebSocket):
        await ws.accept()
        self.conexoes_rede.append(ws)

    async def conectar_cidade(self, ws: WebSocket):
        await ws.accept()
        self.conexoes_cidade.append(ws)

    async def broadcast_rede(self, evento: dict):
        """Envia evento para todas as conexoes da rede social."""
        for ws in self.conexoes_rede:
            try:
                await ws.send_json(evento)
            except:
                self.conexoes_rede.remove(ws)

    async def broadcast_cidade(self, evento: dict):
        """Envia evento para todas as conexoes da cidade 3D."""
        for ws in self.conexoes_cidade:
            try:
                await ws.send_json(evento)
            except:
                self.conexoes_cidade.remove(ws)

gerenciador = GerenciadorConexoes()

# Eventos que sao broadcast:
EVENTOS_WS = {
    "novo_post": "broadcast_rede",        # Novo post no feed
    "novo_comentario": "broadcast_rede",   # Novo comentario
    "nova_reacao": "broadcast_rede",       # Nova reacao
    "helena_sintese": "broadcast_rede",    # Helena publicou
    "agente_moveu": "broadcast_cidade",    # Agente mudou de local
    "debate_iniciado": "broadcast ambos",  # Debate comecou
    "evento_campus": "broadcast ambos",    # Evento programado
}
```

### 8.7 Cache e Otimizacao

**Problema**: 144 agentes x chamadas IA = potencialmente caro.

**Solucao em camadas:**

```python
class CacheVila:
    """Cache para otimizar chamadas IA."""

    def __init__(self, max_tamanho: int = 1000):
        self.cache_comentarios: dict[str, str] = {}  # hash(persona+post) -> comentario
        self.cache_prompts: dict[str, str] = {}       # hash(system_prompt) -> prompt compilado
        self.max_tamanho = max_tamanho

    # Estrategia 1: Templates heuristicos para 70% dos comentarios
    # (ja implementado em _gerar_comentario_heuristico)

    # Estrategia 2: Cache de prompts compilados
    # System prompt do consultor nao muda frequentemente
    # Compilar uma vez, reusar

    # Estrategia 3: Batch requests
    # Agrupar 3-5 pedidos de comentario em um unico prompt
    # "Gere comentarios para 5 consultores diferentes:"

    # Estrategia 4: Tier-based IA usage
    # Tier S: SEMPRE usa IA
    # Tier A: 50% IA, 50% heuristico
    # Tier B: 20% IA, 80% heuristico (se existir)

POLITICA_IA = {
    "tier_S": {"ia_rate": 1.0, "modelo": "cc/claude-sonnet-4-20250514"},
    "tier_A": {"ia_rate": 0.5, "modelo": "cc/claude-sonnet-4-20250514"},
    "tier_B": {"ia_rate": 0.2, "modelo": "cc/claude-haiku-4-5-20251001"},
    "debate_1v1": {"ia_rate": 1.0, "modelo": "cc/claude-sonnet-4-20250514"},
    "helena": {"ia_rate": 1.0, "modelo": "cc/claude-sonnet-4-20250514"},
    "tema_usuario": {"ia_rate": 1.0, "modelo": "cc/claude-sonnet-4-20250514"},
}
```

### 8.8 Metricas e Monitoramento

```python
METRICAS_SISTEMA = {
    # Performance
    "tempo_medio_step_ms": 0,
    "chamadas_ia_por_step": 0,
    "chamadas_ia_total": 0,
    "tokens_consumidos": 0,
    "cache_hit_rate": 0.0,

    # Conteudo
    "posts_por_dia": 0,
    "comentarios_por_dia": 0,
    "debates_por_dia": 0,
    "sinteses_helena": 0,
    "insights_gerados": 0,

    # Engajamento
    "media_comentarios_por_post": 0.0,
    "media_reacoes_por_post": 0.0,
    "consultores_ativos_rede": 0,
    "categorias_representadas": 0,

    # Qualidade
    "diversidade_perspectivas": 0.0,
    "profundidade_media": 0.0,
    "taxa_ia_vs_heuristico": 0.0,
}
```

---

## Apendice A: Diagrama de Fluxo Completo

```
USUARIO POSTA TEMA
       │
       ▼
  [Postagem criada]
       │
       ├──→ Selecionar 6-10 consultores relevantes
       │         │
       │         ├──→ Wave 1: 3 comentarios imediatos (IA para Tier S, heuristico para outros)
       │         ├──→ Wave 2: 3-4 comentarios (step +1)
       │         ├──→ Wave 3: 2-3 comentarios (step +3)
       │         └──→ Wave 4: restantes (step +6)
       │
       ├──→ Na Cidade 3D: consultores se movem para Agora
       │
       ├──→ Helena monitora:
       │         ├──→ 5+ comentarios? → Sintese parcial
       │         ├──→ 80%+ concordam? → Advocacia do diabo
       │         ├──→ Categoria ausente? → Convite
       │         └──→ Debate circular? → Novo angulo
       │
       ├──→ Diabob detecta post:
       │         └──→ Gera provocacao se tema relevante
       │
       └──→ Jesus detecta post:
                 └──→ Gera parabola se tema etico/humano
```

## Apendice B: Exemplo de "Dia Tipico" na Vila

```
06:00  144 consultores acordam em suas residencias
06:30  Cafe da manha no Refeitorio (30-40 presentes)
07:00  Primeiros movimentos para locais de trabalho
08:00  Musk chega ao Laboratorio, comeca post sobre "IA vai substituir advogados"
08:10  Gates responde ao post de Musk (rival, IA imediata)
08:15  Helena percebe tema quente, monitora
08:20  Diabob provoca: "Musk nao entende direito, Gates nao entende IA"
08:30  3 juristas reagem do Tribunal (Tier A, heuristico)
09:00  Sun Tzu posta do Torre de Estrategia sobre geopolitica
09:30  Helena sintetiza debate IA x Direito (5+ comentarios)
10:00  Mesa Redonda na Torre: 6 estrategistas discutem
11:00  Tesla (insone, baixa energia) finalmente acorda, vai ao Lab
12:00  ALMOCO: todos no Refeitorio, encontros forcados
12:30  Maquiavel conversa com Mandela no Refeitorio (opostos!)
13:00  Post espontaneo de Buffett sobre "bolha de IA"
14:00  MASTERCLASS: Steve Jobs apresenta no Auditorio (40 presentes)
15:00  Igor posta: "Como destruir a reputacao de um adversario politico?"
15:05  Diabob responde IMEDIATAMENTE (expertise perfeita)
15:10  Maquiavel oferece "conselho" sombrio
15:15  Jesus responde com parabola sobre consequencias
15:20  Sun Tzu cita A Arte da Guerra
15:30  Helena sintetiza: "5 perspectivas, gap em etica digital"
16:00  DEBATE: Maquiavel vs Gandhi na Arena (20 espectadores)
17:00  Happy hour no Terraco (networking)
18:00  Debate espontaneo: Elon Musk vs Warren Buffett sobre risco
19:00  Jantar no Refeitorio
20:00  Agora: debate noturno sobre tema do dia
21:00  Reflexao no Jardim: Jesus + Buda + Marco Aurelio
22:00  Helena publica RELATORIO DO DIA
22:30  Consultores retornam as residencias
23:00  Maioria dormindo. Tesla ainda no Lab.
```

## Apendice C: Prioridades de Implementacao

| Fase | O que Implementar | Impacto | Esforco |
|------|-------------------|---------|---------|
| 1 | Comentarios IA via OmniRoute (substituir heuristico) | Alto | Medio |
| 2 | Debates espontaneos automaticos | Alto | Medio |
| 3 | Helena sinteses automaticas | Alto | Medio |
| 4 | Personagens especiais (Diabob, Jesus) | Alto | Baixo |
| 5 | WebSocket para tempo real | Medio | Alto |
| 6 | Eventos programados no campus | Medio | Medio |
| 7 | Relacionamentos evolutivos | Medio | Medio |
| 8 | Integracao bidirecional rede-cidade | Medio | Alto |
| 9 | Cache e otimizacao de chamadas IA | Medio | Medio |
| 10 | Relatorio diario Helena | Baixo | Baixo |

**Recomendacao**: Implementar Fases 1-4 primeiro. Isso ja faz a Vila parecer VIVA. As fases 5-10 sao refinamentos.

---

*Documento gerado em 2026-02-24 por Claude Code para o projeto Vila INTEIA.*
*Referencia de codigo: `C:/Agentes/vila-inteia/`*
