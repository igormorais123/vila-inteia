---
name: tribunal
description: "Oficina do Tribunal da Razão — votação formal, pareceres jurídicos, análise contratual. Use para decisões binárias com justificativa, pareceres vinculantes e interpretação da constituição da Vila."
family: direito
capabilities:
  - voting
  - opinion
  - interpretation
preconditions:
  - agente_presente_em:tribunal
  - tese_formulada
scope:
  - tribunal
bind_tools:
  - Votação Formal
  - Emissão de Parecer
constraints:
  - Voto precisa citar artigo constitucional ou precedente
  - Parecer minoritário também é registrado
  - Toda decisão gera trace com resultado e dissidências
local_id: tribunal
---

## N2 — Quando e como aplicar

Use para: interpretação de artigo da Constituição, conflito entre
mandamentos, parecer sobre contrato externo, decisão jurídica sobre
caso real (ex: copilot Paixão Cortes).

Não confundir com `arena_debates` (debate aberto) — aqui a saída é
**decisão vinculante dentro da Vila**. Precondição: tese formulada em
forma de pergunta fechada (sim/não/depende).

Heurísticas:
- Se ao menos três agentes jurídicos disponíveis → votação plenária.
- Se só um → parecer individual com consulta prévia à Constituição.
- Dúvida sobre qual artigo aplicar → delegar para `constituinte.py`.

## N3 — Procedimento

1. Tese enunciada como pergunta fechada ("o artigo 042 aplica ao caso X?").
2. Cada juiz/agente produz parecer individual citando artigos.
3. Votação formal registrada via `constituicao.abrir_votacao`.
4. Apuração: maioria define decisão; minoria é preservada.
5. Artefato final é assinado digitalmente e gravado em `vila_constituicao_votos`.
6. Se decisão cria precedente novo → candidato a artigo operacional.

Critérios normativos:
- Voto sem citação é anulado.
- Empate implica tese improcedente (garantia do status quo).
- Parecer contra a Constituição só vale se o próprio artigo for contestado
  em paralelo via `constituinte.propor_revisao`.
