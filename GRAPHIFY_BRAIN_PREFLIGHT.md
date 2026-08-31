# Graphify Brain — Pre-Flight Report

Generated: 2026-08-28
Scope: OHSC Graphify Brain build + 3-vault validation (BASIC / INTERMEDIATE / ADVANCED)

---

## 1. OHSC version / state
- Project: `D:\HOSC` (Hermes Obsidian System Control)
- Agents: 16 (15 original + `graphify_agent`)
- Core: stdlib-only (no unnecessary external deps)
- Graphify integration: present and previously VERIFIED (50/50 tests) on a temp vault
- Real vault: strictly READ-ONLY for this task

## 2. Graphify version
- `graphify 0.9.50` (PyPI `graphifyy`)
- Installed as uv tool: `C:\Users\HAJI LAPTOP G55\.local\bin\graphify.exe`
- OpenAI extra installed: `graphifyy[openai]` (required for the OpenAI-compatible backend path)
- MCP server: `graphify-mcp` (`C:\Users\HAJI LAPTOP G55\.local\bin\graphify-mcp.exe`)

## 3. Graphify MCP state
- `graphify-mcp` present and runnable
- Tools confirmed earlier: `query_graph`, `get_node`, `get_neighbors`, `get_community`,
  `god_nodes`, `graph_stats`, `shortest_path` (+ `extract`, `merge_graphs`, `diagnose`, etc.)
- MCP is used for the "query layer" validation (Phase 9 / Phase 10).

## 4. Current Graphify integration state
- Adapter layer: `ohsc/integrations/graphify/`
  - `graphify_client.py`  — subprocess wrapper around `graphify` CLI (PYTHONPATH sanitized)
  - `graphify_config.py`  — workspace paths (all under `D:\HOSC\graphify`, OUTSIDE the vault)
  - `graphify_models.py`  — EXTRACTED / INFERRED provenance models
  - `graphify_runner.py`  — build / caching / query / path / explain lifecycle
  - `graphify_mcp.py`     — MCP adapter (uses `graphify-mcp` exe)
- Agent: `ohsc/agents/graphify_agent.py` (READ-only; OpClass.READ)
- ADDED THIS CYCLE (the "Brain"):
  - `graphify_brain_config.py` — `GraphifyBrainConfig` (secrets-free)
  - `graphify_brain_llm.py`    — `GraphifyBrainLLM` (OpenAI-compatible client) +
                                 `OpenCodeBrainBackend` (OpenCode `serve` gateway adapter) +
                                 `GraphifyBrainProxy` (local `/v1/chat/completions` server)
  - `graphify_brain.py`        — `GraphifyBrain` orchestrator (wires config + llm + proxy +
                                 injects the OpenAI-compatible backend env into `graphify extract`)

## 5. Configured vault path (OHSC)
- `config/ohsc.json` → `vault_root = C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault`
- `allowed_roots = [D:\HOSC, C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault]`
- `safety_mode = strict`

## 6. Real vault path
- `C:\Users\HAJI LAPTOP G55\Documents\Obsidian Vault` (confirmed, contains `.obsidian`)
- 16 files; integrity snapshots taken before/after (Phase 13). NOT modified during this task.

## 7. Available LLM backend configuration (environment)
The session environment exposes several provider keys (values NOT printed):
- `OPENCODE_API_KEY`, `OPENCODE_KEY_1..5`   (OpenCode workspace)
- `GEMINI_KEY_1..4`                          (Google Gemini)
- `GROQ_KEY_1..4`                            (Groq)
- `OPENROUTER_KEY_1..4`                      (OpenRouter)
- `NVIDIA_KEY_1`                             (NVIDIA)
- `ANTHROPIC_*`                              (Anthropic)

## 8. Detected OpenCode configuration
- OpenCode CLI: `1.18.23` (npm global `opencode-ai`)
- Gateway config: `C:\Users\HAJI LAPTOP G55\.config\opencode\opencode.jsonc` (minimal)
- Auth: `C:\Users\HAJI LAPTOP G55\.local\share\opencode\auth.json`
  - providers: `cloudflare-ai-gateway`, `opencode` (Zen), `opencode-go`, `github-copilot`
- `opencode serve` exposes a REST gateway at `http://127.0.0.1:8848`:
  - `POST /api/session`            → create session
  - `POST /api/session/{id}/prompt` → submit `{prompt:{text}, model}`
  - `GET  /api/session/{id}/history`→ poll completion (async, streamed to clients)
  - Confirmed: session + prompt accepted; completion delivered via stream/SSE/websocket.

## 9. Detected environment variables (relevant)
- `OPENCODE_API_KEY` present (OpenCode workspace token)
- `GEMINI_KEY_1..4`, `GROQ_KEY_1..4`, `OPENROUTER_KEY_1..4`, `NVIDIA_KEY_1`, `ANTHROPIC_*` present

---

## 10. OpenCode API discovery (Phase 1) — RESULT

| Question | Finding |
|---|---|
| API endpoint | OpenCode `serve` gateway `http://127.0.0.1:8848` (REST + streamed completion). Raw token endpoints (Cloudflare AI Gateway `/compat/chat/completions`, OpenCode Zen `/v1/chat/completions`) also probed. |
| Auth method | OpenCode gateway session cookie/token; raw Cloudflare/OpenCode endpoints use `Bearer` / `cf-aig-api-key`. |
| Model id | OpenCode alias `opencode/deepseek-v4-flash` (client-side). Raw gateway needs provider-native names (e.g. `gpt-4o-mini`, `glm-5.3-flash`). |
| OpenAI-compatible? | **Not directly.** The `serve` gateway is an async streaming chat service, not a static `/v1/chat/completions`. Raw token endpoints are OpenAI-shaped but authorization is rejected (see below). |
| Request format | `POST /api/session/{id}/prompt` `{prompt:{text}, model}` (OpenCode gateway) |
| Response format | async events via history/stream; final assistant text in `data[].data.text` |
| Env var expected | `OPENCODE_API_KEY` (gateway); Cloudflare gateway uses its own stored token |
| Streaming required | Yes (completion is streamed; no simple blocking response) |
| Graphify direct? | No — Graphify needs a blocking OpenAI-compatible `/v1/chat/completions`. |
| Adapter required? | **Yes.** `OpenCodeBrainBackend` + `GraphifyBrainProxy` implement the OpenAI-compatible interface on top of the OpenCode gateway. |

### OpenCode backend status: **NOT USABLE (billing blocked)**
Direct probe of every OpenCode provider (opencode-go `glm-5.3-flash`, cloudflare-ai-gateway
`gpt-4o-mini`, `@cf/meta/llama-3.1-8b-instruct`) through the `serve` gateway returns:

```
session.next.step.failed: Provider request failed with HTTP 401:
{"type":"error","error":{"type":"CreditsError","message":"No payment method.
Add a payment method here: https://opencode.ai/workspace/wrk_01KVESGBGB5FSY022FQTTW18T6/billing"}}
```

**Root cause:** the OpenCode workspace `wrk_01KVESGBGB5FSY022FQTTW18T6` has **no payment
method / credits**. This is an account-billing issue, not a code/config bug. It cannot be
fixed by the agent without adding a payment method (requires user action — not performed).

**OPEN_CODE_CONNECTION = FAIL** (evidence: CreditsError 401 on all providers).

### Working substitute backend (used for the end-to-end proof)
Because OpenCode is billing-blocked, the pipeline is validated through a working
OpenAI-compatible backend available in the user's environment:

- **Gemini** `gemini-2.5-flash` via `https://generativelanguage.googleapis.com/v1beta/openai/`
  using `GEMINI_KEY_1` → **PASS** (STATUS 200, structured JSON returned).
- The `GraphifyBrain` is OpenCode-ready: set `GRAPHIFY_BRAIN_BACKEND=opencode` and it will
  use the OpenCode gateway the moment billing is added — no code change required.

> Note: OpenRouter (`OPENROUTER_KEY_1`) also passed connectivity but its free tier returned
> HTTP 402 (insufficient credits for Graphify's 16k max_tokens). Groq returned 403 (Cloudflare
> WAF ban on this host). Gemini had usable quota, so it is the validation backend.

## 11. Risks
1. OpenCode backend unavailable (CreditsError) — mitigated by OpenCode-ready adapter + working Gemini backend for proof.
2. LLM quota limits on the substitute backend — mitigated by small max_tokens / bounded concurrency.
3. Real vault modification — mitigated by `PathSafety` + read-only agent + integrity snapshots.
4. Long-running extraction (LLM latency) — mitigated by background execution + caching.

## 12. Planned changes
- Add Brain modules (`graphify_brain_config.py`, `graphify_brain_llm.py`, `graphify_brain.py`).
- Wire `GraphifyBrain` into `graphify_agent` + `graphify_runner` (no agent rewrite; no Graphify source change).
- Create isolated test vaults under `D:\HOSC\tests\graphify_brain_validation\{basic,intermediate,advanced}_vault\`.
- Graphify output under `D:\HOSC\graphify\validation\` (never in the vault).
- Run full extract/query/path/communities/god/orphan/explain/MCP per vault.
- Add automated tests; run full `pytest` regression.
- Clean up temp vaults at the end; keep reports + tests.

## Secrets handling
No API key, token, or secret is printed, committed, or logged anywhere in this report or in
the Brain code. Backends are referenced by **environment-variable name only**.
