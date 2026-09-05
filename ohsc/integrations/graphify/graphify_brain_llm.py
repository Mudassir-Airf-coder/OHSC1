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
        """Return ``{\"ok\": bool, \"content\": str, \"error\": str, \"status\": int}``."""
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
            "User-Agent": "OHSC-GraphifyBrain/1.0 (+https://github.com/Mudassir-Airf-coder/OHSC1)",
        }
        if self.cfg.provider == "openrouter":
            headers["HTTP-Referer"] = "https://ohsc.local"
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
