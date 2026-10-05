<#
.SYNOPSIS
  claudio-tts installer for Windows (beta).

.EXAMPLE
  irm https://raw.githubusercontent.com/restante/claudio-tts/main/install.ps1 | iex

.EXAMPLE
  & ([scriptblock]::Create((irm https://raw.githubusercontent.com/restante/claudio-tts/main/install.ps1))) -Lite

.PARAMETER Lite      Use the smaller 92 MB model instead of the 326 MB one.
.PARAMETER NoModel   Skip the model download.
.PARAMETER Uninstall Remove the mod, its settings entries and (unless -KeepModels) all data.
.PARAMETER Local     Install from the checkout this script sits in.
.PARAMETER Ref       Git ref to install (default main).

  With `irm | iex` you cannot pass parameters; set CLAUDIO_TTS_LITE=1, CLAUDIO_TTS_NO_MODEL=1,
  CLAUDIO_TTS_REF=<ref> or CLAUDIO_TTS_UNINSTALL=1 in the environment instead.
#>
[CmdletBinding()]
param(
  [switch]$Lite = ($env:CLAUDIO_TTS_LITE -eq '1'),
  [switch]$NoModel = ($env:CLAUDIO_TTS_NO_MODEL -eq '1'),
  [switch]$Uninstall = ($env:CLAUDIO_TTS_UNINSTALL -eq '1'),
  [switch]$KeepModels,
  [switch]$Local,
  [string]$Ref = $(if ($env:CLAUDIO_TTS_REF) { $env:CLAUDIO_TTS_REF } else { 'main' })
)

$ErrorActionPreference = 'Stop'
$Repo = if ($env:CLAUDIO_TTS_REPO) { $env:CLAUDIO_TTS_REPO } else { 'restante/claudio-tts' }

function Say($m)  { Write-Host "==> $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "warning: $m" -ForegroundColor Yellow }
function Die($m)  { Write-Host "error: $m" -ForegroundColor Red; exit 1 }

# A native command that fails must stop the script (PowerShell does not do this by itself).
function Run {
  param([Parameter(Mandatory)][string]$Exe, [Parameter(ValueFromRemainingArguments)]$Rest)
  & $Exe @Rest
  if ($LASTEXITCODE -ne 0) { Die "$Exe $($Rest -join ' ') failed (exit $LASTEXITCODE)" }
}

$HomeDir = if ($env:CLAUDIO_TTS_HOME) { $env:CLAUDIO_TTS_HOME }
           else { Join-Path $(if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME 'AppData\Local' }) 'claudio-tts' }
$Venv = Join-Path $HomeDir 'venv'
$Py = Join-Path $Venv 'Scripts\python.exe'

if ($Uninstall) {
  Say 'Uninstalling claudio-tts'
  if (Test-Path $Py) { & $Py -m claudio_tts uninstall-mod }
  if ($KeepModels) {
    Remove-Item -Recurse -Force $Venv, (Join-Path $HomeDir 'state') -ErrorAction SilentlyContinue
  } else {
    Remove-Item -Recurse -Force $HomeDir -ErrorAction SilentlyContinue
  }
  Say 'Done. Restart open Claude Code sessions to drop the mod.'
  return
}

# 1. Prerequisites ---------------------------------------------------------------------------
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Warn "Claude Code ('claude') was not found on PATH. The mod is installed anyway; it needs Claude Code to do anything."
  Warn 'Install it from https://claude.com/claude-code'
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Say 'Installing uv (the Python manager; it also fetches Python for us)'
  Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
  $env:Path = "$HOME\.local\bin;$HOME\.cargo\bin;$env:Path"
  if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { Die 'uv installed but is not on PATH; open a new terminal and re-run.' }
}

# 2. Python environment + package -------------------------------------------------------------
Say "Creating a private Python 3.12 environment in $Venv"
New-Item -ItemType Directory -Force $HomeDir | Out-Null
Run uv venv --python 3.12 --allow-existing -q $Venv

if ($Local) {
  $Src = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
  if (-not (Test-Path (Join-Path $Src 'pyproject.toml'))) { Die '-Local needs to run from a claudio-tts checkout.' }
  Say "Installing claudio-tts from $Src"
  Run uv pip install -q --python $Py $Src
} else {
  Say "Installing claudio-tts ($Repo@$Ref)"
  Run uv pip install -q --python $Py "claudio-tts @ git+https://github.com/$Repo@$Ref"
}

# 3. Voice model (checksum-verified) ------------------------------------------------------------
if (-not $NoModel) {
  Say 'Fetching the Kokoro voice model'
  if ($Lite) { Run $Py -m claudio_tts download-model --lite } else { Run $Py -m claudio_tts download-model }
}

# 4. Claude Code mod ---------------------------------------------------------------------------------
Say 'Installing the Claude Code mod'
Run $Py -m claudio_tts install-mod --python $Py

Say 'Checking everything'
& $Py -m claudio_tts doctor
if ($LASTEXITCODE -ne 0) { Warn 'Some checks failed; see above.' }

Write-Host @"

claudio-tts is installed.

  1. Restart Claude Code (open sessions only pick the mod up when they start).
  2. In a session type:  /tts unmute      (new sessions start muted on purpose)
  3. Send a message and listen.

Other commands: /tts volume 7, /tts speed 0.9, /tts device <name|all|default>, /tts status
Test the voice any time:  & "$Py" -m claudio_tts doctor --speak

Windows support is in beta: please report problems at https://github.com/$Repo/issues
"@
