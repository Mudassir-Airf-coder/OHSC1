"""OHSC Universal Capability Gateway.

This is the thin, agent-facing access layer on top of the existing OHSC
system. It does NOT reimplement any agent, skill, or integration. It exposes:

  * a machine-readable capability manifest (``ohsc capabilities`` / ``ohsc manifest``)
  * an activation/health check (``ohsc activate``)
  * a status report (``ohsc status``)

External coding/AI agents (OpenCode, Claude Code, or any CLI agent) call
these to discover and use OHSC capabilities without knowing internal Python
details. The gateway delegates every real operation to the existing
components (Orchestrator, Graphify Agent, Graphify Brain, MCP adapter).

Design rules:
  * No secret ever appears in the manifest or status (only env-var *names*).
  * The gateway is read-only around the vault; it never writes to the vault.
  * It reuses the existing runtime/registry; it does not duplicate agents.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure D:\HOSC is importable when run from any directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from .config import load_config
from .integrations.graphify.graphify_brain_config import GraphifyBrainConfig
from .integrations.graphify.graphify_client import GraphifyClient


# ---------------------------------------------------------------------------
# Capability catalog (curated, accurate to the real registry — not invented).
# ---------------------------------------------------------------------------
GRAPHIFY_CAPABILITIES = [
    {
        "name": "build_graph",
        "purpose": "Build a semantic knowledge graph from a vault (read-only).",
        "inputs": {"vault_path": "path (authorized)"},
        "output": "graph.json + graph.html + GRAPH_REPORT.md",
        "read_only": True,
        "requires_llm": True,
    },
    {
        "name": "query_graph",
        "purpose": "Ask a natural-language question over the built graph.",
        "inputs": {"query": "string"},
        "output": "text answer",
        "read_only": True,
        "requires_llm": False,
    },
    {
        "name": "shortest_path",
        "purpose": "Conceptual shortest path between two concepts (undirected).",
        "inputs": {"source": "string", "target": "string"},
        "output": "path text",
        "read_only": True,
        "requires_llm": False,
    },
    {
        "name": "explain",
        "purpose": "Explain why/how a concept relates to others (provenance).",
        "inputs": {"node": "string"},
        "output": "explanation text",
        "read_only": True,
        "requires_llm": False,
    },
    {
        "name": "analyze",
        "purpose": "Structural report: hubs, communities, orphans, stats.",
        "inputs": {"vault_path": "path"},
        "output": "summary + graph.json reference",
        "read_only": True,
        "requires_llm": False,
    },
]

MCP_TOOLS = [
    "query_graph", "get_node", "get_neighbors",
    "god_nodes", "graph_stats", "shortest_path", "get_community",
]


def _agent_catalog() -> List[Dict[str, Any]]:
    """Build the agent catalog from the live registry (single source of truth)."""
    try:
        from .system import build_runtime
        rt = build_runtime()
        return rt.registry.list_agents()
    except Exception as exc:  # noqa: BLE001
        return [{"error": f"registry unavailable: {exc}"}]


def capability_manifest() -> Dict[str, Any]:
    """Return the full machine-readable capability manifest (no secrets)."""
    cfg = load_config()
    brain_cfg = GraphifyBrainConfig.from_env(cfg.system_root)

    manifest = {
        "ohsc": {
            "name": "OHSC (Hermes Obsidian System Control)",
            "root": str(cfg.system_root),
            "version": "1.0",
            "description": (
                "Autonomous multi-agent control plane for an Obsidian vault. "
                "The Universal Capability Gateway exposes its agents/skills/"
                "Graphify Brain/MCP to external coding/AI agents via one command."
            ),
        },
        "activation": {
            "command": "ohsc activate",
            "note": "Resolves D:\\HOSC automatically from any directory.",
        },
        "architecture": [
            "Planner", "Orchestrator", "Agents", "Skills",
            "Integrations", "Reviewer", "Graphify",
            "Graphify Brain", "MCP",
        ],
        "capability_groups": {
            "graphify": {
                "purpose": "Semantic knowledge-graph analysis of a vault.",
                "backend": "Graphify (graphifyy PyPI package) + Graphify Brain",
                "llm_backend": brain_cfg.provider,
                "model": brain_cfg.model,
                "operations": GRAPHIFY_CAPABILITIES,
                "mcp_tools": MCP_TOOLS,
                "safety": "Read-only on the vault; artifacts written to OHSC workspace.",
            },
            "agents": {
                "purpose": "Specialized vault operations (notes, search, links, ...).",
                "discovery": "ohsc --agents",
                "safety": "WRITE/DESTRUCTIVE ops require explicit authorization.",
            },
            "orchestrator": {
                "purpose": "Plan -> execute -> review a natural-language request.",
                "command": "ohsc \"<natural language request>\"",
                "safety": "Strict mode; destructive ops require --authorized.",
            },
        },
        "supported_external_agents": ["OpenCode", "Claude Code", "any CLI coding agent"],
        "interfaces": {
            "cli": "ohsc <subcommand>",
            "mcp": "graphify-mcp (Graphify's own MCP server, graph-navigation tools)",
            "python": "import ohsc; ohsc.build_runtime()",
        },
        "vault": {
            "authorized_root": str(cfg.vault_root),
            "read_only": True,
            "note": "The real vault is never modified by Graphify analysis.",
        },
        "safety": [
            "Never expose API keys (env-var names only).",
            "Never modify the real vault without explicit authorization.",
            "Never delete user data.",
            "Never fabricate graph results.",
            "Use temporary vaults for testing.",
        ],
    }
    return manifest


def activation_status() -> Dict[str, Any]:
    """Verify installation, config, agents, Graphify, Graphify Brain, env, MCP.

    Returns a structured status object. No secrets are included.
    """
    cfg = load_config()
    brain_cfg = GraphifyBrainConfig.from_env(cfg.system_root)
    client = GraphifyClient()

    checks: Dict[str, Any] = {}

    # 1. Installation
    checks["installation"] = {
        "ok": Path(__file__).resolve().parent.parent.exists(),
        "root": str(cfg.system_root),
    }
    # 2. Python
    checks["python"] = {
        "ok": True,
        "version": sys.version.split()[0],
    }
    # 3. Configuration
    checks["config"] = {
        "ok": True,
        "system_root": str(cfg.system_root),
        "vault_root": str(cfg.vault_root),
        "safety_mode": cfg.safety_mode,
    }
    # 4. Agent registry
    try:
        agents = _agent_catalog()
        reg_ok = isinstance(agents, list) and len(agents) > 0 and "error" not in (agents[0] or {})
        checks["agent_registry"] = {
            "ok": reg_ok,
            "agent_count": len(agents) if reg_ok else 0,
        }
    except Exception as exc:  # noqa: BLE001
        checks["agent_registry"] = {"ok": False, "error": str(exc)}

    # 5. Graphify integration
    gf_available = client.is_available()
    checks["graphify"] = {
        "ok": gf_available,
        "version": client.version() if gf_available else "",
        "binary": client._resolve() if gf_available else None,
    }

    # 6. Graphify Brain config
    checks["graphify_brain"] = {
        "ok": True,
        "provider": brain_cfg.provider,
        "model": brain_cfg.model,
        "key_env": brain_cfg.key_env,           # name only
        "key_present": brain_cfg.has_key(),     # bool only — never the value
        "endpoint": brain_cfg.endpoint,
    }

    # 7. OpenCode backend configuration
    oc_exe = shutil.which("opencode")
    checks["opencode_backend"] = {
        "ok": bool(oc_exe) and brain_cfg.provider == "opencode",
        "executable_present": bool(oc_exe),
        "transport": "opencode run -m <model> (CLI) -> HY3",
    }

    # 8. Required environment variables (presence only)
    checks["environment"] = {
        "ok": brain_cfg.has_key() or brain_cfg.provider != "opencode",
        "GRAPHIFY_BRAIN_BACKEND": os.environ.get("GRAPHIFY_BRAIN_BACKEND", "opencode"),
        "OPENCODE_API_KEY_present": bool(os.environ.get("OPENCODE_API_KEY")),
    }

    # 9. MCP capability
    mcp_exe = shutil.which("graphify-mcp")
    checks["mcp"] = {
        "ok": bool(mcp_exe),
        "executable_present": bool(mcp_exe),
        "tools": MCP_TOOLS,
    }

    overall = all(
        c.get("ok", False) for c in checks.values()
        if isinstance(c, dict)
    )
    checks["overall"] = "ACTIVE" if overall else "DEGRADED"
    return checks


def format_activation(checks: Dict[str, Any]) -> str:
    lines = ["OHSC Capability Gateway", "=" * 40]
    overall = checks.get("overall", "UNKNOWN")
    lines.append(f"Status: {overall}")
    lines.append("")
    lines.append("Capabilities:")
    lines.append("  - Agent orchestration (Planner/Orchestrator/Reviewer)")
    lines.append("  - Graphify (semantic knowledge graph)")
    lines.append("  - Graphify Brain")
    lines.append("  - Knowledge graph queries / shortest path / communities")
    lines.append("  - Vault operations (read/write, authorized)")
    lines.append("  - MCP (graph-navigation tools)")
    lines.append("")
    gb = checks.get("graphify_brain", {})
    lines.append(f"Graphify Brain:")
    lines.append(f"  Backend: {gb.get('provider', '?')}")
    lines.append(f"  Model:   {gb.get('model', '?')}")
    lines.append(f"  Key:     {'CONFIGURED' if gb.get('key_present') else 'MISSING'} "
                 f"({gb.get('key_env', '?')})")
    oc = checks.get("opencode_backend", {})
    lines.append(f"  OpenCode CLI: {'PRESENT' if oc.get('executable_present') else 'MISSING'}")
    gf = checks.get("graphify", {})
    lines.append(f"  Graphify: {'AVAILABLE' if gf.get('ok') else 'UNAVAILABLE'} "
                 f"({gf.get('version', '')})")
    lines.append("")
    lines.append("Command reference:")
    lines.append("  ohsc activate        -> gateway status")
    lines.append("  ohsc capabilities    -> machine-readable manifest")
    lines.append("  ohsc status          -> health checks")
    lines.append("  ohsc --agents        -> list registered agents")
    lines.append("  ohsc \"<request>\"      -> run a natural-language task")
    lines.append("  ohsc --graphify build \"<vault>\"  -> build knowledge graph")
    return "\n".join(lines)


def format_manifest(manifest: Dict[str, Any]) -> str:
    return json.dumps(manifest, indent=2)


def write_capabilities_json(path: Optional[str] = None) -> Path:
    """Emit a static machine-readable capability manifest file.

    Lets external agents discover OHSC capabilities without invoking ``ohsc``
    (they can just read ``D:\\HOSC\\capabilities\\capabilities.json``). No secrets
    are written. By default writes to the spec-preferred location
    ``D:\\HOSC\\capabilities\\capabilities.json``; if ``path`` is given, writes
    there instead.
    """
    target = Path(path) if path else (Path(__file__).resolve().parent.parent / "capabilities" / "capabilities.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_manifest(capability_manifest()), encoding="utf-8")
    return target
