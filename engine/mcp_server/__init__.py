"""
engine.mcp_server — servidor MCP mínimo para expor Vila como tools (Onda 8).

Implementa JSON-RPC 2.0 via stdio/HTTP. Expõe capability cards existentes
como tools MCP, permitindo que agentes externos (Claude Desktop, Cursor,
Colmeia) chamem funções da Vila.

Tools expostas:
    vila.simular_cenario        — roda N steps com tema injetado
    vila.consultar_habitante    — retorna perfil + patente + memória top-K
    vila.obter_proveniencia     — proveniência cognitiva de matéria
    vila.extrair_grafo          — extrai entidades+relações de texto
    vila.prever_trajetoria      — psico-história: forecast
    vila.backtest_dataset       — roda backtest de dataset
    vila.calibrar_genoma        — calibração via grid search
"""

from engine.mcp_server.server import MCPServer, rodar_stdio
from engine.mcp_server.tools import lista_tools_disponiveis

__all__ = ["MCPServer", "rodar_stdio", "lista_tools_disponiveis"]
