"""Languages the speech engine can pronounce. Kokoro ships voices for 9 of them natively;
the phonemizer (espeak-ng) knows about 140, so a voice can read the others with an accent."""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def supported() -> dict[str, str]:
    """Map of espeak-ng language code to English name, like {"de": "German"}."""
    import espeakng_loader
    from phonemizer.backend import EspeakBackend
    from phonemizer.backend.espeak.wrapper import EspeakWrapper

    EspeakWrapper.set_library(espeakng_loader.get_library_path())
    EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
    return dict(sorted(EspeakBackend.supported_languages().items()))


def check(code: str) -> bool:
    return code.lower() in supported()
