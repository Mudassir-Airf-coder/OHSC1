"""Graphify MCP adapter.

Graphify ships an MCP server (the ``graphify-mcp`` executable, backed by
``python -m graphify.serve graph.json``) exposing tools: query_graph,
get_node, get_neighbors, get_community, god_nodes, graph_stats, shortest_path,
list_prs, get_pr_impact, triage_prs.

For an Obsidian knowledge-graph use case we surface only the graph-navigation
tools (the PR tools are code-repo specific and are intentionally excluded).
This adapter speaks to the MCP server over stdio and returns plain results so
the Graphify Agent can use either the CLI or the MCP server transparently.

NOTE: the MCP server must run inside Graphify's own uv-tool venv. We invoke the
standalone ``graphify-mcp`` executable and strip ``PYTHONPATH`` so it resolves
its own dependencies (same isolation rule as GraphifyClient).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from ...core.logging import get_logger

logger = get_logger("ohsc.integrations.graphify.mcp")

# Graph-navigation tools relevant to Obsidian vaults.
RELEVANT_TOOLS = ["query_graph", "get_node", "get_neighbors",
                  "god_nodes", "graph_stats", "shortest_path", "get_community"]


class GraphifyMCPClient:
    """Minimal MCP stdio client for Graphify's graph server."""

    def __init__(self, graph_path: str, timeout: int = 60) -> None:
        self.graph_path = graph_path
        self.timeout = timeout
        self._proc: Optional[subprocess.Popen] = None

    def is_available(self) -> bool:
        """Return True only if the MCP server can actually serve a request.

        ``graphify-mcp`` is a wrapper around ``graphify.serve`` which imports
        the ``mcp`` Python SDK. On this host the SDK's stdio/HTTP transports
        require optional dependencies (``pywintypes`` on Windows, or ``mcp +
        starlette + uvicorn`` for HTTP) that are not installed, so a bare
        ``shutil.which`` check is misleading. We therefore do a real
        round-trip probe: start the server, send an ``initialize`` handshake,
        and confirm a valid JSON-RPC response arrives. If the server crashes or
        never answers, the MCP adapter is unavailable and callers (and tests)
        should fall back to the ``graphify`` CLI interface.
        """
        if shutil.which("graphify-mcp") is None:
            return False
        proc = self._start()
        if proc is None or proc.stdin is None or proc.stdout is None:
            return False
        try:
            proc.stdin.write(json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2024-11-05",
                           "capabilities": {}, "clientInfo": {"name": "ohsc",
                                                              "version": "1.0"}},
            }) + "\n")
            proc.stdin.flush()
            # Expect a server->client initialize response (or any JSON-RPC line).
            # If the server is alive and speaks JSON-RPC, this returns quickly.
            line = proc.stdout.readline()
            return bool(line.strip()) and '"jsonrpc"' in line
        except Exception:  # noqa: BLE001
            return False
        finally:
            try:
                proc.terminate()
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    def _clean_env() -> Dict[str, str]:
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.pop("MCP_PATH", None)
        return env

    def _start(self) -> Optional[subprocess.Popen]:
        cmd = ["graphify-mcp", self.graph_path]
        try:
            self._proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, env=self._clean_env(),
            )
            return self._proc
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"MCP start failed: {exc}")
            return None

    def call(self, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool not in RELEVANT_TOOLS:
            return {"ok": False, "error": f"MCP tool not supported for vaults: {tool}"}
        proc = self._start()
        if proc is None or proc.stdin is None:
            return {"ok": False, "error": "MCP SERVER UNAVAILABLE"}
        try:
            # MCP initialize handshake then tools/call.
            proc.stdin.write(json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2024-11-05",
                           "capabilities": {}, "clientInfo": {"name": "ohsc",
                                                              "version": "1.0"}}}) + "\n")
            proc.stdin.flush()
            # read initialize response
            proc.stdout.readline()
            req = json.dumps({
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": tool, "arguments": arguments},
            })
            proc.stdin.write(req + "\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            data = json.loads(line) if line.strip() else {}
            result = data.get("result", {})
            content = result.get("content", [{}])
            text = content[0].get("text", "") if content else ""
            return {"ok": True, "tool": tool, "answer": text}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"MCP CALL ERROR: {exc}"}
        finally:
            if proc:
                proc.terminate()

    def close(self) -> None:
        if self._proc:
            self._proc.terminate()
