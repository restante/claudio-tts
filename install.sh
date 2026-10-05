#!/usr/bin/env bash
# claudio-tts installer for macOS (and Linux, best effort).
#
#   curl -fsSL https://raw.githubusercontent.com/restante/claudio-tts/main/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --lite        # smaller 92 MB model
#
# Options: --lite  --no-model  --uninstall [--keep-models]  --local  --ref <git ref>  --dev
set -euo pipefail

REPO="${CLAUDIO_TTS_REPO:-restante/claudio-tts}"
REF="${CLAUDIO_TTS_REF:-main}"
LITE=0 NO_MODEL=0 UNINSTALL=0 KEEP_MODELS=0 LOCAL=0 DEV=0

while [ $# -gt 0 ]; do
  case "$1" in
    --lite) LITE=1 ;;
    --no-model) NO_MODEL=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --keep-models) KEEP_MODELS=1 ;;
    --local) LOCAL=1 ;;      # install from the checkout this script sits in
    --dev) DEV=1; LOCAL=1 ;; # like --local, editable, and link the mod instead of copying
    --ref) REF="$2"; shift ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

case "$(uname -s)" in
  Darwin) DEFAULT_HOME="$HOME/Library/Application Support/claudio-tts" ;;
  Linux)  DEFAULT_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/claudio-tts"
          warn "Linux is best effort: it should work, but it is not tested on real hardware." ;;
  *) die "Unsupported OS $(uname -s). On Windows use install.ps1." ;;
esac
HOME_DIR="${CLAUDIO_TTS_HOME:-$DEFAULT_HOME}"
VENV="$HOME_DIR/venv"
PY="$VENV/bin/python"

if [ "$UNINSTALL" = 1 ]; then
  say "Uninstalling claudio-tts"
  if [ -x "$PY" ]; then "$PY" -m claudio_tts uninstall-mod || true; fi
  if [ "$KEEP_MODELS" = 1 ]; then
    rm -rf "$VENV" "$HOME_DIR/state"
  else
    rm -rf "$HOME_DIR"
  fi
  say "Done. Restart open Claude Code sessions to drop the mod."
  exit 0
fi

# 1. Prerequisites ---------------------------------------------------------------------------
command -v curl >/dev/null || die "curl is required."
if ! command -v claude >/dev/null; then
  warn "Claude Code ('claude') was not found on PATH. The mod is installed anyway; it needs"
  warn "Claude Code to do anything. Install it from https://claude.com/claude-code"
fi

if ! command -v uv >/dev/null; then
  say "Installing uv (the Python manager; it also fetches Python for us)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  command -v uv >/dev/null || die "uv installed but is not on PATH; open a new terminal and re-run."
fi

# 2. Python environment + package -------------------------------------------------------------
say "Creating a private Python 3.12 environment in $VENV"
mkdir -p "$HOME_DIR"
uv venv --python 3.12 --allow-existing -q "$VENV"

if [ "$LOCAL" = 1 ]; then
  SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
  [ -f "$SRC/pyproject.toml" ] || die "--local needs to run from a claudio-tts checkout."
  say "Installing claudio-tts from $SRC"
  if [ "$DEV" = 1 ]; then uv pip install -q --python "$PY" -e "$SRC"; else uv pip install -q --python "$PY" "$SRC"; fi
else
  say "Installing claudio-tts ($REPO@$REF)"
  uv pip install -q --python "$PY" "claudio-tts @ git+https://github.com/$REPO@$REF"
fi

# 3. Voice model (checksum-verified) ------------------------------------------------------------
if [ "$NO_MODEL" = 0 ]; then
  say "Fetching the Kokoro voice model"
  if [ "$LITE" = 1 ]; then "$PY" -m claudio_tts download-model --lite; else "$PY" -m claudio_tts download-model; fi
fi

# 4. Claude Code mod ---------------------------------------------------------------------------------
say "Installing the Claude Code mod"
if [ "$DEV" = 1 ]; then "$PY" -m claudio_tts install-mod --python "$PY" --link
else "$PY" -m claudio_tts install-mod --python "$PY"; fi

say "Checking everything"
"$PY" -m claudio_tts doctor || warn "Some checks failed; see above."

cat <<DONE

claudio-tts is installed.

  1. Restart Claude Code (open sessions only pick the mod up when they start).
  2. In a session type:  /tts unmute      (new sessions start muted on purpose)
  3. Send a message and listen.

Other commands: /tts volume 7, /tts speed 0.9, /tts device <name|all|default>, /tts status
Test the voice any time:  "$PY" -m claudio_tts doctor --speak
DONE
