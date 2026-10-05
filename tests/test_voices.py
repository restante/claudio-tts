from claudio_tts import model, voices


def test_language_comes_from_the_first_letter():
    assert voices.language("af_heart") == "en-us"
    assert voices.language("bf_emma") == "en-gb"
    assert voices.language("ef_dora") == "es"
    assert voices.language("ff_siwis") == "fr-fr"
    assert voices.language("jf_alpha") == "ja"
    assert voices.language("zm_yunxi") == "cmn"
    assert voices.language("xx_unknown") == "en-us"


def test_names_are_validated_by_shape():
    assert voices.looks_valid("af_bella")
    assert not voices.looks_valid("bella")
    assert not voices.looks_valid("qf_bella")
    assert not voices.looks_valid("af_")


def test_grouping_is_by_language_in_a_stable_order():
    groups = voices.grouped(["bf_emma", "af_sky", "af_heart", "jm_kumo"])
    assert list(groups) == ["en-us", "en-gb", "ja"]
    assert groups["en-us"] == ["af_sky", "af_heart"]
    assert voices.label("en-gb") == "British English"


def test_suggestions_catch_typos():
    names = ["af_alloy", "af_bella", "am_adam"]
    assert voices.suggest("af_bela", names)  # same-gender-and-language fallback
    assert "af_bella" in voices.suggest("xx_bella", names)


def test_available_is_empty_without_a_model():
    assert voices.available() == []


def test_available_reads_the_voices_file(tmp_path, monkeypatch):
    import numpy as np

    path = tmp_path / "voices.bin"
    with path.open("wb") as handle:
        np.savez(handle, af_heart=np.zeros(1), bm_george=np.zeros(1))
    monkeypatch.setattr(model, "find", lambda: (tmp_path / "m.onnx", path))
    assert voices.available() == ["af_heart", "bm_george"]
