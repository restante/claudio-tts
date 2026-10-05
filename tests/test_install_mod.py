import json
import os

import pytest

from claudio_tts import install_mod


@pytest.fixture
def mod(tmp_path):
    src = tmp_path / "modsrc"
    (src / "hooks").mkdir(parents=True)
    (src / "hooks" / "hooks.json").write_text("{}")
    return src


def _settings(claude):
    return json.loads((claude / "settings.json").read_text())


def test_install_copies_mod_and_registers_it(tmp_path, mod):
    claude = tmp_path / "claude"
    result = install_mod.install("/py", claude_dir=claude, source=mod)
    assert result["changed"] is True
    assert (claude / "mods" / "claudio-tts" / "hooks" / "hooks.json").exists()
    env = _settings(claude)["env"]
    assert env["CLAUDE_CODE_PLUGIN_DIRS"] == str(claude / "mods" / "claudio-tts")
    assert env["CLAUDIO_TTS_PYTHON"] == "/py"


def test_install_is_idempotent_and_keeps_other_settings(tmp_path, mod):
    claude = tmp_path / "claude"
    claude.mkdir()
    (claude / "settings.json").write_text(
        json.dumps({"theme": "dark", "env": {"CLAUDE_CODE_PLUGIN_DIRS": "/other/plugin", "A": "1"}})
    )
    install_mod.install("/py", claude_dir=claude, source=mod)
    first = (claude / "settings.json").read_text()
    again = install_mod.install("/py", claude_dir=claude, source=mod)
    assert again["changed"] is False
    assert (claude / "settings.json").read_text() == first
    data = _settings(claude)
    assert data["theme"] == "dark" and data["env"]["A"] == "1"
    dirs = data["env"]["CLAUDE_CODE_PLUGIN_DIRS"].split(os.pathsep)
    assert dirs == ["/other/plugin", str(claude / "mods" / "claudio-tts")]


def test_install_removes_the_legacy_kokoro_entry(tmp_path, mod):
    claude = tmp_path / "claude"
    claude.mkdir()
    legacy = str(claude / "mods" / "kokoro-tts")
    (claude / "settings.json").write_text(json.dumps({"env": {"CLAUDE_CODE_PLUGIN_DIRS": legacy}}))
    install_mod.install("/py", claude_dir=claude, source=mod)
    dirs = _settings(claude)["env"]["CLAUDE_CODE_PLUGIN_DIRS"].split(os.pathsep)
    assert legacy not in dirs


def test_backup_is_made_once(tmp_path, mod):
    claude = tmp_path / "claude"
    claude.mkdir()
    (claude / "settings.json").write_text('{"x": 1}')
    install_mod.install("/py", claude_dir=claude, source=mod)
    backup = claude / "settings.json.claudio-tts.bak"
    assert backup.read_text() == '{"x": 1}'
    install_mod.install("/py2", claude_dir=claude, source=mod)
    assert backup.read_text() == '{"x": 1}'


def test_invalid_settings_json_is_refused_untouched(tmp_path, mod):
    claude = tmp_path / "claude"
    claude.mkdir()
    (claude / "settings.json").write_text("{not json")
    with pytest.raises(install_mod.SettingsError):
        install_mod.install("/py", claude_dir=claude, source=mod)
    assert (claude / "settings.json").read_text() == "{not json"
    assert not (claude / "mods").exists()


def test_uninstall_restores_a_clean_state(tmp_path, mod):
    claude = tmp_path / "claude"
    claude.mkdir()
    (claude / "settings.json").write_text(json.dumps({"theme": "dark"}))
    install_mod.install("/py", claude_dir=claude, source=mod)
    install_mod.uninstall(claude_dir=claude)
    assert _settings(claude) == {"theme": "dark"}
    assert not (claude / "mods" / "claudio-tts").exists()
