# Contributing to claudio-tts

Thank you for wanting to help! This is a small, friendly project and every kind of contribution is welcome:
code, docs, translations, bug reports, "I tried it on Windows and…" notes, and ideas.

**Want to talk first?** [Start a discussion](https://github.com/restante/claudio-tts/discussions) or find me on
GitHub: [@restante](https://github.com/restante).

## Report a bug

1. Run `claudio-tts doctor --report` and copy the output (it never includes anything you have spoken).
2. [Open a bug report](https://github.com/restante/claudio-tts/issues/new?template=bug_report.yml) and paste it in.

## Set up in five minutes

You need Python 3.10+ (or just [`uv`](https://docs.astral.sh/uv/), which fetches Python for you) and, to work on
the mod, [Claude Code](https://claude.com/claude-code).

```bash
git clone https://github.com/restante/claudio-tts && cd claudio-tts
uv venv --python 3.12
uv pip install -e ".[dev]"
.venv/bin/pytest            # Windows: .venv\Scripts\pytest
.venv/bin/ruff check . && .venv/bin/ruff format --check .
```

To try your changes inside Claude Code (macOS/Linux):

```bash
bash install.sh --dev       # editable install; the mod is symlinked from src/claudio_tts/mod
```

Restart Claude Code once, then edit the mod and it hot-reloads.

## What lives where

| Path | What it is |
| --- | --- |
| `src/claudio_tts/` | The Python package: audio, locking, per-session processes, ducking, model download, CLI |
| `src/claudio_tts/mod/` | The Claude Code mod (TypeScript): events, `/tts` command, per-session mute |
| `tests/` | pytest suite (runs on macOS, Windows and Linux in CI; audio is faked) |
| `install.sh`, `install.ps1` | One-line installers |
| `docs/` | How it works, troubleshooting, Windows notes, demo GIF, voice samples |
| `scripts/` | `make-demo.sh` (re-record the GIF), `make_samples.py` (re-render voice samples) |

## Checks before you open a pull request

```bash
.venv/bin/ruff format . && .venv/bin/ruff check .
.venv/bin/pytest
claude plugin validate src/claudio_tts/mod      # if you touched the mod
claude plugin test src/claudio_tts/mod
```

CI runs the Python checks and the installer smoke tests on all three operating systems.

## Guidelines

- **Keep the split:** anything OS-specific belongs in the Python package. The mod only decides *what* to say and
  *when*, so Windows and macOS keep sharing one code path.
- **Tests with the change.** A bug fix should come with a test that fails without it. (The 0.1.1 fix has one: the
  mod passed `input` instead of `stdin` and nothing noticed until a test checked the speak command's stdin.)
- **No sound card needed in tests.** Set `CLAUDIO_TTS_FAKE_PLAYER=<file>` and playback becomes a log line.
- **Be careful with `settings.json`.** The installer edits a user's real settings: back up first, merge, never
  overwrite, refuse invalid JSON. There are tests for this; keep them green.
- **Small pull requests are easier to review.** One idea per PR, with a short description of *why*.
- **Commit messages** follow [Conventional Commits](https://www.conventionalcommits.org/): `fix(mod): …`,
  `feat(voices): …`, `docs: …`.
- **Docs.** If you change a command or behavior, update the README and `docs/` in the same PR.

## Good first issues

Look for the [`good first issue`](https://github.com/restante/claudio-tts/labels/good%20first%20issue) and
[`help wanted`](https://github.com/restante/claudio-tts/labels/help%20wanted) labels. Testing on real **Windows**
hardware is the single most useful thing right now.

## Being kind

Be respectful and patient, assume good intent, and remember that people here are volunteers. Harassment or
disrespect isn't welcome, and I'll step in if needed.

## License

By contributing you agree that your contribution is licensed under the [MIT License](LICENSE).
