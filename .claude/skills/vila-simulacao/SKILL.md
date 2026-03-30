# Vila INTEIA — Simulacao

> Como o motor de simulacao funciona, como operar, como depurar.

## Ciclo de Vida de um Step

```
executar_step()
  │
  ├── 1. Shuffle agentes (ordem aleatoria)
  ├── 2. Para cada agente ativo:
  │     persona.mover()
  │       ├── perceber()    → O que esta ao redor?
  │       ├── recuperar()   → O que sei sobre isso?
  │       ├── refletir()    → Preciso pensar? (se importancia >= 100)
  │       ├── conversar()   → Devo falar com alguem?
  │       ├── planejar()    → O que fazer a seguir?
  │       └── executar()    → Mover, agir, atualizar energia
  │
  ├── 3. MOTOR DE GATILHOS
  │     motor_gatilhos.executar_step()
  │       ├── Debate entre rivais (cada 20 steps)
  │       ├── Diabob provoca (cada 15 steps)
  │       ├── Jesus parabola (1-2x por dia)
  │       ├── Sun Tzu intervencao (cada 50 steps)
  │       ├── Helena verifica posts ativos
  │       ├── Posts espontaneos (chance variavel por horario)
  │       └── Processar waves de comentarios
  │
  ├── 4. Processar reacoes na rede social
  ├── 5. Avancar tempo (+10 min)
  ├── 6. Sintese coletiva (cada 10 steps)
  └── 7. Auto-save (cada 50 steps)
```

## Personagens Especiais

| Nome | Frequencia | Comportamento |
|------|-----------|---------------|
| Diabob | 15 steps | NUNCA concorda. Ironia como bisturi. |
| Jesus | 30+ steps | Parabolas. Responde Diabob com serenidade. |
| Helena | 5 steps | Observa. Detecta consenso falso. Sintetiza. |
| Sun Tzu | 50 steps | 1-2 frases que mudam tudo. |

## Sistema de Waves

Comentarios chegam em ondas, nao todos de uma vez:

| Wave | Delay | Usa IA | N |
|------|-------|--------|---|
| 1 | Imediato | Sim | 3 |
| 2 | 1 step (10min) | Sim | 4 |
| 3 | 3 steps (30min) | Nao (heuristico) | 3 |
| 4 | 6 steps (1h) | Nao (heuristico) | 3 |

## Depuracao

```python
# Ver estado de um agente
sim.consultar_agente("CL001")

# Ver mapa de calor (onde estao os agentes)
sim.mapa_calor()

# Ver estado completo
sim.estado_mundo()

# Ver feed social
sim.rede_social.feed(limite=10, ordenar_por="engajamento")

# Ver status dos gatilhos
mg = sim.motor_gatilhos
print(f"Posts hoje: {mg.posts_hoje}")
print(f"Waves pendentes: {len(mg.fila_waves)}")
print(f"Proximo debate: step {mg.ultimo_debate_step + 20}")
print(f"Proximo Diabob: step {mg.ultimo_diabob_step + 15}")
```

## Aprendizados (descobertos em testes)

1. **Especiais sempre incluidos**: mesmo com max_agentes=20, Diabob/Jesus/Helena/Sun Tzu sao carregados automaticamente
2. **OmniRoute offline**: sistema cai para heuristicos — funciona 100% sem LLM
3. **Cadencia inicial**: ultimo_*_step inicia negativo para permitir primeiro uso no step 0
4. **Wave fallback**: se IA falha na wave 1, cai para heuristico (nunca perde comentario)
5. **Cap diario**: maximo 75 posts por dia in-game para nao sobrecarregar
6. **Helena auto**: intervem automaticamente quando waves acumulam 5+ comentarios
