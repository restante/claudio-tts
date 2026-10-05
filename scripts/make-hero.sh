#!/usr/bin/env bash
# Re-record the English hero GIF (docs/demo.gif): install, configure, then a REAL Claude Code session.
# Needs: asciinema, agg, tmux, jq, claude (logged in), a downloaded model. Spends one short prompt.
set -euo pipefail
cd "$(dirname "$0")/.."
MODELS="${MODELS:-$HOME/Library/Application Support/claudio-tts/models}"
export LC_ALL=en_US.UTF-8
SANDBOX=/tmp/claudio-demo; rm -rf "$SANDBOX"; mkdir -p "$SANDBOX"
( # part 1 runs in a sandbox so it never touches your real settings
  export CLAUDIO_TTS_HOME="$SANDBOX/home" CLAUDE_CONFIG_DIR="$SANDBOX/claude"
  mkdir -p "$CLAUDIO_TTS_HOME/models" "$CLAUDE_CONFIG_DIR"
  cp "$MODELS"/*.onnx "$MODELS"/voices-v1.0.bin "$CLAUDIO_TTS_HOME/models/"
  echo '{}' > "$CLAUDE_CONFIG_DIR/settings.json"
  PATH="$CLAUDIO_TTS_HOME/venv/bin:$PATH" asciinema rec --overwrite --headless \
    --window-size 108x30 --idle-time-limit 2.5 --command "bash scripts/demo-install.sh" \
    "$SANDBOX/part1.cast" >/dev/null 2>&1
)
python3 scripts/record_claude_demo.py "$SANDBOX/part1.cast" "$SANDBOX/hero.cast"
agg --theme github-dark --font-size 16 --fps-cap 15 --last-frame-duration 4 --idle-time-limit 3 \
  --font-family "Menlo,Hiragino Sans,PingFang SC,Apple Color Emoji" \
  "$SANDBOX/hero.cast" docs/demo.gif >/dev/null 2>&1
ls -lh docs/demo.gif | awk '{print $5, $9}'
