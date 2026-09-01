# OHSC Usage Guide

## Install

```bash
git clone https://github.com/Mudassir-Airf-coder/OHSC1.git
cd OHSC1
pip install -e .
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
ohsc --dry-run "create a MOC for Research"
ohsc --authorized "create a note titled Decisions"
```

## Graphify

```bash
ohsc --graphify build "$OHSC_VAULT_ROOT"
ohsc --graphify query "what are the main themes?"
ohsc --graphify path --source "ConceptA" --target "ConceptB"
ohsc --graphify explain "ConceptA"
ohsc --graphify analyze
```

## Using OHSC from an AI tool

1. Install and configure OHSC on the machine
2. Run `ohsc run` (copy token if required)
3. Load `skills/OHSC_AGENT_SKILL.md` into the tool’s skill / system context
4. Let the tool call `ohsc capabilities --json` and `ohsc agents --json`
5. Execute tasks through the CLI only for normal operation

## Safety tips

- Prefer `--dry-run` before first writes
- Use `--authorized` only when you intend writes / destructive ops
- Keep API keys in environment / `.env`, never in the repo
- Point `OHSC_VAULT_ROOT` at a test vault until you trust the setup

## Troubleshooting

| Symptom | What to check |
|---|---|
| `ohsc` not found | `pip install -e .` from repo root; check PATH |
| Wrong vault | `echo $OHSC_VAULT_ROOT` / PowerShell env |
| Status DEGRADED | Optional Graphify / OpenCode missing — core can still work |
| Path errors | Ensure portable env vars set; avoid old hardcoded paths |
