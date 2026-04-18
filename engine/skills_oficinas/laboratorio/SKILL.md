---
name: laboratorio
description: "Oficina de Ciência da Computação — sandbox Python completo, análise estatística, prototipagem. Use quando a tarefa exige cálculo real, simulação numérica, ou dados tabulados."
family: computacao
capabilities:
  - code
  - analysis
  - prototyping
  - statistics
preconditions:
  - agente_presente_em:laboratorio
  - desafio_ativo
scope:
  - laboratorio
bind_tools:
  - Python Sandbox
  - Análise de Dados
constraints:
  - Executa apenas em sandbox seguro (sem I/O externa)
  - Custo de 5 coins para código e 8 para análise
  - Artefato obrigatório em .py ou .json com resultado estruturado
local_id: laboratorio
---

## N2 — Quando e como aplicar

Aplicável quando o problema pode ser reduzido a cálculo, transformação de
dados ou prototipagem de lógica. Evitar para textos argumentativos puros
(use `arena_debates` ou `tribunal`) ou brainstorm aberto (`cafe_filosofos`).

Precondições: agente precisa estar no local `laboratorio` e ter carteira
com pelo menos 5 coins. Desafio ativo é obrigatório — o artefato produzido
é anexado ao desafio.

Heurísticas de decisão:
- Se o problema menciona números, distribuições, correlações → Análise de Dados.
- Se pede algoritmo, transformação, prototipagem → Python Sandbox.
- Se a saída é um gráfico → delegar para `atelie` depois.

## N3 — Procedimento

1. Agente entra em `laboratorio` e verifica ferramentas disponíveis.
2. Escolhe `python_completo` ou `analise_dados`.
3. Define entrada estruturada (dict JSON) contendo problema e dados.
4. Executa a ferramenta — o sandbox retorna output textual e artefato.
5. Artefato é gravado em `data/entregas/<desafio_id>/<autor>_<ts>.<py|json>`.
6. Agente documenta conclusões em três bullets na sua memória episódica.

Critérios normativos:
- Nunca executar código que acesse rede, disco fora do sandbox, ou APIs externas.
- Falha no sandbox vira trace `resultado=falha` — agente perde metade do custo.
- Resultado aceitável: artefato reproduz em re-execução (determinismo).
