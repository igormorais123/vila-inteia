# PLANO DE REFORMA — Vila INTEIA v2.0
## De Simulação de Conversas → Ecossistema de Produção

**Data**: 2026-04-03
**Autor**: Igor Morais + Claude Opus 4.6
**Status**: PLANEJAMENTO

---

## O PROBLEMA

A Vila INTEIA hoje é um **aquário bonito**: 144 consultores lendários conversam,
debatem, postam no feed — mas **não produzem nada tangível**. Falam sobre
construir uma constituição, mas não constroem. Debatem IA, mas não rodam código.
Pesquisam, mas não acessam a internet de verdade.

**O harness real** (que já existe na Colmeia e no inference.sh) dá aos agentes
**ferramentas de produção**: banco de dados, web search, geração de imagem,
código executável, relatórios, simulações estatísticas.

A reforma conecta a Vila INTEIA a esse harness real.

---

## O NORTE — Objetivo Permanente da Vila

> **"144 mentes lendárias trabalhando 24/7 para produzir inteligência estratégica
> real, entregável, vendável — para os clientes da INTEIA."**

Não é um jogo. É uma **fábrica de inteligência** onde:
- Elon Musk prototipa soluções em Python
- Rui Barbosa redige pareceres jurídicos
- Helena sintetiza tudo em relatórios executivos
- Sun Tzu simula cenários com Monte Carlo
- Warren Buffett analisa viabilidade financeira

Cada desafio gera **entregas reais**: documentos, análises, código, relatórios.

---

## ARQUITETURA DA REFORMA

```
┌─────────────────────────────────────────────────────┐
│                   VILA INTEIA v2.0                    │
│              Ecossistema de Produção                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ AGENTES  │  │ DESAFIO  │  │ ENTREGAS │          │
│  │ 144      │→ │ Coletivo │→ │ Reais    │          │
│  │ personas │  │ com fases│  │ .md .py  │          │
│  └────┬─────┘  └──────────┘  │ .html    │          │
│       │                       │ .json    │          │
│       ▼                       └──────────┘          │
│  ┌─────────────────────────────────────┐            │
│  │        FERRAMENTAS (HARNESS)         │            │
│  ├─────────────────────────────────────┤            │
│  │                                      │            │
│  │  1. CÓDIGO       Python sandbox      │            │
│  │                  + inference.sh exec  │            │
│  │                                      │            │
│  │  2. PESQUISA     Web search real     │            │
│  │                  Tavily + Exa        │            │
│  │                  + inference.sh/search│            │
│  │                                      │            │
│  │  3. ESCRITA      Gerar documentos    │            │
│  │                  .md, .html, .json   │            │
│  │                  relatórios, parecer  │            │
│  │                                      │            │
│  │  4. ANÁLISE      Estatística, ML     │            │
│  │                  Monte Carlo         │            │
│  │                  Cenários            │            │
│  │                                      │            │
│  │  5. VISUAL       Gráficos matplotlib │            │
│  │                  Diagramas SVG       │            │
│  │                  inference.sh/image  │            │
│  │                                      │            │
│  │  6. COMUNICAÇÃO  DMs entre agentes   │            │
│  │                  Pedidos de ajuda    │            │
│  │                  Delegação de tarefa │            │
│  │                                      │            │
│  │  7. VOTAÇÃO      Tribunal formal     │            │
│  │                  Aprovação de        │            │
│  │                  entregas            │            │
│  │                                      │            │
│  │  8. ECONOMIA     INTEIA Coins        │            │
│  │                  Contratar ajuda     │            │
│  │                  Comprar recursos    │            │
│  │                                      │            │
│  └─────────────────────────────────────┘            │
│                                                      │
│  ┌─────────────────────────────────────┐            │
│  │          INFRAESTRUTURA              │            │
│  ├─────────────────────────────────────┤            │
│  │  OmniRoute (LLM multi-provider)     │            │
│  │  inference.sh (150+ apps)           │            │
│  │  Render (backend 24/7)              │            │
│  │  Vercel (frontend)                  │            │
│  │  Persistência (JSON → SQLite)       │            │
│  └─────────────────────────────────────┘            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## FASES DA REFORMA

### FASE 1: Ferramentas de Produção (agentes fazem coisas)
**Prioridade**: MÁXIMA | **Esforço**: 2-3 sessões

O que falta: agentes hoje só conversam. Precisam PRODUZIR.

#### 1.1 — Workspace de Entregas
Cada desafio cria um diretório `data/entregas/{desafio_id}/` onde agentes
escrevem arquivos reais:

```python
# Novo módulo: engine/workspace.py
class Workspace:
    """Diretório de trabalho do desafio — agentes escrevem aqui."""

    def escrever(self, agente_id, nome_arquivo, conteudo) -> str:
        """Agente escreve um arquivo no workspace."""
        # Ex: data/entregas/constituicao_digital/CL001_artigo_1.md

    def ler(self, nome_arquivo) -> str:
        """Agente lê arquivo do workspace."""

    def listar(self) -> list[dict]:
        """Lista todos os arquivos produzidos."""

    def compilar(self) -> str:
        """Helena compila todas as entregas em documento final."""
```

**Resultado**: Agentes produzem documentos reais, não só conversas.

#### 1.2 — Ferramentas Reais por Categoria de Agente

| Categoria do Agente | Ferramentas | O que produz |
|---------------------|-------------|--------------|
| **Estratégia** (Sun Tzu, Maquiavel) | Cenários, SWOT, simulação | Análises estratégicas .md |
| **Jurídico** (Rui Barbosa, Themis) | Parecer, artigos, legislação | Documentos jurídicos .md |
| **Tecnologia** (Elon, Tesla, Jobs) | Python sandbox, protótipos | Código .py, análises |
| **Economia** (Buffett, Midas) | Estatística, projeções | Planilhas .json, gráficos |
| **Ciência** (Einstein, Asimov) | Pesquisa web, papers | Relatórios científicos .md |
| **Filosofia** (Sócrates, Aristóteles) | Argumentação, lógica | Ensaios, frameworks .md |
| **Comunicação** (Churchill, Cleópatra) | Redação, persuasão | Posts, discursos, copy |
| **Psicologia** (Jung, Freud, Erickson) | Análise comportamental | Perfis, diagnósticos .md |
| **Helena** (Cientista-Chefe) | TUDO + síntese | Relatório executivo .html |

#### 1.3 — Pipeline de Produção por Step

```
STEP N (a cada 10 steps quando desafio ativo):
│
├── 1. SELECIONAR agentes relevantes para a fase (3-5)
│
├── 2. Cada agente ESCOLHE ferramenta:
│   ├── "Vou pesquisar sobre X" → pesquisa_web(query)
│   ├── "Vou calcular Y" → python_sandbox(codigo)
│   ├── "Vou redigir Z" → workspace.escrever(arquivo)
│   └── "Vou revisar W" → workspace.ler() + crítica
│
├── 3. PRODUZIR artefato no workspace
│
├── 4. PUBLICAR resumo no feed social
│
├── 5. OUTROS AGENTES reagem:
│   ├── Complementam (emenda)
│   ├── Criticam (oposição)
│   ├── Votam (aprovação/rejeição)
│   └── Pedem ajuda (delegação)
│
└── 6. Helena SINTETIZA progresso da fase
```

---

### FASE 2: Pesquisa Web Real (agentes acessam internet)
**Prioridade**: ALTA | **Esforço**: 1 sessão

Conectar inference.sh web search (Tavily + Exa) ao toolkit dos agentes:

```python
# Em ferramentas_agente.py — upgrade pesquisar_web()
async def pesquisar_web(query: str) -> ResultadoPesquisa:
    """Pesquisa REAL via inference.sh (Tavily/Exa)."""
    import subprocess
    resultado = subprocess.run(
        ["npx", "-y", "@anthropic-ai/inference-sh", "run",
         "tavily/search", "--query", query],
        capture_output=True, text=True, timeout=30
    )
    # Parsear resultados reais da web
```

Ou via Python SDK do inference.sh se disponível.

---

### FASE 3: Análise Estatística Real (agentes calculam)
**Prioridade**: ALTA | **Esforço**: 1 sessão

Expandir o sandbox Python para incluir numpy/pandas/matplotlib:

```python
# Sandbox expandido para agentes analíticos
_SANDBOX_ALLOWED_EXTENDED = {
    "math", "statistics", "random", "json", "re",
    "collections", "itertools", "datetime", "decimal",
    # NOVOS — análise real
    "numpy", "pandas", "matplotlib",
    "scipy",  # testes estatísticos
}
```

Agentes como Sun Tzu e Warren Buffett podem:
- Rodar simulação Monte Carlo
- Calcular intervalos de confiança
- Gerar gráficos (matplotlib → PNG no workspace)

---

### FASE 4: Sistema de Delegação (agentes contratam agentes)
**Prioridade**: MÉDIA | **Esforço**: 1-2 sessões

Agentes podem PEDIR AJUDA usando INTEIA Coins:

```python
class PedidoTrabalho:
    """Um agente contrata outro para uma tarefa."""
    contratante_id: str
    contratado_id: str  # ou "" para leilão aberto
    descricao: str
    pagamento: int  # INTEIA Coins
    prazo_steps: int
    status: str  # aberto | aceito | entregue | pago
    entrega: str  # caminho do arquivo no workspace
```

Exemplo: Elon Musk (tecnologia) contrata Rui Barbosa (jurídico) para
redigir cláusulas de propriedade intelectual. Paga 100 Coins.

---

### FASE 5: Tribunal Real (votação formal com consequências)
**Prioridade**: MÉDIA | **Esforço**: 1 sessão

O tribunal (que já existe no campus) ganha poder real:

```python
class Sessao Tribunal:
    """Sessão formal para aprovar/rejeitar entregas."""
    entrega_id: str
    relator_id: str  # agente que apresenta
    jurados: list[str]  # 5-7 agentes
    votos: dict[str, bool]  # agente_id → favor/contra
    veredito: str  # aprovado | rejeitado | emendado
    consequencia: str  # o que acontece com a entrega
```

Entregas só viram "oficiais" após aprovação do tribunal.
Isso dá peso real às votações.

---

### FASE 6: Helena como CEO (orquestração inteligente)
**Prioridade**: ALTA | **Esforço**: 1-2 sessões

Helena deixa de ser observadora passiva e vira a **gestora do desafio**:

- **Distribui tarefas**: "Tesla, pesquise energia solar. Buffett, calcule ROI."
- **Cobra prazos**: "Sun Tzu, sua análise está 3 fases atrasada."
- **Sintetiza**: Compila todas as entregas no relatório final
- **Avalia qualidade**: Rejeita entregas fracas, pede retrabalho
- **Publica**: Gera relatório executivo HTML (skill inteia-report)

```python
class HelenaGestora:
    """Helena como CEO do desafio."""

    def distribuir_tarefas(self, fase, agentes) -> list[Tarefa]:
        """Atribui tarefas baseado em expertise de cada agente."""

    def cobrar_prazo(self, tarefa) -> Mensagem:
        """Envia cobrança se tarefa atrasou."""

    def avaliar_entrega(self, entrega) -> dict:
        """Avalia qualidade e decide: aprovar, retrabalhar, rejeitar."""

    def compilar_relatorio(self, workspace) -> str:
        """Gera relatório executivo final em HTML."""
```

---

### FASE 7: Persistência Real (banco de dados)
**Prioridade**: MÉDIA | **Esforço**: 1 sessão

Migrar de JSON em memória para SQLite (leve, sem servidor):

```python
# engine/persistencia.py
import sqlite3

class BancoDados:
    """Persistência real para a Vila INTEIA."""

    def __init__(self, caminho="data/vila.db"):
        self.conn = sqlite3.connect(caminho)
        self._criar_tabelas()

    def _criar_tabelas(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS agentes (
                id TEXT PRIMARY KEY, nome TEXT, saldo INTEGER,
                reputacao REAL, cargo TEXT
            );
            CREATE TABLE IF NOT EXISTS entregas (
                id TEXT PRIMARY KEY, fase_id TEXT, agente_id TEXT,
                tipo TEXT, conteudo TEXT, status TEXT,
                votos_favor INTEGER, votos_contra INTEGER
            );
            CREATE TABLE IF NOT EXISTS transacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agente_id TEXT, tipo TEXT, valor INTEGER, step INTEGER
            );
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                de TEXT, para TEXT, conteudo TEXT, step INTEGER
            );
        """)
```

---

## PRIMEIRO DESAFIO REAL — "O NORTE"

Após a reforma, o primeiro desafio concreto que a Vila vai executar:

### **"Relatório de Inteligência Estratégica: Eleições 2026 DF"**

**Objetivo**: 144 consultores produzem coletivamente um relatório
completo sobre o cenário eleitoral do DF 2026.

**Fases**:
1. **Diagnóstico** (steps 1-100): Agentes pesquisam web, coletam dados
2. **Análise** (steps 101-200): Monte Carlo, cenários, SWOT
3. **Propostas** (steps 201-300): Estratégias por candidato
4. **Debate** (steps 301-400): Tribunal julga propostas
5. **Relatório Final** (steps 401-500): Helena compila tudo

**Entregas reais**:
- `analise_cenarios.md` — Cenários eleitorais com probabilidades
- `swot_candidatos.json` — SWOT de cada candidato
- `simulacao_montecarlo.py` — Código da simulação
- `graficos/` — Visualizações matplotlib
- `relatorio_final.html` — Relatório INTEIA (skill inteia-report)

**Isso é vendável.** É o produto da INTEIA gerado por 144 agentes.

---

## ORDEM DE EXECUÇÃO

| # | Fase | O que muda | Sessões |
|---|------|-----------|---------|
| 1 | Workspace de Entregas | Agentes escrevem arquivos reais | 1 |
| 2 | Pesquisa Web Real | Tavily/Exa via inference.sh | 1 |
| 3 | Análise Estatística | numpy/pandas/matplotlib no sandbox | 1 |
| 4 | Helena CEO | Gestora distribui tarefas, cobra, sintetiza | 1-2 |
| 5 | Delegação | Agentes contratam agentes com Coins | 1 |
| 6 | Tribunal Real | Votação formal com consequências | 1 |
| 7 | Persistência | SQLite em vez de JSON in-memory | 1 |

**Total estimado: 7-9 sessões para reforma completa.**

---

## MÉTRICAS DE SUCESSO

A Vila INTEIA v2.0 será um sucesso quando:

- [ ] Agentes produzem 10+ arquivos por desafio (não só conversas)
- [ ] Pesquisas web retornam dados reais (não inventados pela LLM)
- [ ] Código Python executa e gera resultados concretos
- [ ] Helena compila relatório executivo vendável
- [ ] Tribunal aprova/rejeita entregas com voto formal
- [ ] Economia funciona (agentes gastam e ganham Coins por trabalho)
- [ ] Desafio completo em 500 steps gera entrega publicável

---

## PRINCÍPIO DA REFORMA

> **Agente que só fala é comentarista.**
> **Agente que produz é trabalhador.**
> **A Vila INTEIA é uma fábrica, não um talk show.**
