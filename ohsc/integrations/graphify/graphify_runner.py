"""Graphify runner: orchestrates build / incremental / query with caching.

The runner owns the lifecycle of the OHSC-side graph:
  * Full build  -> graphify extract
  * Query       -> reuse existing graph.json when valid
  * Rebuild     -> only when missing / corrupted / forced
  * Caching     -> tracks graph version, vault mtime, build timestamp

It never touches the vault; it only reads it (READ-ONLY) during extract.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Optional

from .graphify_client import GraphifyClient, GraphBuildResult
from .graphify_config import ensure_workspace
from .graphify_brain import GraphifyBrain
from ...core.logging import get_logger
from ...core.filesystem import VaultBackend

logger = get_logger("ohsc.integrations.graphify.runner")


class GraphifyRunner:
    def __init__(self, system_root: Path, client: Optional[GraphifyClient] = None,
                 vault_root: Optional[Path] = None,
                 brain: Optional[GraphifyBrain] = None,
                 graphs_dir: Optional[Path] = None) -> None:
        self.paths = ensure_workspace(system_root)
        self.client = client or GraphifyClient()
        self.vault_root = Path(vault_root) if vault_root else None
        self.brain = brain or GraphifyBrain(system_root=system_root)
        self.meta_path = self.paths["config"] / "graph_meta.json"
        # graphs_dir lets callers (tests, one-off queries) point the runner at a
        # specific graph location instead of the default workspace graph.json.
        self.graphs_dir = Path(graphs_dir) if graphs_dir else self.paths["graphs"]

    # -- meta / caching ---------------------------------------------------
    def _read_meta(self) -> Dict[str, object]:
        if self.meta_path.exists():
            try:
                return json.loads(self.meta_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _write_meta(self, graph_ver: str, source_mtime: float) -> None:
        meta = {
            "graph_version": graph_ver,
            "source_vault": str(self.vault_root),
            "vault_mtime": source_mtime,
            "built_at": time.time(),
            "graph_path": str(self.paths["graphs"] / "graph.json"),
        }
        self.meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    @staticmethod
    def _vault_mtime(vault: Path) -> float:
        newest = 0.0
        for p in Path(vault).rglob("*"):
            if p.is_file():
                newest = max(newest, p.stat().st_mtime)
        return newest

    def needs_rebuild(self) -> bool:
        graph_file = self.paths["graphs"] / "graph.json"
        if not graph_file.exists():
            return True
        meta = self._read_meta()
        if not meta:
            # Graph exists but no metadata -> treat as stale.
            return True
        if self.vault_root:
            if self._vault_mtime(self.vault_root) > float(meta.get("vault_mtime", 0)):
                return True
        return False

    # -- build ------------------------------------------------------------
    def build(self, force: bool = False) -> GraphBuildResult:
        if self.vault_root is None:
            return GraphBuildResult(ok=False, error="VAULT PATH NOT CONFIGURED")
        if not self.vault_root.exists():
            return GraphBuildResult(ok=False, error="VAULT PATH MISMATCH")
        if (not force) and (not self.needs_rebuild()):
            # Reuse existing graph.
            g = self.paths["graphs"] / "graph.json"
            return GraphBuildResult(
                ok=True, graph_path=g, version=self.client.version(),
                stdout="(reused existing graph - no rebuild needed)",
            )
        result = self.client.build_graph(self.vault_root, self.paths["graphs"],
                                          env=self.brain.extract_env())
        if result.ok:
            self._write_meta(result.version, self._vault_mtime(self.vault_root))
        return result

    def graph_path(self) -> Path:
        return self.graphs_dir / "graph.json"

    def query(self, question: str, mode: str = "query") -> Dict[str, object]:
        g = self.graph_path()
        if not g.exists():
            return {"ok": False, "error": "GRAPH NOT BUILT"}
        res = self.client.query(question, g, mode=mode, env=self.brain.extract_env())
        return {"ok": res.ok, "query": res.query,
                "answer": res.answer, "error": res.error}

    def shortest_path(self, source: str, target: str,
                      undirected: bool = True) -> Dict[str, object]:
        g = self.graph_path()
        if not g.exists():
            return {"ok": False, "error": "GRAPH NOT BUILT"}
        res = self.client.shortest_path(source, target, g, undirected=undirected)
        return {"ok": res.ok, "query": res.query,
                "answer": res.answer, "error": res.error}

    def explain(self, node: str) -> Dict[str, object]:
        g = self.graph_path()
        if not g.exists():
            return {"ok": False, "error": "GRAPH NOT BUILT"}
        res = self.client.explain(node, g, env=self.brain.extract_env())
        return {"ok": res.ok, "query": res.query,
                "answer": res.answer, "error": res.error}
