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

# Transient-retry policy for subprocess calls into the external ``graphify``
# CLI (which in turn talks to the configured LLM). Backend cold-starts /
# network blips can cause one-shot timeouts or non-zero exits that succeed on
# the next attempt. We retry with bounded exponential backoff; permanent
# failures (CLI missing, bad args, repeated timeouts) bubble up immediately
# so we don't paper over real bugs.
_TRANSIENT_RETRIES = 2          # max additional attempts (3 total)
_TRANSIENT_BACKOFF_S = (1.0, 3.0)  # sleep between attempts

# Circuit breaker: after N consecutive FAILED _run() invocations (each of
# which already exhausted its own retry budget), short-circuit subsequent
# calls for a cooldown window. The breaker is per-GraphifyClient so test
# isolation is preserved. Half-open probe after cooldown.
_BREAKER_THRESHOLD = 3          # consecutive failed _run() to open
_BREAKER_COOLDOWN_S = 30.0       # how long to stay open
_BREAKER_HALF_OPEN = "half_open" # state strings
_BREAKER_CLOSED = "closed"
_BREAKER_OPEN = "open"


class GraphifyUnavailable(RuntimeError):
    """Raised when the circuit breaker is open and short-circuits a call.

    The caller (runner / agent) should surface this as a transient error
    and skip rather than burn budget. After cooldown the next call is
    allowed as a half-open probe; success closes the breaker.
    """


@dataclass
class _Breaker:
    state: str = _BREAKER_CLOSED
    consecutive_failures: int = 0
    opened_at: float = 0.0

    def allow(self) -> bool:
        """Return True if a call is allowed to proceed right now."""
        if self.state == _BREAKER_CLOSED:
            return True
        if self.state == _BREAKER_OPEN:
            if time.time() - self.opened_at >= _BREAKER_COOLDOWN_S:
                self.state = _BREAKER_HALF_OPEN
                return True
            return False
        # half_open: allow exactly one probe at a time; the next call after
        # the probe settles will resolve state.
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
    """Return True when the subprocess failure is worth retrying.

    Heuristic: timeouts always retry. Non-zero returncodes retry if EITHER
    stderr OR stdout carries a transient-looking signal (timeout / 5xx /
    network / retry). Permanent errors (bad args, auth) surface immediately.
    Scanning both streams matters because the upstream CLI may wrap
    backend errors as JSON in stdout instead of writing to stderr.
    """
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
    """Thin, safe wrapper around the ``graphify`` CLI.

    NOTE on environment isolation: Graphify is installed in its own uv-tool
    Python venv. The host process (e.g. the Hermes agent venv) may export a
    ``PYTHONPATH`` that shadows Graphify's bundled numpy/openai with incompatible
    copies, causing hard import crashes. Every subprocess therefore runs with
    ``PYTHONPATH`` stripped so Graphify always resolves its own dependencies.
    """

    def __init__(self, graphify_bin: Optional[str] = None, timeout: int = 600) -> None:
        self.bin = graphify_bin or self._detect_binary()
        self.timeout = timeout
        # Per-client circuit breaker. Isolated across instances so tests
        # sharing the module don't leak failure state into each other.
        self.breaker = _Breaker()

    # -- discovery --------------------------------------------------------
    @staticmethod
    def _detect_binary() -> Optional[str]:
        found = shutil.which("graphify")
        if found:
            return found
        # uv-installed tools usually live here; fall back to module form.
        return None

    def is_available(self) -> bool:
        return self._resolve() is not None

    def _resolve(self) -> Optional[str]:
        if self.bin:
            return self.bin
        # Try python -m graphify as a fallback (same package).
        return "python -m graphify" if self._module_runs() else None

    def _module_runs(self) -> bool:
        try:
            subprocess.run(
                ["python", "-m", "graphify", "--help"],
                capture_output=True, timeout=30,
                env=self._clean_env(),
            )
            return True
        except Exception:
            return False

    @staticmethod
    def _clean_env() -> Dict[str, str]:
        """Return a copy of the environment with PYTHONPATH removed.

        This prevents the host venv's site-packages from shadowing Graphify's
        own numpy/openai and triggering ABI import crashes.
        """
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        return env

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
                    # out of attempts; classify for the breaker BEFORE returning
                    if _is_transient(proc, None):
                        self.breaker.record_failure()
                    return proc
                if not _is_transient(proc, None):
                    # permanent — breaker unaffected
                    return proc
                # transient — log + back off + retry
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
        # unreachable; loop returns or raises
        assert last_exc is not None
        raise last_exc

    def version(self) -> str:
        """Return the installed graphify version string, or '' if unknown."""
        exe = self._resolve()
        if not exe:
            return ""
        try:
            if exe.endswith("graphify") or exe == "graphify":
                out = self._run([exe, "--version"]).stdout
            else:
                out = self._run(exe.split() + ["--version"]).stdout
            return out.strip().splitlines()[0] if out.strip() else ""
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"graphify version probe failed: {exc}")
            return ""

    # -- build ------------------------------------------------------------
    def build_graph(self, source_dir: Path, out_dir: Path,
                    env: Optional[Dict[str, str]] = None) -> GraphBuildResult:
        """Run ``graphify extract`` against ``source_dir``.

        Output is redirected to ``out_dir`` by copying graphify-out after the
        run (graphify writes into the source dir by default). READ-ONLY on the
        source vault.
        """
        exe = self._resolve()
        if not exe:
            return GraphBuildResult(ok=False, error="GRAPHIFY UNAVAILABLE")
        source_dir = Path(source_dir)
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        # Graphify writes into <source>/graphify-out; we run there then move.
        cmd = (exe.split() if " " in exe else [exe]) + ["extract", str(source_dir)]
        try:
            proc = self._run(cmd, env=env)
        except GraphifyUnavailable as exc:
            return GraphBuildResult(ok=False, error=f"GRAPHIFY UNAVAILABLE: {exc}")
        except subprocess.TimeoutExpired:
            return GraphBuildResult(ok=False, error="GRAPHIFY TIMEOUT")
        except Exception as exc:  # noqa: BLE001
            return GraphBuildResult(ok=False, error=f"GRAPHIFY SUBPROCESS ERROR: {exc}")

        src_out = source_dir / "graphify-out"
        graph_path = src_out / "graph.json"
        if not graph_path.exists() or proc.returncode != 0:
            return GraphBuildResult(
                ok=False, error="GRAPH BUILD FAILED",
                stdout=proc.stdout, stderr=proc.stderr,
            )
        # Move generated artifacts into the OHSC workspace (never leave in vault).
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
        # Clean the graphify-out dir from the source vault.
        shutil.rmtree(src_out, ignore_errors=True)
        return GraphBuildResult(
            ok=True, graph_path=moved_graph, html_path=html_path,
            report_path=report_path, version=self.version(),
            stdout=proc.stdout, stderr=proc.stderr,
        )

    # -- query ------------------------------------------------------------
    def query(self, question: str, graph_path: Path,
              mode: str = "query", extra_args: Optional[List[str]] = None,
              positional: Optional[List[str]] = None,
              env: Optional[Dict[str, str]] = None) -> GraphQueryResult:
        """Run a graph query / path / explain and return the text answer.

        ``positional`` lets callers pass separate positional CLI arguments
        (e.g. ``path`` needs source and target as two distinct args, not one
        space-joined string). ``extra_args`` appends flags like ``--undirected``.
        """
        exe = self._resolve()
        if not exe:
            return GraphQueryResult(ok=False, query=question,
                                    error="GRAPHIFY UNAVAILABLE")
        if not Path(graph_path).exists():
            return GraphQueryResult(ok=False, query=question,
                                    error="GRAPH NOT BUILT")
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
            return GraphQueryResult(ok=False, query=question,
                                    error=f"GRAPHIFY UNAVAILABLE: {exc}")
        except subprocess.TimeoutExpired:
            return GraphQueryResult(ok=False, query=question, error="GRAPHIFY TIMEOUT")
        except Exception as exc:  # noqa: BLE001
            return GraphQueryResult(ok=False, query=question,
                                    error=f"GRAPHIFY SUBPROCESS ERROR: {exc}")
        if proc.returncode != 0:
            return GraphQueryResult(ok=False, query=question,
                                    error="GRAPH QUERY FAILED", raw=proc.stderr)
        return GraphQueryResult(ok=True, query=question,
                                answer=proc.stdout.strip(), raw=proc.stdout)

    def shortest_path(self, source: str, target: str,
                      graph_path: Path, undirected: bool = True) -> GraphQueryResult:
        """Shortest conceptual path between two notes.

        Wikilinks are treated as bidirectional for knowledge discovery, so
        ``--undirected`` is the default. ``source`` and ``target`` are passed
        as separate positional CLI arguments.
        """
        extra = ["--undirected"] if undirected else []
        return self.query(f"{source} -> {target}", graph_path, mode="path",
                          extra_args=extra, positional=[source, target])

    def explain(self, node: str, graph_path: Path,
                env: Optional[Dict[str, str]] = None) -> GraphQueryResult:
        return self.query(node, graph_path, mode="explain", env=env)
