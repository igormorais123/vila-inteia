"""
Sistema de Incentivos da Vila INTEIA.

Recompensa agentes por contribuições ao desafio coletivo.
Integra com INTEIA Coins (economia existente) e métricas sociais.

Tipos de incentivo:
    - Financeiro: INTEIA Coins por contribuição/debate/voto
    - Reputação: Score de influência (quem convence mais)
    - Cargo: Papéis especiais (relator, moderador, líder de eixo)
    - Reconhecimento: Destaque no feed, badge especial

Penalidades:
    - Inatividade prolongada: perda de coins
    - Spam/repetição: sem recompensa
    - Obstrução: penalidade social
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("vila-inteia.incentivos")


# ============================================================
# TABELA DE RECOMPENSAS
# ============================================================

RECOMPENSAS = {
    # Contribuições ao desafio
    "proposta_nova": 50,           # Propor algo novo
    "emenda_aceita": 30,           # Emenda incorporada
    "sintese_publicada": 100,      # Helena sintetizou sua contribuição
    "entrega_aprovada": 200,       # Entrega coletiva aprovada

    # Debates e interações
    "debate_participou": 10,       # Participou de debate
    "debate_venceu": 25,           # Debate com mais apoio
    "comentario_relevante": 5,     # Comentário com reações positivas
    "mentoria_dada": 20,           # Ajudou outro agente
    "pedido_ajuda_respondido": 15, # Respondeu pedido de ajuda

    # Votações
    "voto_registrado": 2,          # Votou (participação)
    "voto_maioria": 5,             # Votou com a maioria (alinhamento)

    # Ferramentas
    "codigo_executado": 10,        # Executou Python com sucesso
    "pesquisa_realizada": 8,       # Pesquisou na web
    "pesquisa_citada": 15,         # Sua pesquisa foi citada por outro

    # Cargos especiais
    "relator_fase": 150,           # Nomeado relator da fase
    "moderador_debate": 50,        # Moderou debate
    "lider_eixo": 100,             # Líder de eixo temático
}

PENALIDADES = {
    "inatividade_10_steps": -5,    # Não fez nada em 10 steps
    "inatividade_50_steps": -20,   # Não fez nada em 50 steps
    "spam_repetido": -10,          # Postou conteúdo repetido
    "obstrucao": -30,              # Bloqueou progresso sem justificativa
}


# ============================================================
# CARTEIRA (INTEIA Coins)
# ============================================================

@dataclass
class Transacao:
    """Registro de transação financeira."""
    agente_id: str
    tipo: str           # motivo da transação
    valor: int          # positivo = ganho, negativo = gasto/penalidade
    saldo_apos: int = 0
    step: int = 0
    descricao: str = ""

    def to_dict(self) -> dict:
        return {
            "agente_id": self.agente_id,
            "tipo": self.tipo,
            "valor": self.valor,
            "saldo_apos": self.saldo_apos,
            "step": self.step,
            "descricao": self.descricao[:200],
        }


@dataclass
class Carteira:
    """Carteira de INTEIA Coins de um agente."""
    agente_id: str = ""
    saldo: int = 1000  # saldo inicial
    historico: list[Transacao] = field(default_factory=list)

    # Métricas de reputação
    reputacao: float = 50.0  # 0-100
    contribuicoes_total: int = 0
    debates_total: int = 0
    votos_total: int = 0
    cargo_atual: str = ""  # relator | moderador | lider_eixo | ""

    def creditar(self, valor: int, tipo: str, step: int = 0, descricao: str = ""):
        """Adiciona coins à carteira."""
        self.saldo += valor
        self.historico.append(Transacao(
            agente_id=self.agente_id,
            tipo=tipo,
            valor=valor,
            saldo_apos=self.saldo,
            step=step,
            descricao=descricao,
        ))
        if len(self.historico) > 200:
            self.historico = self.historico[-200:]

    def debitar(self, valor: int, tipo: str, step: int = 0, descricao: str = "") -> bool:
        """Remove coins da carteira. Retorna False se saldo insuficiente."""
        if self.saldo < valor:
            return False
        self.saldo -= valor
        self.historico.append(Transacao(
            agente_id=self.agente_id,
            tipo=tipo,
            valor=-valor,
            saldo_apos=self.saldo,
            step=step,
            descricao=descricao,
        ))
        if len(self.historico) > 200:
            self.historico = self.historico[-200:]
        return True

    def ajustar_reputacao(self, delta: float):
        """Ajusta reputação (clamped 0-100)."""
        self.reputacao = max(0, min(100, self.reputacao + delta))

    def to_dict(self) -> dict:
        return {
            "agente_id": self.agente_id,
            "saldo": self.saldo,
            "reputacao": round(self.reputacao, 1),
            "contribuicoes_total": self.contribuicoes_total,
            "debates_total": self.debates_total,
            "votos_total": self.votos_total,
            "cargo_atual": self.cargo_atual,
            "historico_recente": [t.to_dict() for t in self.historico[-10:]],
        }


# ============================================================
# MOTOR DE INCENTIVOS
# ============================================================

class MotorIncentivos:
    """
    Gerencia recompensas, penalidades e economia da vila.

    Integra com DesafioColetivo para recompensar progresso.
    """

    def __init__(self):
        self.carteiras: dict[str, Carteira] = {}
        self.ranking_reputacao: list[tuple[str, float]] = []
        self._ultimo_step_atividade: dict[str, int] = {}

    def obter_carteira(self, agente_id: str) -> Carteira:
        """Retorna ou cria carteira do agente."""
        if agente_id not in self.carteiras:
            self.carteiras[agente_id] = Carteira(agente_id=agente_id)
        return self.carteiras[agente_id]

    def saldo(self, agente_id: str) -> int:
        """Retorna saldo do agente."""
        return self.obter_carteira(agente_id).saldo

    # ── Recompensas ──

    def recompensar(self, agente_id: str, tipo: str, step: int = 0, descricao: str = ""):
        """Recompensa agente por ação específica."""
        valor = RECOMPENSAS.get(tipo, 0)
        if valor <= 0:
            return

        carteira = self.obter_carteira(agente_id)
        carteira.creditar(valor, tipo, step, descricao)
        carteira.ajustar_reputacao(valor / 50)  # +1 rep por 50 coins

        # Atualizar métricas
        if "proposta" in tipo or "emenda" in tipo or "entrega" in tipo:
            carteira.contribuicoes_total += 1
        elif "debate" in tipo:
            carteira.debates_total += 1
        elif "voto" in tipo:
            carteira.votos_total += 1

        self._ultimo_step_atividade[agente_id] = step

    def penalizar(self, agente_id: str, tipo: str, step: int = 0, descricao: str = ""):
        """Penaliza agente (saldo nunca fica negativo)."""
        valor = PENALIDADES.get(tipo, 0)
        if valor >= 0:
            return

        carteira = self.obter_carteira(agente_id)
        # Limitar penalidade ao saldo disponível (nunca negativo)
        penalidade_real = max(valor, -carteira.saldo)
        if penalidade_real < 0:
            carteira.creditar(penalidade_real, tipo, step, descricao)
            carteira.ajustar_reputacao(penalidade_real / 10)

    def cobrar_recurso(self, agente_id: str, custo: int, descricao: str, step: int = 0) -> bool:
        """Cobra uso de recurso do local. Retorna False se sem saldo."""
        if custo <= 0:
            return True
        carteira = self.obter_carteira(agente_id)
        return carteira.debitar(custo, "uso_recurso", step, descricao)

    def transferir(self, de_id: str, para_id: str, valor: int, step: int = 0, descricao: str = "") -> bool:
        """Transferência entre agentes."""
        carteira_de = self.obter_carteira(de_id)
        if not carteira_de.debitar(valor, "transferencia_enviada", step, f"Para {para_id}: {descricao}"):
            return False
        carteira_para = self.obter_carteira(para_id)
        carteira_para.creditar(valor, "transferencia_recebida", step, f"De {de_id}: {descricao}")
        return True

    # ── Verificações periódicas ──

    def verificar_inatividade(self, agentes_ids: list[str], step: int):
        """Penaliza agentes inativos (aplica uma vez por threshold, não repetidamente)."""
        for agente_id in agentes_ids:
            ultimo = self._ultimo_step_atividade.get(agente_id, 0)
            inativo = step - ultimo
            # Chave para evitar penalidade repetida no mesmo intervalo
            chave = f"_pen_{agente_id}"
            ultimo_pen = getattr(self, '_penalidades_aplicadas', {}).get(chave, 0)
            if not hasattr(self, '_penalidades_aplicadas'):
                self._penalidades_aplicadas = {}
            if inativo >= 50 and ultimo_pen < 50:
                self.penalizar(agente_id, "inatividade_50_steps", step,
                               f"Sem atividade por {inativo} steps")
                self._penalidades_aplicadas[chave] = 50
            elif inativo >= 10 and ultimo_pen < 10:
                self.penalizar(agente_id, "inatividade_10_steps", step,
                               f"Sem atividade por {inativo} steps")
                self._penalidades_aplicadas[chave] = 10

    def registrar_atividade(self, agente_id: str, step: int):
        """Marca agente como ativo."""
        self._ultimo_step_atividade[agente_id] = step

    # ── Cargos especiais ──

    def nomear_cargo(self, agente_id: str, cargo: str, step: int = 0):
        """Nomeia agente para cargo especial."""
        carteira = self.obter_carteira(agente_id)
        carteira.cargo_atual = cargo
        recompensa_tipo = f"{cargo}_fase" if cargo == "relator" else f"{cargo}_debate" if cargo == "moderador" else "lider_eixo"
        self.recompensar(agente_id, recompensa_tipo, step, f"Nomeado {cargo}")

    # ── Rankings ──

    def atualizar_ranking(self):
        """Recalcula ranking de reputação."""
        self.ranking_reputacao = sorted(
            [(aid, c.reputacao) for aid, c in self.carteiras.items()],
            key=lambda x: x[1],
            reverse=True,
        )

    def top_agentes(self, n: int = 10) -> list[dict]:
        """Top N agentes por reputação."""
        self.atualizar_ranking()
        resultado = []
        for agente_id, rep in self.ranking_reputacao[:n]:
            c = self.carteiras[agente_id]
            resultado.append({
                "agente_id": agente_id,
                "saldo": c.saldo,
                "reputacao": round(rep, 1),
                "contribuicoes": c.contribuicoes_total,
                "cargo": c.cargo_atual,
            })
        return resultado

    def gini_coefficient(self) -> float:
        """Calcula coeficiente de Gini da distribuição de riqueza."""
        saldos = sorted([c.saldo for c in self.carteiras.values()])
        n = len(saldos)
        if n == 0:
            return 0.0
        soma = sum(saldos)
        if soma == 0:
            return 0.0
        index_soma = sum((i + 1) * s for i, s in enumerate(saldos))
        return (2 * index_soma) / (n * soma) - (n + 1) / n

    # ── Serialização ──

    def to_dict(self) -> dict:
        return {
            "total_carteiras": len(self.carteiras),
            "supply_total": sum(c.saldo for c in self.carteiras.values()),
            "gini": round(self.gini_coefficient(), 3),
            "top_10": self.top_agentes(10),
        }

    def salvar(self, caminho: str):
        """Salva estado em JSON."""
        import json
        dados = {
            "carteiras": {k: v.to_dict() for k, v in self.carteiras.items()},
            "ultimo_atividade": self._ultimo_step_atividade,
        }
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
