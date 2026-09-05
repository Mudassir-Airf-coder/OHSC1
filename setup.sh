#!/usr/bin/env bash
# OHSC one-time cross-platform setup (Linux / macOS)
# Usage: bash setup.sh [--unattended]
set -euo pipefail

UNATTENDED=0
for arg in "$@"; do
  case "$arg" in
    --unattended|-y|--yes) UNATTENDED=1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

info()  { printf '\n\033[1;34m[OHSC]\033[0m %s\n' "$*"; }
ok()    { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m[WARN]\033[0m %s\n' "$*"; }
fail()  { printf '\033[1;31m[FAIL]\033[0m %s\n' "$*"; exit 1; }

info "OHSC setup starting in: $ROOT"

PY=""
if command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PY="$(command -v python)"
else
  fail "Neither python3 nor python found. Install Python 3.10+ and retry."
fi
ok "Using Python: $PY ($($PY --version 2>&1))"

info "Installing OHSC package (editable)..."
PIP_FLAGS=(-e .)
if [[ -z "${VIRTUAL_ENV:-}" ]] && [[ -z "${CONDA_PREFIX:-}" ]]; then
  if $PY -c 'import sys; raise SystemExit(0 if sys.base_prefix == sys.prefix else 1)' 2>/dev/null; then
    PIP_FLAGS+=(--break-system-packages)
  fi
fi
$PY -m pip install "${PIP_FLAGS[@]}" || fail "pip install -e . failed"
ok "OHSC package installed (pip install -e .)"

export PATH="$HOME/.local/bin:$PATH"
if ! command -v ohsc >/dev/null 2>&1; then
  warn "'ohsc' not on PATH yet — you can still run: $PY -m ohsc.cli"
fi

info "Checking uv..."
if ! command -v uv >/dev/null 2>&1; then
  info "uv not found — installing via official installer..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  [[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env" || true
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  command -v uv >/dev/null 2>&1 || fail "uv install completed but 'uv' still not on PATH. Open a new shell and re-run setup.sh"
fi
ok "uv available: $(command -v uv)"

info "Installing graphify CLI (graphifyy[mcp,openai]) via uv tool..."
uv tool install "graphifyy[mcp,openai]" --force || warn "uv tool install graphifyy failed — Graphify features may be UNAVAILABLE"
export PATH="$HOME/.local/bin:$PATH"
if command -v graphify >/dev/null 2>&1; then
  ok "graphify CLI: $(command -v graphify)"
else
  warn "graphify binary not on PATH after install"
fi

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    ok "Created .env from .env.example"
  else
    printf '%s\n' 'GRAPHIFY_BRAIN_BACKEND=groq' 'GRAPHIFY_BRAIN_MODEL=openai/gpt-oss-120b' 'GROQ_API_KEY=' > .env
    ok "Created minimal .env"
  fi
  if [[ "$UNATTENDED" -eq 0 ]]; then
    echo
    echo "Optional: paste your GROQ_API_KEY (or press Enter to skip):"
    read -r -s KEY || true
    echo
    if [[ -n "${KEY:-}" ]]; then
      export OHSC_SETUP_GROQ_KEY="$KEY"
      $PY -c 'from pathlib import Path; import os; key=os.environ.get("OHSC_SETUP_GROQ_KEY",""); p=Path(".env"); lines=p.read_text(encoding="utf-8").splitlines() if p.exists() else []; out=[]; found=False
for line in lines:
    if line.startswith("GROQ_API_KEY="):
        out.append("GROQ_API_KEY="+key); found=True
    else:
        out.append(line)
if not found: out.append("GROQ_API_KEY="+key)
p.write_text("\n".join(out)+"\n", encoding="utf-8")'
      unset OHSC_SETUP_GROQ_KEY
      ok "GROQ_API_KEY saved to .env (value not printed)"
    else
      warn "No GROQ_API_KEY entered — Graphify Brain (Groq) disabled until you set it"
    fi
  else
    warn "Unattended mode: left .env placeholders as-is"
  fi
else
  ok ".env already exists — left unchanged"
fi

if [[ -f .env ]]; then
  set -a
  source .env 2>/dev/null || true
  set +a
fi

info "Running diagnostics..."
if command -v ohsc >/dev/null 2>&1; then
  ohsc doctor || warn "ohsc doctor reported issues (see above)"
elif $PY -c 'import ohsc' 2>/dev/null; then
  $PY -m ohsc.cli doctor || warn "ohsc doctor reported issues (see above)"
else
  warn "Could not import ohsc — install may have failed"
fi

info "Setup finished."
echo
echo "Next steps:"
echo "  export OHSC_SYSTEM_ROOT=\"$ROOT\""
echo "  export OHSC_VAULT_ROOT=\"/path/to/your/obsidian/vault\""
echo "  ohsc run"
echo "  ohsc --graphify build \"\$OHSC_VAULT_ROOT\""
echo
ok "OHSC setup complete"
