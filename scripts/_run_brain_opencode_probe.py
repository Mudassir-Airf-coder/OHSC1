"""Probe the Graphify Brain OpenCode backend with HY3 — real execution test.

Runs GraphifyBrainConfig + GraphifyBrainLLM.chat() through the OpenCode CLI
(`opencode run -m opencode/hy3-free`). Proves OHSC -> Graphify Brain -> OpenCode -> HY3.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ohsc.integrations.graphify.graphify_brain_config import GraphifyBrainConfig
from ohsc.integrations.graphify.graphify_brain_llm import GraphifyBrainLLM

# Use the opencode backend explicitly; model HY3 (opencode/hy3-free).
os.environ["GRAPHIFY_BRAIN_BACKEND"] = "opencode"
os.environ["GRAPHIFY_BRAIN_MODEL"] = "opencode/hy3-free"
cfg = GraphifyBrainConfig.from_env()
llm = GraphifyBrainLLM(cfg)

print(f"provider={cfg.provider} model={cfg.model}")
print(f"key present (env {cfg.key_env}): {bool(os.environ.get(cfg.key_env))}")

messages = [
    {"role": "system", "content": "You are a test oracle. Reply concisely."},
    {"role": "user", "content": "Reply with exactly: CONNECTION_OK"},
]

t0 = time.time()
res = llm.chat(messages, max_tokens=64, timeout=120)
dt = time.time() - t0

print(f"elapsed={dt:.2f}s")
print(f"status={res.get('status')} ok={res.get('ok')} error={res.get('error')}")
content = res.get("content", "")
print(f"content={content!r}")
if res.get("detail"):
    print(f"detail={res.get('detail')[:200]}")
print("RESULT:", "PASS" if res.get("ok") and "CONNECTION_OK" in content else "FAIL")
