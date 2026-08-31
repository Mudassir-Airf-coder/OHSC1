"""Graphify Brain — orchestration layer.

Ties together:
  * :class:`GraphifyBrainConfig`  (secrets-free config)
  * :class:`GraphifyBrainLLM`     (OpenAI-compatible client + OpenCode adapter)
  * :class:`GraphifyBrainProxy`   (local /v1/chat/completions server for Graphify)

The Brain is NOT a new agent. It is the LLM-backend/configuration layer that
:class:`GraphifyAgent` uses to drive semantic extraction. Graphify itself is
never modified — the Brain only supplies the OpenAI-compatible backend URL/model
via environment variables understood by ``graphify extract``.

Vault-safety: the Brain never touches the vault. It only provides the LLM
backend and writes Graphify artifacts into the OHSC workspace.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .graphify_brain_config import GraphifyBrainConfig
from .graphify_brain_llm import GraphifyBrainLLM, GraphifyBrainProxy
from ...core.logging import get_logger

logger = get_logger("ohsc.integrations.graphify.brain.orchestrator")


class GraphifyBrain:
    """The LLM intelligence layer backing Graphify inside OHSC."""

    def __init__(self, config: Optional[GraphifyBrainConfig] = None,
                 system_root: Optional[Path] = None) -> None:
        self.config = (config or GraphifyBrainConfig.from_env(system_root)).resolve()
        if system_root and not self.config.graph_output_dir:
            self.config.graph_output_dir = str(Path(system_root) / "graphify" / "graphs")
        self.llm = GraphifyBrainLLM(self.config)
        self._proxy: Optional[GraphifyBrainProxy] = None

    # -- capability reporting --------------------------------------------
    def backend_status(self) -> Dict[str, Any]:
        """Report backend readiness WITHOUT exposing secrets.

        Returns a structured status the Reviewer can use.
        """
        if self.config.provider == "opencode":
            # OpenCode gateway may need `opencode serve` running.
            return {
                "provider": "opencode",
                "endpoint": self.config.endpoint,
                "model": self.config.model,
                "key_env": self.config.key_env,
                "key_present": self.config.has_key(),
                "note": "OpenCode gateway (serve). Workspace billing state is "
                        "checked at connection time.",
            }
        return {
            "provider": self.config.provider,
            "endpoint": self.config.endpoint,
            "model": self.config.model,
            "key_env": self.config.key_env,
            "key_present": self.config.has_key(),
        }

    # -- connection test (Phase 3) ---------------------------------------
    def connection_test(self, probe: str = "Reply with exactly: CONNECTION_OK") -> Dict[str, Any]:
        """Minimal harmless LLM connectivity test.

        Returns:
          {"ok": bool, "status": int, "error": str, "detail": str, "provider": str}
        Never includes the API key.
        """
        if self.config.provider == "opencode":
            # Verify the gateway is reachable + try a real chat (will surface
            # CreditsError honestly if billing is missing).
            res = self.llm.chat([{"role": "user", "content": probe}],
                                max_tokens=16, temperature=0.0)
            return {
                "ok": res["ok"], "status": res.get("status", 0),
                "error": res.get("error", ""), "detail": res.get("detail", "")[:200],
                "provider": "opencode",
            }
        res = self.llm.chat([{"role": "user", "content": probe}],
                            max_tokens=16, temperature=0.0)
        return {
            "ok": res["ok"], "status": res.get("status", 0),
            "error": res.get("error", ""), "detail": res.get("detail", "")[:200],
            "provider": self.config.provider,
        }

    # -- proxy lifecycle --------------------------------------------------
    def start_proxy(self) -> int:
        """Start the local OpenAI-compatible proxy; returns the bound port.

        Graphify's extract is then pointed at this proxy via openai_env().
        """
        self._proxy = GraphifyBrainProxy(self.config)
        return self._proxy.start()

    def stop_proxy(self) -> None:
        if self._proxy:
            self._proxy.stop()
            self._proxy = None

    def openai_env(self) -> Dict[str, str]:
        """Env vars to pass to ``graphify extract`` (via proxy if running)."""
        if self._proxy:
            return self._proxy.openai_env()
        # Direct mode: point Graphify straight at the configured backend.
        return {
            "OPENAI_BASE_URL": self.config.endpoint,
            "OPENAI_MODEL": self.config.model,
            "OPENAI_API_KEY": self.config.api_key() or "MISSING",
        }

    # -- helper: build extract env (cleaned) ------------------------------
    def extract_env(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Return a cleaned subprocess env for ``graphify extract``.

        Strips PYTHONPATH (prevents host-venv numpy/openai shadowing) and injects
        the Brain's OpenAI-compatible backend vars. Never includes secrets in logs.
        """
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.update(self.openai_env())
        if self.config.cache_mode == "off":
            env["GRAPHIFY_FORCE"] = "1"
        if extra:
            env.update(extra)
        return env

    def summary(self) -> Dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "status": self.backend_status(),
        }


def build_brain(system_root: Path,
                provider: Optional[str] = None) -> GraphifyBrain:
    """Factory: build a brain, overriding provider from env/arg if given."""
    if provider:
        os.environ["GRAPHIFY_BRAIN_BACKEND"] = provider
    return GraphifyBrain(system_root=system_root)
