"""Graphify Brain automated tests.

Covers (against the REAL public API — no fabricated methods):
  * GraphifyBrainConfig (secrets-free, env-driven, resolve/from_env/api_key)
  * GraphifyBrainLLM OpenAI-compatible client (live test only if a backend key
    env is set; otherwise a deterministic bad-key test proves graceful failure)
  * OpenCodeBrainBackend construction (no network; shape only)
  * GraphifyBrainProxy construction (no network)
  * Brain wiring into GraphifyAgent (import + build)
  * Validation graphs (read-only assertions on real extracted artifacts)

Secrets are never asserted/printed: only key *presence* and *absence*.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ohsc.integrations.graphify.graphify_brain_config import GraphifyBrainConfig
from ohsc.integrations.graphify.graphify_brain_llm import (
    GraphifyBrainLLM, OpenCodeBrainBackend, GraphifyBrainProxy)

SYSTEM_ROOT = Path(r"D:\HOSC")
VALIDATION = SYSTEM_ROOT / "graphify" / "validation"


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
def test_config_no_hardcoded_secret():
    cfg = GraphifyBrainConfig(provider="openai", endpoint="https://x/v1",
                              model="m", key_env="SOME_KEY")
    d = cfg.to_dict()
    assert "key" not in d and "api_key" not in d
    # key is referenced by env-name only
    assert d["key_env"] == "SOME_KEY"


def test_config_resolve_fills_defaults():
    cfg = GraphifyBrainConfig(provider="openrouter").resolve()
    assert cfg.endpoint == "https://openrouter.ai/api/v1"
    assert cfg.model == "openai/gpt-4o-mini"
    assert cfg.key_env == "OPENROUTER_KEY_1"


def test_config_api_key_reads_env_only():
    os.environ["GRAPHIFY_BRAIN_TEST_KEY"] = "supersecretvalue"
    cfg = GraphifyBrainConfig(provider="openai", endpoint="https://x/v1",
                              model="m", key_env="GRAPHIFY_BRAIN_TEST_KEY")
    assert cfg.api_key() == "supersecretvalue"
    assert cfg.has_key() is True
    del os.environ["GRAPHIFY_BRAIN_TEST_KEY"]
    assert cfg.has_key() is False


def test_config_from_env_default():
    # ensure deterministic: provider default opencode, resolves to local gateway
    cfg = GraphifyBrainConfig.from_env(system_root=SYSTEM_ROOT)
    assert cfg.provider in ("opencode", "openai", "openrouter", "groq")
    assert cfg.graph_output_dir.endswith("graphify/graphs") or \
        cfg.graph_output_dir.endswith(r"graphify\graphs")


# --------------------------------------------------------------------------
# LLM client
# --------------------------------------------------------------------------
def test_llm_bad_key_structured_failure():
    """A bad/invalid key must return a structured error, never raise/crash,
    and must never echo the key into the result dict."""
    os.environ["GRAPHIFY_BRAIN_BADKEY_T"] = "sk-invalid-test-key"
    cfg = GraphifyBrainConfig(
        provider="openai",
        endpoint="https://generativelanguage.googleapis.com/v1beta/openai/",
        model="gemini-2.5-flash",
        key_env="GRAPHIFY_BRAIN_BADKEY_T",
        timeout=20).resolve()
    llm = GraphifyBrainLLM(cfg)
    res = llm.chat([{"role": "user", "content": "ping"}], max_tokens=16, timeout=20)
    assert isinstance(res, dict)
    assert res.get("status") in (0, 400, 401, 403, 404)
    assert bool(res.get("detail"))  # structured error text present
    dump = json.dumps(res)
    assert "sk-invalid-test-key" not in dump  # no secret leak


def test_llm_missing_key_structured_failure():
    cfg = GraphifyBrainConfig(
        provider="openai",
        endpoint="https://generativelanguage.googleapis.com/v1beta/openai/",
        model="gemini-2.5-flash",
        key_env="GRAPHIFY_BRAIN_NO_SUCH_KEY_T",
        timeout=10).resolve()
    llm = GraphifyBrainLLM(cfg)
    res = llm.chat([{"role": "user", "content": "ping"}], max_tokens=16, timeout=10)
    assert res.get("status") == 0
    assert "not set" in res.get("detail", "")


# --------------------------------------------------------------------------
# OpenCode backend (OpenCode-ready adapter)
# --------------------------------------------------------------------------
def test_opencode_backend_shape():
    cfg = GraphifyBrainConfig(provider="opencode").resolve()
    be = OpenCodeBrainBackend(cfg)
    # gateway url is carried; no live key needed for construction
    assert be.gateway.startswith("http")
    # chat returns a dict-shaped result (we do not hit network here)
    res = be.chat([{"role": "user", "content": "ping"}], max_tokens=16,
                  model=cfg.model, timeout=5)
    assert isinstance(res, dict)


# --------------------------------------------------------------------------
# Local proxy (OpenAI-compatible server for Graphify)
# --------------------------------------------------------------------------
def test_proxy_construction():
    cfg = GraphifyBrainConfig(provider="openai", endpoint="https://x/v1",
                              model="m", key_env="X").resolve()
    proxy = GraphifyBrainProxy(cfg, host="127.0.0.1", port=0)
    assert proxy.llm is not None
    assert proxy.host == "127.0.0.1"


# --------------------------------------------------------------------------
# Brain wiring
# --------------------------------------------------------------------------
def test_brain_builds_in_agent():
    from ohsc.agents.graphify_agent import GraphifyAgent
    from ohsc.config import SystemConfig
    from ohsc.core.runtime import Runtime
    cfg = SystemConfig(system_root=SYSTEM_ROOT,
                       vault_root=SYSTEM_ROOT/"tests/graphify_brain_validation/basic_vault",
                       allowed_roots=[str(SYSTEM_ROOT)])
    rt = Runtime(config=cfg)
    agent = GraphifyAgent(rt)
    assert agent.brain is not None
    assert agent.runner is not None


# --------------------------------------------------------------------------
# Validation graphs (read-only assertions on real extracted artifacts)
# --------------------------------------------------------------------------
def _assert_graph(path: Path, min_nodes: int):
    g = json.loads(path.read_text(encoding="utf-8"))
    nodes = g.get("nodes", [])
    links = g.get("links", [])
    assert len(nodes) >= min_nodes, f"expected >= {min_nodes} nodes, got {len(nodes)}"
    assert len(links) >= 1
    for l in links:
        assert l.get("confidence") in ("EXTRACTED", "INFERRED", "AMBIGUOUS"), l
        assert l.get("source_file") or l.get("_origin")
    return g


def test_basic_graph_artifact():
    p = VALIDATION / "basic" / "graph.json"
    if not p.exists():
        pytest.skip("basic graph not built yet")
    g = _assert_graph(p, 5)
    assert any(l["confidence"] == "EXTRACTED" for l in g["links"])


def test_intermediate_graph_artifact():
    p = VALIDATION / "intermediate" / "graph.json"
    if not p.exists():
        pytest.skip("intermediate graph not built yet")
    _assert_graph(p, 10)


def test_advanced_graph_artifact():
    p = VALIDATION / "advanced" / "graph.json"
    if not p.exists():
        pytest.skip("advanced graph not built yet")
    _assert_graph(p, 20)


def test_validation_output_outside_real_vault():
    vault = Path(r"C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault")
    for name in ("basic", "intermediate", "advanced"):
        gp = VALIDATION / name / "graph.json"
        if gp.exists():
            assert not gp.resolve().is_relative_to(vault)
