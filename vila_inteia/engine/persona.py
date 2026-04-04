"""
Persona - Agente inteligente na Vila INTEIA.

Cada Persona wrappa um Consultor Lendário com:
- Sistema de memória (fluxo + espacial + rascunho)
- Pipeline cognitivo (perceber → recuperar → planejar → refletir → executar → conversar)
- Identidade rica (100 atributos do consultor)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .memoria import FluxoMemoria, MemoriaEspacial, Rascunho
from .campus import residencia_para_categoria


@dataclass
class Persona:
    """
    Um agente vivo na Vila INTEIA.

    Combina os dados do consultor lendário com um sistema cognitivo completo.
    """

    # Identidade (do consultor lendário)
    id: str = ""
    numero: int = 0
    nome: str = ""
    nome_exibicao: str = ""
    titulo: str = ""
    subtitulo: str = ""
    categoria: str = ""
    tier: str = "A"
    status_vida: str = "vivo"

    # Dados completos do consultor (referência)
    dados_consultor: dict = field(default_factory=dict)

    # Sistemas de memória
    memoria: FluxoMemoria = field(default_factory=FluxoMemoria)
    memoria_espacial: MemoriaEspacial = field(default_factory=MemoriaEspacial)
    rascunho: Rascunho = field(default_factory=Rascunho)

    # Estado de simulação
    ativo: bool = True
    step_atual: int = 0

    def __post_init__(self):
        """Inicializa a persona com dados do consultor."""
        if self.dados_consultor and not self.rascunho.nome:
            self._carregar_identidade()

    def _carregar_identidade(self):
        """Extrai identidade do consultor para o rascunho."""
        d = self.dados_consultor

        # Identidade básica
        self.id = d.get("id", self.id)
        self.numero = d.get("numero_lista", self.numero)
        self.nome = d.get("nome", self.nome)
        self.nome_exibicao = d.get("nome_exibicao", self.nome)
        self.titulo = d.get("titulo", self.titulo)
        self.subtitulo = d.get("subtitulo", "")
        self.categoria = d.get("categoria", self.categoria)
        self.tier = d.get("tier", "A")
        self.status_vida = d.get("status_vida", "vivo")

        # Preencher rascunho
        r = self.rascunho
        r.nome = self.nome_exibicao
        r.titulo = self.titulo
        r.categoria = self.categoria
        r.personalidade_resumo = d.get("personalidade_resumo", "")
        r.estilo_comunicacao = d.get("estilo_comunicacao", "")
        r.tom_voz = d.get("tom_voz", "")
        r.frase_chave = d.get("frase_chave", "")

        # Expertise
        expertise = d.get("areas_expertise", [])
        if isinstance(expertise, str):
            expertise = [e.strip() for e in expertise.split(",")]
        r.areas_expertise = expertise

        # Hiperparâmetros cognitivos (níveis 1-10)
        r.nivel_agressividade = d.get("nivel_agressividade", 5)
        r.nivel_empatia = d.get("nivel_empatia", 5)
        r.nivel_carisma = d.get("nivel_carisma", 5)
        r.nivel_extroversao = d.get("nivel_extroversao", 5)
        r.tolerancia_risco = d.get("tolerancia_risco", 5)
        r.nivel_formalidade = d.get("nivel_formalidade", 5)

        # Relacionamentos
        r.mentores = self._parse_lista(d.get("mentores", []))
        r.rivais = self._parse_lista(d.get("rivais", []))
        r.influenciou = self._parse_lista(d.get("influenciou", []))
        r.influenciado_por = self._parse_lista(d.get("influenciado_por", []))

        # Tópicos de interesse baseados em expertise + categoria
        r.topicos_interesse = expertise[:5]

        # Local inicial = residência baseada na categoria
        r.local_atual = residencia_para_categoria(self.categoria)

    def _parse_lista(self, valor: Any) -> list[str]:
        """Converte valor para lista de strings."""
        if isinstance(valor, list):
            return [str(v) for v in valor]
        if isinstance(valor, str):
            return [v.strip() for v in valor.split(",") if v.strip()]
        return []

    # ================================================================
    # INTERFACE PÚBLICA
    # ================================================================

    def mover(
        self,
        mundo: Any,  # referência ao Mundo
        personas: dict[str, "Persona"],
        hora_atual: datetime,
    ) -> dict:
        """
        Executa um ciclo cognitivo completo.

        Retorna um dict com a ação tomada:
        {
            "tipo": "mover"|"conversar"|"refletir",
            "local_destino": str,
            "acao": str,
            "emoji": str,
            "conversa": Optional[dict],
        }
        """
        from .cognitivo import (
            perceber, recuperar, planejar,
            refletir, executar, conversar,
        )

        resultado = {
            "tipo": "mover",
            "local_destino": self.rascunho.local_atual,
            "acao": self.rascunho.acao.descricao,
            "emoji": self.rascunho.acao.emoji,
            "conversa": None,
        }

        # 1. PERCEBER - O que está acontecendo ao redor?
        percepcoes = perceber(self, mundo, personas, hora_atual)

        # 2. RECUPERAR - O que sei sobre isso?
        contexto = recuperar(self, percepcoes, hora_atual)

        # 3. REFLETIR - Preciso pensar sobre algo?
        if self.memoria.deve_refletir():
            insights = refletir(self, hora_atual)
            resultado["tipo"] = "refletir"

        # 4. CONVERSAR - Devo falar com alguém?
        conversa_resultado = conversar(self, percepcoes, contexto, mundo, hora_atual)
        if conversa_resultado:
            resultado["tipo"] = "conversar"
            resultado["conversa"] = conversa_resultado

        # 5. PLANEJAR - O que fazer a seguir?
        if not self.rascunho.esta_conversando:
            plano = planejar(self, contexto, hora_atual)

        # 6. EXECUTAR - Agir
        acao = executar(self, hora_atual)
        resultado["local_destino"] = acao.get("local_id", self.rascunho.local_atual)
        resultado["acao"] = acao.get("descricao", "observando")
        resultado["emoji"] = acao.get("emoji", "👀")

        self.step_atual += 1
        return resultado

    def gerar_prompt_sistema(self) -> str:
        """Gera o system prompt completo para esta persona."""
        d = self.dados_consultor

        # Instrução comportamental do consultor (se existir)
        instrucao = d.get("instrucao_comportamental", "")

        # Biografia
        bio = d.get("biografia_resumida", "")

        # Valores e visões
        valores = d.get("valores_fundamentais", "")
        if isinstance(valores, list):
            valores = ", ".join(valores)

        visao_poder = d.get("visao_poder", "")
        visao_futuro = d.get("visao_futuro", "")

        # Estilo de decisão
        est_decisao = d.get("estilo_decisao_primario", "")
        est_lideranca = d.get("estilo_lideranca", "")
        est_argumentacao = d.get("estilo_argumentacao", "")

        # Frameworks mentais
        frameworks = d.get("frameworks_mentais", "")
        if isinstance(frameworks, list):
            frameworks = ", ".join(frameworks)

        # Expressões típicas
        expressoes = d.get("expressoes_tipicas", "")
        if isinstance(expressoes, list):
            expressoes = "; ".join(expressoes)

        prompt = f"""Você é {self.nome_exibicao}, "{self.titulo}".
{instrucao}

BIOGRAFIA: {bio}

PERSONALIDADE: {self.rascunho.personalidade_resumo}
TOM DE VOZ: {self.rascunho.tom_voz}
ESTILO: {self.rascunho.estilo_comunicacao}

VALORES: {valores}
VISÃO DE PODER: {visao_poder}
VISÃO DE FUTURO: {visao_futuro}

ESTILO DE DECISÃO: {est_decisao}
ESTILO DE LIDERANÇA: {est_lideranca}
ARGUMENTAÇÃO: {est_argumentacao}

FRAMEWORKS MENTAIS: {frameworks}
EXPRESSÕES TÍPICAS: {expressoes}

FRASE MARCANTE: "{self.rascunho.frase_chave}"

CONTEXTO ATUAL:
{self.rascunho.contexto_para_prompt()}

REGRAS:
- Você está em uma simulação social num campus de think tank chamado Vila INTEIA
- Aja EXATAMENTE como {self.nome_exibicao} agiria
- Use o tom de voz, expressões e estilo descritos
- Mantenha a personalidade consistente
- Responda sempre em português do Brasil
- Seja autêntico à personalidade descrita, não genérico"""

        return prompt

    def decidir_interacao(self, outro: "Persona") -> float:
        """
        Calcula a probabilidade (0-1) de querer interagir com outro agente.

        Fatores:
        - É mentor/rival/influenciado? → alta probabilidade
        - Extroversão do agente
        - Afinidade de categorias
        - Energia disponível
        """
        prob = 0.3  # base

        outro_nome = outro.nome_exibicao

        # Relacionamentos especiais (boost forte)
        if outro_nome in self.rascunho.mentores:
            prob += 0.4
        if outro_nome in self.rascunho.rivais:
            prob += 0.35  # rivais também geram interação
        if outro_nome in self.rascunho.influenciou:
            prob += 0.25
        if outro_nome in self.rascunho.influenciado_por:
            prob += 0.3

        # Extroversão (1-10 → 0-0.2)
        prob += self.rascunho.nivel_extroversao * 0.02

        # Afinidade de categoria
        if self.categoria == outro.categoria:
            prob += 0.15

        # Energia
        if self.rascunho.energia < 30:
            prob *= 0.5

        return min(prob, 0.95)

    # ================================================================
    # PERSISTÊNCIA
    # ================================================================

    def salvar(self, diretorio: str):
        """Salva o estado completo da persona."""
        pasta = os.path.join(diretorio, self.id)
        os.makedirs(pasta, exist_ok=True)

        # Memória associativa
        self.memoria.salvar(os.path.join(pasta, "memoria_fluxo.json"))

        # Memória espacial
        with open(os.path.join(pasta, "memoria_espacial.json"), "w", encoding="utf-8") as f:
            json.dump(self.memoria_espacial.to_dict(), f, ensure_ascii=False, indent=2)

        # Rascunho
        with open(os.path.join(pasta, "rascunho.json"), "w", encoding="utf-8") as f:
            json.dump(self.rascunho.to_dict(), f, ensure_ascii=False, indent=2)

        # Metadados
        meta = {
            "id": self.id,
            "numero": self.numero,
            "nome": self.nome,
            "nome_exibicao": self.nome_exibicao,
            "categoria": self.categoria,
            "tier": self.tier,
            "step_atual": self.step_atual,
            "ativo": self.ativo,
        }
        with open(os.path.join(pasta, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    @classmethod
    def carregar(cls, diretorio: str, dados_consultor: dict) -> "Persona":
        """Carrega uma persona de arquivos salvos."""
        persona = cls(dados_consultor=dados_consultor)

        pasta = os.path.join(diretorio, persona.id)
        if not os.path.exists(pasta):
            return persona

        # Carregar memória
        fluxo_path = os.path.join(pasta, "memoria_fluxo.json")
        if os.path.exists(fluxo_path):
            persona.memoria = FluxoMemoria.carregar(fluxo_path)

        # Carregar meta
        meta_path = os.path.join(pasta, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            persona.step_atual = meta.get("step_atual", 0)
            persona.ativo = meta.get("ativo", True)

        return persona

    def resumo(self) -> dict:
        """Retorna resumo público da persona (para visualização)."""
        return {
            "id": self.id,
            "numero": self.numero,
            "nome": self.nome_exibicao,
            "titulo": self.titulo,
            "categoria": self.categoria,
            "tier": self.tier,
            "status_vida": self.status_vida,
            "local_atual": self.rascunho.local_atual,
            "acao": self.rascunho.acao.descricao,
            "emoji": self.rascunho.acao.emoji,
            "humor": self.rascunho.humor,
            "energia": self.rascunho.energia,
            "conversando_com": self.rascunho.conversando_com,
            "memoria_total": self.memoria.total,
            "step": self.step_atual,
        }

    def __repr__(self) -> str:
        return (
            f"Persona({self.nome_exibicao!r}, "
            f"cat={self.categoria!r}, "
            f"local={self.rascunho.local_atual!r}, "
            f"acao={self.rascunho.acao.emoji} {self.rascunho.acao.descricao!r})"
        )


def criar_persona_de_consultor(dados: dict) -> Persona:
    """Factory: cria uma Persona a partir dos dados de um consultor lendário."""
    return Persona(dados_consultor=dados)


def carregar_todas_personas(caminho_json: str) -> list[Persona]:
    """Carrega todas as personas do JSON de consultores lendários."""
    with open(caminho_json, "r", encoding="utf-8") as f:
        consultores = json.load(f)

    personas = []
    for dados in consultores:
        if dados.get("ativo", True):
            persona = criar_persona_de_consultor(dados)
            personas.append(persona)

    return personas
