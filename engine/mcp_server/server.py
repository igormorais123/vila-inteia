"""
Servidor MCP stdio (JSON-RPC 2.0).

Implementa protocolo MCP 2024-11-05 mínimo: initialize, tools/list, tools/call.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from engine.mcp_server.tools import lista_tools_disponiveis, executar_tool, TOOLS


class MCPServer:
    def __init__(self, server_name: str = "vila-inteia", version: str = "0.1.0"):
        self.server_name = server_name
        self.version = version

    def handle_request(self, req: dict) -> dict:
        method = req.get("method", "")
        req_id = req.get("id")
        params = req.get("params", {})

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": self.server_name, "version": self.version},
                }
            elif method == "tools/list":
                result = {"tools": lista_tools_disponiveis()}
            elif method == "tools/call":
                tool_name = params.get("name", "")
                args = params.get("arguments", {})
                r = executar_tool(tool_name, args)
                result = {
                    "content": [{"type": "text", "text": json.dumps(r, ensure_ascii=False)}],
                }
            elif method == "ping":
                result = {}
            else:
                return {
                    "jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32601, "message": f"método desconhecido: {method}"},
                }
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as e:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32603, "message": f"{type(e).__name__}: {e}"},
            }


def rodar_stdio() -> None:
    """Loop stdio JSON-RPC. Lê linha, processa, escreve linha."""
    server = MCPServer()
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue
        try:
            req = json.loads(linha)
            resp = server.handle_request(req)
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError as e:
            err = {"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse error: {e}"}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    rodar_stdio()
