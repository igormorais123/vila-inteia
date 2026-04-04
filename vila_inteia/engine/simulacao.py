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
from ..config import config


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

        # Estado da simulação
        self.personas: dict[str, Persona] = {}
        self.step: int = 0
        self.hora_atual: datetime = datetime.now()
        self.rodando: bool = False
        self.pausada: bool = False

        # Rede Social e Motor de Gatilhos
        self.rede_social = RedeSocial()
        self.motor_gatilhos = MotorGatilhos(self.rede_social)

        # Logs e eventos
        self.log_eventos: list[dict] = []
        self.conversas_recentes: list[dict] = []
        self.insights_coletivos: list[dict] = []
        self.sinteses: list[dict] = []

        # Estatísticas
        self.stats = {
            "total_steps": 0,
            "total_conversas": 0,
            "total_reflexoes": 0,
            "total_movimentos": 0,
            "total_sinteses": 0,
        }

        # Diretório de dados
        self.dir_dados = os.path.join(config.diretorio_dados, nome)

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

        if max_agentes:
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
        self.step += 1
        resumo_step = {
            "step": self.step,
            "hora": self.hora_atual.strftime("%Y-%m-%d %H:%M"),
            "acoes": [],
            "conversas": [],
            "insights": [],
            "movimentos": 0,
        }

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
        # Executa todos os 6 gatilhos: debates rivais, Diabob, Jesus,
        # Helena moderadora, posts espontâneos, waves de comentários
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
                    resumo_step["insights"].append(sintese)
                    self.stats["total_sinteses"] += 1

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

        self.log(f"Simulação salva em {self.dir_dados}")

    def carregar(self) -> bool:
        """Carrega estado salvo da simulação."""
        meta_path = os.path.join(self.dir_dados, "meta.json")
        if not os.path.exists(meta_path):
            return False

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.step = meta.get("step", 0)
        self.hora_atual = datetime.fromisoformat(meta["hora_atual"])
        self.stats = meta.get("stats", self.stats)
        config.topicos_ativos = meta.get("topicos_ativos", [])

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

        if config.modo_debug:
            print(f"[Vila INTEIA Step {self.step}] {mensagem}")

    def __repr__(self) -> str:
        return (
            f"SimulacaoVila('{self.nome}', "
            f"step={self.step}, "
            f"agentes={len(self.personas)}, "
            f"hora={self.hora_atual.strftime('%H:%M')})"
        )
