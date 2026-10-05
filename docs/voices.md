# Voices and languages: the full guide

claudio-tts speaks with [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M). The **54 voices in 9 languages** that
ship with it are *examples, not limits*. This page shows how to use any other Kokoro voice, add your own, and read
text in languages Kokoro has no native voice for.

> Hear every built-in voice in the browser player: **https://restante.github.io/claudio-tts/**

## The basics

| Do this | To get this |
| --- | --- |
| `/tts voice` | List every voice and show the current one |
| `/tts voice bf_emma` | Use a voice (it says hello in it) |
| `/tts voice default` | Go back to the default voice |
| `claudio-tts voices` | The same list from a terminal |
| `"KOKORO_VOICE": "bf_emma"` in the `env` block of `~/.claude/settings.json` | A default voice for every session |

A voice name is `<language letter><gender letter>_<name>`. The language letter picks how text is pronounced, so
**claudio-tts chooses the language for you** (`a` American English, `b` British English, `e` Spanish, `f` French,
`h` Hindi, `i` Italian, `j` Japanese, `p` Brazilian Portuguese, `z` Mandarin Chinese).

## Any other voice

Everything `/tts voice` accepts is read from files, not from a fixed list, so there are three ways to bring
more voices.

### 1. Drop in a voice file

A Kokoro voice is a *style vector*: a `float32` array of shape `(510, 1, 256)` saved as `.npy`. Put one in the
`voices` folder of the install and its file name becomes a voice name:

| OS | Folder |
| --- | --- |
| macOS | `~/Library/Application Support/claudio-tts/voices/` |
| Windows | `%LOCALAPPDATA%\claudio-tts\voices\` |
| Linux | `~/.local/share/claudio-tts/voices/` |

```text
voices/my_voice.npy      →   /tts voice my_voice
```

Start the name with a language letter and a gender letter (for example `bf_myvoice`) and it is pronounced in that
language; otherwise it defaults to American English. Check with `claudio-tts voices`.

**Make your own voice by blending two** (this works today, with no extra tools):

```python
# run with the install's Python:  ~/Library/Application Support/claudio-tts/venv/bin/python blend.py
import numpy as np
from pathlib import Path

data = (
    Path.home() / "Library/Application Support/claudio-tts"
)  # Windows: %LOCALAPPDATA%\claudio-tts
voices = np.load(data / "models/voices-v1.0.bin", allow_pickle=True)
blend = 0.7 * voices["af_heart"] + 0.3 * voices["am_adam"]
(data / "voices").mkdir(exist_ok=True)
np.save(data / "voices/af_mix.npy", blend.astype("float32"))
```

Then `/tts voice af_mix`.

### 2. Use another Kokoro model or voices pack

Point claudio-tts at any Kokoro-compatible model and voices file, for example a newer Kokoro release or a
community pack with extra voices. Put both in the `env` block of `~/.claude/settings.json`:

```json
{
  "env": {
    "CLAUDIO_TTS_MODEL": "/path/to/kokoro-model.onnx",
    "CLAUDIO_TTS_VOICES": "/path/to/voices.bin"
  }
}
```

Restart Claude Code. Every voice in that pack now shows up in `/tts voice`. These two files are used as they
are and are not checksum-checked, so only use files you trust. Remove the two lines to go back to the built-in
model.

### 3. Add them to the built-in set

Bundled voices come from the official `voices-v1.0.bin`. If Kokoro releases a new voices file, the installer will
be updated; until then, use option 1 or 2.

## Any language

Kokoro has native voices for **9 languages**, but the speech engine can pronounce **140**. To read text in a
language with no native voice, set the language and keep using any voice:

```text
/tts lang de          # read German through the current voice
/tts lang             # list all 140 language codes
/tts lang auto        # back to the voice's own language
```

or from a terminal:

```bash
claudio-tts languages                                        # every code
claudio-tts say "Goedemorgen, hoe gaat het?" --voice af_heart --lang nl
```

Codes include `de`, `pl`, `ru`, `nl`, `sv`, `tr`, `ar`, `ko`, `vi`, `uk`, `cs`, `el`, `fi`, `da`, `nb`, `ro`, `id`
and many more. Languages without a native voice are read **with an accent** (the voice is trained on other
languages), which is usually understandable but not perfect. If Kokoro adds native voices for a language,
use them with `/tts voice` and set `/tts lang auto`.

Tip: if you chat with Claude in one language, pick a native voice for it (see the table in the README) and leave
`/tts lang` on `auto`.

## Troubleshooting

- **`unknown voice`**: run `claudio-tts voices`; the message suggests close names.
- **`unknown language`**: run `claudio-tts languages`; codes are lowercase (`pt-br`, not `pt_BR`).
- **My `.npy` voice isn't listed**: it must be in the `voices` folder above, end in `.npy`, and the install must
  have a model (`claudio-tts doctor`).
- **Garbled speech with a custom file**: the array shape must be `(510, 1, 256)` and `float32`.
