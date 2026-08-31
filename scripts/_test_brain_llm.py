"""Validate the Graphify Brain LLM client against a real OpenAI-compatible backend.

Reads backend from env (no secret printed):
  GF_PROVIDER, GF_ENDPOINT, GF_MODEL, GF_KEY_ENV
Prints only status / provider / http / model / snippet.
"""
import os, sys
sys.path.insert(0, r"D:\HOSC")
from ohsc.integrations.graphify.graphify_brain_config import GraphifyBrainConfig
from ohsc.integrations.graphify.graphify_brain_llm import GraphifyBrainLLM

provider = os.environ.get("GF_PROVIDER", "openrouter")
cfg = GraphifyBrainConfig(
    provider=provider,
    endpoint=os.environ.get("GF_ENDPOINT", ""),
    model=os.environ.get("GF_MODEL", ""),
    key_env=os.environ.get("GF_KEY_ENV", ""),
).resolve()
print(f"PROVIDER={cfg.provider}")
print(f"ENDPOINT={cfg.endpoint}")
print(f"MODEL={cfg.model}")
print(f"KEY_ENV={cfg.key_env}  KEY_PRESENT={cfg.has_key()}")
llm = GraphifyBrainLLM(cfg)
res = llm.chat([{"role": "user", "content": "Reply with exactly: CONNECTION_OK"}],
               max_tokens=16, temperature=0.0)
print(f"OK={res['ok']}  STATUS={res.get('status')}  ERROR={res.get('error')}  DETAIL={res.get('detail','')[:120]}")
print(f"CONTENT={res.get('content','')[:60]!r}")
