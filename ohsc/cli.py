"""OHSC command-line entry point.

Usage:
    python -m ohsc.cli "Create a note titled Hello with content Hi there"
    python -m ohsc.cli --dry-run "Create a MOC for Python"
    python -m ohsc.cli --authorized --agents
    python -m ohsc.cli --request "Find orphan notes"

The CLI is deliberately thin: it builds the runtime, asks the Orchestrator
to handle the request and prints a structured result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the package root is importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from .system import build_runtime
from .core.orchestrator import Orchestrator
from .gateway import (
    capability_manifest, activation_status, format_activation, format_manifest,
)

_GATEWAY_HELP = {
    "activate": "Gateway activation + status check",
    "capabilities": "Machine-readable capability manifest",
    "manifest": "Alias for capabilities",
    "status": "Health checks",
}


def main(argv=None) -> int:
    # Detect gateway subcommands from argv BEFORE argparse, so they never
    # collide with the natural-language positional request. This keeps both
    #   ohsc activate            (gateway command)
    #   ohsc "build a graph"     (NL request)
    #   ohsc --graphify query "x" (direct graphify mode)
    # unambiguous without a fragile subparser.
    _argv = list(sys.argv[1:] if argv is None else argv)
    _gateway_cmds = {"activate", "capabilities", "manifest", "status", "agents", "run", "doctor"}
    _first = next((a for a in _argv if not a.startswith("-")), None)
    if _first in _gateway_cmds and "--graphify" not in _argv:
        cmd = _first
        as_json = "--json" in _argv
        if cmd == "run":
            from .core.session import create_session_token
            from .gateway import activation_status, format_activation
            checks = activation_status()
            session = create_session_token()
            if as_json:
                payload = {
                    "activation": checks,
                    "session": session,
                }
                print(json.dumps(payload, indent=2, default=str))
            else:
                print(format_activation(checks))
                print()
                print("OHSC Session")
                print("=" * 40)
                print(f"Token     : {session['token']}")
                print(f"Expires   : {session['expires_at']} (unix)")
                print(f"Skill     : {session['skill_path']}")
                print()
                print("Next steps for any AI tool:")
                print("  1. Copy the token above")
                print("  2. Read skills/OHSC_AGENT_SKILL.md")
                print("  3. Run: ohsc activate")
                print("  4. Run: ohsc capabilities --json")
                print("  5. Run: ohsc agents --json")
            return 0 if checks.get("overall") in ("ACTIVE", "DEGRADED") else 1

        if cmd == "doctor":
            from .gateway import activation_status
            checks = activation_status()
            if as_json:
                print(json.dumps(checks, indent=2, default=str))
            else:
                print("OHSC Doctor")
                print("=" * 40)
                for k, v in checks.items():
                    if k == "overall":
                        continue
                    print(f"  {k}: {v}")
                print("-" * 40)
                print(f"Overall: {checks.get('overall')}")
            return 0 if checks.get("overall") == "ACTIVE" else 1

        if cmd == "agents":
            rt = build_runtime()
            if as_json:
                agents = []
                for a in rt.registry.list_agents():
                    agents.append({
                        "name": a.get("name"),
                        "intent": a.get("role"),
                        "enabled": a.get("enabled", True),
                        "healthy": a.get("healthy", True),
                    })
                out = {
                    "total": rt.registry.count(),
                    "enabled": rt.registry.enabled_count(),
                    "agents": agents,
                }
                print(json.dumps(out, indent=2, default=str))
                return 0
            print(rt.registry.summary())
            print(f"\nTotal agents: {rt.registry.count()}  (enabled: {rt.registry.enabled_count()})")
            return 0
        return _gateway_command(cmd, as_json, _argv)

    parser = argparse.ArgumentParser(prog="ohsc", description="Obsidian System Control")
    parser.add_argument("request", nargs="*", help="Natural-language request")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes only")
    parser.add_argument("--authorized", action="store_true",
                        help="Explicitly authorize write/destructive ops")
    parser.add_argument("--agents", action="store_true", help="List registered agents (legacy)")
    parser.add_argument("--no-review", action="store_true", help="Skip reviewer")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--graphify", metavar="MODE",
                        choices=["build", "query", "path", "explain", "analyze"],
                        help="Run a Graphify operation directly (build/query/path/explain/analyze)")
    parser.add_argument("--source", help="For --graphify path: source node")
    parser.add_argument("--target", help="For --graphify path: target node")
    parser.add_argument("--node", help="For --graphify explain: node")
    args = parser.parse_args(argv)

    rt = build_runtime()

    request = " ".join(args.request).strip()

    # Dedicated Graphify mode: hide Graphify internals behind one flag.
    if args.graphify:
        from .core.contracts import OpClass, Task
        if not args.authorized:
            print("NOTE: Graphify analysis is read-only; use --authorized to proceed.")
        action = args.graphify
        if action == "path":
            action = "shortest_path"
        params = {"request": request}
        if action == "shortest_path":
            params.update({"source": args.source or "", "target": args.target or ""})
        elif action == "explain":
            params["node"] = args.node or request
        else:
            params["query"] = request
        task = Task(agent="graphify_agent", action=action, target=request,
                    op_class=OpClass.READ, authorized=args.authorized or True,
                    params=params)
        res = rt.registry.get("graphify_agent").execute(task)
        out = res.to_dict()
        if args.json:
            print(json.dumps(out, indent=2, default=str))
        else:
            print("=" * 60)
            print("GRAPHIFY AGENT:", action)
            print("STATUS        :", out["status"])
            print("SUMMARY       :", out["summary"])
            if out.get("data", {}).get("answer"):
                print("ANSWER        :\n" + out["data"]["answer"])
            if out.get("data", {}).get("graph_path"):
                print("GRAPH PATH    :", out["data"]["graph_path"])
            if out["errors"]:
                print("ERRORS        :", "; ".join(out["errors"]))
            # Surface real subprocess output on failure (Issue G).
            data = out.get("data") or {}
            status = (out.get("status") or "").upper()
            if status in ("FAILURE", "FAILED", "ERROR") or not res.ok():
                for key in ("stderr", "stdout"):
                    val = data.get(key)
                    if val:
                        tail = str(val)
                        if len(tail) > 500:
                            tail = "...(truncated)...\n" + tail[-500:]
                        print(f"{key.upper():<14}:", tail)
            print("=" * 60)
        return 0 if res.ok() else 2

    if args.agents:
        print(rt.registry.summary())
        print(f"\nTotal agents: {rt.registry.count()}  (enabled: {rt.registry.enabled_count()})")
        return 0

    request = " ".join(args.request).strip()
    if not request:
        parser.print_help()
        return 1

    orch = Orchestrator(rt)
    result = orch.handle(
        request,
        authorized=args.authorized,
        dry_run=args.dry_run,
        skip_review=args.no_review,
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 60)
        print("OHSC REQUEST:", request)
        print("STATUS      :", result["status"])
        print("PLAN STEPS  :", result["plan_steps"])
        if result.get("review"):
            rev = result["review"]
            print("REVIEW      :", rev.get("status"), "| APPROVED:", rev.get("approved"))
            if rev.get("required_fixes"):
                print("FIXES       :", "; ".join(rev["required_fixes"]))
        print("=" * 60)
        for step in result["report"]["steps"]:
            print(f"  [{step['status']}] {step['agent']}: {step['summary']}")
    return 0 if result["status"] == "SUCCESS" else 2


def _gateway_command(command: str, as_json: bool, argv: list) -> int:
    """Handle the agent-facing gateway subcommands."""
    if command == "activate":
        checks = activation_status()
        if as_json:
            print(json.dumps(checks, indent=2, default=str))
        else:
            print(format_activation(checks))
        return 0 if checks.get("overall") == "ACTIVE" else 1

    if command in ("capabilities", "manifest"):
        manifest = capability_manifest()
        if "--write" in argv:
            from .gateway import write_capabilities_json
            p = write_capabilities_json()
            print(f"Manifest written: {p}")
        if as_json:
            print(format_manifest(manifest))
        else:
            # Human-readable summary of the manifest.
            print("OHSC Capability Manifest")
            print("=" * 40)
            print(f"Root     : {manifest['ohsc']['root']}")
            print(f"Backend  : Graphify Brain -> {manifest['capability_groups']['graphify']['llm_backend']}")
            print(f"Model    : {manifest['capability_groups']['graphify']['model']}")
            print("")
            print("GRAPHIFY OPERATIONS:")
            for op in manifest["capability_groups"]["graphify"]["operations"]:
                ro = "RO" if op["read_only"] else "RW"
                print(f"  [{ro}] {op['name']:<16} {op['purpose']}")
            print("")
            print("MCP TOOLS:")
            print("  " + ", ".join(manifest["capability_groups"]["graphify"]["mcp_tools"]))
            print("")
            print("INTERFACES:")
            for k, v in manifest["interfaces"].items():
                print(f"  {k:<8}: {v}")
        return 0

    if command == "status":
        checks = activation_status()
        if as_json:
            print(json.dumps(checks, indent=2, default=str))
        else:
            print("OHSC Gateway Status")
            print("=" * 40)
            for name, c in checks.items():
                if name == "overall":
                    print(f"OVERALL: {c}")
                    continue
                if isinstance(c, dict):
                    ok = c.get("ok", "?")
                    extra = {k: v for k, v in c.items() if k != "ok"}
                    print(f"  [{ok}] {name}: {extra}")
        return 0 if checks.get("overall") == "ACTIVE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
