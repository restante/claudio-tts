"""Render the short voice samples linked from the README (docs/samples/*.mp3).

Needs the model (`claudio-tts download-model`) and ffmpeg. Run with the project's Python:
    python scripts/make_samples.py [--all | voice ...]
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import numpy as np
from kokoro_onnx import Kokoro

from claudio_tts import model, voices

OUT = Path(__file__).resolve().parent.parent / "docs" / "samples"

LINES = {
    "es": "Hola, soy {n}. Así sueno leyendo las respuestas de Claude.",
    "fr-fr": "Bonjour, je suis {n}. Voici ma voix pour lire les réponses de Claude.",
    "it": "Ciao, sono {n}. Ecco come leggo le risposte di Claude.",
    "ja": "こんにちは、{n}です。Claudeの返信を読み上げます。",
    "cmn": "你好，我是{n}。我来朗读 Claude 的回复。",
    "hi": "नमस्ते, मैं {n} हूँ। मैं Claude के जवाब पढ़ती हूँ।",
    "pt-br": "Olá, eu sou {n}. É assim que eu leio as respostas do Claude.",
}
ENGLISH = "Hi, I'm {n}. This is how I sound reading Claude's replies."
DEFAULT = [
    "af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky", "am_michael", "am_fenrir",
    "am_puck", "bf_emma", "bf_isabella", "bm_george", "bm_fable", "ef_dora", "ff_siwis",
    "if_sara", "jf_alpha", "zf_xiaoxiao", "hf_alpha", "pf_dora",
]  # fmt: skip


async def render(kokoro: Kokoro, voice: str) -> np.ndarray:
    lang = voices.language(voice)
    text = LINES.get(lang, ENGLISH).format(n=voice[3:].capitalize())
    parts = []
    async for samples, _rate in kokoro.create_stream(text, voice=voice, speed=1.0, lang=lang):
        parts.append(samples)
    return np.concatenate(parts)


def main() -> None:
    found = model.find()
    if found is None:
        raise SystemExit("model missing: run `claudio-tts download-model`")
    kokoro = Kokoro(str(found[0]), str(found[1]))
    OUT.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    chosen = voices.available() if args == ["--all"] else args or DEFAULT
    for voice in chosen:
        audio = asyncio.run(render(kokoro, voice)).astype("float32")
        target = OUT / f"{voice}.mp3"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", "24000", "-ac", "1", "-i", "-",
             "-b:a", "48k", str(target)],
            input=audio.tobytes(), check=True,
        )  # fmt: skip
        print(f"{voice}: {target.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
