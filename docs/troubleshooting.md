# Troubleshooting

Start with `claudio-tts doctor --speak` (use the full path printed by the installer if it is not on your PATH).

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No sound at all | New sessions start muted | `/tts unmute`, or `/tts default on` for new sessions |
| `/tts` command not found | Claude Code was open during install | Restart Claude Code |
| Sound on the wrong device | The saved device name does not match | `/tts device` to list, then `/tts device <part of name>`. An unmatched name falls back to the default output |
| Speech cuts out between sessions | You have two sessions speaking | They take turns by design; mute the one you are not watching |
| Music stays quiet after speech | Rare: the ducking state file is stale | Delete `duck.json` in the `state` folder of the data dir and set the music volume once |
| `model … failed its checksum` | Interrupted or corrupted download | Re-run the installer; it re-downloads |
| Very slow first sentence | First load of the model | Use `--lite` for a smaller model; later replies are faster |
| `unknown voice` / `unknown language` | Typo in the name or code | `/tts voice` and `/tts lang` list the valid ones; the message suggests close matches. See [voices.md](voices.md) |
| Foreign text sounds accented | The voice has no native voice for that language | Expected; use a native voice if one exists, or `/tts lang auto` for text in the voice's own language |
| `doctor` says audio backend failed | PortAudio missing (Linux) | Install `libportaudio2` |

Worker errors are written to `worker.log` in the `state` folder of the data dir.

Data dir: macOS `~/Library/Application Support/claudio-tts`, Windows `%LOCALAPPDATA%\claudio-tts`,
Linux `~/.local/share/claudio-tts`.

## Updating

- `/tts update check` says whether a newer release exists; `/tts update` installs it, then restart open Claude sessions.
- "uv was not found": re-run the installer from the README, it updates in place.
- Don't want the daily check at session start: `/tts update off`.
- Windows: the updater stops speech workers first, because a running worker locks files. If it still fails, close Claude sessions and re-run the installer.
