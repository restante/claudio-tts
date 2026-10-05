# Windows (beta)

claudio-tts runs on Windows 10 and 11, but it has so far been verified only by automated tests on Windows runners,
not on real audio hardware. If something is off, please open an issue with the output of `doctor`.

## Install

```powershell
irm https://raw.githubusercontent.com/restante/claudio-tts/main/install.ps1 | iex
```

If PowerShell blocks the script, allow it for this session: `Set-ExecutionPolicy -Scope Process Bypass`.

## What differs from macOS

- No music ducking yet (Apple Music / Spotify ducking is macOS only).
- Data lives in `%LOCALAPPDATA%\claudio-tts`.
- Device names come from Windows (for example `Speakers (Realtek(R) Audio)`); `/tts device` shows the exact list.
- Bluetooth headsets that switch to "hands-free" mode can sound narrower while another app uses their microphone.

## Reporting a problem

Run `& "$env:LOCALAPPDATA\claudio-tts\venv\Scripts\python.exe" -m claudio_tts doctor --speak` and attach the output.
