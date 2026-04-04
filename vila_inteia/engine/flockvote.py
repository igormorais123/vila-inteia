"""
FlockVote Lite — Pesquisa Eleitoral Sintetica com Calibracao.

Baseado nos papers FlockVote (ICAIS 2025) + "Donald Trumps in Virtual Polls" (Wuhan).
Simplificado para rodar sobre os 1015 eleitores sinteticos do DF.

Pipeline:
1. Carregar perfis demograficos (38 atributos)
2. Injetar contexto dinamico (noticias, cenario)
3. LLM assume persona do eleitor → responde "em quem votaria?"
4. Agregar respostas → distribuicao de intencao de voto
5. Calibrar: final = h * historico + (1-h) * LLM
6. Calcular intervalo de confianca (IC 95%)

Modelo: BestFREE via OmniRoute (custo zero)
Fallback: Anthropic Haiku 4.5 (se IA_ALLOW_API_FALLBACK=true)
Ultimo fallback: retorna None → eleitor pulado (nao contamina resultado).

Benchmark 2022 DF: MAE 4.4pp (calibrado). Custo zero via OmniRoute.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

try:
    from .vila_ia_client import chamar_llm_conversa, MODELO_RAPIDO
except ImportError:
    from .ia_client import chamar_llm_conversa, MODELO_RAPIDO

logger = logging.getLogger("vila-inteia.flockvote")


# Metodologia
_METODOLOGIA = "FlockVote (ICAIS 2025) + calibracao Wuhan University"


# ============================================================
# MODELOS DE DADOS
# ============================================================

@dataclass
class ResultadoEleitor:
    """Resultado da simulacao de voto de 1 eleitor."""
    eleitor_id: str
    eleitor_nome: str
    regiao: str
    voto: str
    certeza: int
    motivo: str
    tempo_ms: int = 0


@dataclass
class ResultadoPesquisa:
    """Resultado agregado da pesquisa."""
    candidatos: list[str]
    contexto: str
    amostra_total: int
    respostas_validas: int
    distribuicao: dict[str, float]
    distribuicao_calibrada: dict[str, float]
    intervalo_confianca: dict[str, dict[str, float]]  # candidato → {lower, upper}
    h_calibracao: float
    por_regiao: dict[str, dict[str, float]]
    por_genero: dict[str, dict[str, float]]
    por_faixa_etaria: dict[str, dict[str, float]]
    por_orientacao: dict[str, dict[str, float]]
    votos_individuais: list[dict]
    tempo_total_s: float
    timestamp: str
    metodologia: str = _METODOLOGIA

    def to_dict(self) -> dict:
        return {
            "metodologia": self.metodologia,
            "candidatos": self.candidatos,
            "contexto": self.contexto[:200],
            "amostra_total": self.amostra_total,
            "respostas_validas": self.respostas_validas,
            "taxa_resposta": f"{self.respostas_validas / max(self.amostra_total, 1) * 100:.1f}%",
            "distribuicao_bruta": self.distribuicao,
            "distribuicao_calibrada": self.distribuicao_calibrada,
            "intervalo_confianca_95": self.intervalo_confianca,
            "h_calibracao": self.h_calibracao,
            "por_regiao": self.por_regiao,
            "por_genero": self.por_genero,
            "por_faixa_etaria": self.por_faixa_etaria,
            "por_orientacao": self.por_orientacao,
            "tempo_total_s": round(self.tempo_total_s, 1),
            "timestamp": self.timestamp,
            "votos_amostra": self.votos_individuais[:20],
        }


# ============================================================
# SINGLETON — carrega JSON 1x, nao a cada request
# ============================================================

_singleton: Optional["FlockVoteLite"] = None


def obter_flockvote(caminho: str = "agentes/banco-eleitores-df.json") -> "FlockVoteLite":
    """Retorna instancia singleton do FlockVote."""
    global _singleton
    if _singleton is None:
        _singleton = FlockVoteLite(caminho)
    return _singleton


class FlockVoteLite:
    """Pesquisa eleitoral sintetica com calibracao academica."""

    # Pool de threads para execucao paralela (5 simultaneas)
    _executor = ThreadPoolExecutor(max_workers=5)

    def __init__(self, caminho_eleitores: str = "agentes/banco-eleitores-df.json"):
        self.caminho = caminho_eleitores
        self.eleitores: list[dict] = []
        self._carregar()

    def _carregar(self):
        caminho = self.caminho
        if not os.path.isabs(caminho):
            candidatos = [
                os.path.join(".", caminho),
                os.path.join(os.getcwd(), caminho),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", caminho),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", caminho),
                os.path.join("/app", "data", "agentes", os.path.basename(caminho)),
                "C:/Agentes/" + caminho,
            ]
            for tentativa in candidatos:
                resolved = os.path.abspath(tentativa)
                if os.path.exists(resolved):
                    caminho = resolved
                    break

        with open(caminho, "r", encoding="utf-8") as f:
            self.eleitores = json.load(f)
        logger.info(f"FlockVote singleton: {len(self.eleitores)} eleitores carregados de {caminho}")

    def executar(
        self,
        candidatos: list[str],
        contexto: str,
        amostra: int = 200,
        h_calibracao: float = 0.8,
        historico: dict[str, float] | None = None,
    ) -> ResultadoPesquisa:
        """Executa pesquisa com execucao paralela (5 threads)."""
        inicio = time.time()

        amostra_eleitores = self._amostrar(amostra)

        # Execucao PARALELA com ThreadPoolExecutor
        votos: list[ResultadoEleitor] = []
        falhas = 0

        futures = {
            self._executor.submit(self._simular_voto, eleitor, candidatos, contexto): eleitor
            for eleitor in amostra_eleitores
        }

        for i, future in enumerate(as_completed(futures)):
            try:
                resultado = future.result(timeout=30)
                if resultado:
                    votos.append(resultado)
                else:
                    falhas += 1
            except Exception:
                falhas += 1

            if (i + 1) % 50 == 0:
                logger.info(f"FlockVote: {i+1}/{len(amostra_eleitores)} ({len(votos)} OK, {falhas} falhas)")

        # Agregar
        distribuicao = self._agregar(votos, candidatos)

        # Calibrar
        if historico:
            distribuicao_calibrada = self._calibrar(distribuicao, historico, h_calibracao)
        else:
            distribuicao_calibrada = distribuicao.copy()

        # Intervalo de confianca 95%
        ic = self._calcular_ic(votos, candidatos, len(amostra_eleitores))

        # Cruzamentos
        por_regiao = self._cruzar(votos, candidatos, "regiao")
        por_genero = self._cruzar_atributo(votos, amostra_eleitores, candidatos, "genero")
        por_faixa = self._cruzar_atributo(votos, amostra_eleitores, candidatos, "faixa_etaria")
        por_orient = self._cruzar_atributo(votos, amostra_eleitores, candidatos, "orientacao_politica")

        tempo_total = time.time() - inicio

        return ResultadoPesquisa(
            candidatos=candidatos,
            contexto=contexto,
            amostra_total=len(amostra_eleitores),
            respostas_validas=len(votos),
            distribuicao=distribuicao,
            distribuicao_calibrada=distribuicao_calibrada,
            intervalo_confianca=ic,
            h_calibracao=h_calibracao,
            por_regiao=por_regiao,
            por_genero=por_genero,
            por_faixa_etaria=por_faixa,
            por_orientacao=por_orient,
            votos_individuais=[
                {
                    "id": v.eleitor_id,
                    "nome": v.eleitor_nome,
                    "regiao": v.regiao,
                    "voto": v.voto,
                    "certeza": v.certeza,
                    "motivo": v.motivo,
                }
                for v in votos
            ],
            tempo_total_s=tempo_total,
            timestamp=datetime.now().isoformat(),
        )

    # ================================================================
    # INTERVALO DE CONFIANCA (IC 95%)
    # ================================================================

    def _calcular_ic(
        self,
        votos: list[ResultadoEleitor],
        candidatos: list[str],
        n_total: int,
    ) -> dict[str, dict[str, float]]:
        """
        IC 95% usando distribuicao binomial (normal approx).
        Formula: p +- z * sqrt(p*(1-p)/n)
        z = 1.96 para 95%
        """
        n = len(votos)
        if n < 5:
            return {c: {"lower": 0.0, "upper": 100.0, "margem": 50.0} for c in candidatos}

        contagem = {c: 0 for c in candidatos}
        for v in votos:
            if v.voto in contagem:
                contagem[v.voto] += 1

        ic = {}
        z = 1.96
        for c in candidatos:
            p = contagem[c] / n
            margem = z * math.sqrt(p * (1 - p) / n) * 100
            pct = p * 100
            ic[c] = {
                "estimativa": round(pct, 1),
                "lower": round(max(0, pct - margem), 1),
                "upper": round(min(100, pct + margem), 1),
                "margem_erro": round(margem, 1),
            }

        return ic

    # ================================================================
    # AMOSTRAGEM ESTRATIFICADA
    # ================================================================

    def _amostrar(self, n: int) -> list[dict]:
        """Amostra estratificada por regiao administrativa."""
        if n >= len(self.eleitores):
            return list(self.eleitores)

        por_regiao: dict[str, list[dict]] = {}
        for e in self.eleitores:
            r = e.get("regiao_administrativa", "outros")
            por_regiao.setdefault(r, []).append(e)

        amostra = []
        for regiao, eleitores_regiao in por_regiao.items():
            proporcao = len(eleitores_regiao) / len(self.eleitores)
            n_regiao = max(1, round(n * proporcao))
            amostra.extend(random.sample(
                eleitores_regiao,
                min(n_regiao, len(eleitores_regiao))
            ))

        if len(amostra) > n:
            amostra = random.sample(amostra, n)

        random.shuffle(amostra)
        return amostra

    # ================================================================
    # SIMULACAO DE VOTO (1 eleitor)
    # ================================================================

    def _simular_voto(
        self,
        eleitor: dict,
        candidatos: list[str],
        contexto: str,
    ) -> ResultadoEleitor | None:
        """Simula o voto de 1 eleitor via LLM."""
        nome = eleitor.get("nome", "Eleitor")
        idade = eleitor.get("idade", "")
        genero = eleitor.get("genero", "")
        regiao = eleitor.get("regiao_administrativa", "")
        escolaridade = eleitor.get("escolaridade", "")
        renda = eleitor.get("renda_salarios_minimos", "")
        religiao = eleitor.get("religiao", "")
        orientacao = eleitor.get("orientacao_politica", "")
        posicao_bolsonaro = eleitor.get("posicao_bolsonaro", "")
        interesse = eleitor.get("interesse_politico", "")
        preocupacoes = eleitor.get("preocupacoes", [])
        if isinstance(preocupacoes, list):
            preocupacoes = ", ".join(preocupacoes[:3])
        valores = eleitor.get("valores", [])
        if isinstance(valores, list):
            valores = ", ".join(valores[:3])
        fontes = eleitor.get("fontes_informacao", [])
        if isinstance(fontes, list):
            fontes = ", ".join(fontes[:3])
        instrucao = eleitor.get("instrucao_comportamental", "")
        estilo = eleitor.get("estilo_decisao", "")

        candidatos_str = ", ".join(candidatos)

        system = f"""Voce eh {nome}, {idade} anos, {genero}, mora em {regiao} (Distrito Federal).
Escolaridade: {escolaridade}. Renda: {renda} salarios minimos. Religiao: {religiao}.
Orientacao politica: {orientacao}. Posicao sobre Bolsonaro: {posicao_bolsonaro}.
Interesse politico: {interesse}. Estilo de decisao: {estilo}.
Valores: {valores}. Preocupacoes: {preocupacoes}.
Fontes de informacao: {fontes}.
{instrucao}

Voce eh um eleitor REAL do DF respondendo uma pesquisa de intencao de voto para governador."""

        user = f"""Contexto politico atual:
{contexto}

Candidatos a governador do DF: {candidatos_str}

Em quem voce votaria para governador? Responda EXATAMENTE neste formato:
VOTO: [nome exato de um dos candidatos]
CERTEZA: [numero de 1 a 10]
MOTIVO: [1 frase curta]"""

        t0 = time.time()
        resposta = chamar_llm_conversa(system, user, modelo=MODELO_RAPIDO, max_tokens=100)
        tempo = int((time.time() - t0) * 1000)

        if not resposta:
            return None

        voto = self._extrair(resposta, "VOTO")
        certeza_str = self._extrair(resposta, "CERTEZA")
        motivo = self._extrair(resposta, "MOTIVO")

        if not voto:
            return None

        voto_normalizado = self._match_candidato(voto, candidatos)
        if not voto_normalizado:
            return None

        try:
            certeza = int(re.sub(r"[^0-9]", "", certeza_str or "5"))
            certeza = max(1, min(10, certeza))
        except (ValueError, TypeError):
            certeza = 5

        return ResultadoEleitor(
            eleitor_id=eleitor.get("id", ""),
            eleitor_nome=nome,
            regiao=regiao,
            voto=voto_normalizado,
            certeza=certeza,
            motivo=motivo or "",
            tempo_ms=tempo,
        )

    # ================================================================
    # UTILITARIOS
    # ================================================================

    def _extrair(self, texto: str, campo: str) -> str | None:
        pattern = rf"{campo}\s*:\s*(.+)"
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip().strip("*\"'")
        return None

    def _match_candidato(self, voto: str, candidatos: list[str]) -> str | None:
        voto_lower = voto.lower().strip()
        for c in candidatos:
            if c.lower() in voto_lower or voto_lower in c.lower():
                return c
            sobrenome = c.split()[-1].lower()
            if sobrenome in voto_lower:
                return c
        return None

    def _agregar(self, votos: list[ResultadoEleitor], candidatos: list[str]) -> dict[str, float]:
        contagem = {c: 0 for c in candidatos}
        for v in votos:
            if v.voto in contagem:
                contagem[v.voto] += 1

        total = sum(contagem.values())
        if total == 0:
            return {c: 0.0 for c in candidatos}

        dist = {}
        for c in candidatos:
            pct = contagem[c] / total * 100
            pct = max(1.0, min(99.0, pct))
            dist[c] = round(pct, 1)

        soma = sum(dist.values())
        if soma > 0:
            for c in dist:
                dist[c] = round(dist[c] / soma * 100, 1)

        return dist

    def _calibrar(self, llm: dict[str, float], historico: dict[str, float], h: float) -> dict[str, float]:
        calibrado = {}
        for c in llm:
            hist_val = historico.get(c, llm[c])
            calibrado[c] = round(h * hist_val + (1 - h) * llm[c], 1)

        soma = sum(calibrado.values())
        if soma > 0:
            for c in calibrado:
                calibrado[c] = round(calibrado[c] / soma * 100, 1)

        return calibrado

    def _cruzar(self, votos: list[ResultadoEleitor], candidatos: list[str], campo: str) -> dict[str, dict[str, float]]:
        grupos: dict[str, list[ResultadoEleitor]] = {}
        for v in votos:
            valor = getattr(v, campo, "outros")
            grupos.setdefault(valor, []).append(v)

        resultado = {}
        for grupo, votos_grupo in grupos.items():
            resultado[grupo] = self._agregar(votos_grupo, candidatos)
        return resultado

    def _cruzar_atributo(self, votos: list[ResultadoEleitor], eleitores: list[dict], candidatos: list[str], atributo: str) -> dict[str, dict[str, float]]:
        mapa = {}
        for e in eleitores:
            eid = e.get("id", "")
            mapa[eid] = str(e.get(atributo, "outros"))

        grupos: dict[str, list[ResultadoEleitor]] = {}
        for v in votos:
            valor = mapa.get(v.eleitor_id, "outros")
            grupos.setdefault(valor, []).append(v)

        resultado = {}
        for grupo, votos_grupo in grupos.items():
            if len(votos_grupo) >= 3:
                resultado[grupo] = self._agregar(votos_grupo, candidatos)
        return resultado
