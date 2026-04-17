# Evolução de Genomas de NPCs — Documentação

## Visão Geral

A partir de **commit e2379ce**, o MotorColmeia implementa um **loop evolutivo de genomas** que permite que os parâmetros de comportamento dos NPCs melhorem através de seleção natural baseada em qualidade.

O sistema é inspirado no `genome.json` da OSA INTEIA e segue a abordagem de "mutar 1 param → testar → comparar → manter/revert".

## Arquitetura

### Componentes Principais

1. **GenomaNPC** (`engine/colmeia.py`, linhas 131-203)
   - Dataclass com 6 parâmetros float/int
   - Método `mutar(param, delta)` cria cópia com 1 parâmetro alterado
   - Campos de rastreamento: `geracao`, `experimentos`, `melhorias`

2. **MotorColmeia.evoluir_genomas()** (`engine/colmeia.py`, linhas 585-709)
   - Loop evolutivo chamado a cada step
   - Roda para NPCs com ≥10 histórico de scores
   - Gerencia `self.experimentos_evolucao` (dict de experimentos pendentes)
   - Retorna eventos de evolução para logging/UI

3. **MotorColmeia.obter_genoma()** (`engine/colmeia.py`, linhas 572-583)
   - Getter do genoma atual (principal ou candidato)
   - Chamado pelo construtor de prompts para ajustar LLM behavior
   - Se há experimento em andamento, retorna candidato; senão, retorna principal

## Fluxo de Evolução

### Fase 1: Iniciação (quando NPC tem 10+ scores)

```
if len(historico[npc]) >= 10 and npc not in experimentos:
  baseline = media(historico[-10:])
  criterio = random_choice(concisao, profundidade, originalidade, relevancia, acionabilidade)
  param = criterio_para_param[criterio]
  delta = random(±0.1 ou ±1 conforme param)
  genoma_candidato = genoma_atual.mutar(param, delta)
  
  experimentos[npc] = {
    baseline, genoma_candidato, param, delta, step_inicio
  }
```

**Evento retornado**: `"tipo": "evolucao_iniciada"`

### Fase 2: Teste (5 contribuições seguintes)

- NPC usa genoma_candidato durante esta fase
- `obter_genoma(npc)` retorna candidato, não principal
- Próximas 5 contribuições são avaliadas

### Fase 3: Decisão (após 5 contribuições)

```
if step_atual - step_inicio >= 5:
  media_recente = media(historico[-5:])
  
  if media_recente >= baseline + 2.0:  # Melhorou +2 ou mais
    genoma_principal = genoma_candidato  # Aprova
    melhorias += 1
    evento = "evolucao_aprovada"
  else:
    genoma_principal = genoma_anterior  # Reverte
    evento = "evolucao_revertida"
  
  del experimentos[npc]
```

**Eventos retornados**: `"tipo": "evolucao_aprovada"` ou `"evolucao_revertida"`

## Mapeamento Critério → Parâmetro

Definido em `evoluir_genomas()` linhas 601-607:

| Critério | Parâmetro | Lógica |
|----------|-----------|--------|
| concisão | temperatura | Temp baixa → resposta mais telegráfica |
| profundidade | profundidade | Direto: mais profundidade → análise mais funda |
| originalidade | contrarianism | Maior contrarianism → mais discordância → mais original |
| relevância | foco | Maior foco → resposta mais no tema |
| acionabilidade | iniciativa | Maior iniciativa → mais proativo → mais ações |

## Integração com step()

Chamado automaticamente no final de `step()`:

```python
def step(self, step_atual, personas_ativas):
  # ... mandamentos e decaimento ...
  
  eventos_evolucao = self.evoluir_genomas(step_atual)
  eventos.extend(eventos_evolucao)
  return eventos
```

## Estado Persistido

O `experimentos_evolucao` **NÃO** é salvo em `salvar()`. Isso significa:
- Se o processo morrer durante um experimento, o NPC reverte ao genoma anterior no carregamento
- Futura melhoria: adicionar `self.experimentos_evolucao` a `estado` em `salvar()` para continuidade entre sessões

## Exemplo de Uso (Python)

```python
from engine.colmeia import MotorColmeia

motor = MotorColmeia()
motor.inicializar_npc("Helena", {"tier": "S"})

# Simular 10 contribuições
for i in range(10):
    motor.historico["Helena"].append(70.0)

# Step 1: Evolução iniciada
eventos = motor.step(1, ["Helena"])
# → eventos contém {"tipo": "evolucao_iniciada", "param": "temperatura", ...}

# Genoma em teste (chamado pelo prompt builder)
genoma = motor.obter_genoma("Helena")  # ← Retorna candidato
# genoma.temperatura pode ter mudado de 0.5 para 0.6

# Simular 5 mais contribuições com melhoria
for i in range(5):
    motor.historico["Helena"].append(75.0)

# Step 6: Evolução finalizada
eventos = motor.step(6, ["Helena"])
# → eventos contém {"tipo": "evolucao_aprovada", "baseline": 70.0, "novo_score": 75.0}

# Genoma permanente (mutação aprovada)
genoma = motor.obter_genoma("Helena")  # ← Retorna principal (mutado)
# genoma.temperatura agora é 0.6
```

## Testes

Rodados com sucesso em `teste_colmeia_evolucao.py`:

1. ✓ Inicialização e obter_genoma
2. ✓ Evolução iniciada com 10+ scores
3. ✓ Aprovação de mutação (+2 melhor)
4. ✓ Rejeição de mutação (sem melhoria)
5. ✓ Integração com step()
6. ✓ Ciclo completo em 15 steps

## Futuras Melhorias (v2+)

### Curto Prazo
- [ ] Persistir `experimentos_evolucao` em save/load
- [ ] Detecção mais inteligente de critério fraco (usar scores reais da avaliação, não aleatório)
- [ ] Experimentos simultâneos (múltiplos parâmetros por NPC)
- [ ] Crossover: combinar genomas de 2 NPCs de alta qualidade

### Médio Prazo
- [ ] Fitness landscape visualization (gráfico de cada parâmetro vs score)
- [ ] População genética: manter histórico de mutações bem-sucedidas
- [ ] Mutação adaptativa: delta varia com fitness do NPC
- [ ] Seleção de elite: top-k% de NPCs evoluem 3x mais rápido

### Longo Prazo
- [ ] Co-evolução: NPCs evoluem uns contra os outros em debates
- [ ] Multi-objetivo: otimizar simultâneamente relevancia+acionabilidade
- [ ] Transfer learning: genomas de NPCs antigos informam priors de novos

## Referências

- **Inspiração**: `genome.json` e evolução da OSA INTEIA
- **Teoria**: Algoritmos genéticos simples (mutation + fitness)
- **Similaridade**: A/B testing + Thompson sampling (mas mais fácil)

## Contato

Implementado por Claude Opus 4.6. Dúvidas?
