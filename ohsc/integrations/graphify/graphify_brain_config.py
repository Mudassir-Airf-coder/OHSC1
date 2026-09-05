"""Graphify Brain configuration.

Clean, secrets-free configuration layer for the Graphify Brain — the LLM
backend/configuration layer used by :class:`GraphifyAgent` for semantic graph
extraction.

Design rules (mandate):
  * API keys are NEVER hardcoded, committed, printed, or logged.
  * Backends are selected by *name* + an environment variable that holds the key.
  * The Brain speaks the OpenAI-compatible ``/v1/chat/completions`` interface so
    Graphify (which natively supports ``OPENAI_BASE_URL``/``OPENAI_MODEL``/
    ``OPENAI_API_KEY``) can consume it unchanged.

Supported backend names:
  * ``opencode``    -> OpenCode gateway (OpenAI-compatible proxy). OpenCode-ready:
                       wired to ``opencode serve`` session/prompt/history protocol.
                       NOTE: the user's OpenCode workspace currently has NO payment
                       method (CreditsError) so this backend is not usable until
                       billing is added. See GRAPHIFY_BRAIN_PREFLIGHT.md.
  * ``openai``      -> any OpenAI-compatible endpoint (OpenRouter, Groq, vLLM, ...).

The active backend for validation is chosen by the ``GRAPHIFY_BRAIN_BACKEND``
environment variable (default ``opencode``); a working OpenAI-compatible backend
(OpenRouter) is used for the end-to-end pipeline proof because OpenCode is
billing-blocked.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional


# Default backend -> key env var mapping. Keys are read at runtime only.
BACKEND_DEFAULTS: Dict[str, Dict[str, str]] = {
    "opencode": {
        # OpenCode is the production LLM execution layer. HY3 is the model.
        # Driven via the OpenCode CLI (`opencode run -m opencode/hy3-free`),
        # which executes HY3 using the locally-configured provider credential.
        # (opencode serve is NOT used: it routes through the hosted workspace
        #  which is billing-blocked with CreditsError on this account.)
        "key_env": "OPENCODE_API_KEY",
        "base_url": "http://127.0.0.1:8848/v1",
        "model": "opencode/hy3-free",
    },
    "openai": {
        "key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "openrouter": {
        "key_env": "OPENROUTER_KEY_1",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-4o-mini",
    },
    "groq": {
        "key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        # Working Groq model id for this project (verify with your account).
        "model": "openai/gpt-oss-120b",
    },
}


@dataclass
class GraphifyBrainConfig:
    """Configuration for the Graphify Brain LLM backend.

    Every secret is referenced by *environment variable name* only. The value
    is resolved lazily at request time and is never stored on the object in a
    way that could be serialized/printed accidentally.
    """

    provider: str = "opencode"
    endpoint: str = ""            # OpenAI-compatible base URL
    model: str = ""
    key_env: str = ""             # env var that holds the API key
    timeout: int = 120            # per-request timeout (s)
    retry_count: int = 3
    temperature: float = 0.0       # Graphify wants deterministic extraction
    concurrency: int = 2          # bounded parallelism for extraction chunks
    extraction_mode: str = "semantic"   # semantic | structural
    cache_mode: str = "auto"      # auto | force | off
    graph_output_dir: str = ""    # where graph.json lives (outside vault)
    log_level: str = "INFO"
    # OpenCode gateway (used only when provider == opencode)
    opencode_gateway_url: str = "http://127.0.0.1:8848"

    def resolve(self) -> "GraphifyBrainConfig":
        """Fill endpoint/model/key_env from backend defaults if not set."""
        if self.endpoint and self.model and self.key_env:
            return self
        d = BACKEND_DEFAULTS.get(self.provider)
        if d:
            self.endpoint = self.endpoint or d["base_url"]
            self.model = self.model or d["model"]
            self.key_env = self.key_env or d["key_env"]
        return self

    def api_key(self) -> str:
        """Return the resolved API key from the environment (NOT stored)."""
        primary = os.environ.get(self.key_env or "", "") or ""
        if primary:
            return primary
        # Aliases so either GROQ_API_KEY or GROQ_KEY_1 works for Groq.
        if self.provider == "groq":
            for alias in ("GROQ_API_KEY", "GROQ_KEY_1"):
                val = os.environ.get(alias, "") or ""
                if val:
                    return val
        return ""

    def has_key(self) -> bool:
        return bool(self.api_key())

    def to_dict(self, include_secret: bool = False) -> Dict[str, Any]:
        d = {
            "provider": self.provider,
            "endpoint": self.endpoint,
            "model": self.model,
            "key_env": self.key_env,           # name only, never the value
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "temperature": self.temperature,
            "concurrency": self.concurrency,
            "extraction_mode": self.extraction_mode,
            "cache_mode": self.cache_mode,
            "graph_output_dir": self.graph_output_dir,
            "log_level": self.log_level,
            "opencode_gateway_url": self.opencode_gateway_url,
        }
        if include_secret:
            # Only used by diagnostics that must never print the value.
            d["key_present"] = self.has_key()
        return d

    # -- env-driven factory ----------------------------------------------
    @classmethod
    def from_env(cls, system_root: Optional[Path] = None) -> "GraphifyBrainConfig":
        """Build config from GRAPHIFY_BRAIN_* env vars with sane defaults.

        GRAPHIFY_BRAIN_BACKEND  -> provider (default opencode)
        GRAPHIFY_BRAIN_ENDPOINT -> endpoint override
        GRAPHIFY_BRAIN_MODEL    -> model override
        GRAPHIFY_BRAIN_KEY_ENV  -> key env var name override
        GRAPHIFY_BRAIN_TIMEOUT  -> timeout
        GRAPHIFY_BRAIN_LOG_LEVEL-> log level
        """
        provider = os.environ.get("GRAPHIFY_BRAIN_BACKEND", "opencode")
        cfg = cls(provider=provider)
        cfg.resolve()
        # Apply overrides.
        cfg.endpoint = os.environ.get("GRAPHIFY_BRAIN_ENDPOINT", cfg.endpoint)
        cfg.model = os.environ.get("GRAPHIFY_BRAIN_MODEL", cfg.model)
        cfg.key_env = os.environ.get("GRAPHIFY_BRAIN_KEY_ENV", cfg.key_env)
        if "GRAPHIFY_BRAIN_TIMEOUT" in os.environ:
            try:
                cfg.timeout = int(os.environ["GRAPHIFY_BRAIN_TIMEOUT"])
            except ValueError:
                pass
        cfg.log_level = os.environ.get("GRAPHIFY_BRAIN_LOG_LEVEL", cfg.log_level)
        if system_root:
            cfg.graph_output_dir = str(Path(system_root) / "graphify" / "graphs")
        return cfg
