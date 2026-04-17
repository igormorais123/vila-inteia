# Referencia Tecnica — Vila INTEIA

> Documentacao completa extraida do codigo-fonte.
> Gerada automaticamente por docs/gerar_referencia.py

---

## main.py (356 linhas)

**Proposito:** Vila INTEIA - Entry Point.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `banner` |  | 24 | Exibe banner da Vila INTEIA. |
| `modo_cli` | args | 43 | Executa simulação via CLI com output no terminal. |
| `modo_serve` | args | 103 | Inicia servidor FastAPI. |
| `modo_demo` | args | 155 | Executa demo rápido com 10 agentes e 20 steps. |
| `modo_live` | args | 195 | Vila INTEIA 24/7 — servidor + simulação contínua em background. |
| `main` |  | 309 |  |

---

## config.py (88 linhas)

**Proposito:** Configuração da Vila INTEIA.

### Classe `ConfigSimulacao` (linha 11)

Parâmetros da simulação.

### Classe `ConfigCampus` (linha 69)

Layout do Campus INTEIA.

---

# Engine — Motor de Simulacao

## engine/arquetipos.py (385 linhas)

**Proposito:** Sistema de Prompts Profundos — Inconsciente Coletivo.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `gerar_prompt_profundo` | consultor | 216 | Gera prompt de sistema profundo para um consultor lendário. |
| `gerar_prompt_debate` | consultor_a, consultor_b, tema | 357 | Gera par de prompts para debate entre dois consultores. |
| `gerar_prompt_reacao` | consultor, post_titulo, post_conteudo | 373 | Gera prompt para consultor reagir a um post no feed. |

---

## engine/autoresearch.py (381 linhas)

**Proposito:** Motor de Autoresearch da Vila INTEIA.

### Classe `CicloResearch` (linha 25)

Um ciclo de pesquisa evolutiva.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 38 |  |

### Classe `PesquisaCompleta` (linha 53)

Resultado de uma pesquisa completa (multi-ciclo).

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 62 |  |

### Classe `MotorAutoresearch` (linha 74)

Motor de pesquisa autonoma integrado ao loop da simulacao.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` | intervalo_steps, max_ciclos | 82 |  |
| `deve_pesquisar` | step | 89 | Verifica se e hora de iniciar nova pesquisa. |
| `selecionar_tema` | tendencias, topicos_ativos | 93 | Seleciona o melhor tema para pesquisar. |
| `executar_pesquisa` | tema, personas, step | 118 | Executa pesquisa evolutiva completa (sincrono). |
| `to_dict` |  | 375 |  |

---

## engine/campus.py (890 linhas)

**Proposito:** Campus INTEIA - Mapa do Think Tank.

### Classe `Local` (linha 38)

Um local no Campus INTEIA.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `esta_aberto` |  | 56 | Locais residenciais sempre abertos, outros verificam horário. |
| `afinidade_consultor` | categorias_consultor | 60 | Calcula afinidade de um consultor com este local (0-1). |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `obter_local` | local_id | 816 | Retorna um local pelo ID. |
| `obter_todos_locais` |  | 821 | Retorna todos os locais do campus. |
| `obter_conexoes` | local_id | 826 | Retorna locais conectados a um dado local. |
| `obter_locais_por_tipo` | tipo | 834 | Retorna locais de um tipo específico. |
| `calcular_distancia` | local_a_id, local_b_id | 839 | Calcula distância mínima (em hops) entre dois locais via BFS. |
| `residencia_para_categoria` | categoria | 861 | Retorna o ID da residência mais adequada para uma categoria. |
| `locais_abertos` | hora | 877 | Retorna locais abertos em determinada hora. |

---

## engine/chateaubriand.py (479 linhas)

**Proposito:** Assis Chateaubriand — Editor-Chefe do Jornal da Vila INTEIA.

### Classe `MateriaBruta` (linha 82)

Matéria submetida por um habitante da Vila.

### Classe `ParecerChateaubriand` (linha 96)

O que o editor-chefe decide sobre uma matéria.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `avaliar` | materia | 140 | Dá parecer editorial sobre uma matéria bruta. |
| `reescrever` | materia, parecer | 213 | Reescreve a matéria seguindo o parecer, mantendo a voz do autor. |
| `escrever_materia_propria` | tema, vila_id, tipo, contexto | 256 | Chateaubriand escreve uma matéria do próprio punho. |
| `sugerir_colunistas` | habitantes_recentes, vila_id | 311 | Analisa histórico recente e indica colunistas fixos por editoria. |
| `relatar_descoberta` | descoberta, vila_id | 357 | Transforma uma descoberta da Vila em matéria para o mundo real. |
| `processar_e_publicar` | materia | 409 | Pipeline editorial completo. |

---

## engine/colmeia.py (756 linhas)

**Proposito:** Motor Colmeia — Doutrina da Colmeia como mecânica de jogo.

### Classe `GenomaNPC` (linha 132)

Parâmetros mutáveis de comportamento de um NPC.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `mutar` | param, delta | 163 | Cria cópia mutada (não altera o original). |
| `to_dict` |  | 186 |  |
| `from_dict` | cls, d | 201 |  |

### Classe `MemoriaFitness` (linha 210)

Memória com fitness — baseado na Doutrina da Colmeia.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `reforcar` | step | 229 | Memória foi útil — reforçar. |
| `decair` |  | 238 | Um ciclo passou sem uso — decair. |
| `esta_viva` |  | 248 | Memória está acessível (não arquivada)? |
| `to_dict` |  | 252 |  |

### Classe `MotorColmeia` (linha 373)

Integra todos os sistemas da Colmeia na simulação.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` |  | 387 |  |
| `inicializar_npc` | nome, dados_consultor | 406 | Inicializa sistemas da Colmeia para um NPC. |
| `registrar_contribuicao` | nome, texto, contexto, step | 427 | NPC fez uma contribuição — avaliar e pontuar. |
| `step` | step_atual, personas_ativas | 479 | Executa um ciclo da Colmeia. |
| `ranking` |  | 535 | Retorna ranking completo ordenado por pontos. |
| `estado` |  | 554 | Snapshot completo do estado da Colmeia. |
| `obter_genoma` | nome | 577 | Retorna o genoma atual (possível mutado) de um NPC. |
| `evoluir_genomas` | step_atual | 590 | Loop evolutivo — roda quando há dados suficientes de um NPC. |
| `salvar` | caminho | 720 | Salva estado completo da Colmeia. |
| `carregar` | cls, caminho | 739 | Carrega estado da Colmeia do disco. |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `obter_patente` | pontos | 119 | Retorna a patente correspondente aos pontos acumulados. |
| `avaliar_contribuicao` | texto, contexto | 293 | Avalia qualidade de uma contribuição de NPC. |

---

## engine/constituicao.py (254 linhas)

**Proposito:** Constituição viva da Vila INTEIA.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `propor_artigo` | vila_id, tipo, titulo, texto | 45 | Propõe novo artigo. Exige evento_origem não-vazio: forçar que o agente |
| `abrir_votacao` | artigo_id, quorum_necessario | 88 |  |
| `votar` | artigo_id, agente_id, voto, agente_nome | 100 | Registra voto (favor/contra/abstencao). |
| `apurar` | artigo_id | 148 | Verifica se atingiu quórum e decide aprovação. |
| `promulgar_se_aprovado` | artigo_id | 180 | Se aprovado, promulga. Se estrutural, cria ticket executivo. |
| `revogar` | artigo_id, motivo | 221 |  |
| `listar_vigentes` | vila_id, tipo | 236 |  |
| `listar_em_votacao` | vila_id | 243 |  |
| `listar_tickets_executivo` | status, limite | 250 |  |

---

## engine/constituinte.py (225 linhas)

**Proposito:** Constituinte — ciclo de propostas com detecção de problema real.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `detectar_problemas_reais` | vila_id, limite | 39 | Varre eventos recentes da Vila e identifica lacunas/conflitos que |
| `propor_via_agente` | vila_id, agente_id, agente_nome, problema | 102 | Agente redige artigo a partir do problema detectado. |
| `colher_votos_sinteticos` | artigo_id, artigo, habitantes, fracao_votantes | 155 | Simula votação pedindo a cada habitante um voto em caráter. |
| `abrir_assembleia` | artigo_id, total_habitantes_vila, quorum_pct | 205 | Abre votação com quórum derivado. |

---

## engine/desafio.py (461 linhas)

**Proposito:** Motor de Desafios Coletivos — O propósito da Vila INTEIA.

### Classe `Contribuicao` (linha 46)

Uma proposta/contribuição de um agente para uma entrega.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 57 |  |

### Classe `Entrega` (linha 71)

Um artefato produzido coletivamente durante o desafio.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 83 |  |

### Classe `FaseDesafio` (linha 99)

Uma fase/etapa do desafio coletivo.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 112 |  |

### Classe `DesafioColetivo` (linha 128)

O desafio central que dá propósito à simulação.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `fase_atual` |  | 151 |  |
| `ativo` |  | 157 |  |
| `iniciar` | step | 160 | Inicia o desafio na fase 0. |
| `registrar_contribuicao` | contribuicao, step | 168 | Registra uma contribuição de um agente. |
| `registrar_voto` | agente_id, entrega_id, favor | 203 | Registra voto em uma entrega e atualiza status se atingir consenso. |
| `atualizar_progresso` | step | 226 | Recalcula progresso total e verifica transições de fase. |
| `gerar_contexto_para_agente` |  | 271 | Gera contexto textual do desafio para injetar no prompt dos agentes. |
| `gerar_topicos_fase` |  | 301 | Gera tópicos de discussão baseados na fase atual. |
| `to_dict` |  | 314 |  |
| `salvar` | caminho | 338 | Salva estado do desafio em JSON. |
| `carregar` | cls, caminho | 347 | Carrega desafio de JSON. |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `criar_desafio_livre` | tema, descricao, documento, steps_por_fase | 390 | Cria desafio a partir de input do usuário. |
| `criar_desafio` | tema_ou_id, descricao, documento | 438 | Cria desafio a partir de qualquer input. |
| `desafio_aleatorio` |  | 446 | Cria desafio placeholder — o usuário deve definir o tema. |
| `listar_desafios` |  | 451 | Não há catálogo fixo. Retorna instruções. |

---

## engine/economia.py (258 linhas)

**Proposito:** Economia viva da Vila INTEIA.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `garantir_perfil` | vila_id, agente_id, ambicao, propensao_risco | 61 | Cria ou retorna perfil econômico do habitante. |
| `get_perfil` | vila_id, agente_id | 88 |  |
| `atualizar_ambicao` | vila_id, agente_id, ambicao | 94 |  |
| `precificar` | tipo_trabalho, contexto | 107 | Calcula valor final de um trabalho, aplicando multiplicadores. |
| `decidir_aceitar` | perfil, tipo_trabalho, contexto, custo_cognitivo | 135 | Decide se o habitante aceita o trabalho. |
| `creditar` | vila_id, agente_id, tipo_trabalho, contexto | 169 | Credita valor pelo trabalho realizado. Retorna a transação. |
| `debitar` | vila_id, agente_id, valor, motivo | 208 | Debita (contratar colaborador, patrocinar, multa). Valida saldo. |
| `top_ricos` | vila_id, n | 247 |  |
| `historico_agente` | vila_id, agente_id, limite | 254 |  |

---

## engine/executor_constitucional.py (136 linhas)

**Proposito:** Executor Constitucional — aplica artigos vigentes ao runtime.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `invalidar_cache` | vila_id | 49 |  |
| `pode_publicar` | vila_id, materia | 59 | Verifica se a publicação proposta viola alguma regra operacional. |
| `multiplicador_economico` | vila_id, tipo_trabalho | 95 | Procura artigos econômicos que alterem precificação. |
| `deve_banir` | vila_id, agente_id | 117 | Verifica se artigo estrutural determinou banimento. |
| `status_vila` | vila_id | 131 |  |

---

## engine/ferramentas_agente.py (588 linhas)

**Proposito:** Ferramentas dos Agentes — O toolkit que dá poder real aos habitantes da Vila.

### Classe `ResultadoExecucao` (linha 93)

Resultado da execução de código Python.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 101 |  |

### Classe `ResultadoPesquisa` (linha 225)

Resultado de pesquisa web.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 232 |  |

### Classe `Mensagem` (linha 319)

Mensagem direta entre agentes.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 330 |  |

### Classe `CaixaCorreio` (linha 343)

Sistema de mensagens diretas entre agentes.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` |  | 346 |  |
| `enviar` | msg | 350 | Envia mensagem. |
| `caixa_entrada` | agente_id, apenas_nao_lidas | 356 | Retorna mensagens para um agente. |
| `pedidos_ajuda` | agente_id | 366 | Retorna pedidos de ajuda pendentes. |
| `to_dict` |  | 373 |  |

### Classe `AcaoFerramenta` (linha 467)

Registro de uso de ferramenta por um agente.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 477 |  |

### Classe `ToolkitAgente` (linha 489)

Controlador de ferramentas de um agente.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` |  | 496 |  |
| `pode_usar` | agente_id, ferramenta, local_atual, saldo | 501 | Verifica se agente pode usar a ferramenta. |
| `executar_python` | agente_id, codigo, local_atual, saldo, ... | 521 | Executa Python se o agente tiver acesso. |
| `pesquisar` | agente_id, query, local_atual, saldo, ... | 542 | Pesquisa web se o agente tiver acesso. |
| `stats` |  | 569 | Estatísticas de uso de ferramentas. |
| `to_dict` |  | 583 |  |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `executar_python` | codigo, timeout_s | 113 | Executa código Python em sandbox restrito. |
| `pesquisar_web` | query, max_resultados | 241 | Pesquisa na web — 3 tentativas em cascata. |
| `ferramentas_disponiveis_no_local` | local_id | 450 | Retorna ferramentas disponíveis num local. |
| `custo_uso_local` | local_id | 456 | Retorna custo em INTEIA Coins para usar recursos do local. |

---

## engine/flockvote.py (477 linhas)

**Proposito:** FlockVote Lite — Pesquisa Eleitoral Sintetica com Calibracao.

### Classe `ResultadoEleitor` (linha 53)

Resultado da simulacao de voto de 1 eleitor.

### Classe `ResultadoPesquisa` (linha 65)

Resultado agregado da pesquisa.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 84 |  |

### Classe `FlockVoteLite` (linha 121)

Pesquisa eleitoral sintetica com calibracao academica.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` | caminho_eleitores | 127 |  |
| `executar` | candidatos, contexto, amostra, h_calibracao, ... | 153 | Executa pesquisa com execucao paralela (5 threads). |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `obter_flockvote` | caminho | 113 | Retorna instancia singleton do FlockVote. |

---

## engine/gatilhos.py (1382 linhas)

**Proposito:** Motor de Gatilhos de Conteúdo — O coração pulsante da Vila INTEIA.

### Classe `DiabobController` (linha 84)

O Provocador Universal.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `deve_provocar` | step, ultimo_step_provocacao | 109 |  |
| `gerar_provocacao_ia` | diabob, rede, personas | 113 | Gera provocação via IA olhando o feed atual. |

### Classe `JesusCristoController` (linha 166)

O Mestre das Parábolas.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `deve_postar` | step, ultimo_step_post, hora | 180 |  |
| `gerar_parabola_ia` | jesus, contexto_feed | 188 | Gera parábola baseada no que está acontecendo na Vila. |
| `responder_diabob_ia` | jesus, provocacao | 222 | Responde a Diabob com serenidade devastadora. |

### Classe `HelenaController` (linha 236)

A Moderadora — Inteligência Coletiva da Vila.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `deve_intervir` | post, step | 255 | Decide SE e COMO Helena deve intervir. |
| `gerar_intervencao_ia` | helena, post, tipo, todas_categorias | 284 | Gera intervenção de Helena via IA. |
| `gerar_sintese_diaria` | helena, rede | 351 | Gera síntese do dia — resumo dos debates mais relevantes. |

### Classe `MotorDebate` (linha 395)

Orquestra debates estruturados entre pares rivais.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `selecionar_par` | personas | 403 | Seleciona par rival disponível para debate. |
| `executar_debate_ia` | persona_a, persona_b, tema_contexto, n_turnos | 417 | Executa debate completo entre dois rivais via IA. |

### Classe `WaveConfig` (linha 498)

Configura as ondas de comentários em posts.

### Classe `PostAgendado` (linha 513)

Post na fila aguardando waves de comentários.

### Classe `MotorGatilhos` (linha 525)

Orquestra todos os 6 gatilhos de conteúdo da Vila INTEIA.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` | rede | 532 |  |
| `executar_step` | step, hora_atual, personas | 569 | Executa todos os gatilhos para este step. |
| `injetar_tema` | titulo, conteudo, tags, personas, ... | 1260 | Igor injeta tema — prioridade máxima. |
| `injetar_evento` | titulo, conteudo, tags, step | 1306 | Injeta evento/notícia para consultores reagirem. |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|

---

## engine/helena_ceo.py (166 linhas)

**Proposito:** Helena CEO — Coordenadora do Desafio Coletivo.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `distribuir_tarefas` | desafio, personas, step | 21 | Helena analisa a fase atual e distribui tarefas para agentes relevantes. |
| `gerar_cobranca` | desafio, step, contribuicoes_esperadas | 94 | Helena cobra se o progresso está lento. |
| `avaliar_workspace` | workspace, desafio_id | 131 | Helena avalia as entregas no workspace. |

---

## engine/ia_client.py (247 linhas)

**Proposito:** Cliente IA da Vila INTEIA — OmniRoute (VPS nova) + Anthropic fallback.

### Classe `ThrottleConfig` (linha 29)

Controle de taxa de chamadas.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `pode_chamar` |  | 34 |  |
| `registrar` |  | 39 |  |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `chamar_llm` | mensagens, modelo, max_tokens, temperatura | 123 | Chamada SÍNCRONA ao LLM. |
| `chamar_llm_conversa` | system_prompt, user_prompt, modelo, max_tokens | 235 | Atalho: system + user → resposta. |

---

## engine/incentivos.py (345 linhas)

**Proposito:** Sistema de Incentivos da Vila INTEIA.

### Classe `Transacao` (linha 75)

Registro de transação financeira.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 84 |  |

### Classe `Carteira` (linha 96)

Carteira de INTEIA Coins de um agente.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `creditar` | valor, tipo, step, descricao | 109 | Adiciona coins à carteira. |
| `debitar` | valor, tipo, step, descricao | 123 | Remove coins da carteira. Retorna False se saldo insuficiente. |
| `ajustar_reputacao` | delta | 140 | Ajusta reputação (clamped 0-100). |
| `to_dict` |  | 144 |  |

### Classe `MotorIncentivos` (linha 161)

Gerencia recompensas, penalidades e economia da vila.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` |  | 168 |  |
| `obter_carteira` | agente_id | 173 | Retorna ou cria carteira do agente. |
| `saldo` | agente_id | 179 | Retorna saldo do agente. |
| `recompensar` | agente_id, tipo, step, descricao | 185 | Recompensa agente por ação específica. |
| `penalizar` | agente_id, tipo, step, descricao | 205 | Penaliza agente (saldo nunca fica negativo). |
| `cobrar_recurso` | agente_id, custo, descricao, step | 218 | Cobra uso de recurso do local. Retorna False se sem saldo. |
| `transferir` | de_id, para_id, valor, step, ... | 225 | Transferência entre agentes. |
| `verificar_inatividade` | agentes_ids, step | 236 | Penaliza agentes inativos (aplica uma vez por threshold, não repetidamente). |
| `registrar_atividade` | agente_id, step | 255 | Marca agente como ativo. |
| `nomear_cargo` | agente_id, cargo, step | 261 | Nomeia agente para cargo especial. |
| `atualizar_ranking` |  | 270 | Recalcula ranking de reputação. |
| `top_agentes` | n | 278 | Top N agentes por reputação. |
| `gini_coefficient` |  | 293 | Calcula coeficiente de Gini da distribuição de riqueza. |
| `to_dict` |  | 307 |  |
| `salvar` | caminho | 315 | Salva estado em JSON. |
| `carregar` | caminho | 325 | Carrega estado de JSON. Retorna True se carregou. |

---

## engine/mirante_client.py (366 linhas)

**Proposito:** Cliente Mirante — publica matérias da Vila no jornal externo.

### Classe `Autor` (linha 101)
### Classe `ParecerEditorial` (linha 108)
### Classe `Submissao` (linha 116)
| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 127 |  |

### Classe `ResultadoPublicacao` (linha 133)
### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `slugify` | titulo | 146 | kebab-case sem acento. |
| `normalizar_categoria` | cat_agente, categoria_proposta | 161 |  |
| `gerar_mdx` | submissao | 167 | Monta MDX com frontmatter compatível com o schema Zod do Mirante. |
| `publicar` | submissao | 317 | Publica submissão no Mirante. Escolhe transporte automaticamente. |
| `status_integracao` |  | 356 | Retorna estado da configuração do cliente. |

---

## engine/mirofish_bridge.py (255 linhas)

**Proposito:** Bridge Mirofish — motor de simulação de rede social com grafos.

### Classe `GrafoMirofish` (linha 50)
### Classe `SimulacaoMirofish` (linha 58)
### Classe `RelatorioMirofish` (linha 67)
### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `upload_corpus` | corpus | 112 | Envia corpus (ex: matérias e debates da Vila) para Mirofish montar grafo. |
| `obter_grafo` | graph_id | 128 |  |
| `iniciar_simulacao` | graph_id, habitantes, cenario, steps | 136 | Dispara simulação Mirofish com habitantes da Vila como perfis OASIS. |
| `status_simulacao` | simulation_id | 164 |  |
| `gerar_relatorio` | simulation_id | 181 |  |
| `obter_relatorio` | report_id | 194 |  |
| `simular_rede_social` | corpus, habitantes, cenario, steps | 210 | Pipeline Vila → Mirofish → relatório de uma vez só. |
| `status_integracao` |  | 250 |  |

---

## engine/oficinas.py (1142 linhas)

**Proposito:** Oficinas da Vila INTEIA — Cada local é um centro de produção real.

### Classe `Workspace` (linha 40)

Diretório de trabalho de um desafio.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` | base_dir | 46 |  |
| `escrever` | desafio_id, agente_id, agente_nome, nome_arquivo, ... | 56 | Agente escreve um arquivo real no workspace. |
| `ler` | desafio_id, nome_arquivo | 91 | Agente lê arquivo do workspace. |
| `listar` | desafio_id | 99 | Lista todos os arquivos do workspace. |
| `compilar` | desafio_id | 108 | Compila todas as entregas em documento único. |
| `to_dict` | desafio_id | 122 |  |

### Classe `Ferramenta` (linha 138)

Uma ferramenta real disponível num local.

### Classe `Oficina` (linha 152)

Conjunto de ferramentas reais de um local do campus.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `tem_ferramenta` | tipo | 160 |  |
| `obter_ferramenta` | tipo | 163 |  |
| `to_dict` |  | 169 |  |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `oficina_do_local` | local_id | 1114 | Retorna a oficina (ferramentas reais) de um local. |
| `ferramentas_no_local` | local_id | 1119 | Retorna lista de ferramentas disponíveis num local. |
| `todas_oficinas` |  | 1131 | Lista todas as oficinas do campus. |
| `ferramenta_por_id` | ferramenta_id | 1136 | Busca ferramenta por ID em qualquer oficina. |

---

## engine/osa_bridge.py (176 linhas)

**Proposito:** Bridge entre Vila INTEIA e OSA (Optimal System Agent).

### Classe `OSABridge` (linha 26)

Interface entre Vila INTEIA e OSA.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` | url | 29 |  |
| `classificar_complexidade` | topico | 50 | Retorna weight 0.0-1.0 via Signal Theory do OSA. |
| `modelo_por_complexidade` | weight | 78 | Retorna combo OmniRoute baseado no weight do Signal Theory. |
| `buscar_noticias` | topico, max_resultados | 90 | Busca notícias recentes via OSA web_search. |
| `salvar_insights` | persona_id, insights | 122 | Salva insights no Vault do OSA para próxima sessão. |
| `carregar_insights` | persona_id, topico | 146 | Carrega insights do Vault do OSA da sessão anterior. |

---

## engine/pacotes_habitantes.py (181 linhas)

**Proposito:** Pacotes de Habitantes — carrega agentes sintéticos para uma Vila.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `listar_pacotes` |  | 40 | Une metadados do Supabase com arquivos presentes em disco. |
| `carregar_pacote` | pacote_id | 90 | Lê o JSON do pacote e retorna lista de agentes. |
| `amostrar` | pacote_id, qtd, seed | 114 | Pega amostra aleatória do pacote. |
| `combinar` | configs | 128 | Mistura pacotes seguindo configs. |
| `validar_pacote` | pacote_id | 164 | Retorna diagnóstico do pacote: quantidade, campos, problemas. |

---

## engine/persona.py (652 linhas)

**Proposito:** Persona - Agente inteligente na Vila INTEIA.

### Classe `Persona` (linha 23)

Um agente vivo na Vila INTEIA.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `mover` | mundo, personas, hora_atual | 121 | Executa um ciclo cognitivo completo. |
| `gerar_prompt_sistema` |  | 182 | Gera o system prompt completo para esta persona. |
| `gerar_prompt_pesquisa` | tema, tipo | 263 | Gera prompt RICO para pesquisa/autoresearch — Helena Master montou. |
| `decidir_interacao` | outro | 512 | Calcula a probabilidade (0-1) de querer interagir com outro agente. |
| `salvar` | diretorio | 553 | Salva o estado completo da persona. |
| `carregar` | cls, diretorio, dados_consultor | 584 | Carrega uma persona de arquivos salvos. |
| `resumo` |  | 607 | Retorna resumo público da persona (para visualização). |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `criar_persona_de_consultor` | dados | 636 | Factory: cria uma Persona a partir dos dados de um consultor lendário. |
| `carregar_todas_personas` | caminho_json | 641 | Carrega todas as personas do JSON de consultores lendários. |

---

## engine/previsibilidade.py (277 linhas)

**Proposito:** Motor de Previsibilidade da Vila INTEIA.

### Classe `Tendencia` (linha 26)

Uma tendencia detectada na vila.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 36 |  |

### Classe `PrevisaoDebate` (linha 49)

Previsao de resultado de debate entre consultores.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 58 |  |

### Classe `MotorPrevisibilidade` (linha 68)

Analisa historico da vila para gerar previsoes.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` |  | 75 |  |
| `registrar_step` | resumo_step, rede_social | 89 | Registra dados de um step para analise futura. |
| `analisar_tendencias` |  | 119 | Detecta tendencias nos ultimos 50 steps. |
| `prever_engajamento` | topico | 197 | Preve engajamento esperado para um topico (0-100). |
| `prever_saturacao` | topico | 216 | Preve nivel de saturacao de um topico (0.0 a 1.0). |
| `sugerir_proximo_topico` | topicos_atuais | 235 | Sugere topico que geraria mais engajamento. |
| `gerar_briefing_helena` |  | 252 | Gera briefing preditivo para Helena consumir. |
| `to_dict` |  | 272 |  |

---

## engine/publicar_mirante.py (287 linhas)

**Proposito:** Publicação no Mirante News — Canal real de output da Vila INTEIA.

### Classe `ArtigoMirante` (linha 79)

Artigo pronto para publicação no Mirante News.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `gerar_mdx` |  | 94 | Gera conteúdo MDX completo com frontmatter. |
| `to_dict` |  | 125 |  |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `publicar_no_mirante` | artigo, auto_push | 138 | Publica artigo no Mirante News. |
| `criar_artigo_de_workspace` | workspace, desafio_id, agente_id, agente_nome | 238 | Compila artefatos do workspace em artigo publicável. |

---

## engine/rede_social.py (926 linhas)

**Proposito:** Rede Social INTEIA - O coração da Vila.

### Classe `Reacao` (linha 33)

Reação a um post ou comentário.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 40 |  |

### Classe `Comentario` (linha 50)

Comentário de um consultor em um post.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 63 |  |

### Classe `Postagem` (linha 80)

Post principal no feed — pode ser do usuário ou de um consultor.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `total_comentarios` |  | 102 |  |
| `total_reacoes` |  | 106 |  |
| `engajamento` |  | 110 | Score de engajamento (para ranking). |
| `to_dict` |  | 119 |  |

### Classe `RedeSocial` (linha 146)

Motor da rede social dos consultores lendários.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` |  | 160 |  |
| `publicar_tema_usuario` | titulo, conteudo, tags, hora_atual | 170 | Usuário publica um tema para os consultores discutirem. |
| `publicar_opiniao_consultor` | persona, conteudo, titulo, tags, ... | 203 | Consultor publica uma opinião/observação espontânea. |
| `publicar_evento` | titulo, conteudo, tags, hora_atual | 238 | Sistema publica evento/notícia para consultores reagirem. |
| `comentar` | post_id, persona, conteudo, em_resposta_a, ... | 269 | Consultor comenta em um post. |
| `reagir` | post_id, persona, tipo | 300 | Consultor reage a um post. |
| `processar_reacoes` | personas, hora_atual, max_reacoes_por_step | 323 | Processa a fila: consultores reagem aos posts pendentes. |
| `gerar_posts_autonomos` | personas, hora_atual, chance, sim_ref, ... | 381 | Consultores geram posts espontâneos baseados em suas reflexões. |
| `feed` | limite, offset, tipo, tag, ... | 433 | Retorna o feed formatado. |
| `obter_post` | post_id | 471 | Retorna um post completo com todos os comentários. |
| `trending_tags` | n | 479 | Tags mais usadas recentemente. |
| `stats` |  | 489 | Estatísticas da rede social. |
| `salvar` | caminho | 521 | Persiste feed em JSON. |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `gerar_prompt_comentario_ia` | persona, post | 911 | Gera prompt para o LLM criar comentário autêntico. |

---

## engine/relatorio.py (153 linhas)

**Proposito:** Motor de Relatório Executivo da Vila INTEIA.

### Classe `RelatorioExecutivo` (linha 14)

Relatório estratégico consolidado.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `to_dict` |  | 35 |  |
| `to_markdown` |  | 54 |  |

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `gerar_relatorio` | simulacao | 85 | Gera relatório executivo consolidado da simulação. |

---

## engine/save_load.py (212 linhas)

**Proposito:** Save/Load de Vilas — cada vila é um "jogo salvo" retomável.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `criar_vila` | nome, pacote_base, qtd_habitantes, objetivo | 48 | Cria nova instância de vila. Retorna registro completo. |
| `listar_vilas` | status, limite | 76 | Lista vilas, opcionalmente filtradas por status. |
| `get_vila` | vila_id | 84 |  |
| `pausar_vila` | vila_id | 89 | Pausa vila. Não apaga estado, só marca. |
| `retomar_vila` | vila_id | 99 | Marca vila como ativa de novo. |
| `arquivar_vila` | vila_id | 109 | Move vila para arquivada (não aparece em listas padrão). |
| `snapshot_vila` | vila_id, simulacao, tipo | 122 | Tira snapshot completo da vila. |
| `listar_snapshots` | vila_id, limite | 153 |  |
| `snapshot_mais_recente` | vila_id | 158 |  |
| `restaurar_snapshot` | snapshot_id | 163 | Retorna o estado serializado do snapshot. |

---

## engine/simulacao.py (918 linhas)

**Proposito:** Motor de Simulação da Vila INTEIA.

### Classe `SimulacaoVila` (linha 37)

Controlador principal da simulação.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` | nome, caminho_consultores | 49 |  |
| `workspace` |  | 110 | Workspace lazy — só cria quando dir_dados já existe. |
| `inicializar` | max_agentes | 118 | Carrega consultores e inicializa todas as personas. |
| `executar_step` |  | 197 | Executa um step da simulação. |
| `executar` | n_steps, callback | 575 | Executa N steps da simulação. |
| `pausar` |  | 602 | Pausa a simulação. |
| `retomar` |  | 606 | Retoma a simulação. |
| `parar` |  | 610 | Para a simulação. |
| `injetar_topico` | topico, importancia | 619 | Injeta um tópico no campus para os agentes discutirem. |
| `iniciar_desafio` | desafio_id, descricao, documento, steps_por_fase | 658 | Inicia um desafio coletivo a partir do tema do usuário. |
| `contribuir_desafio` | agente_id, conteudo, tipo | 687 | Registra contribuição manual de um agente ao desafio. |
| `votar_desafio` | agente_id, entrega_id, favor | 707 | Registra voto de um agente em uma entrega. |
| `consultar_agente` | agente_id | 718 | Retorna estado detalhado de um agente. |
| `estado_mundo` |  | 744 | Retorna snapshot do estado atual de toda a simulação. |
| `mapa_calor` |  | 813 | Retorna ocupação de cada local (para heatmap). |
| `salvar` |  | 827 | Salva estado completo da simulação. |
| `carregar` |  | 866 | Carrega estado completo: meta + desafio + incentivos. |
| `log` | mensagem | 898 | Registra evento no log. |

---

## engine/supabase_db.py (237 linhas)

**Proposito:** Persistência Supabase — Vila INTEIA na nuvem.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `inserir` | table, data | 89 | Insere registro. Retorna o registro criado. |
| `buscar` | table, params | 97 | Busca registros. Retorna lista. |
| `atualizar` | table, filtro, data | 103 | Atualiza registro por filtro. Ex: filtro='id=eq.abc' |
| `deletar` | table, filtro | 111 | Deleta registro por filtro. |
| `salvar_desafio` | desafio_dict | 121 | Salva ou atualiza desafio no Supabase. |
| `salvar_contribuicao` | desafio_id, contrib | 157 | Salva contribuição no Supabase. |
| `salvar_carteira` | agente_id, carteira_dict | 171 | Salva carteira no Supabase (upsert). |
| `salvar_artefato` | desafio_id, artefato | 195 | Salva artefato produzido. |
| `carregar_desafio` | desafio_id | 211 | Carrega desafio do Supabase. |
| `carregar_carteiras` |  | 217 | Carrega todas as carteiras. |
| `carregar_artefatos` | desafio_id | 223 | Carrega artefatos de um desafio. |
| `status_conexao` |  | 228 | Verifica conexão com Supabase. |

---

# engine/cognitivo/ — Pipeline Cognitivo

## engine/cognitivo/conversar.py (423 linhas)

**Proposito:** CONVERSAR - Módulo de Conversação entre Agentes.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `conversar` | persona, percepcoes, contexto, mundo | 23 | Decide se conversa e com quem, e gera a conversa. |
| `gerar_conversa_com_ia` | persona_a, persona_b, topico, max_turnos | 385 | Prompt para gerar conversa autêntica via LLM. |

---

## engine/cognitivo/executar.py (280 linhas)

**Proposito:** EXECUTAR - Módulo de Execução de Ações.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `executar` | persona, hora_atual | 26 | Executa a ação planejada. |

---

## engine/cognitivo/perceber.py (157 linhas)

**Proposito:** PERCEBER - Módulo de Percepção.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `perceber` | persona, mundo, personas, hora_atual | 19 | Percebe o ambiente ao redor. |

---

## engine/cognitivo/planejar.py (304 linhas)

**Proposito:** PLANEJAR - Módulo de Planejamento.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `gerar_plano_diario` | persona, hora_atual | 157 | Gera o plano diário do agente. |
| `planejar` | persona, contexto, hora_atual | 202 | Decide a próxima ação do agente. |

---

## engine/cognitivo/recuperar.py (111 linhas)

**Proposito:** RECUPERAR - Módulo de Recuperação de Memória.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `recuperar` | persona, percepcoes, hora_atual | 20 | Recupera memórias relevantes para o contexto atual. |

---

## engine/cognitivo/refletir.py (204 linhas)

**Proposito:** REFLETIR - Módulo de Reflexão.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `refletir` | persona, hora_atual, forcar | 22 | Gera reflexões/insights baseados em memórias acumuladas. |
| `gerar_reflexao_com_ia` | persona, ponto_focal, memorias | 175 | Gera reflexão usando LLM (para uso futuro com OmniRoute). |

---

## engine/cognitivo/sintetizar.py (377 linhas)

**Proposito:** SINTETIZAR - Módulo exclusivo INTEIA (não existe no Smallville).

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `sintetizar` | personas, topico, hora_atual, min_perspectivas | 23 | Sintetiza insights de múltiplos agentes sobre um tópico. |

---

# engine/memoria/ — Sistema de Memoria

## engine/memoria/espacial.py (129 linhas)

**Proposito:** Memória Espacial - Consciência de localização do agente.

### Classe `RegistroPresenca` (linha 16)

Registro de quem foi visto em determinado local.

### Classe `MemoriaEspacial` (linha 26)

Modelo mental do espaço que o agente mantém.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` |  | 37 |  |
| `registrar_visita` | local_id, quando | 53 | Registra que o agente visitou um local. |
| `registrar_presenca` | agente_id, agente_nome, local_id, acao, ... | 62 | Registra que viu outro agente em um local. |
| `onde_esta` | agente_id | 79 | Retorna o último local conhecido de outro agente. |
| `quem_esta_em` | local_id | 84 | Retorna quem foi visto em um local (pode estar desatualizado). |
| `locais_favoritos` | n | 91 | Retorna os N locais mais visitados. |
| `local_atual` |  | 100 | Retorna o local mais recente no histórico. |
| `tempo_no_local_atual` | agora | 106 | Retorna horas no local atual. |
| `to_dict` |  | 114 |  |

---

## engine/memoria/fluxo.py (371 linhas)

**Proposito:** Fluxo de Memória (Memory Stream) - Memória Associativa de Longo Prazo.

### Classe `NoMemoria` (linha 22)

Um nó na memória do agente (evento, pensamento ou conversa).

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `esta_expirado` | agora | 50 |  |
| `to_dict` |  | 55 |  |
| `from_dict` | cls, dados | 74 |  |

### Classe `FluxoMemoria` (linha 83)

Fluxo de Memória Associativa.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` | decay, max_memorias | 91 |  |
| `total` |  | 114 |  |
| `adicionar` | no | 117 | Adiciona um nó de memória ao fluxo. |
| `adicionar_evento` | descricao, sujeito, predicado, objeto, ... | 154 | Atalho para adicionar um evento. |
| `adicionar_pensamento` | descricao, importancia, evidencias, palavras_chave | 177 | Atalho para adicionar um pensamento/reflexão. |
| `adicionar_conversa` | descricao, participantes, local_id, importancia, ... | 195 | Atalho para adicionar uma conversa. |
| `recuperar` | consulta, n, peso_relevancia, peso_recencia, ... | 214 | Recupera memórias relevantes usando pontuação tripla. |
| `recuperar_por_participante` | nome, n | 273 | Recupera memórias envolvendo um participante específico. |
| `recuperar_por_local` | local_id, n | 279 | Recupera memórias de um local específico. |
| `ultimas` | n, tipos | 283 | Retorna as últimas N memórias. |
| `deve_refletir` | limiar | 290 | Verifica se acumulou importância suficiente para reflexão. |
| `resetar_acumulador` |  | 294 | Reseta o acumulador de importância após reflexão. |
| `pontos_focais` | n | 298 | Retorna os N temas mais importantes recentes (para reflexão). |
| `salvar` | caminho | 331 | Persiste o fluxo de memória em JSON. |
| `carregar` | cls, caminho | 343 | Carrega um fluxo de memória de JSON. |
| `resumo` |  | 360 | Retorna resumo estatístico da memória. |

---

## engine/memoria/rascunho.py (230 linhas)

**Proposito:** Rascunho (Scratch Memory) - Memória de trabalho do agente.

### Classe `AcaoAtual` (linha 16)

A ação que o agente está executando agora.

### Classe `PlanoItem` (linha 29)

Um item no plano do agente.

### Classe `ConversaAtiva` (linha 41)

Estado de uma conversa em andamento.

### Classe `Rascunho` (linha 53)

Memória de trabalho do agente.

| Metodo | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `__init__` |  | 61 |  |
| `esta_conversando` |  | 109 |  |
| `esta_dormindo` |  | 113 |  |
| `esta_ocupado` |  | 117 |  |
| `iniciar_conversa` | parceiro_id, parceiro_nome, local_id, topico | 120 | Inicia uma conversa com outro agente. |
| `adicionar_turno_conversa` | nome, fala | 136 | Adiciona um turno à conversa ativa. |
| `encerrar_conversa` |  | 141 | Encerra a conversa ativa e retorna o registro. |
| `atualizar_acao` | descricao, emoji, local_id, duracao | 151 | Atualiza a ação atual do agente. |
| `atualizar_energia` | delta | 166 | Ajusta energia do agente. |
| `contexto_para_prompt` |  | 189 | Gera contexto textual para uso em prompts de IA. |
| `to_dict` |  | 207 |  |

---

# API — Endpoints REST

## api/rotas_colmeia.py (601 linhas)

**Proposito:** API REST da Colmeia — Sistema de Ranking e Dinâmicas Orgânicas.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `obter_simulacao` |  | 25 | Retorna a simulação ativa ou cria uma nova. |
| `ranking_colmeia` | top | 44 | Retorna o ranking completo da Colmeia ordenado por pontos. |
| `estado_colmeia` |  | 97 | Retorna snapshot do estado completo da Colmeia. |
| `detalhe_npc_colmeia` | nome | 122 | Retorna dados completos de um NPC no sistema da Colmeia. |
| `npcs_por_patente` | patente | 216 | Retorna NPCs agrupados por patente, ou filtra por patente específica. |
| `listar_latentes` |  | 271 | Retorna todos os NPCs em modo latente (inatividade >= 50 steps). |
| `listar_mandamentos` |  | 313 | Retorna os 11 Mandamentos da Colmeia com explicação. |
| `listar_patentes` |  | 356 | Retorna tabela completa de patentes (ranking por pontos). |
| `listar_criterios_avaliacao` |  | 387 | Retorna critérios usados para avaliar contribuições de NPCs. |
| `memorias_npc` | nome, camada, limite | 417 | Retorna memórias de um NPC, opcionalmente filtradas por camada. |
| `genoma_npc` | nome | 490 | Retorna genoma evolutivo completo de um NPC. |
| `comparar_genomas` | npc1, npc2 | 546 | Compara genomas de dois NPCs lado a lado. |

---

## api/rotas_rede_social.py (415 linhas)

**Proposito:** API da Rede Social INTEIA.

### Classe `PostTemaRequest` (linha 49)
### Classe `PostEventoRequest` (linha 55)
### Classe `ComentarioRequest` (linha 61)
### Classe `ReacaoRequest` (linha 66)
### Classe `DebateRequest` (linha 257)

Força debate entre dois consultores específicos.

### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `obter_rede` |  | 28 | Retorna a rede social da simulação ativa. |
| `obter_motor_gatilhos` |  | 34 | Retorna o motor de gatilhos da simulação ativa. |
| `obter_feed` | limite, offset, tipo, tag | 75 | Retorna o feed social. |
| `obter_post` | post_id | 97 | Retorna um post com todos os comentários. |
| `trending` |  | 107 | Tags em alta. |
| `stats_rede` |  | 114 | Estatísticas da rede social. |
| `publicar_tema` | req | 125 | Gatilho 1 — Usuário injeta tema (prioridade máxima). |
| `publicar_evento` | req | 157 | Publica evento/notícia para os consultores reagirem. |
| `forcar_comentario` | post_id, agente_id, req | 178 | Força um consultor específico a comentar em um post. |
| `forcar_reacao` | post_id, agente_id, req | 202 | Força um consultor a reagir a um post. |
| `processar_reacoes` | max_reacoes | 219 | Processa reações pendentes na fila. |
| `gerar_posts_autonomos` | chance | 231 | Gera posts autônomos dos consultores. |
| `alternar_destaque` | post_id | 243 | Alterna destaque de um post. |
| `forcar_debate` | req | 265 | Gatilho 5 — Força debate entre par rival. |
| `forcar_provocacao` |  | 320 | Gatilho 6 — Diabob provoca o feed. |
| `forcar_parabola` |  | 344 | Gatilho 6 — Jesus Cristo posta uma parábola. |
| `forcar_sintese` |  | 367 | Helena gera síntese dos debates mais relevantes. |
| `status_gatilhos` |  | 390 | Status do Motor de Gatilhos — cadência e contadores. |

---

## api/rotas_vila.py (755 linhas)

**Proposito:** API REST da Vila INTEIA.

### Classe `IniciarRequest` (linha 54)
### Classe `StepRequest` (linha 59)
### Classe `TopicoRequest` (linha 63)
### Classe `DesafioRequest` (linha 386)
### Classe `ContribuicaoRequest` (linha 395)
### Classe `VotoRequest` (linha 401)
### Classe `PythonRequest` (linha 407)
### Classe `PublicarMiranteRequest` (linha 590)
### Funcoes

| Funcao | Parametros | Linha | Descricao |
|--------|-----------|-------|-----------|
| `obter_simulacao` |  | 34 | Retorna a simulação ativa ou cria uma nova. |
| `iniciar_simulacao` | req | 73 | Inicializa uma nova simulação. |
| `executar_steps` | req | 86 | Executa N steps da simulação. |
| `pausar` |  | 100 | Pausa a simulação. |
| `retomar` |  | 108 | Retoma a simulação. |
| `parar` |  | 116 | Para e salva a simulação. |
| `estado_mundo` |  | 128 | Retorna o estado completo do mundo. |
| `mapa_calor` |  | 135 | Retorna mapa de calor de ocupação dos locais. |
| `listar_agentes` | local, categoria, tier | 146 | Lista agentes com filtros opcionais. |
| `detalhe_agente` | agente_id | 171 | Retorna detalhes completos de um agente. |
| `conversas_recentes` | limite | 181 | Lista conversas recentes. |
| `listar_sinteses` |  | 191 | Lista sínteses de inteligência coletiva. |
| `listar_locais` |  | 201 | Lista todos os locais do campus. |
| `estatisticas` |  | 225 | Retorna estatísticas da simulação. |
| `injetar_topico` | req | 242 | Injeta um tópico para os agentes discutirem. |
| `forcar_sintese` | topico | 254 | Força síntese de inteligência coletiva sobre um tópico. |
| `salvar` |  | 273 | Salva o estado atual da simulação (desafio + incentivos + personas). |
| `carregar` |  | 281 | Carrega estado salvo (desafio + incentivos + meta). |
| `previsibilidade` |  | 300 | Retorna tendências e previsões da vila. |
| `saturacao_topico` | topico | 312 | Retorna nível de saturação de um tópico. |
| `autoresearch_status` |  | 323 | Retorna estado do motor de autoresearch. |
| `executar_autoresearch` | req | 330 | Força execução de autoresearch sobre um tema. |
| `estado_live` |  | 342 | Estado completo da vila em tempo real. |
| `relatorio_executivo` |  | 364 | Relatório executivo consolidado — CONCLUSÕES, não dados brutos. |
| `relatorio_markdown` |  | 373 | Relatório em Markdown para leitura humana. |
| `listar_desafios_disponiveis` |  | 413 | Retorna instruções — o tema é definido pelo usuário. |
| `iniciar_desafio` | req | 420 | Inicia um desafio coletivo a partir do tema do usuário. |
| `estado_desafio` |  | 435 | Retorna estado atual do desafio. |
| `contribuir_desafio` | req | 444 | Registra contribuição ao desafio. |
| `votar_desafio` | req | 451 | Registra voto em uma entrega. |
| `executar_python_sandbox` | req | 462 | Executa Python no sandbox de um agente. |
| `recursos_local` | local_id | 487 | Retorna recursos disponíveis em um local. |
| `economia` |  | 501 | Retorna estado da economia da vila. |
| `carteira_agente` | agente_id | 508 | Retorna carteira de um agente. |
| `ranking_economia` | top | 515 | Ranking de agentes por reputação. |
| `listar_oficinas` |  | 526 | Lista todas as oficinas (ferramentas reais por local). |
| `detalhe_oficina` | local_id | 533 | Detalhe de uma oficina: ferramentas, artefatos produzidos. |
| `workspace_listar` |  | 543 | Lista artefatos produzidos no workspace do desafio ativo. |
| `workspace_desafio` | desafio_id | 553 | Lista artefatos de um desafio específico. |
| `workspace_avaliar` | desafio_id | 560 | Helena avalia as entregas do workspace. |
| `workspace_compilar` | desafio_id | 568 | Compila todas as entregas em documento único. |
| `workspace_ler_arquivo` | desafio_id, nome_arquivo | 577 | Lê conteúdo de um artefato. |
| `publicar_mirante` | req | 601 | Publica artigo no Mirante News (mirantenews.com.br). |
| `publicar_workspace_mirante` | titulo, agente_id, auto_push | 618 | Compila artefatos de um agente no workspace e publica no Mirante. |
| `proxy_chat` | body | 670 | Proxy para OmniRoute/chat — resolve CORS. |
| `proxy_mensagens_salvar` | body | 685 | Proxy para salvar mensagens — resolve CORS. |
| `proxy_mensagens_carregar` | tipo, sessao_id, limit | 700 | Proxy para carregar mensagens — resolve CORS. |
| `proxy_estado_salvar` | body | 715 | Proxy para salvar estado — resolve CORS. |
| `proxy_estado_carregar` | tipo, sessao_id | 730 | Proxy para carregar estado — resolve CORS. |
| `proxy_constituicao` |  | 745 | Proxy para constituição — resolve CORS. |

---
