#!/usr/bin/env bash
# Re-record the demo GIFs in throwaway sandboxes (needs: asciinema, agg, a downloaded model).
# Usage: scripts/make-demo.sh [lang ...]     langs: en it pl fr de ja zh-CN hi ru es pt-BR (default: all)
#        MODELS=/path/to/models scripts/make-demo.sh en
# Writes docs/demo.gif for en and docs/demo.<lang>.gif for the others.
set -euo pipefail
cd "$(dirname "$0")/.."
MODELS="${MODELS:-$HOME/Library/Application Support/claudio-tts/models}"
LANGS=("$@"); [ ${#LANGS[@]} -gt 0 ] || LANGS=(en it pl fr de ja zh-CN hi ru es pt-BR)
export LC_ALL=en_US.UTF-8
for L in "${LANGS[@]}"; do
  OUT="docs/demo.$L.gif"; [ "$L" = en ] && OUT=docs/demo.gif
  SANDBOX=/tmp/claudio-demo; rm -rf "$SANDBOX"; mkdir -p "$SANDBOX"
  export CLAUDIO_TTS_HOME="$SANDBOX/home" CLAUDE_CONFIG_DIR="$SANDBOX/claude"
  mkdir -p "$CLAUDIO_TTS_HOME/models" "$CLAUDE_CONFIG_DIR"
  cp "$MODELS"/*.onnx "$MODELS"/voices-v1.0.bin "$CLAUDIO_TTS_HOME/models/"
  PATH="$CLAUDIO_TTS_HOME/venv/bin:$PATH" DEMO_LANG="$L" \
    asciinema rec --overwrite --headless --window-size 108x30 --idle-time-limit 2.5 \
      --command "bash scripts/demo.sh" "$SANDBOX/demo.cast" >/dev/null 2>&1
  agg --theme github-dark --font-size 16 --fps-cap 15 --last-frame-duration 4 \
    --font-family "Menlo,Hiragino Sans,PingFang SC,Devanagari Sangam MN,Apple Color Emoji" \
    "$SANDBOX/demo.cast" "$OUT" >/dev/null 2>&1
  rm -rf "$SANDBOX"
  ls -lh "$OUT" | awk '{print $5, $9}'
done
