# Changelog

## 0.5.0

- New: **add-on outputs.** Packages can register extra audio outputs under the `claudio_tts.sinks` entry-point
  group (see `claudio_tts/sinks.py`). They show in `claudio-tts devices` and can be chosen with `/tts device <name>`.
  The first user is [claudio-vibecode](https://github.com/restante/claudio-vibecode), which plays Claude's speech on
  your phone.
- New: a small per-session state file (`claudio-tts session-state`) that add-ons can read to show whether a session
  is muted.
- Docs: the README points to the new companion project claudio-vibecode (phone remote).
- `install_mod.install()` takes `name` and `python_var`, so add-ons can reuse its safe `settings.json` merge.

## 0.4.0

- New: **updates on your say-so.** `/tts update` (or `claudio-tts update --yes`) installs the newest GitHub
  release and refreshes the mod. A session start checks at most once a day and shows
  `update available`; nothing is installed until you ask. `/tts update off` turns the check off.
- Fix: the `/tts` command description now lists `voice` and `lang` (and `update`).
- Releases are published automatically from `v*` tags.

## 0.3.0

- New: a **browser voice player** (GitHub Pages) with a play button for each of the 54 voices, plus samples
  for every voice. GitHub can't play audio inside a README, so the README links to the player.
- New: **any voice, any language.** `/tts lang <code>` makes a voice read any of 140 languages
  (`claudio-tts languages`), your own `voices/<name>.npy` files appear in `/tts voice`, and
  `CLAUDIO_TTS_MODEL` / `CLAUDIO_TTS_VOICES` point to another Kokoro model or voices pack.
- Docs: new `docs/voices.md` (including how to blend two voices today); the README stresses the 54 voices
  and 9 languages are examples, not limits.

## 0.2.0

- New: `/tts voice <name>` to change the voice, `/tts voice` to list all 54 voices, `/tts voice default` to reset.
  `claudio-tts voices` lists them from a terminal. The language is chosen from the voice automatically.
- New: `claudio-tts doctor --report` prints a ready-to-paste block for bug reports.
- New: demo GIF, voice samples, and a rewritten README with translations
  (Italian, Polish, French, German, Japanese, Simplified Chinese).
- New: contributing guide, issue templates and a pull request template.
- Docs: Kokoro advantages (no tokens, no APIs, offline) and how to use the voices.

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
