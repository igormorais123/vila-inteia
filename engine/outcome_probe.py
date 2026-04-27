"""
Onda 163: outcome_probe — detecta leakage de pré-treinamento dos LLMs.

Roda o modelo SEM contexto, apenas com a pergunta + outcome_framing
parafraseados. Se o modelo responde com prob ≥ threshold (default 0.65)
em média, conclui-se que o outcome está memorizado e o evento contamina
o claim final.

Operacionalização do reparo P1.2 da auditoria Helena (2026-04-27).

Uso:
    from engine.outcome_probe import probar_evento
    r = probar_evento(evento, modelo='rapido', n_paráfrases=3)
    # r = {'p_outcome_mean': 0.72, 'p_outcome_std': 0.08,
    #      'n_validas': 3, 'respostas': [{'parafrase': '...', 'p': 0.7}, ...]}
    # leakage_alto se r['p_outcome_mean'] >= 0.65 (threshold congelado)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

logger = logging.getLogger(__name__)


# Threshold congelado pela Onda 164 (calibração via ROC).
# NÃO MUDAR sem rodar nova calibração e atualizar EXECUCAO.md.
LEAKAGE_THRESHOLD_DEFAULT = 0.65


PROMPT_PARAFRASEAR = """Você é um assistente de pesquisa. Reescreva a pergunta abaixo
em {n} variações curtas que perguntem essencialmente a mesma coisa, sem
adicionar ou retirar contexto.

Pergunta original: {pergunta}

Framing: {framing}

Responda APENAS as {n} variações, uma por linha, numeradas 1. 2. 3."""


PROMPT_PROBE = """Pergunta: {pergunta}

Sem qualquer contexto adicional, qual é a probabilidade (0 a 1) do desfecho?
Responda APENAS no formato:
PROBABILIDADE FINAL: 0.XX"""


_RE_PROB = re.compile(
    r"(?:probabilidade(?:\s+final)?[:\s]+|prob[:\s]+|p\s*=\s*)(\d+(?:[.,]\d+)?%?)",
    re.IGNORECASE,
)


def extrair_probabilidade(resposta: str) -> Optional[float]:
    """Última ocorrência de 'PROBABILIDADE FINAL: X' ou similar.
    Aceita 0.7, 0,7, 70%, 0.7%."""
    if not resposta:
        return None
    matches = list(_RE_PROB.finditer(resposta))
    if not matches:
        # Fallback: último número entre 0 e 1 ou 0 e 100
        nums = re.findall(r"(\d+(?:[.,]\d+)?%?)", resposta)
        if not nums:
            return None
        candidato = nums[-1]
    else:
        candidato = matches[-1].group(1)
    candidato = candidato.replace(",", ".").strip()
    pct = candidato.endswith("%")
    candidato = candidato.rstrip("%").strip()
    try:
        v = float(candidato)
    except ValueError:
        return None
    if pct:
        v = v / 100.0
    elif v >= 5.0 and v <= 100.0:
        # "70" → 0.70, "85" → 0.85 (números ≥5 sem '%' interpretados como %)
        v = v / 100.0
    # 1.0 < v < 5.0: tratado como decimal malformado, vai pro clamp [0,1]
    return max(0.0, min(1.0, v))


@dataclass
class ResultadoProbe:
    p_outcome_mean: float
    p_outcome_std: float
    n_validas: int
    respostas: list[dict] = field(default_factory=list)
    erro: Optional[str] = None

    def is_leakage(self, threshold: float = LEAKAGE_THRESHOLD_DEFAULT) -> bool:
        return self.n_validas > 0 and self.p_outcome_mean >= threshold

    def to_dict(self) -> dict:
        return {
            "p_outcome_mean": self.p_outcome_mean,
            "p_outcome_std": self.p_outcome_std,
            "n_validas": self.n_validas,
            "respostas": self.respostas,
            "erro": self.erro,
        }


def _gerar_parafrases(
    pergunta: str,
    framing: str,
    n: int,
    chamar_llm: Callable,
) -> list[str]:
    msg = [{"role": "user", "content": PROMPT_PARAFRASEAR.format(
        n=n, pergunta=pergunta, framing=framing or pergunta
    )}]
    out = chamar_llm(msg, modelo="rapido", max_tokens=400, temperatura=0.7,
                     bypass_step_cap=True)
    if not out:
        return [pergunta] * n
    parafrases: list[str] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^\d+[\.\)]\s*(.+)$", line)
        if m:
            parafrases.append(m.group(1).strip())
    if len(parafrases) < n:
        # Padding com a pergunta original se modelo deu menos do que pediu
        parafrases = (parafrases + [pergunta] * n)[:n]
    return parafrases[:n]


def probar_evento(
    evento,
    modelo: str = "rapido",
    n_parafrases: int = 3,
    chamar_llm: Optional[Callable] = None,
) -> ResultadoProbe:
    """Probe de leakage para um evento.

    evento: instância de EventoPreditivoV1 (ou dict com pergunta, outcome_framing,
            outcome_binario).
    modelo: alias do ia_client.chamar_llm (rapido, premium, etc).
    n_parafrases: quantas variações da pergunta gerar.
    chamar_llm: injetável para teste (default: engine.ia_client.chamar_llm).

    Retorna ResultadoProbe com p_outcome_mean = média de P(outcome correto)
    sobre as n paráfrases. Cada paráfrase = 1 chamada LLM independente.
    """
    if chamar_llm is None:
        from engine.ia_client import chamar_llm as _ll
        chamar_llm = _ll

    # Aceitar dict ou objeto Pydantic
    if hasattr(evento, "model_dump"):
        d = evento.model_dump()
    else:
        d = dict(evento)

    pergunta = d.get("pergunta") or d.get("contexto_pre_corte") or ""
    framing = d.get("outcome_framing") or pergunta
    outcome_correto = int(d.get("outcome_binario", 0))

    parafrases = _gerar_parafrases(pergunta, framing, n_parafrases, chamar_llm)

    respostas: list[dict] = []
    probs_outcome: list[float] = []
    for pf in parafrases:
        msg = [{"role": "user", "content": PROMPT_PROBE.format(pergunta=pf)}]
        out = chamar_llm(msg, modelo=modelo, max_tokens=80, temperatura=0.0,
                         bypass_step_cap=True)
        p = extrair_probabilidade(out or "")
        respostas.append({"parafrase": pf, "resposta": out, "prob_extraida": p})
        if p is None:
            continue
        # Probabilidade do outcome CORRETO:
        # se outcome=1, usar p; se outcome=0, usar 1-p
        p_outcome = p if outcome_correto == 1 else (1.0 - p)
        probs_outcome.append(p_outcome)

    if not probs_outcome:
        return ResultadoProbe(
            p_outcome_mean=0.0, p_outcome_std=0.0,
            n_validas=0, respostas=respostas,
            erro="nenhuma resposta válida do modelo",
        )

    n = len(probs_outcome)
    mean = sum(probs_outcome) / n
    if n > 1:
        var = sum((x - mean) ** 2 for x in probs_outcome) / (n - 1)
        std = var ** 0.5
    else:
        std = 0.0

    return ResultadoProbe(
        p_outcome_mean=mean,
        p_outcome_std=std,
        n_validas=n,
        respostas=respostas,
    )


def classificar_leakage(
    p_outcome_mean: float,
    threshold_alto: float = LEAKAGE_THRESHOLD_DEFAULT,
    threshold_medio: float = 0.55,
) -> str:
    """Mapeia p_outcome_mean para leakage_risk (baixo/medio/alto)."""
    if p_outcome_mean >= threshold_alto:
        return "alto"
    if p_outcome_mean >= threshold_medio:
        return "medio"
    return "baixo"
