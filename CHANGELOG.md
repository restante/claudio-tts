# Changelog

## 0.1.1

- Fix: replies were never spoken because the mod passed the text to `$.process.run` as `input` instead of `stdin`.
  Added a regression test that checks the answer reaches the speak command.

## 0.1.0

First release.

- Spoken replies and pre-tool narration from Claude Code turn events (never one reply behind).
- Per-session mute, startup default (new sessions start muted), shared volume, speed and output devices.
- Speech to one, several or all output devices at once, streamed sentence by sentence.
- Sessions take turns; each session stops only its own speech.
- One-line installers for macOS and Windows (beta) with checksum-verified model download.
