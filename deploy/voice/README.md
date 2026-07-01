# Voice reference sample

Place the owner's cloned-voice reference here as **`reference.wav`** (git-ignored). The home
sound-worker mounts this read-only and uses it for XTTS-v2 zero-shot voice cloning.

## How to record it

- **Length:** ~30–90 seconds of clean speech is plenty for zero-shot cloning.
- **Content:** read naturally in the language you'll narrate in (English by default).
- **Quality:** quiet room, consistent distance from the mic, no music/background noise.
- **Format:** mono WAV, 22.05 kHz or 24 kHz. Convert anything with:
  ```bash
  ffmpeg -i raw.m4a -ac 1 -ar 22050 reference.wav
  ```

Then start the worker on the GPU machine (see `sound-worker/README.md`). The reference sample and
the model stay on the home machine — they are never uploaded to the VPS.
