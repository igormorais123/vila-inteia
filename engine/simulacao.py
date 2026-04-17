"""
Motor de Simulação da Vila INTEIA.

Orquestra o ciclo de vida de 144 consultores lendários
vivendo no Campus INTEIA.
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timedelta
from typing import Optional

from .persona import Persona, carregar_todas_personas
from .campus import LOCAIS, obter_local
from .cognitivo.sintetizar import sintetizar
from .rede_social import RedeSocial
from .gatilhos import MotorGatilhos
from .previsibilidade import MotorPrevisibilidade
from .autoresearch import MotorAutoresearch
from .desafio import DesafioColetivo, criar_desafio, desafio_aleatorio, Contribuicao, listar_desafios
from .ferramentas_agente import ToolkitAgente, ferramentas_disponiveis_no_local, custo_uso_local
from .incentivos import MotorIncentivos
from .oficinas import Workspace, OFICINAS, todas_oficinas
from .helena_ceo import distribuir_tarefas, gerar_cobranca, avaliar_workspace
from .colmeia import MotorColmeia

# Import config: relativo (package mode) ou direto (standalone)
try:
    from ..config import config
except (ImportError, ValueError):
    from config import config


class SimulacaoVila:
    """
    Controlador principal da simulação.

    Responsabilidades:
    - Carregar e inicializar personas
    - Executar ciclos de simulação (steps)
    - Gerenciar interações entre agentes
    - Coletar e agregar insights
    - Persistir estado
    """

    def __init__(
        self,
        nome: str = "simulacao_padrao",
        caminho_consultores: str = "data/banco-consultores-lendarios.json",
    ):
        self.nome = nome
        self.caminho_consultores = caminho_consultores

        # Lock para acesso thread-safe (API lê enquanto loop escreve)
        import threading
        self._step_lock = threading.RLock()

        # Estado da simulação
        self.personas: dict[str, Persona] = {}
        self.step: int = 0
        self.hora_atual: datetime = datetime.now()
        self.rodando: bool = False
        self.pausada: bool = False

        # Rede Social e Motor de Gatilhos
        self.rede_social = RedeSocial()
        self.motor_gatilhos = MotorGatilhos(self.rede_social)

        # Motores de inteligencia
        self.motor_previsibilidade = MotorPrevisibilidade()
        self.motor_autoresearch = MotorAutoresearch(
            intervalo_steps=100, max_ciclos=3,
        )

        # Harness: Desafio Coletivo + Ferramentas + Incentivos + Workspace
        self.desafio: DesafioColetivo = DesafioColetivo()
        self.toolkit = ToolkitAgente()
        self.incentivos = MotorIncentivos()
        self.colmeia = MotorColmeia.carregar(
            os.path.join(config.diretorio_dados, "colmeia_estado.json")
        )
        self._workspace: Optional[Workspace] = None

        # Logs e eventos (com limites para evitar memory leak em 24/7)
        self.log_eventos: list[dict] = []
        self.conversas_recentes: list[dict] = []
        self.insights_coletivos: list[dict] = []
        self.sinteses: list[dict] = []
        self._MAX_LOG = 5000
        self._MAX_SINTESES = 500
        self._MAX_INSIGHTS = 200

        # Estatísticas
        self.stats = {
            "total_steps": 0,
            "total_conversas": 0,
            "total_reflexoes": 0,
            "total_movimentos": 0,
            "total_sinteses": 0,
            "total_pesquisas": 0,
        }

        # Diretório de dados
        self.dir_dados = os.path.join(config.diretorio_dados, nome)

    @property
    def workspace(self) -> Workspace:
        """Workspace lazy — só cria quando dir_dados já existe."""
        if self._workspace is None:
            self._workspace = Workspace(
                base_dir=os.path.join(self.dir_dados, "entregas")
            )
        return self._workspace

    def inicializar(self, max_agentes: int | None = None):
        """
        Carrega consultores e inicializa todas as personas.
        """
        # Resolver caminho relativo — tenta múltiplas raízes
        caminho = self.caminho_consultores
        if not os.path.isabs(caminho):
            dir_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidatos = [
                os.path.join(dir_projeto, caminho),
                os.path.join(dir_projeto, "data", "banco-consultores-lendarios.json"),
                os.path.join(dir_projeto, "frontend", "public", "data", "banco-consultores-lendarios.json"),
                os.path.join(".", caminho),
                os.path.join(os.getcwd(), caminho),
            ]
            for tentativa in candidatos:
                if os.path.exists(tentativa):
                    caminho = tentativa
                    break

        if not os.path.exists(caminho):
            raise FileNotFoundError(
                f"Arquivo de consultores não encontrado: {caminho}"
            )

        # Carregar personas
        todas = carregar_todas_personas(caminho)

        if max_agentes and max_agentes < len(todas):
            # Sempre incluir personagens especiais mesmo com limite
            NOMES_ESPECIAIS = {
                "diabob", "jesus cristo", "helena montenegro",
                "sun tzu", "nikola tesla",
            }
            primeiros = todas[:max_agentes]
            ids_incluidos = {p.id for p in primeiros}

            especiais_extras = [
                p for p in todas[max_agentes:]
                if p.id not in ids_incluidos
                and p.nome_exibicao.lower() in NOMES_ESPECIAIS
            ]

            todas = primeiros + especiais_extras
        elif max_agentes:
            todas = todas[:max_agentes]

        for persona in todas:
            self.personas[persona.id] = persona

        # Configurar tempo inicial
        self.hora_atual = datetime.strptime(
            f"{config.data_inicio} {config.hora_inicio}",
            "%Y-%m-%d %H:%M:%S",
        )

        # Distribuir agentes pelos locais iniciais
        self._distribuir_inicial()

        self.log(
            f"Simulação '{self.nome}' inicializada com "
            f"{len(self.personas)} agentes"
        )

    def _distribuir_inicial(self):
        """Distribui agentes pelas residências com base em suas categorias."""
        for persona in self.personas.values():
            local_inicial = persona.rascunho.local_atual
            if local_inicial:
                persona.memoria_espacial.registrar_visita(
                    local_inicial, self.hora_atual
                )

    def executar_step(self) -> dict:
        """
        Executa um step da simulação.

        Retorna resumo do step:
        {
            "step": int,
            "hora": str,
            "acoes": list[dict],
            "conversas": list[dict],
            "insights": list[dict],
            "movimentos": int,
        }
        """
        with self._step_lock:
            return self._executar_step_interno()

    def _executar_step_interno(self) -> dict:
        """Execução real do step (protegida por lock)."""
        self.step += 1
        resumo_step = {
            "step": self.step,
            "hora": self.hora_atual.strftime("%Y-%m-%d %H:%M"),
            "acoes": [],
            "conversas": [],
            "insights": [],
            "movimentos": 0,
        }

        # Setar referência da simulação nas personas (evita circular import)
        Persona._sim_ref = self

        # Processar cada agente
        agentes_lista = list(self.personas.values())
        random.shuffle(agentes_lista)  # Ordem aleatória por step

        for persona in agentes_lista:
            if not persona.ativo:
                continue

            # Executar ciclo cognitivo
            resultado = persona.mover(
                mundo=self,
                personas=self.personas,
                hora_atual=self.hora_atual,
            )

            # Registrar ação
            acao_resumo = {
                "agente_id": persona.id,
                "agente_nome": persona.nome_exibicao,
                "tipo": resultado["tipo"],
                "local": resultado["local_destino"],
                "acao": resultado["acao"],
                "emoji": resultado["emoji"],
            }
            resumo_step["acoes"].append(acao_resumo)

            if resultado.get("conversa"):
                resumo_step["conversas"].append(resultado["conversa"])
                self.conversas_recentes.append(resultado["conversa"])
                self.stats["total_conversas"] += 1

            if resultado["tipo"] == "refletir":
                self.stats["total_reflexoes"] += 1

            if resultado["tipo"] == "mover":
                self.stats["total_movimentos"] += 1

        # Manter conversas recentes limitadas
        self.conversas_recentes = self.conversas_recentes[-50:]

        # ========== MOTOR DE GATILHOS ==========
        # Executa todos os 7 gatilhos: debates rivais, Diabob, Jesus,
        # Helena moderadora, posts espontâneos, waves, desafio
        self.motor_gatilhos._sim_ref = self  # Referência direta (sem circular import)
        eventos_gatilhos = self.motor_gatilhos.executar_step(
            step=self.step,
            hora_atual=self.hora_atual,
            personas=self.personas,
        )
        for evento in eventos_gatilhos:
            resumo_step["acoes"].append({
                "agente_id": "sistema",
                "agente_nome": "Motor de Gatilhos",
                "tipo": evento["tipo"],
                "local": "campus",
                "acao": evento["descricao"],
                "emoji": "⚡",
            })
        # Processar reações pendentes na rede social
        interacoes_rede = self.rede_social.processar_reacoes(
            self.personas, self.hora_atual, max_reacoes_por_step=15
        )
        self.stats["total_conversas"] += len(interacoes_rede)
        # ========================================

        # Avançar tempo
        self.hora_atual += timedelta(seconds=config.segundos_por_step)

        # Verificar se deve gerar síntese coletiva
        if self.step % 10 == 0 and config.topicos_ativos:
            for topico in config.topicos_ativos:
                sintese = sintetizar(
                    self.personas, topico, self.hora_atual
                )
                if sintese:
                    self.sinteses.append(sintese)
                    if len(self.sinteses) > self._MAX_SINTESES:
                        self.sinteses = self.sinteses[-self._MAX_SINTESES:]
                    resumo_step["insights"].append(sintese)
                    self.stats["total_sinteses"] += 1

                    # HELENA FEEDBACK: Publicar sintese no feed
                    helena = self.personas.get("CL085")
                    if helena and sintese.get("sintese"):
                        from .rede_social import Postagem
                        post_sintese = Postagem(
                            tipo="insight",
                            autor_id=helena.id,
                            autor_nome=helena.nome_exibicao,
                            autor_titulo="Cientista-Chefe INTEIA",
                            autor_categoria="inteia",
                            titulo=f"Sintese: {topico[:40]}",
                            conteudo=sintese["sintese"][:500],
                            tags=["sintese", "helena"],
                            destaque=True,
                        )
                        self.rede_social._adicionar_post(post_sintese)

                    # HELENA FEEDBACK: Registrar na memoria dos participantes
                    texto_sintese = sintese.get("sintese", "")[:150]
                    if texto_sintese:
                        for pid in sintese.get("participantes", [])[:5]:
                            p = self.personas.get(pid)
                            if p:
                                p.memoria.adicionar_pensamento(
                                    descricao=texto_sintese,
                                    importancia=8,
                                    palavras_chave=set(topico.lower().split()),
                                )

        # ========== PREVISIBILIDADE ==========
        self.motor_previsibilidade.registrar_step(
            resumo_step, self.rede_social,
        )
        if self.step % 50 == 0:
            tendencias = self.motor_previsibilidade.analisar_tendencias()
            if tendencias:
                briefing = self.motor_previsibilidade.gerar_briefing_helena()
                resumo_step["briefing_preditivo"] = briefing

                # AÇÃO 1: Sugestão vira tópico ativo
                sugestao = self.motor_previsibilidade.sugerir_proximo_topico(
                    config.topicos_ativos,
                )
                if sugestao and sugestao not in config.topicos_ativos:
                    self.injetar_topico(sugestao, importancia=7)
                    self.log(f"[BRIEFING] Topico sugerido ativado: {sugestao}")

                # AÇÃO 2: Temas saturando ganham novo ângulo
                for t in briefing.get("saturando", [])[:1]:
                    nome = t.get("topico", "")
                    if nome and nome in config.topicos_ativos:
                        config.topicos_ativos.remove(nome)
                        novo = f"futuro de {nome} sob perspectiva inedita"
                        self.injetar_topico(novo, importancia=9)
                        self.log(f"[BRIEFING] Tema saturado renovado: {nome} → {novo}")

                # AÇÃO 3: Tema emergente prioriza autoresearch
                emergentes = briefing.get("emergentes", [])
                if emergentes:
                    self.motor_autoresearch.ultimo_research_step = max(
                        0, self.step - self.motor_autoresearch.intervalo_steps
                    )
                    self.log(f"[BRIEFING] Autoresearch priorizado para: {emergentes[0].get('topico','?')}")
        # ========================================

        # ========== AUTORESEARCH EVOLUTIVO ==========
        if self.motor_autoresearch.deve_pesquisar(self.step):
            tema = self.motor_autoresearch.selecionar_tema(
                tendencias=self.motor_previsibilidade.tendencias,
                topicos_ativos=config.topicos_ativos,
            )
            if tema:
                pesquisa = self.motor_autoresearch.executar_pesquisa(
                    tema, self.personas, self.step,
                )
                if pesquisa:
                    self.stats["total_pesquisas"] += 1
                    resumo_step["autoresearch"] = pesquisa.to_dict()

                    # Injetar topicos gerados na simulacao
                    for topico in pesquisa.topicos_gerados[:2]:
                        if topico not in config.topicos_ativos:
                            config.topicos_ativos.append(topico)
                            self.log(f"[AUTORESEARCH] Novo topico injetado: '{topico}'")

                    # Publicar descoberta no feed
                    if pesquisa.descoberta_principal:
                        helena = self.personas.get("CL085")
                        if helena:
                            from .rede_social import Postagem
                            post = Postagem(
                                tipo="insight",
                                autor_id=helena.id,
                                autor_nome=helena.nome_exibicao,
                                autor_titulo="Cientista-Chefe INTEIA",
                                autor_categoria="inteia",
                                titulo=f"Pesquisa Evolutiva: {tema[:50]}",
                                conteudo=pesquisa.descoberta_principal,
                                tags=["autoresearch", "helena", "descoberta"],
                                destaque=True,
                            )
                            self.rede_social._adicionar_post(post)
        # ========================================

        # ========== DESAFIO COLETIVO ==========
        if self.desafio.ativo:
            # Atualizar progresso do desafio
            self.desafio.atualizar_progresso(self.step)

            # A cada 5 steps: injetar tópicos do desafio como temas ativos
            if self.step % 5 == 0:
                topicos_desafio = self.desafio.gerar_topicos_fase()
                for t in topicos_desafio[:1]:
                    if t and t not in config.topicos_ativos:
                        config.topicos_ativos.append(t)

            # A cada 10 steps: gerar contribuições automáticas dos agentes
            if self.step % 10 == 0 and self.desafio.fase_atual:
                fase = self.desafio.fase_atual
                # Selecionar 3-5 agentes relevantes para contribuir
                agentes_sample = random.sample(
                    list(self.personas.values()),
                    min(5, len(self.personas)),
                )
                for persona in agentes_sample:
                    if not persona.ativo:
                        continue
                    # Contribuição baseada na expertise do agente
                    expertise = ", ".join(persona.rascunho.areas_expertise[:3])
                    contrib = Contribuicao(
                        agente_id=persona.id,
                        agente_nome=persona.nome_exibicao,
                        conteudo=f"[{persona.titulo}] Perspectiva sobre '{fase.descricao}' com base em {expertise}",
                        tipo="proposta",
                    )
                    self.desafio.registrar_contribuicao(contrib, self.step)
                    self.incentivos.recompensar(
                        persona.id, "proposta_nova", self.step,
                        f"Contribuiu na fase '{fase.nome}'"
                    )
                    self.incentivos.registrar_atividade(persona.id, self.step)

            # Verificar inatividade a cada 25 steps
            if self.step % 25 == 0:
                ids = list(self.personas.keys())
                self.incentivos.verificar_inatividade(ids, self.step)

            # Helena CEO: distribuir tarefas no início de cada fase (a cada 20 steps)
            if self.step % 20 == 0:
                # Distribuir tarefas
                atribuicoes = distribuir_tarefas(self.desafio, self.personas, self.step)
                if atribuicoes:
                    helena = self.personas.get("CL085")
                    if helena:
                        nomes = ", ".join(a["agente_nome"] for a in atribuicoes[:5])
                        from .rede_social import Postagem
                        post = Postagem(
                            tipo="sistema",
                            autor_id=helena.id,
                            autor_nome=helena.nome_exibicao,
                            autor_titulo="Cientista-Chefe | CEO do Desafio",
                            autor_categoria="inteia",
                            titulo=f"Distribuição de tarefas: {self.desafio.fase_atual.nome}",
                            conteudo=(
                                f"Fase '{self.desafio.fase_atual.nome}': "
                                f"convocados {nomes} e outros. "
                                f"Progresso: {self.desafio.progresso_total:.0%}"
                            ),
                            tags=["helena", "gestao", "desafio"],
                        )
                        self.rede_social._adicionar_post(post)

                # Cobrança se necessário
                cobranca = gerar_cobranca(self.desafio, self.step)
                if cobranca:
                    helena = self.personas.get("CL085")
                    if helena:
                        from .rede_social import Postagem
                        post_cob = Postagem(
                            tipo="sistema",
                            autor_id=helena.id,
                            autor_nome=helena.nome_exibicao,
                            autor_titulo="Cientista-Chefe | CEO do Desafio",
                            autor_categoria="inteia",
                            titulo="Cobrança de Progresso",
                            conteudo=cobranca,
                            tags=["helena", "cobranca", "urgente"],
                            destaque=True,
                        )
                        self.rede_social._adicionar_post(post_cob)

            # Info no resumo
            resumo_step["desafio"] = {
                "nome": self.desafio.nome,
                "fase": self.desafio.fase_atual.nome if self.desafio.fase_atual else "",
                "progresso": round(self.desafio.progresso_total, 3),
            }
        # ========================================

        # ========== MOTOR COLMEIA (Doutrina) ==========
        nomes_ativos = [p.nome_exibicao for p in self.personas.values() if p.ativo]
        eventos_colmeia = self.colmeia.step(self.step, nomes_ativos)
        for evento in eventos_colmeia:
            resumo_step["acoes"].append({
                "agente_id": "colmeia",
                "agente_nome": "Motor Colmeia",
                "tipo": evento["tipo"],
                "local": "campus",
                "acao": evento["mensagem"],
                "emoji": "🐝",
                "mandamento": evento.get("mandamento"),
            })
        # Persistir estado da Colmeia periodicamente
        if self.step % 10 == 0:
            caminho_colmeia = os.path.join(config.diretorio_dados, "colmeia_estado.json")
            self.colmeia.salvar(caminho_colmeia)
        # ========================================

        # Auto-save
        if self.step % config.auto_save_intervalo == 0:
            self.salvar()

        self.stats["total_steps"] = self.step

        # Log
        n_conversas = len(resumo_step["conversas"])
        if n_conversas > 0:
            self.log(
                f"Step {self.step} ({self.hora_atual.strftime('%H:%M')}): "
                f"{n_conversas} conversa(s), "
                f"{len(resumo_step['insights'])} insight(s)"
            )

        return resumo_step

    def executar(self, n_steps: int = 100, callback=None) -> list[dict]:
        """
        Executa N steps da simulação.

        Args:
            n_steps: Número de steps a executar
            callback: Função chamada a cada step com o resumo

        Returns:
            Lista de resumos de cada step
        """
        self.rodando = True
        resumos = []

        for i in range(n_steps):
            if not self.rodando or self.pausada:
                break

            resumo = self.executar_step()
            resumos.append(resumo)

            if callback:
                callback(resumo)

        self.rodando = False
        return resumos

    def pausar(self):
        """Pausa a simulação."""
        self.pausada = True

    def retomar(self):
        """Retoma a simulação."""
        self.pausada = False

    def parar(self):
        """Para a simulação."""
        self.rodando = False
        self.salvar()

    # ================================================================
    # INTERAÇÃO DO USUÁRIO
    # ================================================================

    def injetar_topico(self, topico: str, importancia: int = 8):
        """
        Injeta um tópico no campus para os agentes discutirem.

        Gatilho 1 (prioridade máxima): publica na rede social com
        comentários imediatos dos consultores mais relevantes,
        E registra como evento nos locais públicos do campus.
        """
        if topico not in config.topicos_ativos:
            config.topicos_ativos.append(topico)

        # Publicar na rede social via Motor de Gatilhos (gera comentários IA)
        self.motor_gatilhos.injetar_tema(
            titulo=topico,
            personas=self.personas,
            step=self.step,
        )

        # Anunciar nos locais públicos (para pipeline cognitivo)
        for local_id, local in LOCAIS.items():
            if local.tipo in ("publico", "trabalho"):
                for persona in self.personas.values():
                    if persona.rascunho.local_atual == local_id:
                        persona.memoria.adicionar_evento(
                            descricao=f"Novo tópico em discussão no campus: {topico}",
                            sujeito="Campus INTEIA",
                            predicado="anuncia",
                            objeto=topico,
                            local_id=local_id,
                            importancia=importancia,
                            palavras_chave=set(topico.lower().split()),
                        )

        self.log(f"Tópico injetado: '{topico}' (importância: {importancia})")

    # ================================================================
    # DESAFIO COLETIVO
    # ================================================================

    def iniciar_desafio(self, desafio_id: str = "", descricao: str = "",
                        documento: str = "", steps_por_fase: int = 100) -> dict:
        """Inicia um desafio coletivo a partir do tema do usuário."""
        tema = desafio_id  # o "id" agora é o tema livre
        if not tema:
            return {"erro": "Informe o tema do desafio"}

        desafio = criar_desafio(tema, descricao, documento)

        self.desafio = desafio
        self.desafio.iniciar(self.step)

        # Inicializar carteiras para todos os agentes
        for pid in self.personas:
            self.incentivos.obter_carteira(pid)

        # Injetar primeiro tópico do desafio
        topicos = self.desafio.gerar_topicos_fase()
        if topicos:
            self.injetar_topico(topicos[0], importancia=10)

        self.log(f"Desafio iniciado: {desafio.icone} {desafio.nome}")

        return {
            "status": "ok",
            "desafio": self.desafio.to_dict(),
            "mensagem": f"Desafio '{desafio.nome}' iniciado na fase '{desafio.fases[0].nome}'",
        }

    def contribuir_desafio(self, agente_id: str, conteudo: str, tipo: str = "proposta") -> dict:
        """Registra contribuição manual de um agente ao desafio."""
        if not self.desafio.ativo:
            return {"erro": "Nenhum desafio ativo"}

        persona = self.personas.get(agente_id)
        nome = persona.nome_exibicao if persona else agente_id

        contrib = Contribuicao(
            agente_id=agente_id,
            agente_nome=nome,
            conteudo=conteudo,
            tipo=tipo,
        )
        self.desafio.registrar_contribuicao(contrib, self.step)
        self.incentivos.recompensar(agente_id, "proposta_nova", self.step, conteudo[:100])
        self.incentivos.registrar_atividade(agente_id, self.step)

        return {"status": "ok", "contribuicao": contrib.to_dict()}

    def votar_desafio(self, agente_id: str, entrega_id: str, favor: bool) -> dict:
        """Registra voto de um agente em uma entrega."""
        if not self.desafio.ativo:
            return {"erro": "Nenhum desafio ativo"}

        self.desafio.registrar_voto(agente_id, entrega_id, favor)
        self.incentivos.recompensar(agente_id, "voto_registrado", self.step)
        self.incentivos.registrar_atividade(agente_id, self.step)

        return {"status": "ok", "voto": "favor" if favor else "contra"}

    def consultar_agente(self, agente_id: str) -> dict | None:
        """Retorna estado detalhado de um agente."""
        persona = self.personas.get(agente_id)
        if not persona:
            return None

        return {
            **persona.resumo(),
            "memoria_resumo": persona.memoria.resumo(),
            "locais_favoritos": persona.memoria_espacial.locais_favoritos(3),
            "plano_diario": persona.rascunho.to_dict().get("plano_diario", []),
            "dados_consultor": {
                "titulo": persona.titulo,
                "subtitulo": persona.subtitulo,
                "categoria": persona.categoria,
                "tier": persona.tier,
                "personalidade": persona.rascunho.personalidade_resumo,
                "expertise": persona.rascunho.areas_expertise,
                "frase_chave": persona.rascunho.frase_chave,
            },
        }

    # ================================================================
    # ESTADO DO MUNDO
    # ================================================================

    def estado_mundo(self) -> dict:
        """Retorna snapshot do estado atual de toda a simulação."""
        with self._step_lock:
            return self._estado_mundo_interno()

    def _estado_mundo_interno(self) -> dict:
        """Snapshot real (protegido por lock)."""
        # Contar agentes por local
        agentes_por_local: dict[str, list[dict]] = {}
        for persona in self.personas.values():
            local = persona.rascunho.local_atual
            if local not in agentes_por_local:
                agentes_por_local[local] = []
            agentes_por_local[local].append({
                "id": persona.id,
                "nome": persona.nome_exibicao,
                "emoji": persona.rascunho.acao.emoji,
                "acao": persona.rascunho.acao.descricao,
                "categoria": persona.categoria,
                "tier": persona.tier,
            })

        # Montar estado dos locais
        locais_estado = []
        for local_id, local in LOCAIS.items():
            agentes = agentes_por_local.get(local_id, [])
            locais_estado.append({
                "id": local.id,
                "nome": local.nome,
                "tipo": local.tipo,
                "descricao": local.descricao[:100],
                "capacidade": local.capacidade,
                "ocupacao": len(agentes),
                "agentes": agentes,
                "posicao_x": local.posicao_x,
                "posicao_y": local.posicao_y,
            })

        return {
            "simulacao": self.nome,
            "step": self.step,
            "hora": self.hora_atual.strftime("%Y-%m-%d %H:%M"),
            "hora_formatada": self.hora_atual.strftime("%H:%M"),
            "data_formatada": self.hora_atual.strftime("%d/%m/%Y"),
            "rodando": self.rodando,
            "pausada": self.pausada,
            "total_agentes": len(self.personas),
            "agentes_ativos": sum(1 for p in self.personas.values() if p.ativo),
            "locais": locais_estado,
            "conversas_recentes": self.conversas_recentes[-10:],
            "topicos_ativos": config.topicos_ativos,
            "stats": self.stats,
            "rede_social": {
                "total_posts": self.rede_social.total_posts,
                "total_comentarios": self.rede_social.total_comentarios,
                "total_reacoes": self.rede_social.total_reacoes,
                "trending": self.rede_social.trending_tags(5),
                "posts_hoje": self.motor_gatilhos.posts_hoje,
                "waves_pendentes": len(self.motor_gatilhos.fila_waves),
            },
            "desafio": self.desafio.to_dict() if self.desafio.ativo else None,
            "economia": self.incentivos.to_dict(),
            "ferramentas": self.toolkit.to_dict(),
            "oficinas": todas_oficinas(),
            "workspace": self.workspace.to_dict(
                self.desafio.id if self.desafio.ativo else ""
            ),
        }

    def mapa_calor(self) -> dict[str, int]:
        """Retorna ocupação de cada local (para heatmap)."""
        mapa = {}
        for local_id in LOCAIS:
            mapa[local_id] = sum(
                1 for p in self.personas.values()
                if p.rascunho.local_atual == local_id
            )
        return mapa

    # ================================================================
    # PERSISTÊNCIA
    # ================================================================

    def salvar(self):
        """Salva estado completo da simulação."""
        os.makedirs(self.dir_dados, exist_ok=True)

        # Meta da simulação
        meta = {
            "nome": self.nome,
            "step": self.step,
            "hora_atual": self.hora_atual.isoformat(),
            "total_agentes": len(self.personas),
            "stats": self.stats,
            "topicos_ativos": config.topicos_ativos,
        }
        with open(os.path.join(self.dir_dados, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # Salvar cada persona
        dir_personas = os.path.join(self.dir_dados, "personas")
        os.makedirs(dir_personas, exist_ok=True)
        for persona in self.personas.values():
            persona.salvar(dir_personas)

        # Salvar sinteses
        if self.sinteses:
            with open(
                os.path.join(self.dir_dados, "sinteses.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(self.sinteses, f, ensure_ascii=False, indent=2)

        # Salvar rede social
        self.rede_social.salvar(os.path.join(self.dir_dados, "rede_social.json"))

        # Salvar desafio e incentivos
        if self.desafio.ativo or self.desafio.status == "concluido":
            self.desafio.salvar(os.path.join(self.dir_dados, "desafio.json"))
        self.incentivos.salvar(os.path.join(self.dir_dados, "incentivos.json"))

        self.log(f"Simulação salva em {self.dir_dados}")

    def carregar(self) -> bool:
        """Carrega estado completo: meta + desafio + incentivos."""
        meta_path = os.path.join(self.dir_dados, "meta.json")
        if not os.path.exists(meta_path):
            return False

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.step = meta.get("step", 0)
        self.hora_atual = datetime.fromisoformat(meta["hora_atual"])
        self.stats = meta.get("stats", self.stats)
        config.topicos_ativos = meta.get("topicos_ativos", [])

        # Carregar desafio
        desafio_path = os.path.join(self.dir_dados, "desafio.json")
        desafio_carregado = DesafioColetivo.carregar(desafio_path)
        if desafio_carregado:
            self.desafio = desafio_carregado
            self.log(f"Desafio carregado: {self.desafio.nome} (fase {self.desafio.fase_atual_idx})")

        # Carregar incentivos
        incentivos_path = os.path.join(self.dir_dados, "incentivos.json")
        self.incentivos.carregar(incentivos_path)

        self.log(f"Simulação carregada: step {self.step}")
        return True

    # ================================================================
    # LOG
    # ================================================================

    def log(self, mensagem: str):
        """Registra evento no log."""
        evento = {
            "step": self.step,
            "hora": self.hora_atual.isoformat(),
            "mensagem": mensagem,
        }
        self.log_eventos.append(evento)
        if len(self.log_eventos) > self._MAX_LOG:
            self.log_eventos = self.log_eventos[-self._MAX_LOG:]

        if config.modo_debug:
            print(f"[Vila INTEIA Step {self.step}] {mensagem}")

    def __repr__(self) -> str:
        return (
            f"SimulacaoVila('{self.nome}', "
            f"step={self.step}, "
            f"agentes={len(self.personas)}, "
            f"hora={self.hora_atual.strftime('%H:%M')})"
        )
