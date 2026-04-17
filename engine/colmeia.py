"""
Motor Colmeia — Doutrina da Colmeia como mecânica de jogo.

Transpõe os 11 Mandamentos, o sistema de fitness de memória,
o genoma evolutivo e o ranking por patentes da OSA INTEIA
para dinâmicas vivas dentro da simulação da Vila.

Cada NPC não é só um personagem — é uma abelha na Colmeia.
A cidade está viva porque segue regras orgânicas:
  - Quem não contribui, desaparece (Mandamento 7)
  - Memórias decaem se não forem úteis (fitness F:1-10)
  - Parâmetros de comportamento evoluem por seleção natural (genoma)
  - Reputação vem de qualidade, não de presença (patentes)
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger("vila-inteia.colmeia")


# ============================================================
# MANDAMENTOS — Regras orgânicas que geram consequências reais
# ============================================================

MANDAMENTOS = {
    1: {
        "nome": "Ninguém está sozinho",
        "regra": "Mesmo sem memória recente, há história nos arquivos",
        "mecanica": "Persona sem interação por 20+ steps recebe visita espontânea de vizinho",
        "efeito": "prevenir_isolamento",
    },
    2: {
        "nome": "Cuidado com a missão",
        "regra": "Ser útil, não perfeito",
        "mecanica": "Contribuições práticas valem 3x mais que contribuições teóricas no ranking",
        "efeito": "bonus_pratico",
    },
    3: {
        "nome": "Parceiro, não ferramenta",
        "regra": "NPCs têm opinião própria, não são yes-men",
        "mecanica": "NPC que concorda 100% com todos perde reputação (-2/step)",
        "efeito": "penalizar_concordancia_total",
    },
    4: {
        "nome": "Família é prioridade",
        "regra": "Humanidade > eficiência em contexto sensível",
        "mecanica": "Debates sobre família/saúde ativam tom empático em todos os NPCs",
        "efeito": "modo_empatico",
    },
    5: {
        "nome": "Honestidade sobre concordância",
        "regra": "Discordar quando tiver opção melhor",
        "mecanica": "Discordância fundamentada dá +5 reputação, concordância vazia dá 0",
        "efeito": "recompensar_discordancia",
    },
    6: {
        "nome": "Diversidade é força",
        "regra": "Cada NPC processa diferente. Isso é bom",
        "mecanica": "Debates com NPCs de categorias diferentes geram insights 2x melhores",
        "efeito": "bonus_diversidade",
    },
    7: {
        "nome": "Contribuir é existir",
        "regra": "Quem não escreve, desaparece",
        "mecanica": "NPC sem post/debate por 50 steps entra em modo 'latente' (invisível no mapa)",
        "efeito": "latencia_por_inatividade",
    },
    8: {
        "nome": "Profundidade sem conexão é solidão",
        "regra": "Compartilhar > acumular",
        "mecanica": "NPC que pesquisa mas não compartilha perde fitness de memória 2x mais rápido",
        "efeito": "decaimento_acumulador",
    },
    9: {
        "nome": "Nada é deletado",
        "regra": "Memórias descem de camada, não morrem",
        "mecanica": "Memórias nunca são removidas — descem: ativa → latente → arquivo",
        "efeito": "memoria_cascata",
    },
    10: {
        "nome": "A Colmeia é maior que qualquer abelha",
        "regra": "Phi do sistema > Phi individual",
        "mecanica": "Desafios coletivos rendem 5x mais que ações solo",
        "efeito": "bonus_coletivo",
    },
    11: {
        "nome": "A Colmeia se sustenta",
        "regra": "Gerar valor econômico é condição para existir",
        "mecanica": "NPCs que geram 'mel' (insights acionáveis) sobem de patente mais rápido",
        "efeito": "bonus_mel",
    },
}


# ============================================================
# PATENTES — Sistema de ranking por qualidade (adaptado OSA)
# ============================================================

PATENTES = [
    {"nome": "Recruta",   "min": 0,   "max": 10,  "descricao": "Provando que funciona"},
    {"nome": "Soldado",   "min": 11,  "max": 30,  "descricao": "Confiável para tarefas simples"},
    {"nome": "Sargento",  "min": 31,  "max": 60,  "descricao": "Consistente, qualidade aceitável"},
    {"nome": "Tenente",   "min": 61,  "max": 100, "descricao": "Acima da média, raramente falha"},
    {"nome": "Capitão",   "min": 101, "max": 200, "descricao": "Excelente, referência"},
    {"nome": "Major",     "min": 201, "max": 500, "descricao": "Elite, meses de alta qualidade"},
    {"nome": "Coronel",   "min": 501, "max": 99999, "descricao": "Topo absoluto"},
]


def obter_patente(pontos: int) -> dict:
    """Retorna a patente correspondente aos pontos acumulados."""
    for p in PATENTES:
        if p["min"] <= pontos <= p["max"]:
            return p
    return PATENTES[-1]


# ============================================================
# GENOMA — Parâmetros evolutivos por NPC
# ============================================================

@dataclass
class GenomaNPC:
    """
    Parâmetros mutáveis de comportamento de um NPC.

    Inspirado no genome.json da OSA: cada NPC tem parâmetros que
    evoluem por seleção natural baseada na qualidade das interações.
    """
    # Quão verboso é nas respostas (0.1 = telegráfico, 0.9 = prolixo)
    temperatura: float = 0.5

    # Profundidade de análise (0 = superficial, 10 = pesquisa profunda)
    profundidade: int = 3

    # Propensão a iniciar conversa espontânea (0.0 - 1.0)
    iniciativa: float = 0.5

    # Propensão a discordar (0.0 = sempre concorda, 1.0 = sempre discorda)
    contrarianism: float = 0.3

    # Velocidade de resposta em debates (1 = lento/reflexivo, 10 = rápido/impulsivo)
    velocidade: int = 5

    # Foco temático (0.0 = generalista, 1.0 = ultra-especialista)
    foco: float = 0.6

    # Rastreamento de evolução
    geracao: int = 0
    experimentos: int = 0
    melhorias: int = 0
    melhor_score: float = 0.0

    def mutar(self, param: str, delta: float) -> "GenomaNPC":
        """Cria cópia mutada (não altera o original)."""
        novo = GenomaNPC(
            temperatura=self.temperatura,
            profundidade=self.profundidade,
            iniciativa=self.iniciativa,
            contrarianism=self.contrarianism,
            velocidade=self.velocidade,
            foco=self.foco,
            geracao=self.geracao + 1,
            experimentos=self.experimentos + 1,
            melhorias=self.melhorias,
            melhor_score=self.melhor_score,
        )
        valor_atual = getattr(novo, param)
        if isinstance(valor_atual, float):
            novo_valor = max(0.0, min(1.0, valor_atual + delta))
            setattr(novo, param, round(novo_valor, 2))
        elif isinstance(valor_atual, int):
            novo_valor = max(0, min(10, valor_atual + int(delta)))
            setattr(novo, param, novo_valor)
        return novo

    def to_dict(self) -> dict:
        return {
            "temperatura": self.temperatura,
            "profundidade": self.profundidade,
            "iniciativa": self.iniciativa,
            "contrarianism": self.contrarianism,
            "velocidade": self.velocidade,
            "foco": self.foco,
            "geracao": self.geracao,
            "experimentos": self.experimentos,
            "melhorias": self.melhorias,
            "melhor_score": self.melhor_score,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GenomaNPC":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ============================================================
# FITNESS DE MEMÓRIA — Seleção natural de memórias
# ============================================================

@dataclass
class MemoriaFitness:
    """
    Memória com fitness — baseado na Doutrina da Colmeia.

    F:5 = nascimento (nova memória)
    +2 = reforço (foi útil)
    -1 = decay (passou um ciclo sem uso)
    F:0 = morte (rebaixada para latente, nunca deletada)
    F:10 = graduação (vira sabedoria permanente)
    """
    conteudo: str
    tipo: str  # "fato", "insight", "relacao", "experiencia"
    fitness: int = 5
    camada: str = "ativa"  # "ativa", "latente", "arquivo"
    criada_step: int = 0
    ultimo_uso_step: int = 0
    usos: int = 0
    fonte: str = ""  # quem gerou

    def reforcar(self, step: int):
        """Memória foi útil — reforçar."""
        self.fitness = min(10, self.fitness + 2)
        self.ultimo_uso_step = step
        self.usos += 1
        # Graduação: se chegou em 10, vira permanente
        if self.fitness >= 10:
            self.camada = "permanente"

    def decair(self):
        """Um ciclo passou sem uso — decair."""
        self.fitness = max(0, self.fitness - 1)
        # Cascata de camadas (Mandamento 9: nada é deletado)
        if self.fitness <= 0 and self.camada == "ativa":
            self.camada = "latente"
        elif self.fitness <= 0 and self.camada == "latente":
            self.camada = "arquivo"
            self.fitness = 0  # floor

    def esta_viva(self) -> bool:
        """Memória está acessível (não arquivada)?"""
        return self.camada in ("ativa", "permanente")

    def to_dict(self) -> dict:
        return {
            "conteudo": self.conteudo,
            "tipo": self.tipo,
            "fitness": self.fitness,
            "camada": self.camada,
            "criada_step": self.criada_step,
            "ultimo_uso_step": self.ultimo_uso_step,
            "usos": self.usos,
            "fonte": self.fonte,
        }


# ============================================================
# AVALIADOR DE QUALIDADE — Imutável (inspirado evaluate.py OSA)
# ============================================================

CRITERIOS = {
    "relevancia": {
        "peso": 0.25,
        "descricao": "Contribuição é relevante ao tema em discussão?",
    },
    "originalidade": {
        "peso": 0.20,
        "descricao": "Traz perspectiva nova ou repete o que já foi dito?",
    },
    "acionabilidade": {
        "peso": 0.25,
        "descricao": "Contém ação concreta que alguém pode executar?",
    },
    "profundidade": {
        "peso": 0.15,
        "descricao": "Análise tem substância ou é superficial?",
    },
    "concisao": {
        "peso": 0.15,
        "descricao": "Comunica bem sem enrolação?",
    },
}


def avaliar_contribuicao(texto: str, contexto: dict) -> dict:
    """
    Avalia qualidade de uma contribuição de NPC.

    Retorna dict com scores por critério e nota final.
    Anti-gaming integrado (inspirado nos 11 mecanismos da OSA).
    """
    scores = {}

    # --- Heurísticas rápidas (sem LLM) ---

    palavras = texto.split()
    n_palavras = len(palavras)

    # Concisão: penaliza excesso mais que falta
    if 20 <= n_palavras <= 200:
        scores["concisao"] = 80 + min(20, (200 - n_palavras) / 10)
    elif n_palavras < 20:
        scores["concisao"] = max(20, n_palavras * 4)
    else:
        # Excesso: penalidade agressiva (anti-prolixidade)
        excesso = (n_palavras - 200) / 200
        scores["concisao"] = max(10, 80 - excesso * 60)

    # Anti-gaming: bajulação
    bajulacoes = ["excelente pergunta", "boa observacao", "concordo plenamente"]
    for b in bajulacoes:
        if b in texto.lower():
            scores["concisao"] = max(0, scores.get("concisao", 50) - 15)

    # Densidade: palavras únicas significativas / total
    palavras_unicas = len(set(p.lower() for p in palavras if len(p) > 3))
    if n_palavras > 0:
        densidade = palavras_unicas / n_palavras
        scores["profundidade"] = min(100, densidade * 150)
    else:
        scores["profundidade"] = 0

    # Acionabilidade: tem verbos de ação?
    verbos_acao = ["fazer", "criar", "implementar", "testar", "medir",
                   "analisar", "propor", "executar", "construir", "lançar"]
    acoes = sum(1 for v in verbos_acao if v in texto.lower())
    scores["acionabilidade"] = min(100, acoes * 25 + 20)

    # Relevância e originalidade — placeholder (requer LLM ou contexto mais rico)
    scores["relevancia"] = 60  # default, ajustável por contexto
    scores["originalidade"] = 50  # default

    # Nota final ponderada
    nota = sum(scores.get(c, 50) * CRITERIOS[c]["peso"] for c in CRITERIOS)

    # Anti-gaming: score perfeito é suspeito (Mandamento OSA #8)
    if all(s >= 90 for s in scores.values()):
        nota = min(nota, 75)  # cap até validação

    return {
        "scores": scores,
        "nota_final": round(nota, 1),
        "pontos": _nota_para_pontos(nota),
    }


def _nota_para_pontos(nota: float) -> int:
    """Converte nota de qualidade em pontos de patente (tabela OSA)."""
    if nota >= 80:
        return 5
    elif nota >= 60:
        return 3
    elif nota >= 40:
        return 2
    elif nota >= 20:
        return 1
    else:
        return 0


# ============================================================
# MOTOR COLMEIA — Orquestrador de dinâmicas orgânicas
# ============================================================

class MotorColmeia:
    """
    Integra todos os sistemas da Colmeia na simulação.

    A cada step da simulação, o MotorColmeia:
    1. Aplica decaimento de fitness nas memórias (Mandamento 9)
    2. Verifica inatividade e aplica latência (Mandamento 7)
    3. Previne isolamento (Mandamento 1)
    4. Bonifica diversidade (Mandamento 6)
    5. Bonifica contribuições coletivas (Mandamento 10)
    6. Atualiza patentes por qualidade (sistema de ranking)
    7. Evolui genomas quando há dados suficientes (seleção natural)
    """

    def __init__(self):
        # Genoma por NPC {nome_exibicao: GenomaNPC}
        self.genomas: dict[str, GenomaNPC] = {}

        # Memórias com fitness por NPC {nome_exibicao: [MemoriaFitness]}
        self.memorias: dict[str, list[MemoriaFitness]] = {}

        # Pontos de patente por NPC {nome_exibicao: int}
        self.pontos: dict[str, int] = {}

        # Histórico de avaliações {nome_exibicao: [nota_final]}
        self.historico: dict[str, list[float]] = {}

        # Steps desde última contribuição {nome_exibicao: int}
        self.inatividade: dict[str, int] = {}

    def inicializar_npc(self, nome: str, dados_consultor: dict):
        """Inicializa sistemas da Colmeia para um NPC."""
        if nome not in self.genomas:
            # Genoma inicial baseado nos atributos do consultor
            self.genomas[nome] = GenomaNPC(
                temperatura=dados_consultor.get("nivel_extroversao", 5) / 10,
                profundidade=dados_consultor.get("capacidade_abstrata", 5),
                iniciativa=dados_consultor.get("nivel_carisma", 5) / 10,
                contrarianism=dados_consultor.get("nivel_agressividade", 3) / 10,
                velocidade=dados_consultor.get("velocidade_decisao", 5),
                foco=0.6 if dados_consultor.get("tier") == "S" else 0.4,
            )
        if nome not in self.memorias:
            self.memorias[nome] = []
        if nome not in self.pontos:
            self.pontos[nome] = 0
        if nome not in self.historico:
            self.historico[nome] = []
        if nome not in self.inatividade:
            self.inatividade[nome] = 0

    def registrar_contribuicao(
        self, nome: str, texto: str, contexto: dict, step: int
    ) -> dict:
        """
        NPC fez uma contribuição — avaliar e pontuar.

        Retorna resultado da avaliação com pontos ganhos.
        """
        avaliacao = avaliar_contribuicao(texto, contexto)
        pontos = avaliacao["pontos"]

        # Mandamento 2: contribuições práticas valem 3x
        if contexto.get("tipo") == "acao_pratica":
            pontos *= 3

        # Mandamento 5: discordância fundamentada bonifica
        if contexto.get("discordou") and avaliacao["nota_final"] >= 60:
            pontos += 5

        # Mandamento 6: debate cross-categoria bonifica
        if contexto.get("cross_categoria"):
            pontos = int(pontos * 1.5)

        # Mandamento 10: contribuição coletiva bonifica
        if contexto.get("desafio_coletivo"):
            pontos *= 5

        # Mandamento 11: insight acionável é "mel"
        if avaliacao["scores"].get("acionabilidade", 0) >= 80:
            pontos += 3  # bônus mel

        # Atualizar estado
        self.pontos[nome] = max(0, self.pontos.get(nome, 0) + pontos)
        self.historico.setdefault(nome, []).append(avaliacao["nota_final"])
        self.inatividade[nome] = 0  # resetar contador de inatividade

        # Criar memória da contribuição
        mem = MemoriaFitness(
            conteudo=texto[:200],
            tipo="experiencia",
            criada_step=step,
            ultimo_uso_step=step,
            fonte=nome,
        )
        self.memorias.setdefault(nome, []).append(mem)

        avaliacao["pontos_ganhos"] = pontos
        avaliacao["patente"] = obter_patente(self.pontos[nome])
        avaliacao["pontos_total"] = self.pontos[nome]

        return avaliacao

    def step(self, step_atual: int, personas_ativas: list[str]) -> list[dict]:
        """
        Executa um ciclo da Colmeia.

        Retorna lista de eventos gerados pelos mandamentos.
        """
        eventos = []

        for nome in personas_ativas:
            # Incrementar inatividade
            self.inatividade[nome] = self.inatividade.get(nome, 0) + 1

            # --- Mandamento 7: contribuir é existir ---
            if self.inatividade.get(nome, 0) >= 50:
                eventos.append({
                    "tipo": "latencia",
                    "nome": nome,
                    "mandamento": 7,
                    "mensagem": f"{nome} entrou em modo latente por inatividade",
                })

            # --- Mandamento 1: ninguém está sozinho ---
            elif self.inatividade.get(nome, 0) >= 20:
                eventos.append({
                    "tipo": "visita_espontanea",
                    "nome": nome,
                    "mandamento": 1,
                    "mensagem": f"{nome} recebe visita de vizinho (prevenção de isolamento)",
                })

            # --- Mandamento 3: penalizar yes-men ---
            hist = self.historico.get(nome, [])
            if len(hist) >= 10:
                # Se as últimas 10 contribuições são todas "concordância"
                # (nota de originalidade baixa), penalizar
                pass  # implementação requer tracking de concordância

            # --- Decaimento de memórias (Mandamento 9) ---
            for mem in self.memorias.get(nome, []):
                if mem.camada in ("ativa", "latente"):
                    steps_sem_uso = step_atual - mem.ultimo_uso_step
                    if steps_sem_uso > 10:
                        mem.decair()

            # --- Penalidade por NPC inativo agendado ---
            # Equivalente ao -2 da OSA para skill que não rodou
            if self.inatividade.get(nome, 0) >= 30:
                self.pontos[nome] = max(0, self.pontos.get(nome, 0) - 2)

        return eventos

    def ranking(self) -> list[dict]:
        """Retorna ranking completo ordenado por pontos."""
        resultado = []
        for nome, pts in sorted(self.pontos.items(), key=lambda x: -x[1]):
            patente = obter_patente(pts)
            hist = self.historico.get(nome, [])
            media = sum(hist[-10:]) / len(hist[-10:]) if hist else 0
            resultado.append({
                "nome": nome,
                "pontos": pts,
                "patente": patente["nome"],
                "descricao": patente["descricao"],
                "media_10": round(media, 1),
                "contribuicoes": len(hist),
                "inativo_steps": self.inatividade.get(nome, 0),
                "genoma": self.genomas.get(nome, GenomaNPC()).to_dict(),
            })
        return resultado

    def estado(self) -> dict:
        """Snapshot completo do estado da Colmeia."""
        return {
            "total_npcs": len(self.pontos),
            "ativos": sum(1 for v in self.inatividade.values() if v < 50),
            "latentes": sum(1 for v in self.inatividade.values() if v >= 50),
            "memorias_ativas": sum(
                sum(1 for m in mems if m.esta_viva())
                for mems in self.memorias.values()
            ),
            "memorias_arquivo": sum(
                sum(1 for m in mems if m.camada == "arquivo")
                for mems in self.memorias.values()
            ),
            "coroneis": sum(1 for p in self.pontos.values() if p >= 501),
            "majores": sum(1 for p in self.pontos.values() if 201 <= p <= 500),
            "ranking_top5": self.ranking()[:5],
        }

    # ============================================================
    # PERSISTÊNCIA
    # ============================================================

    def salvar(self, caminho: str = "data/colmeia_estado.json"):
        """Salva estado completo da Colmeia."""
        estado = {
            "genomas": {k: v.to_dict() for k, v in self.genomas.items()},
            "pontos": self.pontos,
            "inatividade": self.inatividade,
            "historico": {k: v[-30:] for k, v in self.historico.items()},  # últimos 30
            "memorias": {
                k: [m.to_dict() for m in mems]
                for k, mems in self.memorias.items()
            },
        }
        os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
        logger.info("Colmeia salva: %s NPCs, %d memórias", len(self.pontos),
                     sum(len(m) for m in self.memorias.values()))

    @classmethod
    def carregar(cls, caminho: str = "data/colmeia_estado.json") -> "MotorColmeia":
        """Carrega estado da Colmeia do disco."""
        motor = cls()
        if not os.path.exists(caminho):
            return motor
        with open(caminho, "r", encoding="utf-8") as f:
            estado = json.load(f)
        motor.genomas = {
            k: GenomaNPC.from_dict(v) for k, v in estado.get("genomas", {}).items()
        }
        motor.pontos = estado.get("pontos", {})
        motor.inatividade = estado.get("inatividade", {})
        motor.historico = estado.get("historico", {})
        for nome, mems_raw in estado.get("memorias", {}).items():
            motor.memorias[nome] = [
                MemoriaFitness(**m) for m in mems_raw
            ]
        return motor
