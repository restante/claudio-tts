# Audiobooks

`claudio-tts audiobook` turns a text or markdown file into audio files with the same local Kokoro voices.
It is a batch job: nothing is played, and nothing leaves your machine.

```bash
claudio-tts audiobook book.md --dry-run                 # chapters and estimated length, writes nothing
claudio-tts audiobook book.md --voice af_heart          # folder book-audiobook/ with 01-intro.wav, 02-...
claudio-tts audiobook book.md --format m4b              # one file with chapter marks (needs ffmpeg)
```

| Option | Meaning |
|---|---|
| `-o, --output DIR` | output folder (default: `<file>-audiobook` next to the file) |
| `--format wav\|mp3\|m4b` | `wav` (default) keeps one file per chapter; `mp3` and `m4b` also pack them with ffmpeg |
| `--voice`, `--speed`, `--lang` | same as `/tts` (see [voices](voices.md)) |
| `--force` | redo chapters that already exist |
| `--dry-run` | print the plan only |

**Chapters.** Markdown headings (`#`, `##`, `###`) and lines such as `Chapter 3` start a chapter, and the title
is read aloud. A file without headings is cut into parts of about 3,000 characters on paragraph boundaries.

**Resume.** Each chapter is written to a `.part` file and renamed when complete, so an interrupted run never
leaves a broken chapter. Run the same command again to continue.

**ffmpeg.** Not required. Without it you get the chapter WAVs and a hint. On macOS: `brew install ffmpeg`.

**Claude Code skill.** `skills/audiobook/SKILL.md` lets Claude Code run this for you. Copy the folder to
`~/.claude/skills/audiobook/`. Claude Desktop cannot run local commands from a skill; it needs a local
MCP bundle, which is not built yet.
