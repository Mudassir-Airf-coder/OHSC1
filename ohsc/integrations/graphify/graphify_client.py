"""Graphify CLI client adapter.

Isolates all Graphify subprocess invocation behind a single, clean
interface so the rest of OHSC never shells out to ``graphify`` directly.

Graphify (https://github.com/Graphify-Labs/graphify) is a knowledge-graph
tool that turns a folder of mixed content (code, docs, PDFs, images,
markdown notes) into a queryable graph. The PyPI package is ``graphifyy``;
the CLI command is ``graphify``.

Supported, documented operations used by OHSC:
  * ``graphify extract <dir>``            -> builds graphify-out/graph.json (+ html/report)
  * ``graphify query "<q>" --graph G``   -> semantic question over the graph
  * ``graphify path A B --graph G``      -> shortest conceptual path
  * ``graphify explain X --graph G``     -> why two concepts relate

All operations are READ-ONLY against the source vault. Output is written
ONLY under the OHSC graphify workspace, never inside the user's vault.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ...core.logging import get_logger

logger = get_logger("ohsc.integrations.graphify")

_TRANSIENT_RETRIES = 2
_TRANSIENT_BACKOFF_S = (1.0, 3.0)
_BREAKER_THRESHOLD = 3
_BREAKER_COOLDOWN_S = 30.0
_BREAKER_HALF_OPEN = "half_open"
_BREAKER_CLOSED = "closed"
_BREAKER_OPEN = "open"


class GraphifyUnavailable(RuntimeError):
    """Raised when the circuit breaker is open and short-circuits a call."""


@dataclass
class _Breaker:
    state: str = _BREAKER_CLOSED
    consecutive_failures: int = 0
    opened_at: float = 0.0

    def allow(self) -> bool:
        if self.state == _BREAKER_CLOSED:
            return True
        if self.state == _BREAKER_OPEN:
            if time.time() - self.opened_at >= _BREAKER_COOLDOWN_S:
                self.state = _BREAKER_HALF_OPEN
                return True
            return False
        return True

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = _BREAKER_CLOSED

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        if self.consecutive_failures >= _BREAKER_THRESHOLD:
            self.state = _BREAKER_OPEN
            self.opened_at = time.time()


_TRANSIENT_MARKERS = ("timeout", "timed out", "temporarily", "connection",
                       "503", "504", "502", "500", "internal server",
                       "unavailable", "reset", "try again")


def _looks_transient(text: str) -> bool:
    return any(m in text for m in _TRANSIENT_MARKERS)


def _is_transient(proc: "subprocess.CompletedProcess", exc: Optional[BaseException]) -> bool:
    if isinstance(exc, subprocess.TimeoutExpired):
        return True
    if proc is None or proc.returncode == 0:
        return False
    return (_looks_transient((proc.stderr or "").lower())
            or _looks_transient((proc.stdout or "").lower()))


@dataclass
class GraphBuildResult:
    ok: bool
    graph_path: Optional[Path] = None
    html_path: Optional[Path] = None
    report_path: Optional[Path] = None
    version: str = ""
    error: str = ""
    stdout: str = ""
    stderr: str = ""


@dataclass
class GraphQueryResult:
    ok: bool
    query: str = ""
    answer: str = ""
    error: str = ""
    raw: str = ""


class GraphifyClient:
    """Thin, safe wrapper around the ``graphify`` CLI."""

    def __init__(self, graphify_bin: Optional[str] = None, timeout: int = 600) -> None:
        self.bin = graphify_bin or self._detect_binary()
        self.timeout = timeout
        self.breaker = _Breaker()

    @staticmethod
    def _detect_binary() -> Optional[str]:
        found = shutil.which("graphify")
        if found:
            return found
        return None

    def is_available(self) -> bool:
        return self._resolve() is not None

    def _resolve(self) -> Optional[str]:
        if self.bin:
            return self.bin
        found = shutil.which("graphify")
        if found:
            return found
        return f"{self._python_bin()} -m graphify" if self._module_runs() else None

    @staticmethod
    def _python_bin() -> str:
        """Prefer python3 (Ubuntu/Debian), fall back to python (Windows/venv)."""
        for cand in ("python3", "python"):
            if shutil.which(cand):
                return cand
        return "python3"

    def _module_runs(self) -> bool:
        try:
            subprocess.run(
                [self._python_bin(), "-m", "graphify", "--help"],
                capture_output=True, timeout=30,
                env=self._clean_env(),
            )
            return True
        except Exception:
            return False

    @staticmethod
    def _clean_env() -> Dict[str, str]:
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        return env

    @staticmethod
    def _openai_compatible_provider() -> bool:
        backend = (os.environ.get("GRAPHIFY_BRAIN_BACKEND") or "").strip().lower()
        if backend in ("groq", "openrouter", "openai"):
            return True
        base = (os.environ.get("OPENAI_BASE_URL") or "").strip()
        return bool(base)

    def _inject_openai_backend(self, cmd: List[str], env: Dict[str, str]) -> List[str]:
        if not self._openai_compatible_provider() and not env.get("OPENAI_API_KEY"):
            return cmd
        if "--backend" not in cmd:
            cmd = list(cmd) + ["--backend", "openai"]
        return cmd

    def _run(self, cmd: List[str], env: Optional[Dict[str, str]] = None) -> "subprocess.CompletedProcess":
        if not self.breaker.allow():
            raise GraphifyUnavailable(
                f"circuit open: {_BREAKER_THRESHOLD} consecutive failures; "
                f"cooldown {_BREAKER_COOLDOWN_S}s remaining")
        run_env = env if env is not None else self._clean_env()
        last_exc: Optional[BaseException] = None
        for attempt in range(_TRANSIENT_RETRIES + 1):
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True,
                    timeout=self.timeout, env=run_env)
                if proc.returncode == 0:
                    self.breaker.record_success()
                    return proc
                if attempt == _TRANSIENT_RETRIES:
                    if _is_transient(proc, None):
                        self.breaker.record_failure()
                    return proc
                if not _is_transient(proc, None):
                    return proc
                logger.warning(
                    f"graphify transient exit rc={proc.returncode} "
                    f"attempt={attempt + 1}/{_TRANSIENT_RETRIES + 1}; "
                    f"retrying. stderr_tail={(proc.stderr or '').strip()[-160:]}")
            except subprocess.TimeoutExpired as exc:
                last_exc = exc
                if attempt == _TRANSIENT_RETRIES:
                    self.breaker.record_failure()
                    raise
                logger.warning(
                    f"graphify timeout after {self.timeout}s "
                    f"attempt={attempt + 1}/{_TRANSIENT_RETRIES + 1}; retrying.")
            time.sleep(_TRANSIENT_BACKOFF_S[min(attempt, len(_TRANSIENT_BACKOFF_S) - 1)])
        assert last_exc is not None
        raise last_exc

    def version(self) -> str:
        exe = self._resolve()
        if not exe:
            return ""
        try:
            if exe.endswith("graphify") or exe == "graphify":
                out = self._run([exe, "--version"]).stdout
            else:
                out = self._run(exe.split() + ["--version"]).stdout
            return out.strip().splitlines()[0] if out.strip() else ""
        except Exception as exc:
            logger.warning(f"graphify version probe failed: {exc}")
            return ""

    def build_graph(self, source_dir: Path, out_dir: Path,
                    env: Optional[Dict[str, str]] = None) -> GraphBuildResult:
        exe = self._resolve()
        if not exe:
            return GraphBuildResult(ok=False, error="GRAPHIFY UNAVAILABLE")
        source_dir = Path(source_dir)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        run_env = env if env is not None else self._clean_env()
        cmd = (exe.split() if " " in exe else [exe]) + ["extract", str(source_dir)]
        cmd = self._inject_openai_backend(cmd, run_env)
        try:
            proc = self._run(cmd, env=run_env)
        except GraphifyUnavailable as exc:
            return GraphBuildResult(ok=False, error=f"GRAPHIFY UNAVAILABLE: {exc}")
        except subprocess.TimeoutExpired:
            return GraphBuildResult(ok=False, error="GRAPHIFY TIMEOUT")
        except Exception as exc:
            return GraphBuildResult(ok=False, error=f"GRAPHIFY SUBPROCESS ERROR: {exc}")

        src_out = source_dir / "graphify-out"
        graph_path = src_out / "graph.json"
        if not graph_path.exists() or proc.returncode != 0:
            return GraphBuildResult(
                ok=False, error="GRAPH BUILD FAILED",
                stdout=proc.stdout, stderr=proc.stderr,
            )
        moved_graph = out_dir / "graph.json"
        shutil.copy2(graph_path, moved_graph)
        html_path = None
        report_path = None
        for name in ("graph.html", "GRAPH_REPORT.md"):
            src = src_out / name
            if src.exists():
                dst = out_dir / name
                shutil.copy2(src, dst)
                if name.endswith(".html"):
                    html_path = dst
                else:
                    report_path = dst
        shutil.rmtree(src_out, ignore_errors=True)
        return GraphBuildResult(
            ok=True, graph_path=moved_graph, html_path=html_path,
            report_path=report_path, version=self.version(),
            stdout=proc.stdout, stderr=proc.stderr,
        )

    def query(self, question: str, graph_path: Path,
              mode: str = "query", extra_args: Optional[List[str]] = None,
              positional: Optional[List[str]] = None,
              env: Optional[Dict[str, str]] = None) -> GraphQueryResult:
        exe = self._resolve()
        if not exe:
            return GraphQueryResult(ok=False, query=question, error="GRAPHIFY UNAVAILABLE")
        if not Path(graph_path).exists():
            return GraphQueryResult(ok=False, query=question, error="GRAPH NOT BUILT")
        cmd = (exe.split() if " " in exe else [exe]) + [mode]
        if positional:
            cmd.extend(positional)
        else:
            cmd.append(question)
        cmd += ["--graph", str(graph_path)]
        if extra_args:
            cmd.extend(extra_args)
        try:
            proc = self._run(cmd, env=env if env is not None else self._clean_env())
        except GraphifyUnavailable as exc:
            return GraphQueryResult(ok=False, query=question, error=f"GRAPHIFY UNAVAILABLE: {exc}")
        except subprocess.TimeoutExpired:
            return GraphQueryResult(ok=False, query=question, error="GRAPHIFY TIMEOUT")
        except Exception as exc:
            return GraphQueryResult(ok=False, query=question, error=f"GRAPHIFY SUBPROCESS ERROR: {exc}")
        if proc.returncode != 0:
            return GraphQueryResult(ok=False, query=question, error="GRAPH QUERY FAILED", raw=proc.stderr)
        return GraphQueryResult(ok=True, query=question, answer=proc.stdout.strip(), raw=proc.stdout)

    def shortest_path(self, source: str, target: str,
                      graph_path: Path, undirected: bool = True) -> GraphQueryResult:
        extra = ["--undirected"] if undirected else []
        return self.query(f"{source} -> {target}", graph_path, mode="path",
                          extra_args=extra, positional=[source, target])

    def explain(self, node: str, graph_path: Path,
                env: Optional[Dict[str, str]] = None) -> GraphQueryResult:
        return self.query(node, graph_path, mode="explain", env=env)
