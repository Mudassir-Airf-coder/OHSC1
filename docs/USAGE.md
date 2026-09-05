# OHSC Usage Guide

## Install

```bash
git clone https://github.com/Mudassir-Airf-coder/OHSC1.git
cd OHSC1
bash setup.sh          # Linux / macOS  (or: .\setup.ps1 on Windows)
# Unattended: bash setup.sh --unattended
```

Manual alternative (if you prefer not to use the setup script):

```bash
python3 -m pip install -e .
# optional Graphify CLI:
# curl -LsSf https://astral.sh/uv/install.sh | sh
# uv tool install "graphifyy[mcp,openai]"
```

## Configure vault

```bash
export OHSC_SYSTEM_ROOT="$(pwd)"
export OHSC_VAULT_ROOT="/absolute/path/to/vault"
```

Windows PowerShell:

```powershell
$env:OHSC_SYSTEM_ROOT = (Get-Location).Path
$env:OHSC_VAULT_ROOT = "D:\path\to\vault"
```

## Everyday commands

```bash
ohsc run                  # session token + status
ohsc activate             # gateway health
ohsc doctor               # diagnostics
ohsc agents               # list agents
ohsc capabilities --json  # full manifest
ohsc status --json        # component health
```

## Natural language tasks

```bash
ohsc "find orphan notes"
ohsc "create a note titled Inbox with content hello"
ohsc "search for tags #project"
ohsc --dry-run "create a MOC for Python"
```

## Graphify

```bash
export GRAPHIFY_BRAIN_BACKEND=groq
export GROQ_API_KEY=your_key   # or set in .env

ohsc --graphify build "$OHSC_VAULT_ROOT"
ohsc --graphify query "What are the main themes?"
ohsc --graphify path "Topic A" "Topic B"
```

Only `GROQ_API_KEY` is required. OHSC maps it to the OPENAI_* env vars that
the external `graphify` CLI expects and passes `--backend openai` automatically.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ohsc` not found | Run `bash setup.sh` or `python3 -m pip install -e .` from repo root; check PATH |
| Graphify: UNAVAILABLE | `uv tool install "graphifyy[mcp,openai]" --force` |
| no LLM API key found | Set `GROQ_API_KEY` (or matching key for your backend) in `.env` |
| Groq HTTP 403 | Ensure User-Agent is present (current code includes it); check key validity |
| `python` not found | Use `python3` — setup scripts already prefer it |

## Session token flow

1. `ohsc run` prints a short-lived session token.
2. External AI tools that load `skills/OHSC_AGENT_SKILL.md` can present that token when calling OHSC.
3. Token is local-only; treat it like a temporary capability grant.
