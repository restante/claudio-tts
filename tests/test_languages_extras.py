import numpy as np
import pytest

from claudio_tts import languages, model, voices


def test_espeak_knows_far_more_languages_than_the_nine_with_native_voices():
    known = languages.supported()
    assert len(known) > 100
    for code in ("de", "pl", "ru", "nl", "tr", "ko", "ar", "sv", "pt-br", "cmn"):
        assert code in known


def test_language_check_is_case_insensitive_and_rejects_unknown_codes():
    assert languages.check("DE")
    assert not languages.check("zz")


def test_model_override_wins_when_both_files_exist(tmp_path, monkeypatch):
    m, v = tmp_path / "other.onnx", tmp_path / "other.bin"
    m.write_bytes(b"m")
    v.write_bytes(b"v")
    monkeypatch.setenv("CLAUDIO_TTS_MODEL", str(m))
    monkeypatch.setenv("CLAUDIO_TTS_VOICES", str(v))
    assert model.find() == (m, v)


def test_model_override_needs_both_variables_and_real_files(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDIO_TTS_MODEL", str(tmp_path / "missing.onnx"))
    assert model.override() is None
    monkeypatch.setenv("CLAUDIO_TTS_VOICES", str(tmp_path / "missing.bin"))
    assert model.override() is None


def _fake_installed_voices(tmp_path, monkeypatch, names):
    path = tmp_path / "voices.bin"
    with path.open("wb") as handle:
        np.savez(handle, **{n: np.zeros(1) for n in names})
    monkeypatch.setattr(model, "find", lambda: (tmp_path / "m.onnx", path))


def test_extra_voice_files_are_listed_and_resolved(tmp_path, monkeypatch):
    _fake_installed_voices(tmp_path, monkeypatch, ["af_heart"])
    folder = voices.extras_dir()
    folder.mkdir(parents=True)
    style = np.ones((510, 1, 256), dtype="float32")
    np.save(folder / "my_voice.npy", style)
    assert voices.available() == ["af_heart", "my_voice"]
    assert voices.resolve("af_heart") == "af_heart"
    resolved = voices.resolve("my_voice")
    assert isinstance(resolved, np.ndarray) and resolved.shape == (510, 1, 256)


def test_extra_voice_language_defaults_to_us_english(tmp_path, monkeypatch):
    _fake_installed_voices(tmp_path, monkeypatch, ["af_heart"])
    assert voices.language("my_voice") == "en-us"
    assert voices.language("ef_custom") == "es"


@pytest.mark.parametrize("code", ["de", "pl", "ru"])
def test_the_languages_without_native_voices_are_still_accepted(code):
    assert languages.check(code)
