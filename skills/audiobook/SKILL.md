---
name: audiobook
description: Turn a text or markdown file into an audiobook (one WAV per chapter, optionally one m4b/mp3) with the local Kokoro voices from claudio-tts. Use when the user asks to make an audiobook, read a document or book aloud into audio files, or convert text to audio. Runs entirely on the user's machine.
---

# Audiobook from a text file

Requires claudio-tts installed (`claudio-tts doctor` should pass, model downloaded).

1. Confirm the file path with the user if it is not clear. Never guess between several files.
2. For anything larger than a few pages, preview first:
   `claudio-tts audiobook "<file>" --dry-run`
   Show the chapter list and the estimated length, and let the user adjust (voice, speed) before a long run.
3. Run it:
   `claudio-tts audiobook "<file>" [-o "<folder>"] [--voice af_heart] [--speed 1.0] [--format wav|m4b|mp3]`
   - Default output is a folder `<file>-audiobook` next to the file with `NN-title.wav` per chapter.
   - `m4b` (with chapter marks) and `mp3` need `ffmpeg`. If it is missing the WAVs are kept and a hint is printed;
     tell the user (macOS: `brew install ffmpeg`), do not install it yourself.
   - Long books take a while. If interrupted, run the same command again: finished chapters are skipped
     (`--force` redoes them). Run it in the background for large files.
4. Report the output path printed on the last line. Voices: `claudio-tts voices`; other languages: `--lang de`.

Output stays on the machine. Never upload, share or publish the audio unless the user asks.
