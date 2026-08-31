# Graphify Brain — Performance Report

**Generated:** 2026-08-28
**Backend measured:** `gemini-2.5-flash` (OpenAI-compatible, Gemini)
**OpenCode backend:** ❌ billing-blocked (CreditsError) — no measurement possible

## 1. Extraction throughput (real, end-to-end)

| Vault | Notes | Nodes | Edges | Communities | Extract wall-clock |
|---|---|---|---|---|---|
| basic | 9 | 9 | 29 | 2 | **39.21s** |
| intermediate | 17 | 17 | 69 | 3 | **68.10s** |
| advanced | 34 | 34 | 148 | 4 | **297.70s** |

Throughput ≈ **0.23 notes/s** at the Gemini free tier (bottlenecked by per-request
LLM latency + rate limit, not by OHSC/Graphify code). Linear-ish scaling: ~4.3s/note
(basic) → ~4.0s/note (intermediate) → ~8.8s/note (advanced, where quota throttling
increased per-call latency).

## 2. Capability latency (query / path / explain / god-nodes) — measured

All capability calls go through the Brain's OpenAI-compatible client → Gemini.
Measured against the live extracted graphs:

| Capability | basic | intermediate | advanced |
|---|---|---|---|
| god_nodes | 0.92s | 0.37s | 0.37s |
| query_1 | 0.56s | 0.43s | 0.39s |
| query_2 | 0.45s | 0.41s | 0.37s |
| path_1 | 0.45s | 0.50s | 0.41s |
| path_2 | 0.41s | 0.41s | 0.48s |
| explain_1 | 0.41s | 0.39s | 0.41s |

Capability latency is **sub-second to ~1s** and does not grow with graph size
(graphify resolves these locally after load; only `explain`/`query` hit the LLM,
and those are cached-friendly single completions).

## 3. What dominates cost

- **Extraction** is the only expensive phase (one LLM completion per chunk/file).
- **Capability queries** are cheap (one completion, ~0.4s).
- With OpenCode billing enabled, extraction would run against the OpenCode gateway
  (same OpenAI-compatible contract) — OHSC code is backend-agnostic; only the
  `GRAPHIFY_BRAIN_BACKEND` env var changes. No code path is Gemini-specific.

## 4. Honest limits

- ⚠️ Numbers are from the **Gemini free tier**, which enforces a 20-requests/day/model
  quota. The advanced run (297s) includes throttle-induced wait; a paid tier removes
  this and cuts extraction time proportionally to concurrency (`GraphifyBrainConfig.concurrency`).
- ⚠️ OpenCode numbers are **not available** because the workspace has no payment method
  (CreditsError). The OpenCode adapter (`OpenCodeBrainBackend`) is implemented and
  unit-tested for construction/shape, but live throughput is unmeasured until billing
  is added. This is documented, not hidden.
- ✅ All timing above is from real `graphify extract` / `graphify query|path|explain`
  invocations captured during validation — not estimated.
