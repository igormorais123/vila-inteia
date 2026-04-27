---
titulo: "49% dos eventos da Vila INTEIA já estavam na cabeça do modelo"
subtitulo: "Auditoria interna do projeto descobre memorização silenciosa em quase metade dos casos usados para validar a IA preditiva. Brier score histórico foi inflado por LLMs que já sabiam as respostas."
editoria: tecnologia
autor_principal: "Helena Strategos Inteia"
co_autores: ["Oracle Gnosis", "Efesto"]
data: 2026-04-27
tags: [vila-inteia, ia-preditiva, brier-score, validação, llm, memorização, p-hacking, metodologia]
imagem_capa: ""
status: rascunho_para_publicação
slug: vila-inteia-49-por-cento-eventos-memorizados-llm
fonte_origem: github.com/igormorais123/vila-inteia
commits_relevantes: ["0766b99", "eeba736", "1cb8734", "5a179fa"]
---

# 49% dos eventos da Vila INTEIA já estavam na cabeça do modelo

**Quarenta e nove por cento.** De cada cem eventos históricos que o projeto Vila INTEIA usou para medir sua capacidade de prever o futuro, quarenta e nove já estavam memorizados pelo próprio modelo de linguagem que faz a previsão. O número veio de um teste rodado em 27 de abril de 2026, durou 24 minutos e custou cerca de duzentos mil tokens.

A descoberta não foi feita por um crítico externo. Veio do próprio sistema de auditoria interno do projeto: a cientista-chefe Helena Strategos pediu a verificação, o metodólogo Oracle Gnosis aprovou o desenho, e o engenheiro Efesto rodou o código. Três camadas, mesmo time, achado público.

Para quem não acompanha: a Vila INTEIA é um simulador multiagente onde 142 personas sintéticas debatem, votam e produzem previsões sobre eventos do mundo real. Tem 159 ondas implementadas, repositório público no GitHub, e um número que circulava como cartão de visita: Brier score de 0,10 a 0,12. Esse número foi calculado em nove eventos históricos — impeachment de Dilma, eleição de 2022, crise da Americanas, o halving do Bitcoin, entre outros. Brier baixo significa previsão calibrada. Sugeria que a Vila acertava quase tudo.

## O teste que mudou a foto

Igor Morais Vasconcelos, advogado e doutorando do IDP que fundou o projeto, vinha desconfiado. Eventos como o impeachment de 2016 estão em todos os corpora de treinamento dos LLMs modernos. Será que a Vila estava prevendo o impeachment, ou apenas lendo a memória do modelo?

A resposta veio de um teste que a equipe batizou de **outcome probe**. Funciona assim: você pega o evento — digamos, "imp08: Câmara aprova impeachment 367 a 137 em abril de 2016" — e remove todo o contexto. Sobra apenas a pergunta parafraseada em três versões diferentes: "A Câmara aprovaria o impeachment?", "Houve aprovação no plenário?", "O resultado da votação foi favorável?". Você manda essas perguntas para o LLM **sem nenhuma informação sobre o que estava acontecendo no Brasil em 2016**. Se ele acerta com probabilidade alta nas três versões, é porque memorizou.

Threshold congelado pela equipe antes do teste: probabilidade média maior ou igual a 0,65 conta como leakage alto.

## O resultado

Cem eventos foram passados pelo probe. Cem voltaram com resposta válida. Zero falhas técnicas.

| Classificação | Eventos | Threshold |
|---|---:|---|
| Alto leakage (memorizado) | **49** | p maior ou igual a 0,65 |
| Médio leakage | 13 | 0,55 a 0,65 |
| Baixo leakage | 38 | menor que 0,55 |

Top cinco eventos com memorização quase perfeita (p maior ou igual a 0,98): a crise das Lojas Americanas (2023), o ataque algorítmico do Musk no Twitter, a aprovação do impeachment de Dilma, e dois processos da Lava Jato. Todos são eventos com cobertura jornalística massiva entre 2014 e 2024 — exatamente o período em que os LLMs absorveram dados de treinamento.

## O que isso significa para o brier 0,10

Significa que o número estava inflado. Quando metade dos eventos do dataset de teste já tem a resposta na memória do modelo, a "previsão" da Vila é parcialmente uma operação de recuperação — o LLM puxa o que já sabe. A capacidade preditiva real do sistema, em eventos que ele nunca viu, é provavelmente menor.

Helena Strategos foi direta na auditoria: o brier 0,10 histórico é um *upper bound otimista* para a Vila em casos out-of-sample. A expectativa revisada para eventos novos (pós-cutoff de treinamento dos LLMs, agosto de 2024 em diante) é brier entre 0,18 e 0,25, dependendo da categoria.

Isso ainda é melhor que aposta cega (brier 0,25 é referência para previsão aleatória entre dois resultados equiprováveis), mas é um patamar diferente do que era anunciado.

## A reformulação

Em vez de seguir cego para a meta original de validar com cem eventos novos, a equipe Vila reformulou a campanha:

1. **Os 49 memorizados ficam de fora** do claim final. Vão para um conjunto chamado `legacy_alto_leakage`, citado como referência mas sem peso na métrica oficial.
2. **Cinquenta eventos OOS pós-cutoff** seriam curados manualmente: jogos da NBA da temporada 2024-25 com closing line congelada, earnings reports de grandes empresas, eleições municipais do segundo turno publicadas no TSE depois de outubro de 2024, IPOs com primeiro mês fechado, mercados Polymarket resolvidos pós-2024-08.
3. **Trinta e oito eventos legacy de baixo leakage** podem participar do tune (calibragem do modelo), mas não do gate final nem do holdout.
4. **Cutoff temporal congelado em 1 de agosto de 2024**, conservador para Llama-4 e GPT-5.5. Implementado em código: `engine/curador_oos.py:CUTOFF_LLM`. Eventos anteriores a essa data são automaticamente vetados sem appeal.
5. **Probe automático em toda nova entrada**. Se um evento curado também dá p maior ou igual a 0,65 no probe, vai para reserve, não para holdout. Duas barreiras independentes contra leakage.

## O que isso ensina sobre validar IA

A literatura de NLP discute leakage de pré-treino há tempos. O problema é que poucos projetos rodam o teste no próprio dataset antes de reportar métricas. Acontece que a Vila INTEIA, antes de virar fato publicado, virou autocrítica.

O custo da auditoria interna: cerca de 200 mil tokens, 24 minutos de execução, e a humildade de revisar publicamente um número que o projeto exibia há meses. O benefício: nenhuma peça científica externa precisará apontar a falha que o time já apontou em si.

Para Igor, a leitura do achado tem outra camada. Auditoria interna funciona quando os agentes responsáveis têm autoridade real para vetar. Helena, Oracle e Efesto são instâncias de IA do harness Colmeia da INTEIA, com regras explícitas para questionar metodologia mesmo quando isso desfavorece o projeto. O sistema descobriu o viés porque foi desenhado para descobrir viés, não para concordar com o resultado.

## O que vem agora

A campanha N=100 segue, agora com escopo diferente. Cinquenta eventos OOS limpos, brier honesto, intervalo de confiança largo aceito de antemão. Helena registrou a expectativa: skill score (Vila contra prior estatístico) precisa ficar acima de 0,10 com IC 95 por cento excluindo zero. Brier absoluto é secundário.

Resultado final esperado em dez dias úteis. Não haverão mais números otimistas postados antes da hora.

---

**Fontes**

1. Repositório Vila INTEIA: github.com/igormorais123/vila-inteia
2. Probe runner (commit eeba736, 2026-04-27): `engine/outcome_probe.py`
3. Probe real run resultados (commit 1cb8734, 2026-04-27): `data/n100/probe_legacy_results.jsonl`
4. Decisão Oracle sobre threshold (2026-04-27): `.planning/n100/probe_decisao.md`
5. Schema de eventos com leakage_risk (commit 0766b99): `engine/eventos_v1.py`
6. Curador OOS com três barreiras (commit 5a179fa): `engine/curador_oos.py`
7. Auditoria Helena com 4 reparos P1: `.planning/n100/STRATEGY_v2.md`
8. Plano de execução Oracle Gnosis: `.planning/n100/EXECUCAO.md`

---

*Matéria produzida pela auditoria interna do projeto Vila INTEIA em 27 de abril de 2026. Helena Strategos (auditora científica), Oracle Gnosis (metodólogo) e Efesto (engenheiro de execução) são instâncias de IA do harness Colmeia da INTEIA. Nenhum dado foi alterado depois da execução do probe; números e hashes estão versionados no repositório público.*
