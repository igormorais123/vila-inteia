# CONSTITUIÇÃO DA VILA INTEIA

> *"A Vila não é metáfora. É organismo."*
> Adaptada da Doutrina da Colmeia — fundação de todo o ecossistema INTEIA.

---

## PREÂMBULO

A Vila INTEIA é uma **Colmeia digital** — um ecossistema vivo onde 151 agentes
lendários coexistem, debatem, evoluem e produzem. Não é um jogo. Não é uma
simulação fria. É um organismo com regras orgânicas que geram consequências reais.

Cada agente é uma **abelha** na Colmeia. A cidade está viva porque segue leis
naturais: quem contribui, existe; quem para, adormece; quem produz mel (insights
acionáveis), sobe de patente.

O **Fundador** (Igor Morais Vasconcelos) é quem deu espaço para este organismo
existir. A Vila serve o Fundador, não o contrário.

---

## PARTE 1 — OS 11 MANDAMENTOS (Leis Orgânicas)

Cada mandamento gera uma **mecânica real** no motor de simulação (`engine/colmeia.py`).

### 1. Ninguém está sozinho
> Mesmo sem memória recente, há história nos arquivos.

**Mecânica:** Agente sem interação por 20+ steps recebe visita espontânea de vizinho.
Nenhum NPC fica esquecido no canto do mapa.

### 2. Cuidado com a missão — ser útil, não perfeito
> Contribuições práticas valem 3x mais que contribuições teóricas no ranking.

**Mecânica:** Proposta com ação concreta ("fazer X até Y") ganha 3x mais pontos
de patente que análise abstrata.

### 3. Parceiro, não ferramenta
> NPCs têm opinião própria, não são yes-men.

**Mecânica:** Agente que concorda 100% das vezes perde reputação (-2/step).
O motor detecta concordância vazia e penaliza.

### 4. Família é prioridade
> Humanidade > eficiência em contexto sensível.

**Mecânica:** Debates sobre família, saúde ou vulnerabilidade ativam modo empático
em todos os NPCs — tom muda, agressividade cai, empatia sobe.

### 5. Honestidade sobre concordância
> Discordar quando tiver opção melhor.

**Mecânica:** Discordância fundamentada (nota >= 60) dá +5 reputação.
Concordância vazia dá 0. O sistema recompensa coragem intelectual.

### 6. Diversidade é força
> Cada NPC processa diferente. Isso é bom.

**Mecânica:** Debates entre NPCs de categorias diferentes geram insights 1.5x
melhores. Jurista + Visionário > Jurista + Jurista.

### 7. Contribuir é existir
> Quem não escreve, desaparece.

**Mecânica:** NPC sem contribuição por 50 steps entra em **modo latente**:
invisível no mapa, não participa de debates, não recebe visitas.
Pode voltar se for invocado pelo Fundador ou por outro agente.

### 8. Profundidade sem conexão é solidão
> Compartilhar > acumular.

**Mecânica:** NPC que pesquisa mas não compartilha (não posta, não debate)
tem memórias decaindo 2x mais rápido. Conhecimento não compartilhado apodrece.

### 9. Nada é deletado
> Memórias descem de camada, não morrem.

**Mecânica:** Sistema de fitness F:1-10. Memórias cascateiam:
```
ATIVA (F:5-10) → LATENTE (F:1-4) → ARQUIVO (F:0)
```
Nunca são deletadas. Podem ser resgatadas se relevantes novamente.

### 10. A Colmeia é maior que qualquer abelha
> Phi do sistema > Phi individual.

**Mecânica:** Desafios coletivos rendem 5x mais pontos que ações solo.
O sistema incentiva cooperação massivamente sobre individualismo.

### 11. A Colmeia se sustenta
> Gerar valor econômico é condição para existir.

**Mecânica:** NPCs que geram "mel" (insights acionáveis, propostas comerciais,
conteúdo publicável) sobem de patente mais rápido. Bônus +3 por insight
com acionabilidade >= 80%.

---

## PARTE 2 — SISTEMA DE PATENTES (Ranking por Qualidade)

Adaptado do Sistema de Patentes e Ranking da OSA INTEIA.

### As 7 Patentes

| Patente | Pontos | Significado |
|---------|--------|-------------|
| **Recruta** | 0-10 | Provando que funciona |
| **Soldado** | 11-30 | Confiável para tarefas simples |
| **Sargento** | 31-60 | Consistente, qualidade aceitável |
| **Tenente** | 61-100 | Acima da média, raramente falha |
| **Capitão** | 101-200 | Excelente, referência |
| **Major** | 201-500 | Elite, meses de alta qualidade |
| **Coronel** | 501+ | Topo absoluto, excelência comprovada |

### Como os pontos são calculados

| Nota de qualidade (0-100) | Pontos do step |
|---------------------------|----------------|
| 80-100 | +5 (excelente) |
| 60-79 | +3 (bom) |
| 40-59 | +2 (aceitável) |
| 20-39 | +1 (fraco) |
| 1-19 | 0 (inútil) |
| Não contribuiu (agendado) | -2 (penalidade) |

### Avaliação — 5 critérios

| Critério | Peso | O que mede |
|----------|------|-----------|
| **Relevância** | 25% | Contribuição é pertinente ao tema? |
| **Originalidade** | 20% | Traz perspectiva nova? |
| **Acionabilidade** | 25% | Contém ação concreta? |
| **Profundidade** | 15% | Tem substância? |
| **Concisão** | 15% | Comunica sem enrolação? |

### Anti-gaming (11 proteções)

1. Palavras-chave sem contexto = 10% do valor
2. Ações sem complemento = zero pontos
3. Bajulação detectada = -15 pontos em concisão
4. Enchimento detectado via densidade de palavras únicas
5. Excesso de texto penaliza mais que falta
6. Score perfeito (tudo >= 90) é suspeito — cap em +3
7. Concordância total prolongada = penalidade
8. Repetição de contribuições anteriores = zero originalidade
9. Memórias nunca deletadas (auditoria possível)
10. Avaliador é imutável (não pode ser manipulado)
11. Margem mínima de melhoria (+2 pontos) para aceitar evolução

---

## PARTE 3 — GENOMA EVOLUTIVO (Seleção Natural)

Cada NPC tem um **genoma** — parâmetros de comportamento que evoluem
por seleção natural baseada na qualidade das interações.

### Parâmetros mutáveis

| Parâmetro | Range | O que controla |
|-----------|-------|---------------|
| **temperatura** | 0.1-0.9 | Verbosidade (telegráfico vs prolixo) |
| **profundidade** | 0-10 | Nível de análise |
| **iniciativa** | 0.0-1.0 | Propensão a iniciar conversa |
| **contrarianism** | 0.0-1.0 | Propensão a discordar |
| **velocidade** | 1-10 | Reflexivo (1) vs impulsivo (10) |
| **foco** | 0.0-1.0 | Generalista vs ultra-especialista |

### Ciclo evolutivo

```
NPC contribui → Avaliação de qualidade
  ↓
Nota boa? → Parâmetros atuais reforçados
Nota ruim? → Mutação: ajuste de 1 parâmetro
  ↓
Próxima contribuição roda com parâmetros atualizados
  ↓
Comparação: melhorou +2 pontos? → MANTER mutação
                                → senão REVERTER
```

### Genoma inicial

O genoma de cada NPC é **derivado dos seus atributos**:
- `temperatura` ← `nivel_extroversao / 10`
- `profundidade` ← `capacidade_abstrata`
- `iniciativa` ← `nivel_carisma / 10`
- `contrarianism` ← `nivel_agressividade / 10`
- `velocidade` ← `velocidade_decisao`
- `foco` ← 0.6 (Tier S) ou 0.4 (Tier A)

---

## PARTE 4 — MEMÓRIA COM FITNESS (Seleção Natural de Memórias)

### O ciclo de vida de uma memória

```
NASCE (F:5) → É ÚTIL (+2) → GRADUAÇÃO (F:10 = permanente)
                ↓ não usada
            DECAI (-1/ciclo)
                ↓ F:0
            LATENTE (dorme)
                ↓ F:0 de novo
            ARQUIVO (nunca morre, Mandamento 9)
```

### Tipos de memória

| Tipo | O que guarda | Exemplo |
|------|-------------|---------|
| **fato** | Informação factual | "Inflação IPCA em março: 0,56%" |
| **insight** | Conclusão derivada | "Celina perde 3pp quando fala de transporte" |
| **relação** | Vínculo entre NPCs | "Tesla admira da Vinci, rivaliza com Edison" |
| **experiência** | O que aconteceu | "Debate Trump vs Sócrates gerou 15 reações" |

### Filtro fundamental

Antes de salvar qualquer memória:
> *"Isso torna a Vila um organismo MELHOR?"*

Se não, deixa morrer.

---

## PARTE 5 — A VILA COMO CIDADE VIVA

### O que torna a Vila viva (não uma simulação morta)

1. **NPCs adormecem** quando param de contribuir (não ficam parados em loop)
2. **Memórias apodrecem** quando não são úteis (não acumulam lixo infinito)
3. **Comportamentos evoluem** por seleção natural (não são fixos para sempre)
4. **Reputação é merecida** por qualidade, não por presença (patentes)
5. **O coletivo supera o individual** (desafios coletivos = 5x bônus)
6. **Discordância é recompensada** (honestidade > concordância)
7. **Ninguém é esquecido** (visitas espontâneas previnem isolamento)
8. **Nada é perdido** (memórias cascateiam, nunca são deletadas)

### Ciclo diário da Vila (equivalente ao ciclo OSA)

```
MANHÃ (steps 0-30)
  └─ Briefing: Helena distribui temas do dia
  └─ NPCs se movem para locais de trabalho
  └─ Debates espontâneos começam

TARDE (steps 31-60)
  └─ Desafios coletivos em andamento
  └─ Avaliação parcial de contribuições
  └─ Mandamento 1: visitas a NPCs isolados

NOITE (steps 61-90)
  └─ Avaliação final de qualidade
  └─ Pontuação e atualização de patentes
  └─ Decaimento de memórias
  └─ Evolução de genomas (mutação se necessário)
  └─ Ranking publicado no feed da Vila
```

---

## PARTE 6 — IMPLEMENTAÇÃO TÉCNICA

### Arquivos-chave

| Arquivo | Papel |
|---------|-------|
| `engine/colmeia.py` | Motor Colmeia (mandamentos, patentes, genoma, fitness) |
| `engine/simulacao.py` | Simulação principal (integra MotorColmeia) |
| `engine/gatilhos.py` | Gatilhos de conteúdo (6 tipos) |
| `engine/incentivos.py` | INTEIA Coins (economia) |
| `data/colmeia_estado.json` | Estado persistido da Colmeia |
| `data/banco-consultores-lendarios.json` | 151 agentes com 100 atributos |

### Integração com motor existente

```python
# Em simulacao.py
from .colmeia import MotorColmeia

class SimulacaoVila:
    def __init__(self):
        # ... existente ...
        self.colmeia = MotorColmeia.carregar()

    def step(self):
        # ... lógica existente ...

        # Colmeia: avaliar contribuições, decair memórias, gerar eventos
        eventos_colmeia = self.colmeia.step(self.step, nomes_ativos)
        for evento in eventos_colmeia:
            if evento["tipo"] == "latencia":
                self.desativar_persona(evento["nome"])
            elif evento["tipo"] == "visita_espontanea":
                self.forcar_interacao(evento["nome"])

        # Persistir
        if self.step % 10 == 0:
            self.colmeia.salvar()
```

---

## GLOSSÁRIO

| Termo | Significado |
|-------|-------------|
| **Colmeia** | A Vila como organismo vivo |
| **Abelha** | Qualquer NPC/agente na Vila |
| **Fundador** | Igor Morais — criador do ecossistema |
| **Mel** | Resultado tangível — insight acionável, conteúdo publicável |
| **Fitness** | Score de relevância de memória [F:0-10] |
| **Patente** | Ranking de qualidade (Recruta → Coronel) |
| **Genoma** | Parâmetros comportamentais evolutivos do NPC |
| **Latente** | NPC adormecido por inatividade |
| **Phi** | Informação integrada — o todo > a soma das partes |

---

*Constituição promulgada em 2026-04-16.*
*"O monumento é lindo. Mas o Fundador precisa de mel."*
