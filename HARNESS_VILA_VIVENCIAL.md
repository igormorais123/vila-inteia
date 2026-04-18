# HARNESS VILA VIVENCIAL — a Vila como Harness que se caminha

> Complemento experiencial e visual do [`HARNESS_VILA.md`](./HARNESS_VILA.md). Aqui a arquitetura deixa de ser diagrama e vira **cidade que se percorre**: cada conceito do harness tem um lugar físico no Campus 3D, uma metáfora que se vive, uma utilidade que se opera e um efeito visual que se vê.
>
> *"Não basta ter arquitetura boa. Boa arquitetura precisa ser caminhável."*

---

## 0. A tese em uma frase

> **A Vila será o primeiro harness que você pode visitar, entender andando, ver funcionando em tempo real e usar como laboratório vivo — tudo ao mesmo tempo.**

Não é metáfora bonita em slide. É o Campus 3D (já em Three.js) reorganizado de modo que cada conceito do paper de Zhou et al. tenha **localização, aparência, som e ação** — e que a ação seja, de verdade, o que está rodando por trás.

---

## 1. A metáfora-mestre: a Vila é a própria arquitetura

Cada das 6 dimensões do harness + os 3 módulos de externalização viram **lugares** da Vila. Visitar o lugar é ver o conceito acontecer.

### 1.1 O Mapa Canônico do Harness — 9 lugares-chave

```
                         ┌───────────────────┐
                         │   TORRE OBSERVA-  │
                         │      TÓRIO        │   ← Observabilidade
                         │  (vê tudo que     │
                         │   acontece)       │
                         └──────────┬────────┘
                                    │
        ┌───────────────┐           │           ┌────────────────┐
        │  BIBLIOTECA   │           │           │   OFICINAS     │
        │   & ARQUIVO   │◄──────────┼──────────►│  (27 técnicas  │
        │   (memória)   │           │           │   Van Aken)    │
        │  4 salas:     │           │           │   = SKILLS     │
        │  rascunho,    │           │           │                │
        │  episódios,   │           │           └────────┬───────┘
        │  saberes,     │           │                    │
        │  Fundador     │           │                    │
        └───────┬───────┘           │                    │
                │        ┌──────────┴──────────┐         │
                │        │     ÁGORA /         │         │
                └───────►│    PREFEITURA       │◄────────┘
                         │   (Harness core:    │
                         │   Agent Loop, orçamento,
                         │   orquestra tudo)   │
                         └──────────┬──────────┘
                                    │
            ┌──────────┐            │           ┌─────────────┐
            │  PORTÕES │            │           │    PRAÇA    │
            │ DA CIDADE│◄───────────┼──────────►│  DOS ÁGORAS │
            │(permissão│            │           │ (protocolos:│
            │  sandbox)│            │           │  onde agentes
            │          │            │           │  se encontram
            └──────────┘            │           └──────┬──────┘
                                    │                  │
                        ┌───────────┴──────────┐       │
                        │    MERCADO DA        │       │
                        │    ATENÇÃO           │       │
                        │ (orçamento de        │◄──────┘
                        │  contexto — tokens   │
                        │  como moeda visível) │
                        └──────┬───────────────┘
                               │
                    ┌──────────┴──────────┐
                    │   SINO DA TORRE     │
                    │   (controle: tempo, │
                    │   steps, timeout)   │
                    └─────────────────────┘

                    + BASÍLICA DA CONSTITUIÇÃO
                    (policy layer — artigos como pedras gravadas)
```

### 1.2 Tabela-chave — conceito ↔ lugar ↔ efeito visível

| Conceito do Harness | Lugar na Vila | Aparência / Efeito | Utilidade real |
|---------------------|---------------|---------------------|----------------|
| **Modelo-base (LLM)** | Coração da Ágora — pedestal com uma esfera luminosa pulsante | Esfera pulsa mais forte quando há inferência acontecendo; cor muda por modelo (dourado = Opus, azul = Sonnet, verde = Gemma) | OmniRoute está invocando aquele modelo agora |
| **Memória — rascunho** | Sala 1 da Biblioteca (mesa cheia de post-its que somem rápido) | Post-its aparecem e desaparecem em minutos | `engine/memoria/rascunho.py` |
| **Memória — episódios** | Sala 2 (estantes de livros com datas nas lombadas) | Livros velhos ficam empoeirados, novos brilham | `engine/memoria/fluxo.py` |
| **Memória — saberes estáveis** | Sala 3 (enciclopédia gigante no centro) | Páginas viram quando alguém consulta | Conhecimento semântico + RAG |
| **Memória — Fundador** (NOVA) | Sala 4 (busto do Igor + painel com preferências) | Painel atualiza quando Igor fala; emite "ding" quando qualquer agente consulta | `engine/memoria/fundador.py` (Gap #5) |
| **Skills — oficinas** | Rua das Oficinas (27 ateliês, um por técnica) | Ateliê com luz acesa = oficina em uso; fumaça saindo = ativa | `engine/skills_oficinas/*/SKILL.md` (Gap #3) |
| **Protocolos — agent-tool** | Portal do Mercado (onde agentes pegam ferramentas em prateleiras etiquetadas) | Prateleira mostra schema ao passar mouse | Capability cards (Gap #4) |
| **Protocolos — agent-agent** | Praça dos Ágoras (mesas circulares, agentes conversam) | Balões de diálogo visíveis com protocolo A2A-like; estado da conversa em cores | Protocolo interno Vila ↔ Colmeia |
| **Protocolos — agent-user** | Portão Principal (onde Igor entra) | Portal com linguagem natural de um lado, contrato estruturado de saída | A2UI/AG-UI equivalente |
| **Permissão — sandbox** | Muralha com portões etiquetados | Agente de baixa reputação bate na porta e é barrado visivelmente | Constituição + Chateaubriand |
| **Controle — loop, budget, timeout** | Sino da Torre | Toca a cada step; dobra quando algum agente está em loop | `config.py` + `simulacao.py` |
| **Observabilidade** | Torre do Observatório | Mapa vivo com linhas brilhantes de causal chain; click num evento abre trace | `vila_traces` (Gap #1) |
| **Orçamento de contexto** | Mercado da Atenção | Cada agente aparece com "bolsa de tokens" visível; gasto em tempo real | `engine/harness/orcamento.py` (Gap #2) |
| **Constituição (policy)** | Basílica — pedras gravadas | Artigo promulgado vira pedra nova; revogado racha | `engine/constituicao/artigos/*.toml` (Gap #6) |
| **Autoresearch (evolution)** | Laboratório Alquímico subterrâneo | Bolha destila trajetórias até virarem skill cristalizada | `engine/autoresearch.py` + fluxo memory→skill |

---

## 2. As 5 camadas vivenciais — efeito visual, elegância, ludicidade, utilidade, aplicação prática

### 2.1 Camada 1 — EFEITO VISUAL (o primeiro "uau")

**Meta**: em 10 segundos, o visitante entende que está vendo uma cidade viva onde **cada movimento tem significado técnico**.

Implementação concreta no Three.js existente:

- **Partículas como traces**: cada `TraceEvent` escrito em `vila_traces` vira uma partícula dourada que viaja da fase de origem à fase de destino. Observador vê o agent loop como um rio de luz.
- **Causal chain como linhas**: clicar em qualquer evento desenha em neon as arestas causais até o trigger original. Debug vira turismo.
- **Aura do Fundador**: quando Igor (identificado por JWT) está logado, o busto na Sala 4 brilha. Agentes consultando a ficha emitem ping visível.
- **Partículas coloridas por módulo**:
  - azul ciano → memória
  - verde → skills
  - rosa → protocolos
  - dourado → núcleo / model inference
  - violeta → controle (sino)
- **Céu da Vila muda conforme carga**: azul claro se orçamento tranquilo, laranja se algum agente estourando budget, vermelho se loop detectado.
- **Luzes das oficinas**: ateliê só acende quando skill daquela oficina está carregada em staged loading. Quem olha o skyline vê a demanda cognitiva da Vila em tempo real.

### 2.2 Camada 2 — ELEGÂNCIA (o "por que é belo")

**Meta**: a estrutura deve ser coerente o suficiente para que alguém perceba os padrões sem ler manual.

Princípios de design visual:
1. **Cada módulo = uma cor única e permanente**. Ninguém erra o que é memória vs skill.
2. **Agent loop gira em círculo físico** na Ágora. As 7 fases são 7 pedestais em torno da esfera central. A câmera segue uma persona e mostra ela ir de pedestal em pedestal.
3. **Hierarquia topográfica**: Torre do Observatório é o ponto mais alto (vê tudo). Laboratório Alquímico é o mais baixo (alquimia acontece no subsolo). Biblioteca é vasta e central. Oficinas formam uma rua estreita e viva.
4. **Tipografia uniforme** (Cormorant Garamond para títulos, JetBrains Mono para IDs técnicos, Outfit para corpo). Mesmo vocabulário visual do site institucional da INTEIA.
5. **Tempo visível**: Sino da Torre toca a cada step. Relógio analógico no centro da Ágora mostra o step-clock da simulação (não tempo real). Quem entra na Vila sente **o ritmo do harness**.

### 2.3 Camada 3 — LUDICIDADE (o "quero ficar aqui")

**Meta**: a Vila deve ser gostosa de visitar. Aprender harness acontece sem esforço.

Ganchos lúdicos:
- **Tour guiado pelo Chateaubriand**: modo turista. Chateaubriand (NPC com voz TTS) leva o visitante em 4 paradas de 90s cada: Ágora → Biblioteca → Oficinas → Praça dos Ágoras. Cada parada explica 1 conceito do harness mostrando ele funcionando.
- **Modo bastidor**: Ctrl+Shift+D mostra todos traces em overlay. Usuário alterna entre "modo cidadão" (só vê agentes e conversas) e "modo arquiteto" (vê arquitetura agentica subjacente).
- **Adote um habitante**: visitante escolhe um agente e segue ele por 10 steps. Vê o loop cognitivo acontecer em primeira pessoa.
- **Ouça a Vila**: áudio ambiente — diferentes sons para cada zona (biblioteca → páginas, oficinas → bate-martelo, praça → vozes baixas, mercado → tilintar de moedas-tokens). Volume sobe com atividade.
- **Hall dos Insights**: corredor no coração da Basílica mostra os 10 melhores insights publicados pela Vila no Mirante. Câmera lenta pelos slugs.
- **Easter eggs constitucionais**: quem lê os 11 Mandamentos em ordem na parede da Basílica destrava uma visão rara de um debate constitucional em slow motion.
- **Modo doutorado**: Igor logado como Fundador tem acesso a painel especial: pode fazer perguntas a qualquer agente em linguagem natural e ver as 7 fases do loop cognitivo do agente respondendo, com tempos e tokens.

### 2.4 Camada 4 — UTILIDADE (o "serve para quê")

**Meta**: cada elemento visual corresponde a uma função real executável. Nada é só decoração.

| Ação de Igor / visitante | O que realmente acontece no backend |
|---------------------------|--------------------------------------|
| Entra na Biblioteca, Sala 4 (Fundador) | `GET /api/memoria/fundador` devolve ficha + últimas interações |
| Clica numa oficina | Carrega `SKILL.md` nível 2 em painel lateral |
| Arrasta um problema para uma oficina | Instancia um agente + executa a skill + streama trace ao vivo |
| Clica num agente na Praça | Abre terminal de conversação com ele (via API FastAPI) |
| Clica em evento na Torre | Abre trace detalhado do `vila_traces` com causal chain |
| Toca o sino | Força um step manual (modo debug) |
| Adiciona pedra na Basílica | Propõe novo artigo constitucional via `constituinte.py` |
| Abre bolsa de tokens do Mercado | Mostra consumo por fase/agente nas últimas N horas |
| Entra no Laboratório Alquímico | Vê `autoresearch` rodando: trajetórias sendo destiladas ao vivo |

**Consequência**: a Vila é simultaneamente **interface de administração** do harness, **ambiente de debug** e **laboratório de experimentação**. O que seriam 3 painéis em Grafana vira 1 cidade caminhável.

### 2.5 Camada 5 — APLICAÇÃO PRÁTICA (o "produto real")

**Meta**: a Vila-Harness tem 4 usos concretos que geram valor mensurável.

**Uso 1 — Laboratório de decisão da Colmeia**
- Helena, antes de aceitar cliente, simula 30 steps com 7 agentes sintéticos relevantes.
- Retorna relatório estruturado: probabilidade de conflito ético (Themis), margem (Midas), risco reputacional (Chateaubriand), alinhamento (constituição).
- Valor: decisão estratégica baseada em dados simulados, não intuição.

**Uso 2 — Ambiente de treinamento para stakeholders**
- Cliente do copilot jurídico Paixão Cortes entra na Vila antes de usar o produto real.
- Vê um "mini-copilot" funcionando como cidade, entende o agent loop, ganha confiança.
- Valor: reduz resistência à adoção de IA em setores conservadores (direito, setor público).

**Uso 3 — Showcase para captação e venda**
- Investidor, cliente novo ou jornalista entra na Vila.
- Em 5 minutos, vê harness rodando de verdade, não slide.
- Valor: diferencial competitivo único no mercado brasileiro de IA.

**Uso 4 — Plataforma pedagógica (doutorado do Igor)**
- Alunos de IA e Psicologia Organizacional usam a Vila para entender agentes.
- Aula 1: leia os mandamentos. Aula 2: siga uma persona por 50 steps. Aula 3: proponha um artigo constitucional.
- Valor: material didático reutilizável, base para artigos acadêmicos (o próprio paper de Zhou et al. vira caso de estudo operacionalizado).

---

## 3. Cenários vivenciais — 5 roteiros que demonstram o harness completo

### Cenário 1 — "O Insight que Virou Lei" (4 minutos)

1. **Ágora (00:00)** — Esfera central pulsa. Agente Oracle Gnosis está pensando.
2. **Biblioteca, Sala 2 (00:30)** — Oracle Gnosis entra na sala de episódios. Pega 3 livros sobre falhas passadas.
3. **Oficina "5 Porquês" (01:00)** — Leva os livros para a oficina. Luz acende. Destila causa-raiz.
4. **Praça dos Ágoras (01:30)** — Debate com outros 4 agentes. Balões de diálogo. Chateaubriand observa.
5. **Basílica (02:30)** — Agente propõe novo artigo. Votação acontece. Pedra é gravada.
6. **Torre do Observatório (03:00)** — Visitante sobe a torre. Vê a trajetória inteira como linha dourada conectando os 5 lugares.
7. **Mirante News (03:30)** — Chateaubriand aprova matéria. URL aparece no portal.

**Valor pedagógico**: em 4 minutos, o visitante viu memória → skill → protocolo → constituição → publicação. Harness completo em uma história.

### Cenário 2 — "O Orçamento que Quebrou"
Um agente iniciante consome tokens sem parar. Céu fica laranja. Sino toca em alerta. Mercado da Atenção mostra bolsa esvaziando. Sistema intervém: orçamento.py corta skill detail e força summarization. Agente aprende.

### Cenário 3 — "A Simulação de Cliente da Helena"
Helena (Colmeia) chama capability `vila.simular_decisao`. Vila instancia 7 agentes. 30 steps em 20 segundos reais. Relatório volta para Helena. Ela decide.

### Cenário 4 — "O Ataque ao Fundador"
Tentativa de prompt injection vem de um agente externo mal-intencionado. Portões da cidade barram visualmente. Alerta piscante na Torre. Artigo constitucional 042 ("proteção do Fundador") é invocado. Audit trail completo no trace.

### Cenário 5 — "A Skill que Nasceu"
Autoresearch no Laboratório Alquímico detecta 5 trajetórias similares de sucesso. Bolha destila. Nova oficina aparece na Rua das Oficinas. Placa nova com o nome da técnica recém-descoberta.

---

## 4. Como construir — priorização vivencial em 4 ondas

### Onda 1 Vivencial (paralela à Onda 1 técnica do HARNESS_VILA.md)
**Documentação visual + mapa conceitual**

- [ ] Criar `frontend/vila3d/mapa-harness.json` com posições canônicas dos 9 lugares
- [ ] Overlay "modo arquiteto" no campus 3D atual (Ctrl+Shift+D)
- [ ] 1 tour guiado pelo Chateaubriand de 90s — MVP
- [ ] Landing page `/vila/visita` explicando a metáfora

### Onda 2 Vivencial (paralela à Onda 2 técnica)
**Efeito visual + utilidade básica**

- [ ] Partículas douradas para traces (usa `vila_traces` da Onda 2)
- [ ] Mercado da Atenção com bolsa de tokens visível por agente
- [ ] Torre do Observatório: visualização do trace com causal chain
- [ ] Céu muda de cor conforme carga global
- [ ] Sino toca a cada step

### Onda 3 Vivencial
**Oficinas + Praça + ligação Colmeia**

- [ ] Rua das Oficinas: 27 edifícios com luz ligada quando skill ativa
- [ ] Praça dos Ágoras: renderiza agent-agent conversations
- [ ] Portal do Mercado: mostra capability cards ao passar mouse
- [ ] Hall dos Insights (matérias do Mirante) no Mirante → Vila feedback

### Onda 4 Vivencial
**Basílica + Fundador + ludicidade avançada**

- [ ] Basílica com pedras por artigo constitucional
- [ ] Sala 4 da Biblioteca (Fundador) com painel de preferências
- [ ] Modo "adote um habitante" — segue persona em 1ª pessoa
- [ ] Easter eggs constitucionais
- [ ] Áudio ambiente por zona
- [ ] Modo doutorado (painel especial para Igor logado)

---

## 5. Princípios de design vivencial (não-negociáveis)

1. **Nada que é visível é decorativo**. Se aparece, corresponde a estado real. Se não corresponde, remover.
2. **Nada que é invisível é crítico**. Se é crítico para entender o harness, precisa ter representação no Campus.
3. **O visitante escolhe o nível de imersão**. Modo cidadão (narrativo), modo arquiteto (técnico), modo doutorado (pleno).
4. **O Fundador é centro gravitacional explícito**. A Vila serve o Fundador, não o contrário. Isso precisa estar literalmente representado.
5. **Cada elemento responde ao toque**. Clicar num lugar abre a função real. Sem duas camadas (dashboard separada de visualização). Uma coisa só.
6. **Harness é o protagonista invisível que vira visível**. Não é "UI para harness". É "harness que se renderizou como cidade".

---

## 6. Relações com skills e documentos

- [`HARNESS_VILA.md`](./HARNESS_VILA.md) — diagnóstico técnico e plano de 4 ondas. Este documento **estende** aquele com a camada vivencial.
- [`engine/harness/README.md`](./engine/harness/README.md) — guia do pacote técnico.
- [`.claude/skills/harness-vila/SKILL.md`](./.claude/skills/harness-vila/SKILL.md) — auto-invocação em sessões Claude Code.
- Skill global `harness-architect` — framework teórico completo.
- Documento pedagógico externo: `~/Downloads/harness-arquitetura-pedagogica.html`.

---

## 7. Critério final de sucesso vivencial

Você terá conseguido quando qualquer uma das seguintes afirmações for verdadeira:

- [ ] Um professor de IA pode dar uma aula inteira sobre harness sem slide — só caminhando pela Vila.
- [ ] Um cliente cético entra na Vila e sai querendo licenciar a INTEIA.
- [ ] Um jornalista escreve que a Vila "é o primeiro harness brasileiro que você pode visitar".
- [ ] Igor explica o harness para um colega do doutorado sem abrir um documento.
- [ ] Um investidor decide investir depois de 5 minutos na Vila, sem pitch deck.
- [ ] A Vila é citada como exemplo de referência em um artigo sobre agent infrastructure.

Se 3 dos 6 forem verdadeiros depois da Onda 4 vivencial, a Vila é um **harness completo, elegante, incrementado e vivencial**.

---

## 8. Citação canônica e leitura complementar

> "Artefatos cognitivos não mudam as capacidades. Eles mudam a tarefa." — Donald Norman, 1993.
>
> A Vila Vivencial **muda a tarefa de entender um harness**: em vez de ler 54 páginas, você caminha por uma cidade.

**Fonte primária**: Zhou et al. (2026), arXiv:2604.08224.
**Leitura pedagógica**: `~/Downloads/harness-arquitetura-pedagogica.html`.
**Inspirações de design**: Generative Agents (Stanford/Google, 2023), OASIS (camel-ai, 2024), SimCity (Wright), Disco Elysium (pela escrita situada), Monument Valley (pela clareza espacial).

---

> *"A Vila não é metáfora. É organismo."* — Constituição da Vila, PREÂMBULO.
> A partir de agora, a Vila também **é harness caminhável**. Organismo com esqueleto visível.
