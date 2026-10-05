#!/usr/bin/env bash
# Part 1 of the English hero demo (install and configure), run by scripts/make-demo.sh --claude.
# Everything it runs is real, inside a throwaway sandbox (see make-demo.sh).
set -u
export PS1='$ '
RS=$'\033[0m'
type_cmd() {
  printf '%s$ ' "$RS"
  local text="$1" i
  for ((i = 0; i < ${#text}; i++)); do printf '%s' "${text:$i:1}"; sleep 0.03; done
  sleep 0.5; printf '\n'; eval "$1"; sleep "${2:-1.2}"
}
S="$CLAUDE_CONFIG_DIR/settings.json"
clear
type_cmd "bash install.sh --local 2>&1 | grep -E '==>|ok |All good'" 2.2
printf '\n'
type_cmd "jq '.env' $S" 2.2
type_cmd "jq '.env.KOKORO_VOICE=\"af_heart\" | .voice={enabled:true,mode:\"hold\"}' $S > $S.new && mv $S.new $S" 0.6
type_cmd "jq '{env: .env, voice: .voice}' $S" 3
type_cmd "claudio-tts voices | sed -n '1,3p'" 2
