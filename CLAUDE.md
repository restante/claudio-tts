# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv venv --python 3.12 && uv pip install -e ".[dev]"   # setup
.venv/bin/pytest                                       # all tests (Windows: .venv\Scripts\pytest)
.venv/bin/pytest tests/test_speak_flow.py::test_name   # single test
.venv/bin/ruff format . && .venv/bin/ruff check .      # lint (line length 100; CI also runs format --check)
claude plugin validate src/claudio_tts/mod             # if you touched the mod
claude plugin test src/claudio_tts/mod
bash install.sh --dev                                  # editable install, mod symlinked; restart Claude Code once, then it hot-reloads
```

- Tests need no sound card: set `CLAUDIO_TTS_FAKE_PLAYER=<file>` and playback becomes a log line (`CLAUDIO_TTS_FAKE_SECONDS` sets its duration).
- Other env vars: `CLAUDIO_TTS_HOME` (data dir), `CLAUDIO_TTS_PYTHON` (interpreter the mod uses, set by `install-mod`), `CLAUDIO_TTS_MODEL` / `CLAUDIO_TTS_VOICES` (model paths).
- CI runs lint + pytest on macOS, Windows and Linux, plus installer smoke tests (`install.sh --local --no-model`, then uninstall).

## Architecture

Two layers with a strict split:

- **Mod** (`src/claudio_tts/mod/`, TypeScript, Claude Code mod system): `hooks/register.ts` handles `turn.complete`, `turn.step`, `turn.start`, `session.end`, registers the `/tts` command and status line. `hooks/speech.ts` holds pure logic (arg parsing, text selection) so it can be unit tested (`register.test.ts`). The mod only decides *what* to say and *when*.
- **Python package** (`src/claudio_tts/`): all OS-specific work (audio, process control, locking, ducking). Keeps macOS/Windows on one code path. Anything OS-specific goes here, never in the mod.

Speech flow (see `docs/how-it-works.md`): the mod gets the final text in the event itself (never reads the transcript), checks the session's mute state, then runs `python -m claudio_tts speak --session <id> ...` with the text on stdin. `speak` (in `cli.py`) kills that session's previous worker, spawns a detached `_worker` and returns immediately. The worker (`player.py`) cleans markdown (`markdown.py`), ducks music (`duck.py`, macOS only), takes a cross-session speak lock (`locks.py`: `flock` / `msvcrt`), and streams Kokoro audio sentence by sentence. `stop --session <id>` ends only that session's process tree (`procs.py`, pid file plus process start time check).

State scope: mute is per session (mod session state, new sessions start muted); volume, speed, voice, devices, mic live in the mod store for all sessions.

Other pieces:
- `install_mod.py`: merges into the user's real `~/.claude/settings.json` (backup first, never overwrite, refuse invalid JSON). `install(name=, python_var=)` is reused by add-ons. Tests guard this; keep them green.
- `sinks.py`: add-ons (e.g. claudio-vibecode) register extra audio outputs via the `claudio_tts.sinks` entry-point group. A broken add-on must never silence speech.
- `sessionstate.py` / `claudio-tts session-state`: small per-session file add-ons read.
- `update.py`: opt-in updates from GitHub releases (`/tts update`).
- `model.py`: Kokoro model download with SHA-256 verification.
- `install.sh` / `install.ps1`: one-line installers (uv, private Python 3.12, venv, model, mod registration).

## Conventions

- Bug fixes come with a test that fails without the fix.
- Conventional Commits (`fix(mod): ...`, `feat(voices): ...`, `docs: ...`).
- Changing a command or behavior means updating README and `docs/` in the same change. README has 10 translations (`README.<lang>.md`); the English one is the source.
- Record user-facing changes in `CHANGELOG.md`; version lives in `pyproject.toml` and `src/claudio_tts/__init__.py`.
