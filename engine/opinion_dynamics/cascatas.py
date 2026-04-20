"""
Information cascades: agentes seguem decisão alheia ignorando sinal próprio.

Referência:
    Bikhchandani, Hirshleifer, Welch (1992), A Theory of Fads, Fashion, Custom...

Uso na Vila: modelar viralização de temas sem recorrer a LLM, puramente estatístico.
"""

from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass
class ResultadoCascata:
    decisoes: list[int]              # 0 ou 1 por agente em ordem
    cascata_formada: bool
    posicao_cascata: int             # índice onde cascata começou (-1 se não formou)
    decisao_final: int               # 0 ou 1


def bikhchandani(
    sinais_privados: list[int],
    prior: float = 0.5,
    precisao_sinal: float = 0.7,
    seed: int = 42,
) -> ResultadoCascata:
    """
    Modelo BHW clássico:
        - Cada agente observa decisões públicas dos anteriores + seu sinal privado
        - Se decisões anteriores são unânimes de um lado (diferença >=2 na contagem),
          agente seguinte ignora seu sinal e segue a maioria
        - Cascata pode ser INCORRETA (todos seguem mesmo sendo errado)

    sinais_privados: lista de 0/1 (sinais que cada agente recebeu)
    prior: crença inicial
    precisao_sinal: 0.5 a 1.0, quão preciso é o sinal privado
    """
    rng = random.Random(seed)
    decisoes = []
    cascata_pos = -1
    for i, sinal in enumerate(sinais_privados):
        n1 = decisoes.count(1)
        n0 = decisoes.count(0)
        diff = n1 - n0
        if diff >= 2:
            d = 1                        # cascata em 1
            if cascata_pos < 0:
                cascata_pos = i
        elif diff <= -2:
            d = 0
            if cascata_pos < 0:
                cascata_pos = i
        else:
            if diff == 0:
                d = sinal
            else:
                # sinal + diff pequena: bayesian update
                p_1 = (prior * precisao_sinal ** (sinal + max(0, diff))) / (
                    prior * precisao_sinal ** (sinal + max(0, diff)) +
                    (1 - prior) * (1 - precisao_sinal) ** (sinal + max(0, diff)) +
                    1e-9
                )
                d = 1 if p_1 > 0.5 else 0
        decisoes.append(d)
    return ResultadoCascata(
        decisoes=decisoes,
        cascata_formada=cascata_pos >= 0,
        posicao_cascata=cascata_pos,
        decisao_final=decisoes[-1] if decisoes else 0,
    )
