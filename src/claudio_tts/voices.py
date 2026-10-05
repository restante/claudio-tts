"""Kokoro voices: listing, validation and the language each voice speaks."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from claudio_tts import model, paths

# First letter of a voice name is its language, second letter its gender (f/m).
LANGUAGES = {
    "a": ("en-us", "American English"),
    "b": ("en-gb", "British English"),
    "e": ("es", "Spanish"),
    "f": ("fr-fr", "French"),
    "h": ("hi", "Hindi"),
    "i": ("it", "Italian"),
    "j": ("ja", "Japanese"),
    "p": ("pt-br", "Brazilian Portuguese"),
    "z": ("cmn", "Mandarin Chinese"),
}
_NAME = re.compile(r"^[a-z]{2}_[a-z0-9]+$")


def language(voice: str) -> str:
    """The espeak language code for a voice (defaults to American English)."""
    return LANGUAGES.get(voice[:1], LANGUAGES["a"])[0]


def looks_valid(voice: str) -> bool:
    return bool(_NAME.match(voice)) and voice[:1] in LANGUAGES and voice[1:2] in ("f", "m")


def extras_dir() -> Path:
    """Drop `<name>.npy` style-vector files here to add your own voices (see docs/voices.md)."""
    return paths.data_dir() / "voices"


def extras() -> dict[str, Path]:
    folder = extras_dir()
    return {p.stem: p for p in sorted(folder.glob("*.npy"))} if folder.is_dir() else {}


def available() -> list[str]:
    """Every usable voice: the ones in the voices file plus your own extras, sorted.

    Empty if the model is missing.
    """
    found = model.find()
    if found is None:
        return []
    import numpy as np

    with np.load(found[1], allow_pickle=True) as data:
        names = set(data.files)
    return sorted(names | set(extras()))


def resolve(name: str):
    """What to hand to Kokoro for `name`: the name itself, or the style array of an extra voice."""
    path = extras().get(name)
    if path is None:
        return name
    import numpy as np

    return np.load(path).astype("float32")


def grouped(names: list[str]) -> dict[str, list[str]]:
    """Voices grouped by language, in a stable human order."""
    groups: dict[str, list[str]] = defaultdict(list)
    for name in names:
        groups[language(name)].append(name)
    order = [code for code, _ in LANGUAGES.values()]
    return {code: groups[code] for code in order if code in groups}


def label(code: str) -> str:
    return next(text for key, text in LANGUAGES.values() if key == code)


def suggest(voice: str, names: list[str]) -> list[str]:
    """Close matches for a mistyped voice (shared prefix or substring), best first."""
    bare = voice.split("_", 1)[-1]
    close = [n for n in names if bare and bare in n] or [n for n in names if n[:2] == voice[:2]]
    return close[:5]
