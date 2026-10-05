# How claudio-tts works

## The pieces

| Piece | Where | Job |
| --- | --- | --- |
| **Mod** | `src/claudio_tts/mod` (TypeScript) | Listens to Claude Code events, keeps per-session mute, calls the CLI |
| **CLI** | `claudio_tts.cli` | `speak`, `stop`, `devices`, `doctor`, `download-model`, `install-mod` |
| **Worker** | `claudio-tts _worker` (detached) | Cleans text, waits for its turn, streams audio |
| **Model** | `<data dir>/models` | Kokoro `.onnx` + voices, SHA-256 verified |

## A reply, step by step

1. Claude finishes a turn. The mod's `turn.complete` hook receives the final text **in the event itself**
   (no transcript file is read, so there is no race that could make it one reply behind).
2. The mod checks this session's mute state, then runs
   `python -m claudio_tts speak --session <id> --volume … --speed … --devices …` with the text on stdin.
3. `speak` stops this session's previous worker (a new reply replaces an older one), starts a **detached worker**
   and returns at once, so the hook never blocks Claude.
4. The worker cleans the markdown (code dropped, links keep their label), ducks your music (macOS), then takes the
   **speak lock**: only one session talks at a time. It streams Kokoro audio sentence by sentence to the chosen
   device(s) and finally restores your music.
5. A new prompt, `/tts mute` or the end of the session calls `stop --session <id>`, which ends **only that
   session's** worker (its process tree, found through a pid file that also checks the process start time).

## Narration before tools

Before the first tool call of a turn the mod speaks the text Claude wrote ahead of it, unless that text carries a
`TTS_SUMMARY` block (the final answer will read that instead).

## State

| Setting | Scope | Stored |
| --- | --- | --- |
| mute | this session | Claude Code mod session state |
| startup default, volume, speed, devices, mic | all sessions | Claude Code mod store |

## Cross-platform notes

- Locking: `fcntl.flock` on macOS/Linux, `msvcrt.locking` on Windows.
- Detaching: `start_new_session` on macOS/Linux, `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` on Windows.
- Ducking: AppleScript on macOS (Apple Music and Spotify); not implemented on Windows yet.
