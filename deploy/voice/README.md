# Voice reference sample

Place the owner's cloned-voice reference here as **`reference_pt.wav`** (and optionally
**`reference_en.wav`**) — git-ignored. It is the source for the cloned voice:

- **VoiceStudio** (default engine): you upload it once in the VoiceStudio UI to create a voice
  profile (below). The worker then only references the profile id.
- **F5 / XTTS** (fallback engines): the home sound-worker mounts this folder read-only and clones
  zero-shot from the file on every job.

## How to record it

- **Length:** ~30–90 seconds of clean speech is plenty for zero-shot cloning (F5 trims to ~12 s).
- **Content:** read naturally in the language you'll narrate in.
- **Quality:** quiet room, consistent distance from the mic, no music/background noise.
- **Format:** mono WAV, 22.05 kHz or 24 kHz. Convert anything with:
  ```bash
  ffmpeg -i raw.m4a -ac 1 -ar 24000 reference_pt.wav
  ```

## Create the VoiceStudio voice profile(s) (one-time)

1. Start VoiceStudio and wait until it's healthy (~10 s; no weights are downloaded yet):
   ```bash
   docker compose --env-file .env -f deploy/compose.home.yml up -d voicestudio
   docker compose --env-file .env -f deploy/compose.home.yml ps voicestudio   # → (healthy)
   ```
2. Open **http://127.0.0.1:3900** (loopback only) and sign in with `OMNIVOICE_API_KEY`.
3. In **Settings → Models**, accept the **OmniVoice** licence and download it (~2.4 GB). Note the
   weights are **CC-BY-NC — non-commercial only** (see DEPLOY.md → Licensing). Then install the
   **Balanced** pack: it adds Whisper large-v3 Turbo, which transcribes the reference clip when a
   profile is saved. (The pack tier only sets UI defaults; the worker sends its own
   `VOICESTUDIO_NUM_STEP`.)
4. Create a **voice clone** profile and confirm the consent prompt (it's your own voice). The clip
   must be **≤ 75 s** (VoiceStudio rejects longer clips without a transcript). Trim a long take at
   a pause, e.g. `ffmpeg -ss 1.4 -to 62.6 -i reference_pt.wav -ac 1 reference_pt_61s.wav`.
   Set the profile's **language** (Portuguese / English) — not Auto. An English profile is
   optional: the pt-BR profile narrated English just as well in A/B tests.
5. Copy the profile id(s) into the home `.env`. They are listed (`"type": "profile"`) by:
   ```bash
   curl -s http://127.0.0.1:3900/v1/audio/voices -H "Authorization: Bearer $OMNIVOICE_API_KEY"
   ```
   ```ini
   VOICESTUDIO_VOICE=<pt-BR profile voice_id>
   VOICESTUDIO_VOICE_EN=<english profile voice_id, optional>
   ```
6. Start the worker: `docker compose --env-file .env -f deploy/compose.home.yml up -d`.

The reference samples, VoiceStudio profiles and models stay on the home machine — they are never
uploaded to the VPS.
