# OHSC one-time setup for Windows PowerShell
# Usage: powershell -ExecutionPolicy Bypass -File .\setup.ps1 [-Unattended]
param(
  [switch]$Unattended
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Info($m) { Write-Host "`n[OHSC] $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[OK] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; exit 1 }

Info "OHSC setup starting in: $Root"

$PyCmd = $null
$PyArgs = @()
foreach ($c in @("python3", "py", "python")) {
  $cmd = Get-Command $c -ErrorAction SilentlyContinue
  if ($cmd) {
    if ($c -eq "py") {
      $PyCmd = "py"
      $PyArgs = @("-3")
    } else {
      $PyCmd = $c
      $PyArgs = @()
    }
    break
  }
}
if (-not $PyCmd) { Fail "Python 3.10+ not found. Install from https://python.org and retry." }
Ok "Using Python launcher: $PyCmd $($PyArgs -join ' ')"

Info "Installing OHSC package (editable)..."
& $PyCmd @PyArgs -m pip install -e .
if ($LASTEXITCODE -ne 0) { Fail "pip install -e . failed" }
Ok "OHSC package installed"

Info "Checking uv..."
$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
  Info "uv not found — installing via official Windows installer..."
  try {
    irm https://astral.sh/uv/install.ps1 | iex
  } catch {
    Warn "Automatic uv install failed: $_"
  }
  $env:Path = "$env:USERPROFILE\.local\bin;$env:USERPROFILE\.cargo\bin;$env:Path"
  $uv = Get-Command uv -ErrorAction SilentlyContinue
  if (-not $uv) { Warn "uv still not on PATH — open a new terminal and re-run setup.ps1 for graphify install" }
}
if (Get-Command uv -ErrorAction SilentlyContinue) {
  Ok "uv available"
  Info "Installing graphify CLI (graphifyy[mcp,openai])..."
  uv tool install "graphifyy[mcp,openai]" --force
  if ($LASTEXITCODE -ne 0) { Warn "uv tool install graphifyy failed" } else { Ok "graphify tool installed" }
}

if (-not (Test-Path ".env")) {
  if (Test-Path ".env.example") {
    Copy-Item ".env.example" ".env"
    Ok "Created .env from .env.example"
  } else {
    @(
      "GRAPHIFY_BRAIN_BACKEND=groq"
      "GRAPHIFY_BRAIN_MODEL=openai/gpt-oss-120b"
      "GROQ_API_KEY="
    ) | Set-Content -Path ".env" -Encoding UTF8
    Ok "Created minimal .env"
  }
  if (-not $Unattended) {
    $key = Read-Host "Optional: paste GROQ_API_KEY (leave blank to skip)"
    if ($key) {
      $lines = Get-Content ".env"
      $out = @()
      $found = $false
      foreach ($line in $lines) {
        if ($line -match '^GROQ_API_KEY=') {
          $out += "GROQ_API_KEY=$key"
          $found = $true
        } else {
          $out += $line
        }
      }
      if (-not $found) { $out += "GROQ_API_KEY=$key" }
      $out | Set-Content ".env" -Encoding UTF8
      Ok "GROQ_API_KEY saved to .env (value not printed)"
    } else {
      Warn "No GROQ_API_KEY entered — set it later in .env for Graphify Brain"
    }
  } else {
    Warn "Unattended mode: left .env placeholders as-is"
  }
} else {
  Ok ".env already exists — left unchanged"
}

Get-Content ".env" -ErrorAction SilentlyContinue | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
  $parts = $_.Split('=', 2)
  if ($parts.Length -eq 2) {
    $k = $parts[0].Trim()
    $v = $parts[1]
    if ($k) { Set-Item -Path "Env:$k" -Value $v }
  }
}

Info "Running diagnostics..."
if (Get-Command ohsc -ErrorAction SilentlyContinue) {
  ohsc doctor
} else {
  & $PyCmd @PyArgs -m ohsc.cli doctor
}

Info "Setup finished."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  `$env:OHSC_SYSTEM_ROOT = '$Root'"
Write-Host "  `$env:OHSC_VAULT_ROOT = 'C:\path\to\your\obsidian\vault'"
Write-Host "  ohsc run"
Write-Host "  ohsc --graphify build `$env:OHSC_VAULT_ROOT"
Write-Host ""
Ok "OHSC setup complete"
