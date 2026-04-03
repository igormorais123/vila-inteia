"""
Ferramentas dos Agentes — O toolkit que dá poder real aos habitantes da Vila.

Cada agente pode:
    1. Executar Python (sandbox seguro)
    2. Pesquisar na web (via OmniRoute/web search)
    3. Comunicar (DM, broadcast, pedir ajuda)
    4. Propor (contribuir para o desafio coletivo)
    5. Votar (aprovar/rejeitar propostas)
    6. Gastar moedas (contratar ajuda, acessar recursos)

Integra com:
    - DesafioColetivo (propósito)
    - RedeSocial (comunicação pública)
    - INTEIA Coins (economia)
    - Campus (locais com recursos)
    - Autoresearch (pesquisa)
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger("vila-inteia.ferramentas")


# ============================================================
# SANDBOX PYTHON
# ============================================================

# Módulos permitidos dentro do sandbox
_SANDBOX_ALLOWED = {
    "math", "statistics", "random", "json", "re", "collections",
    "itertools", "functools", "datetime", "decimal", "fractions",
    "textwrap", "string", "unicodedata", "hashlib", "base64",
    "csv", "io",
}

# Builtins proibidos
_SANDBOX_BLOCKED_BUILTINS = {
    "exec", "eval", "compile", "__import__", "open", "exit", "quit",
    "breakpoint", "input", "help", "globals", "locals", "vars",
    "delattr", "setattr", "getattr",
}


def _criar_sandbox_globals() -> dict:
    """Cria o namespace sandbox para execução segura."""
    import builtins as _builtins
    import math, statistics, random, json as _json, re, collections
    import itertools, functools, datetime as _dt, decimal, textwrap

    # Copiar builtins seguros
    safe_builtins = {}
    for name in dir(_builtins):
        if name not in _SANDBOX_BLOCKED_BUILTINS:
            try:
                safe_builtins[name] = getattr(_builtins, name)
            except AttributeError:
                pass

    # __import__ restrito a módulos permitidos
    _orig_import = _builtins.__import__
    def _restricted_import(name, *args, **kwargs):
        base = name.split(".")[0]
        if base in _SANDBOX_ALLOWED:
            return _orig_import(name, *args, **kwargs)
        raise ImportError(f"Módulo '{name}' não permitido no sandbox")

    safe_builtins["__import__"] = _restricted_import

    return {
        "__builtins__": safe_builtins,
        "math": math,
        "statistics": statistics,
        "random": random,
        "json": _json,
        "re": re,
        "collections": collections,
        "itertools": itertools,
        "functools": functools,
        "datetime": _dt,
        "decimal": decimal,
        "textwrap": textwrap,
    }


@dataclass
class ResultadoExecucao:
    """Resultado da execução de código Python."""
    sucesso: bool = False
    saida: str = ""
    erro: str = ""
    variaveis_retornadas: dict = field(default_factory=dict)
    tempo_ms: float = 0

    def to_dict(self) -> dict:
        return {
            "sucesso": self.sucesso,
            "saida": self.saida[:2000],
            "erro": self.erro[:500],
            "variaveis_retornadas": {
                k: str(v)[:200] for k, v in self.variaveis_retornadas.items()
            },
            "tempo_ms": round(self.tempo_ms, 1),
        }


def executar_python(codigo: str, timeout_s: float = 5.0) -> ResultadoExecucao:
    """
    Executa código Python em sandbox restrito.

    Permitido: math, statistics, json, re, collections, datetime.
    Proibido: open, exec, eval, import, network, filesystem.
    """
    import time
    import io
    import sys

    resultado = ResultadoExecucao()
    inicio = time.monotonic()

    # Verificações de segurança — analisa apenas statements, não strings
    import ast
    try:
        tree = ast.parse(codigo)
    except SyntaxError as e:
        resultado.erro = f"SyntaxError: {e}"
        resultado.tempo_ms = (time.monotonic() - inicio) * 1000
        return resultado

    # Verificar imports proibidos
    _MODULOS_PROIBIDOS = {"os", "sys", "subprocess", "socket", "urllib",
                          "http", "requests", "shutil", "pathlib", "signal",
                          "ctypes", "multiprocessing", "threading"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in _MODULOS_PROIBIDOS:
                    resultado.erro = f"Módulo proibido no sandbox: '{alias.name}'"
                    resultado.tempo_ms = (time.monotonic() - inicio) * 1000
                    return resultado
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in _MODULOS_PROIBIDOS:
                resultado.erro = f"Módulo proibido no sandbox: '{node.module}'"
                resultado.tempo_ms = (time.monotonic() - inicio) * 1000
                return resultado
        elif isinstance(node, ast.Call):
            # Bloquear open(), exec(), eval(), compile()
            if isinstance(node.func, ast.Name) and node.func.id in ("open", "exec", "eval", "compile", "__import__"):
                resultado.erro = f"Função proibida no sandbox: '{node.func.id}()'"
                resultado.tempo_ms = (time.monotonic() - inicio) * 1000
                return resultado

    # Bloquear acesso a __subclasses__ e outros escapes do object graph
    _ESCAPE_PATTERNS = ["__subclasses__", "__bases__", "__mro__", "__globals__",
                        "__code__", "__builtins__", "getattr(", "type("]
    for pat in _ESCAPE_PATTERNS:
        if pat in codigo:
            resultado.erro = f"Padrão proibido no sandbox: '{pat}'"
            resultado.tempo_ms = (time.monotonic() - inicio) * 1000
            return resultado

    # Capturar stdout
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        sandbox_globals = _criar_sandbox_globals()
        sandbox_globals["_resultado"] = {}

        # Timeout real via threading
        import threading
        exec_error = [None]
        def _run_code():
            try:
                exec(codigo + "\n", sandbox_globals)
            except Exception as e:
                exec_error[0] = e

        thread = threading.Thread(target=_run_code, daemon=True)
        thread.start()
        thread.join(timeout=timeout_s)

        if thread.is_alive():
            resultado.erro = f"Timeout: execução excedeu {timeout_s}s"
            resultado.tempo_ms = (time.monotonic() - inicio) * 1000
            sys.stdout = old_stdout
            return resultado

        if exec_error[0]:
            raise exec_error[0]

        resultado.saida = buffer.getvalue()
        resultado.sucesso = True

        # Capturar variáveis definidas pelo agente
        _base_keys = set(_criar_sandbox_globals().keys()) | {"_resultado"}
        for k, v in sandbox_globals.items():
            if not k.startswith("_") and k not in _base_keys:
                try:
                    resultado.variaveis_retornadas[k] = v
                except Exception:
                    pass

    except Exception as e:
        resultado.erro = f"{type(e).__name__}: {e}"
        resultado.saida = buffer.getvalue()
    finally:
        sys.stdout = old_stdout
        resultado.tempo_ms = (time.monotonic() - inicio) * 1000

    return resultado


# ============================================================
# PESQUISA WEB
# ============================================================

@dataclass
class ResultadoPesquisa:
    """Resultado de pesquisa web."""
    query: str = ""
    resultados: list[dict] = field(default_factory=list)
    resumo: str = ""
    sucesso: bool = False

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "resultados": self.resultados[:5],
            "resumo": self.resumo[:1000],
            "sucesso": self.sucesso,
        }


def pesquisar_web(query: str, max_resultados: int = 5) -> ResultadoPesquisa:
    """
    Pesquisa na web — 3 tentativas em cascata.

    1. Playwright headless (pesquisa REAL via Google)
    2. inference.sh Tavily/Exa (pesquisa REAL via API)
    3. LLM como fallback (MARCADO como não-real)
    """
    resultado = ResultadoPesquisa(query=query)

    # Tentativa 1: Playwright headless — pesquisa REAL no Google
    try:
        import subprocess
        # Usa gstack browse (CLI) se disponível
        import os
        browse_bin = os.path.expanduser("~/.claude/skills/gstack/browse/dist/browse")
        if os.path.exists(browse_bin):
            proc = subprocess.run(
                [browse_bin, "goto", f"https://www.google.com/search?q={query.replace(' ', '+')}&num={max_resultados}"],
                capture_output=True, text=True, timeout=20,
            )
            if proc.returncode == 0:
                # Extrair texto da página
                proc2 = subprocess.run(
                    [browse_bin, "text"],
                    capture_output=True, text=True, timeout=10,
                )
                if proc2.returncode == 0 and proc2.stdout.strip():
                    texto = proc2.stdout.strip()[:3000]
                    resultado.resumo = texto
                    resultado.sucesso = True
                    resultado.resultados = [{"fonte": "google_playwright_real", "conteudo": texto}]
                    logger.info(f"Pesquisa REAL via Playwright: '{query}' ({len(texto)} chars)")
                    return resultado
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"Playwright browse indisponível: {e}")

    # Tentativa 2: inference.sh Tavily (pesquisa REAL via API)
    try:
        import subprocess
        proc = subprocess.run(
            ["npx", "-y", "@anthropic-ai/inference-sh", "run",
             "tavily/search", "--query", query, "--max-results", str(max_resultados)],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            resultado.resumo = proc.stdout.strip()[:2000]
            resultado.sucesso = True
            resultado.resultados = [{"fonte": "tavily_real", "conteudo": resultado.resumo}]
            return resultado
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"inference.sh indisponível: {e}")

    # Tentativa 3: LLM como fallback (MARCADO como não-real)
    try:
        from .ia_client import chamar_llm_conversa, MODELO_RAPIDO
        resposta = chamar_llm_conversa(
            "Você é um assistente de pesquisa. Responda de forma factual e concisa.",
            f"Pesquise e resuma: {query}",
            modelo=MODELO_RAPIDO,
            max_tokens=500,
        )
        if resposta:
            resultado.resumo = resposta
            resultado.sucesso = True
            resultado.resultados = [{"fonte": "llm_fallback_NAO_REAL", "conteudo": resposta}]
    except Exception as e:
        resultado.resumo = f"Pesquisa indisponível: {e}"
        logger.warning(f"Pesquisa web falhou: {e}")

    return resultado


# ============================================================
# COMUNICAÇÃO ENTRE AGENTES
# ============================================================

@dataclass
class Mensagem:
    """Mensagem direta entre agentes."""
    remetente_id: str
    remetente_nome: str
    destinatario_id: str = ""  # vazio = broadcast
    conteudo: str = ""
    tipo: str = "mensagem"  # mensagem | pedido_ajuda | convite | proposta
    step: int = 0
    respondida: bool = False
    resposta: str = ""

    def to_dict(self) -> dict:
        return {
            "remetente_id": self.remetente_id,
            "remetente_nome": self.remetente_nome,
            "destinatario_id": self.destinatario_id,
            "conteudo": self.conteudo[:500],
            "tipo": self.tipo,
            "step": self.step,
            "respondida": self.respondida,
            "resposta": self.resposta[:500],
        }


class CaixaCorreio:
    """Sistema de mensagens diretas entre agentes."""

    def __init__(self):
        self.mensagens: list[Mensagem] = []
        self._max_mensagens = 1000

    def enviar(self, msg: Mensagem):
        """Envia mensagem."""
        self.mensagens.append(msg)
        if len(self.mensagens) > self._max_mensagens:
            self.mensagens = self.mensagens[-self._max_mensagens:]

    def caixa_entrada(self, agente_id: str, apenas_nao_lidas: bool = True) -> list[Mensagem]:
        """Retorna mensagens para um agente."""
        msgs = [
            m for m in self.mensagens
            if m.destinatario_id == agente_id or m.destinatario_id == ""
        ]
        if apenas_nao_lidas:
            msgs = [m for m in msgs if not m.respondida]
        return msgs[-20:]

    def pedidos_ajuda(self, agente_id: str = "") -> list[Mensagem]:
        """Retorna pedidos de ajuda pendentes."""
        msgs = [m for m in self.mensagens if m.tipo == "pedido_ajuda" and not m.respondida]
        if agente_id:
            msgs = [m for m in msgs if m.destinatario_id == agente_id or m.destinatario_id == ""]
        return msgs[-10:]

    def to_dict(self) -> dict:
        return {
            "total_mensagens": len(self.mensagens),
            "pendentes": len([m for m in self.mensagens if not m.respondida]),
            "ultimas": [m.to_dict() for m in self.mensagens[-10:]],
        }


# ============================================================
# RECURSOS DOS LOCAIS
# ============================================================

# Cada local do campus tem recursos que agentes podem usar
RECURSOS_POR_LOCAL = {
    "laboratorio": {
        "nome": "Laboratório de IA",
        "ferramentas": ["python_sandbox", "dados", "modelos"],
        "descricao": "Execução de código, análise de dados, prototipagem",
        "custo_por_uso": 5,  # INTEIA Coins
    },
    "biblioteca": {
        "nome": "Biblioteca Infinita",
        "ferramentas": ["pesquisa_web", "documentos", "referencias"],
        "descricao": "Pesquisa, leitura, compilação de conhecimento",
        "custo_por_uso": 2,
    },
    "torre_estrategia": {
        "nome": "Torre de Estratégia",
        "ferramentas": ["simulacao", "cenarios", "war_room"],
        "descricao": "Simulação de cenários, planejamento estratégico",
        "custo_por_uso": 10,
    },
    "arena_debates": {
        "nome": "Arena de Debates",
        "ferramentas": ["debate_formal", "votacao", "tribunal"],
        "descricao": "Debates estruturados, votações, julgamentos",
        "custo_por_uso": 0,  # debates são gratuitos
    },
    "tribunal": {
        "nome": "Tribunal Constituinte",
        "ferramentas": ["votacao", "constituicao", "regimento"],
        "descricao": "Votação de artigos, emendas, regimento interno",
        "custo_por_uso": 0,
    },
    "observatorio": {
        "nome": "Observatório de Tendências",
        "ferramentas": ["pesquisa_web", "tendencias", "previsoes"],
        "descricao": "Monitoramento de tendências, previsões",
        "custo_por_uso": 3,
    },
    "atelie": {
        "nome": "Ateliê Criativo",
        "ferramentas": ["design", "prototipagem", "criacao"],
        "descricao": "Criação de protótipos, design de soluções",
        "custo_por_uso": 5,
    },
    "sala_guerra": {
        "nome": "Sala de Guerra",
        "ferramentas": ["python_sandbox", "simulacao", "dados"],
        "descricao": "Análise quantitativa, simulações intensivas",
        "custo_por_uso": 8,
    },
    "agora": {
        "nome": "Ágora Central",
        "ferramentas": ["broadcast", "assembleia", "discurso"],
        "descricao": "Discursos públicos, assembleias, anúncios",
        "custo_por_uso": 0,
    },
    "cafe_filosofos": {
        "nome": "Café dos Filósofos",
        "ferramentas": ["networking", "conversa_informal", "mentoria"],
        "descricao": "Networking, conversas informais, mentoria",
        "custo_por_uso": 0,
    },
}


def ferramentas_disponiveis_no_local(local_id: str) -> list[str]:
    """Retorna ferramentas disponíveis num local."""
    recurso = RECURSOS_POR_LOCAL.get(local_id, {})
    return recurso.get("ferramentas", [])


def custo_uso_local(local_id: str) -> int:
    """Retorna custo em INTEIA Coins para usar recursos do local."""
    recurso = RECURSOS_POR_LOCAL.get(local_id, {})
    return recurso.get("custo_por_uso", 0)


# ============================================================
# TOOLKIT INTEGRADO DO AGENTE
# ============================================================

@dataclass
class AcaoFerramenta:
    """Registro de uso de ferramenta por um agente."""
    agente_id: str
    ferramenta: str
    input_resumo: str
    resultado_resumo: str
    custo: int = 0
    step: int = 0
    sucesso: bool = True

    def to_dict(self) -> dict:
        return {
            "agente_id": self.agente_id,
            "ferramenta": self.ferramenta,
            "input": self.input_resumo[:200],
            "resultado": self.resultado_resumo[:200],
            "custo": self.custo,
            "step": self.step,
            "sucesso": self.sucesso,
        }


class ToolkitAgente:
    """
    Controlador de ferramentas de um agente.

    Verifica permissões (local + saldo), executa, registra uso, cobra.
    """

    def __init__(self):
        self.historico: list[AcaoFerramenta] = []
        self.caixa_correio = CaixaCorreio()
        self._max_historico = 500

    def pode_usar(self, agente_id: str, ferramenta: str, local_atual: str, saldo: int) -> tuple[bool, str]:
        """Verifica se agente pode usar a ferramenta."""
        ferramentas_local = ferramentas_disponiveis_no_local(local_atual)

        # Comunicação e votação disponíveis em qualquer lugar
        if ferramenta in ("mensagem", "broadcast", "votar", "propor"):
            return True, ""

        if ferramenta == "python_sandbox" and "python_sandbox" not in ferramentas_local:
            return False, f"Python sandbox não disponível em '{local_atual}'. Vá ao Laboratório ou Sala de Guerra."

        if ferramenta == "pesquisa_web" and "pesquisa_web" not in ferramentas_local:
            return False, f"Pesquisa web não disponível em '{local_atual}'. Vá à Biblioteca ou Observatório."

        custo = custo_uso_local(local_atual)
        if custo > saldo:
            return False, f"Saldo insuficiente: Ξ{saldo} (custo: Ξ{custo})"

        return True, ""

    def executar_python(self, agente_id: str, codigo: str, local_atual: str, saldo: int, step: int) -> ResultadoExecucao:
        """Executa Python se o agente tiver acesso."""
        pode, motivo = self.pode_usar(agente_id, "python_sandbox", local_atual, saldo)
        if not pode:
            return ResultadoExecucao(sucesso=False, erro=motivo)

        resultado = executar_python(codigo)
        custo = custo_uso_local(local_atual)

        self._registrar(AcaoFerramenta(
            agente_id=agente_id,
            ferramenta="python_sandbox",
            input_resumo=codigo[:100],
            resultado_resumo=resultado.saida[:100] if resultado.sucesso else resultado.erro[:100],
            custo=custo,
            step=step,
            sucesso=resultado.sucesso,
        ))

        return resultado

    async def pesquisar(self, agente_id: str, query: str, local_atual: str, saldo: int, step: int) -> ResultadoPesquisa:
        """Pesquisa web se o agente tiver acesso."""
        pode, motivo = self.pode_usar(agente_id, "pesquisa_web", local_atual, saldo)
        if not pode:
            return ResultadoPesquisa(query=query, resumo=motivo)

        resultado = await pesquisar_web(query)
        custo = custo_uso_local(local_atual)

        self._registrar(AcaoFerramenta(
            agente_id=agente_id,
            ferramenta="pesquisa_web",
            input_resumo=query[:100],
            resultado_resumo=resultado.resumo[:100],
            custo=custo,
            step=step,
            sucesso=resultado.sucesso,
        ))

        return resultado

    def _registrar(self, acao: AcaoFerramenta):
        """Registra uso de ferramenta."""
        self.historico.append(acao)
        if len(self.historico) > self._max_historico:
            self.historico = self.historico[-self._max_historico:]

    def stats(self) -> dict:
        """Estatísticas de uso de ferramentas."""
        por_tipo = {}
        for a in self.historico:
            por_tipo[a.ferramenta] = por_tipo.get(a.ferramenta, 0) + 1
        return {
            "total_usos": len(self.historico),
            "por_ferramenta": por_tipo,
            "custo_total": sum(a.custo for a in self.historico),
            "taxa_sucesso": (
                sum(1 for a in self.historico if a.sucesso) / max(len(self.historico), 1)
            ),
        }

    def to_dict(self) -> dict:
        return {
            "stats": self.stats(),
            "historico_recente": [a.to_dict() for a in self.historico[-10:]],
            "caixa_correio": self.caixa_correio.to_dict(),
        }
