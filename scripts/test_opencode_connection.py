"""Phase 3: Minimal OpenCode LLM connectivity test.

Proves the configured OpenCode backend can serve a chat completion through an
OpenAI-compatible interface. Reads credentials at RUNTIME from OpenCode's
auth.json (never hardcoded, never printed). Uses only environment-derived
config. Exits 0 on PASS.

Safe: prints status code, model id, and a short response snippet only.
"""
from __future__ import annotations
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

HOME = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))
AUTH = HOME / ".local" / "share" / "opencode" / "auth.json"


def load_backend():
    """Return (base_url, api_key, model, provider_label) from OpenCode config."""
    if not AUTH.exists():
        raise RuntimeError("OpenCode auth.json not found")
    data = json.loads(AUTH.read_text())
    # Preferred: Cloudflare AI Gateway (OpenAI-compatible, well-known URL shape)
    cfg = data.get("cloudflare-ai-gateway")
    if cfg and cfg.get("key") and cfg.get("metadata", {}).get("accountId"):
        meta = cfg["metadata"]
        base = (
            f"https://gateway.ai.cloudflare.com/v1/"
            f"{meta['accountId']}/{meta['gatewayId']}/openai"
        )
        return base, cfg["key"], "openai/gpt-5", "cloudflare-ai-gateway"
    # Fallback: OpenCode Zen key (env)
    key = os.environ.get("OPENCODE_API_KEY")
    if key:
        return "https://api.opencode.ai/v1", key, "opencode/deepseek-v4-flash", "opencode-zen"
    raise RuntimeError("No usable OpenCode backend credential found")


def main() -> int:
    try:
        base, api_key, model, provider = load_backend()
    except Exception as e:
        print(f"OPEN_CODE_CONNECTION = FAIL (config: {e})")
        return 1
    url = f"{base}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: CONNECTION_OK"}],
        "max_tokens": 16,
    }).encode()
    req = urllib.request.Request(url, data=payload, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status = r.status
            body = json.loads(r.read().decode())
        content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"OPEN_CODE_CONNECTION = PASS")
        print(f"PROVIDER = {provider}")
        print(f"MODEL = {model}")
        print(f"HTTP = {status}")
        print(f"RESPONSE_SNIPPET = {content.strip()[:60]}")
        return 0
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:160]
        print(f"OPEN_CODE_CONNECTION = FAIL")
        print(f"PROVIDER = {provider}")
        print(f"HTTP = {e.code}")
        print(f"ERROR = {detail}")
        return 1
    except Exception as e:
        print(f"OPEN_CODE_CONNECTION = FAIL (runtime: {type(e).__name__}: {e})")
        print(f"PROVIDER = {provider}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
