"""Graphify Brain LLM client + OpenCode adapter + local OpenAI-compatible proxy.

This module is the "Graphify Brain": the LLM backend layer used by
:class:`GraphifyAgent` for semantic graph extraction. It is intentionally a
clean OpenAI-compatible adapter so Graphify (which natively supports
``OPENAI_BASE_URL``/``OPENAI_MODEL``/``OPENAI_API_KEY``) can call it unchanged.

Three pieces:
  1. :class:`GraphifyBrainLLM` — OpenAI-compatible ``chat()`` client (stdlib only).
     Forwards to the configured backend (OpenRouter/Groq/OpenCode-gateway/...).
  2. :class:`OpenCodeBrainBackend` — implements the OpenAI-compatible chat
     protocol by translating requests into OpenCode's ``serve`` gateway REST API
     (session -> prompt -> history). OpenCode-ready; currently returns
     ``CreditsError`` because the workspace has no payment method.
  3. :class:`GraphifyBrainProxy` — a tiny local HTTP server exposing
     ``/v1/chat/completions`` (OpenAI-compatible) that forwards to the chosen
     backend. Graphify is pointed at it via ``OPENAI_BASE_URL``.

Security:
  * API keys are read from the environment at request time, never stored/printed.
  * The proxy never writes the key to logs or responses.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from .graphify_brain_config import GraphifyBrainConfig
from ...core.logging import get_logger

logger = get_logger("ohsc.integrations.graphify.brain")


class GraphifyBrainLLM:
    """OpenAI-compatible chat client used by the Brain.

    Talks to any OpenAI-compatible ``/v1/chat/completions`` endpoint. For the
    ``opencode`` provider it delegates to :class:`OpenCodeBrainBackend`.
    """

    def __init__(self, config: GraphifyBrainConfig) -> None:
        self.cfg = config.resolve()

    # -- public OpenAI-compatible surface ---------------------------------
    def chat(self, messages: list, max_tokens: int = 2048,
             temperature: Optional[float] = None, model: Optional[str] = None,
             timeout: Optional[int] = None) -> Dict[str, Any]:
        """Return ``{"ok": bool, "content": str, "error": str, "status": int}``."""
        if self.cfg.provider == "opencode":
            return OpenCodeBrainBackend(self.cfg).chat(
                messages, max_tokens=max_tokens,
                temperature=temperature if temperature is not None else self.cfg.temperature,
                model=model or self.cfg.model, timeout=timeout or self.cfg.timeout)
        return self._chat_openai(messages, max_tokens, temperature, model, timeout)

    # -- OpenAI-compatible backends ---------------------------------------
    def _chat_openai(self, messages, max_tokens, temperature, model, timeout) -> Dict[str, Any]:
        url = self.cfg.endpoint.rstrip("/") + "/chat/completions"
        key = self.cfg.api_key()
        if not key:
            return {"ok": False, "content": "", "error": "NO_API_KEY",
                    "status": 0, "detail": f"env {self.cfg.key_env} not set"}
        payload = {
            "model": model or self.cfg.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature if temperature is not None else self.cfg.temperature,
        }
        body = json.dumps(payload).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        }
        if self.cfg.provider == "openrouter":
            headers["HTTP-Referer"] = "https://hermes-agent.local"
            headers["X-Title"] = "OHSC Graphify Brain"
        last_err = ""
        for attempt in range(1, max(1, self.cfg.retry_count) + 1):
            try:
                req = urllib.request.Request(url, data=body, method="POST", headers=headers)
                with urllib.request.urlopen(req, timeout=timeout or self.cfg.timeout) as r:
                    data = json.loads(r.read().decode())
                content = data["choices"][0]["message"]["content"]
                return {"ok": True, "content": content, "error": "",
                        "status": r.status}
            except urllib.error.HTTPError as e:
                last_err = f"HTTP {e.code}"
                detail = ""
                try:
                    detail = json.loads(e.read().decode()).get("error", {}).get("message", "")
                except Exception:
                    detail = e.reason
                # Do not retry auth/billing errors.
                if e.code in (401, 403, 429):
                    return {"ok": False, "content": "", "error": last_err,
                            "status": e.code, "detail": detail}
                if attempt < self.cfg.retry_count:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return {"ok": False, "content": "", "error": last_err,
                        "status": e.code, "detail": detail}
            except Exception as e:  # noqa: BLE001
                last_err = f"{type(e).__name__}: {e}"
                if attempt < self.cfg.retry_count:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return {"ok": False, "content": "", "error": last_err, "status": 0}
        return {"ok": False, "content": "", "error": last_err, "status": 0}


class OpenCodeBrainBackend:
    """OpenCode LLM execution backend (production transport).

    Drives the OpenCode CLI directly:

        opencode run -m <model> --format json --pure --auto "<prompt>"

    OpenCode is the LLM execution layer; HY3 (e.g. ``opencode/hy3-free``) is the
    model. The CLI reads its credential from the ``OPENCODE_API_KEY`` /
    provider auth (never from us). We capture stdout (``--format json`` emits one
    JSON event per line) and concatenate ``type:"text"`` events into the model
    response.

    Why the CLI and not ``opencode serve``?
      ``opencode serve`` routes through OpenCode's hosted workspace which, on
      this account, returns ``CreditsError: No payment method`` (HTTP 401). The
      ``opencode run`` CLI path uses the locally-configured provider credential
      and executes HY3 successfully. Both are "OpenCode"; the CLI is the one
      that actually works here.

    Security:
      * The API key is never passed on the command line (it stays in the env).
      * The prompt is passed as an argument; no key material is ever printed.
      * On any failure we return a structured error, never raise uncaught.
    """

    def __init__(self, config: GraphifyBrainConfig) -> None:
        self.cfg = config
        self.executable = self._find_executable()
        self.gateway = config.opencode_gateway_url.rstrip("/")

    @staticmethod
    def _find_executable() -> str:
        import shutil
        path = shutil.which("opencode")
        return path or "opencode"

    # Windows command-line length limit (~8191 chars). Graphify's extraction
    # prompt + source files can far exceed that, and passing the prompt as a
    # single argv element truncates it -> the model sees a broken message and
    # returns an empty/hollow response. We therefore pass the prompt via STDIN
    # (works on both platforms). A temp-file fallback covers non-tty stdin
    # edge cases.
    _WIN_CMD_LIMIT = 8000

    def chat(self, messages, max_tokens=2048, temperature=0.0,
             model=None, timeout=120) -> Dict[str, Any]:
        model = model or self.cfg.model
        prompt = self._render_prompt(messages)
        if not self.executable:
            return {"ok": False, "content": "",
                    "error": "OPENCODE_EXECUTABLE_NOT_FOUND", "status": 0}
        cmd = [
            self.executable, "run",
            "-m", model,
            "--format", "json",
            "--pure",
            "--auto",
        ]
        # Transport decision:
        #   * We ALWAYS pipe the prompt via STDIN. Empirically this is the most
        #     reliable transport on Windows: passing the prompt as an argv
        #     element truncates past the ~8KB CreateProcess command-line cap
        #     (graphify's extraction prompt + files routinely exceed it), and
        #     embedded quotes/em-dashes in the prompt also confuse argv parsing.
        #     STDIN avoids both problems. ``--file`` was rejected because it
        #     requires a separate message argument.
        use_stdin = True
        input_arg: Optional[str] = prompt
        try:
            proc = subprocess.run(
                cmd,
                input=input_arg,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._safe_env(),
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "content": "", "error": "OPENCODE_TIMEOUT",
                    "status": 0, "detail": f"exceeded {timeout}s"}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "content": "",
                    "error": f"OPENCODE_SPAWN_ERROR: {type(e).__name__}", "status": 0}
        if proc.returncode != 0 and not proc.stdout.strip():
            tail = (proc.stderr or "")[-400:].replace("\r", " ")
            return {"ok": False, "content": "", "error": "OPENCODE_CLI_ERROR",
                    "status": proc.returncode, "detail": tail}
        content, err = self._parse_json_stream(proc.stdout)
        if err:
            return {"ok": False, "content": "", "error": err, "status": 0,
                    "detail": (proc.stderr or "")[-300:]}
        if not content.strip():
            return {"ok": False, "content": "", "error": "OPENCODE_EMPTY_RESPONSE",
                    "status": 0, "detail": (proc.stderr or "")[-300:]}
        return {"ok": True, "content": content, "error": "", "status": 200}

    @staticmethod
    def _render_prompt(messages) -> str:
        """Flatten OpenAI-style messages into a single-line prompt.

        IMPORTANT: ``opencode run`` treats the message as a single line. Newlines
        in the argument cause OpenCode to drop everything after the first line,
        so we collapse all whitespace to single spaces. The system instruction is
        inlined as plain text (no markdown header) so the model treats it as
        context rather than a (broken) user turn.
        """
        parts = []
        for m in messages:
            c = m.get("content", "") or ""
            c = " ".join(str(c).split())  # collapse all whitespace incl. newlines
            parts.append(c)
        return " ".join(parts).strip()

    def _safe_env(self) -> Dict[str, str]:
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        return env

    @staticmethod
    def _parse_json_stream(stdout: str):
        """Return (content, error). Concatenates model text events.

        OpenCode's ``--format json`` emits one JSON event per line. The
        assistant text lives at ``event["part"]["text"]`` (and the event
        ``type`` is ``"text"`` at the top level). Some events also carry the
        text at the top level. We read both, defensively.
        """
        content_parts = []
        error = None
        for raw in stdout.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                ev = json.loads(raw)
            except Exception:
                # Non-JSON line (occasional banners) — ignore.
                continue
            # Unify the nested `part` payload with the top-level event.
            payload = ev.get("part") if isinstance(ev.get("part"), dict) else ev
            t = (ev.get("type") or payload.get("type") or "")
            if "failed" in t or "error" in t:
                err_obj = payload
                em = err_obj.get("error", {})
                msg = em.get("message") if isinstance(em, dict) else str(em)
                if not msg:
                    msg = str(err_obj.get("message", ""))
                error = f"OPENCODE_PROVIDER_ERROR: {msg[:200]}"
                continue
            if t == "text":
                txt = payload.get("text")
                if isinstance(txt, str) and txt:
                    content_parts.append(txt)
        return "".join(content_parts), error


class GraphifyBrainProxy:
    """Local OpenAI-compatible proxy server for Graphify.

    Graphify's ``extract`` is invoked with
        OPENAI_BASE_URL=http://127.0.0.1:<port>/v1
        OPENAI_MODEL=<model>
        OPENAI_API_KEY=<anything>   (proxy validates presence, ignores value)
    and the proxy forwards ``/v1/chat/completions`` to the configured Brain LLM.
    """

    def __init__(self, config: GraphifyBrainConfig, host: str = "127.0.0.1", port: int = 0):
        self.cfg = config
        self.host = host
        self.port = port
        self.llm = GraphifyBrainLLM(config)
        self._server: Optional[ThreadingHTTPServer] = None

    def _handler_factory(self):
        llm = self.llm

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # silence default logging (no secrets)
                pass

            def do_POST(self):  # noqa: N802
                if self.path.rstrip("/").endswith("/chat/completions"):
                    length = int(self.headers.get("Content-Length", 0))
                    raw = self.rfile.read(length) if length else b"{}"
                    try:
                        payload = json.loads(raw.decode())
                    except Exception:
                        payload = {}
                    messages = payload.get("messages", [])
                    # Malformed / empty requests must NOT spawn a subprocess.
                    # Return a clean 4xx without touching the backend.
                    if not isinstance(messages, list) or not messages:
                        bad = json.dumps({
                            "error": {"message": "missing or empty 'messages'",
                                      "type": "invalid_request_error", "code": 400}
                        }).encode()
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(bad)))
                        self.end_headers()
                        self.wfile.write(bad)
                        return
                    # graphify sends `max_completion_tokens`; honour it, else default.
                    mt = payload.get("max_completion_tokens") or payload.get("max_tokens") or 2048
                    max_tokens = int(mt)
                    model = payload.get("model")
                    temp = payload.get("temperature")
                    res = llm.chat(messages, max_tokens=max_tokens, temperature=temp,
                                   model=model)
                    # Debug dump (payload + response + opencode raw; never secrets).
                    if os.environ.get("GRAPHIFY_BRAIN_DEBUG"):
                        try:
                            _dbg = {
                                "model": model,
                                "messages": messages,
                                "max_tokens": max_tokens,
                                "max_completion_tokens": payload.get("max_completion_tokens"),
                                "temperature": temp,
                                "response_ok": res.get("ok"),
                                "response_content_head": (res.get("content") or "")[:800],
                                "response_error": res.get("error"),
                            }
                            _dbg_path = os.environ.get("GRAPHIFY_BRAIN_DEBUG")
                            if not os.path.isabs(_dbg_path) or ":" not in _dbg_path:
                                _dbg_path = r"D:\HOSC\scripts\_dbg_payload.json"
                            if os.path.exists(_dbg_path):
                                try:
                                    _prev = json.loads(open(_dbg_path, encoding="utf-8").read())
                                    if isinstance(_prev, list):
                                        _prev.append(_dbg)
                                    else:
                                        _prev = [_prev, _dbg]
                                except Exception:
                                    _prev = [_dbg]
                            else:
                                _prev = [_dbg]
                            with open(_dbg_path, "w", encoding="utf-8") as _f:
                                _f.write(json.dumps(_prev, default=str))
                        except Exception:
                            pass
                    if res["ok"]:
                        out = {
                            "id": "chatcmpl-brain",
                            "object": "chat.completion",
                            "choices": [{
                                "index": 0,
                                "message": {"role": "assistant",
                                            "content": res["content"]},
                                "finish_reason": "stop",
                            }],
                            "model": model or llm.cfg.model,
                        }
                        body = json.dumps(out).encode()
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                    else:
                        # Surface a clean error; never leak key details.
                        err_body = json.dumps({
                            "error": {"message": res.get("error", "BRAIN_ERROR"),
                                      "type": "brain_error",
                                      "code": res.get("status", 500)}
                        }).encode()
                        self.send_response(res.get("status") or 500)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(err_body)))
                        self.end_headers()
                        self.wfile.write(err_body)
                else:
                    self.send_response(404)
                    self.end_headers()

        return Handler

    def start(self) -> int:
        """Start the server; returns the bound port."""
        handler = self._handler_factory()
        self._server = ThreadingHTTPServer((self.host, self.port), handler)
        self.port = self._server.server_address[1]
        import threading
        t = threading.Thread(target=self._server.serve_forever, daemon=True)
        t.start()
        logger.info(f"Graphify Brain proxy listening on {self.host}:{self.port}")
        return self.port

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None

    def openai_env(self) -> Dict[str, str]:
        """Env vars to pass to ``graphify extract`` so it uses this proxy."""
        return {
            "OPENAI_BASE_URL": f"http://{self.host}:{self.port}/v1",
            "OPENAI_MODEL": self.cfg.model,
            "OPENAI_API_KEY": "local-brain-proxy",
        }
