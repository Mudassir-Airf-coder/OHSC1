"""Graphify Agent — semantic graph intelligence for OHSC.

This agent is the ONLY part of OHSC that knows how Graphify works. It owns
graph extraction, semantic queries, shortest-path, explanation, community
and hub discovery. It is READ-ONLY against the user's vault by default:
a graph request only reads the vault and writes Graphify artifacts into the
OHSC workspace (``D:\\HOSC\\graphify``), never into the vault.

It complements (does NOT replace) the Linking Agent:
  * Linking Agent  -> explicit Obsidian wikilinks (structural, modifiable)
  * Graphify Agent -> semantic relationships (inferred/extracted, advisory)

EXTRACTED vs INFERRED provenance is preserved so inferred relationships are
never presented as explicit facts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ..core.agent_base import BaseAgent, AgentContract
from ..core.contracts import AgentResult, OpClass, Task, TaskStatus
from ..integrations.graphify.graphify_runner import GraphifyRunner
from ..integrations.graphify.graphify_client import GraphifyClient
from ..integrations.graphify.graphify_brain import GraphifyBrain


class GraphifyAgent(BaseAgent):
    name = "graphify_agent"
    role = "graph_intelligence"
    contract = AgentContract(
        name=name, role=role,
        responsibilities=[
            "Build semantic knowledge graph from the vault (read-only)",
            "Query graph: concepts, neighbors, shortest path, communities",
            "Explain conceptual relationships with provenance",
            "Discover hubs, orphans and hidden relationships",
        ],
        allowed_operations=["build", "query", "analyze", "explain"],
        input_contract="natural-language graph request + authorized flag",
        output_contract="graph analysis / query answer (no vault writes)",
        dependencies=["vault_agent", "path_safety"],
        permission_scope="read-only on vault; writes only to OHSC graphify workspace",
        reviewer_rules=[
            "Must never modify notes",
            "Must report GRAPHIFY UNAVAILABLE when binary missing",
            "Must distinguish EXTRACTED vs INFERRED edges",
            "Must keep all output outside the vault",
        ],
    )

    def __init__(self, runtime) -> None:
        super().__init__()
        self.rt = runtime
        self.client = GraphifyClient()
        self.brain = GraphifyBrain(system_root=runtime.config.system_root)
        self.runner = GraphifyRunner(
            runtime.config.system_root,
            client=self.client,
            vault_root=runtime.config.vault_root,
            brain=self.brain,
        )

    # -- vault safety gate ------------------------------------------------
    def _verify_vault(self) -> Any:
        vr = self.rt.config.vault_root
        if not vr.exists():
            return AgentResult(
                task_id="", agent=self.name, status=TaskStatus.FAILURE,
                summary="VAULT PATH MISMATCH",
                errors=["Configured vault_root does not exist: " + str(vr)],
            )
        if not (vr / ".obsidian").exists():
            return AgentResult(
                task_id="", agent=self.name, status=TaskStatus.FAILURE,
                summary="VAULT PATH MISMATCH",
                errors=["Path exists but is not an Obsidian vault: " + str(vr)],
            )
        return None

    # -- task dispatch ----------------------------------------------------
    def execute(self, task: Task) -> AgentResult:
        if not task.authorized:
            return AgentResult(
                task_id=task.id, agent=self.name, status=TaskStatus.FAILURE,
                summary="UNAUTHORIZED",
                errors=["Graphify analysis requires an authorized request."],
            )
        vault_err = self._verify_vault()
        if vault_err is not None:
            vault_err.task_id = task.id
            return vault_err

        action = task.action
        params = task.params

        if not self.client.is_available():
            return AgentResult(
                task_id=task.id, agent=self.name, status=TaskStatus.FAILURE,
                summary="GRAPHIFY UNAVAILABLE",
                errors=["The graphify executable is not installed."],
                data={"suggestion": "uv tool install graphifyy"},
            )

        try:
            if action == "build":
                force = params.get("force", False)
                res = self.runner.build(force=force)
                if not res.ok:
                    return AgentResult(
                        task_id=task.id, agent=self.name, status=TaskStatus.FAILURE,
                        summary=res.error or "GRAPH BUILD FAILED",
                        errors=[res.error], data={"stdout": res.stdout,
                                                  "stderr": res.stderr},
                    )
                return AgentResult(
                    task_id=task.id, agent=self.name, status=TaskStatus.SUCCESS,
                    summary=f"Graph built at {res.graph_path}",
                    data={"graph_path": str(res.graph_path),
                          "html_path": str(res.html_path) if res.html_path else "",
                          "report_path": str(res.report_path) if res.report_path else "",
                          "version": res.version},
                )

            if action == "query":
                q = params.get("query") or params.get("question") or task.target
                r = self.runner.query(q, mode="query")
                return self._query_result(task, r)

            if action == "shortest_path":
                src = params.get("source", "")
                tgt = params.get("target", "")
                r = self.runner.shortest_path(src, tgt)
                return self._query_result(task, r)

            if action == "explain":
                node = params.get("node") or task.target
                r = self.runner.explain(node)
                return self._query_result(task, r)

            if action == "analyze":
                # Lightweight structural report using our runner + client.
                g = self.runner.graph_path()
                if not g.exists():
                    return AgentResult(
                        task_id=task.id, agent=self.name, status=TaskStatus.FAILURE,
                        summary="GRAPH NOT BUILT",
                        errors=["Run graphify build first."],
                    )
                return AgentResult(
                    task_id=task.id, agent=self.name, status=TaskStatus.SUCCESS,
                    summary="Graph available for analysis.",
                    data={"graph_path": str(g),
                          "version": self.client.version()},
                )

            return AgentResult(
                task_id=task.id, agent=self.name, status=TaskStatus.FAILURE,
                summary="UNKNOWN ACTION", errors=[f"graphify: {action}"],
            )
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                task_id=task.id, agent=self.name, status=TaskStatus.FAILURE,
                summary=f"GRAPHIFY ERROR: {exc}", errors=[str(exc)],
            )

    @staticmethod
    def _query_result(task: Task, r: Dict[str, Any]) -> AgentResult:
        if not r.get("ok"):
            return AgentResult(
                task_id=task.id, agent="graphify_agent", status=TaskStatus.FAILURE,
                summary=r.get("error", "GRAPH QUERY FAILED"),
                errors=[r.get("error", "")], data={"query": r.get("query", "")},
            )
        return AgentResult(
            task_id=task.id, agent="graphify_agent", status=TaskStatus.SUCCESS,
            summary=(r.get("answer") or "")[:200],
            data={"query": r.get("query", ""), "answer": r.get("answer", "")},
        )

    def health(self) -> bool:
        return self.client.is_available()
