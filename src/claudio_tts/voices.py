"""Kokoro voices: listing, validation and the language each voice speaks."""

from __future__ import annotations

import re
from collections import defaultdict

from claudio_tts import model

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


def available() -> list[str]:
    """Every voice shipped in the installed voices file, sorted. Empty if the model is missing."""
    found = model.find()
    if found is None:
        return []
    import numpy as np

    with np.load(found[1], allow_pickle=True) as data:
        return sorted(data.files)


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
