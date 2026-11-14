# VoiceStudio narration cutover — deploy plan

Moves production narration from F5-TTS (and, if it was ever enabled, ElevenLabs) to the
self-hosted **VoiceStudio** (OmniVoice) on the home GPU. OpenSpec change:
`openspec/changes/switch-narration-to-voicestudio/` (task 6.5).

**Already verified locally (2026-11-13):** VoiceStudio 0.5.7 running healthy on the home PC with
the `tiago-pt` profile (id `612945bd`); A/B listening (32 steps, single profile); a full local
end-to-end run (4 episodes, pt-BR + EN, episode pages and feeds rebuilt with the new audio).

| Phase | Where | Downtime |
|---|---|---|
| 0. Merge the PR | GitHub | none |
| 1. Deploy the pipeline | VPS (`/root/vaccaricode_podcast`) | ~1 min of narration-api restart; the site stays up |
| 2. Switch the home worker | Home PC (`C:\BoosterDigital\projects\boosternews-voicestudio`) | jobs queue while the worker restarts |
| 3. Verify in production | Dashboard + feed | none |
| 4. Wrap up | Repo + VPS `.env` | none |

Order matters: deploy the **VPS first** so jobs carry their `language`. The new worker also falls
back to `LANGUAGE=pt` if it ever talks to an old VPS, so a Portuguese script is never read as
English.

---

## Phase 0 — Merge (GitHub)

1. Open and merge the PR `feat/voicestudio-narration` → `main` in `tvaccari34/vaccaricode_podcast`.
   No DB migrations are included.

## Phase 1 — VPS

```bash
# on the VPS (SSH in as usual)
cd /root/vaccaricode_podcast
git fetch origin main && git show origin/main:deploy/voicestudio-cutover.sh > /tmp/voicestudio-cutover.sh

bash /tmp/voicestudio-cutover.sh --check   # preflight only: merged? clean checkout? valid NARRATION_PROVIDER?
bash /tmp/voicestudio-cutover.sh           # backs up .env, fixes NARRATION_PROVIDER if needed, runs redeploy.sh, verifies
```

(The script is run from `/tmp` because it is only in the repo after the pull; once deployed it
lives at `deploy/voicestudio-cutover.sh`.)

The script:
1. **Preflight:** `origin/main` contains the VoiceStudio code and no `tts/elevenlabs.py`; the
   checkout has no local changes to tracked files; `.env` exists.
2. **`.env`:** copies it to `.env.bak-voicestudio-<timestamp>`. `NARRATION_PROVIDER=elevenlabs`
   would stop the new code at startup, so it is set to `local`. Unset, `local` or `custom` are left
   alone. Leftover `ELEVENLABS_*` lines are ignored by the new code (it only warns).
3. **`deploy/redeploy.sh`:** pull, build `boosternews/pipeline:local`, migrations, `docker stack
   deploy`, force-update `scheduler narration-api dashboard`, rebuild the static site.
4. **Verify:** the new image loads `.env`; the three services are `1/1`;
   `https://tiagovaccari.com/api/health` returns 200; no `Traceback`/`ValidationError` in the
   narration-api logs.

Expected end: `==> VPS done.` The old F5 home worker keeps working against the new VPS (the claim
response only gained a `language` field), so nothing breaks between Phase 1 and Phase 2.

## Phase 2 — Home PC (Git Bash)

The home stack moves from the main checkout (`C:\BoosterDigital\projects\boosternews`, which stays
on `feat/content-strategy` with its uncommitted work, untouched) to the dedicated worktree
`C:\BoosterDigital\projects\boosternews-voicestudio`. The compose project name
(`boosternews-home`) and the `boosternews-home_voicestudio-data` volume are the same, so
VoiceStudio keeps its model, licence acceptance and voice profiles.

```bash
W=/c/BoosterDigital/projects/boosternews-voicestudio
MAIN=/c/BoosterDigital/projects/boosternews
REL=/c/BoosterDigital/projects/boosternews-release

# 1. The merged code
cd $W && git fetch origin && git switch --detach origin/main

# 2. Home .env for the worktree (gitignored): the current home settings + VoiceStudio
cp $MAIN/.env $W/.env
sed -i 's/^TTS_ENGINE=.*/TTS_ENGINE=voicestudio/' $W/.env
grep -qE '^TTS_ENGINE=' $W/.env || echo 'TTS_ENGINE=voicestudio' >> $W/.env
grep -E '^(OMNIVOICE_API_KEY|VOICESTUDIO_VOICE)=' $REL/.env >> $W/.env   # same key the running VoiceStudio uses; profile 612945bd
grep -E '^(TTS_ENGINE|VOICESTUDIO_VOICE|VPS_API_URL)=' $W/.env | sed -E 's#(https?://[^/]+).*#\1/...#'
grep -c '^OMNIVOICE_API_KEY=.\+' $W/.env    # → 1

# 3. Reference WAVs (only used by the f5/xtts fallback; gitignored)
cp $MAIN/deploy/voice/*.wav $W/deploy/voice/

# 4. Restart the home stack from the worktree (rebuilds the worker image with the new code)
cd $W/deploy
docker compose --env-file ../.env -f compose.home.yml up -d --build
docker compose --env-file ../.env -f compose.home.yml ps          # voicestudio (healthy), sound-worker Up
docker compose --env-file ../.env -f compose.home.yml logs -f sound-worker
```

Expected worker log:

```
sound-worker 'home-4060ti' starting; VPS=https://tiagovaccari.com/api engine=voicestudio voice=tiago
VoiceStudio at http://voicestudio:3900 is ready
HTTP Request: POST https://tiagovaccari.com/api/narration/claim "HTTP/1.1 204 No Content"
```

If it says `engine=f5`, `TTS_ENGINE` in `$W/.env` is still `f5`. If it says `not ready; holding
off`, check `docker compose ... logs voicestudio` (the model loads on the first request; `/health`
should already be 200).

## Phase 3 — Verify in production

1. On `https://dashboard.tiagovaccari.com`, pick a published pt-BR episode → **Edit script &
   re-narrate** → save without changes.
2. Watch the home worker log: `claimed job …` then `completed job …` (about 25 s of rendering per
   minute of audio).
3. Within ~1 minute the rebuild cron (`deploy/rebuild-watch.sh`) rebuilds the site. Check the
   episode page plays the new audio and `https://tiagovaccari.com/podcast/feed.xml` shows the new
   `length` and `itunes:duration` for that episode.
4. Optional — English. The dashboard's re-narrate list only shows pt-BR episodes, and English
   episodes are auto-narrated only when `NARRATION_SECONDARY_ENABLED=true` is set in the VPS
   `.env` (then `bash deploy/redeploy.sh`). With it on, the next English episode is narrated by
   the same home worker with the same profile (it reads English well). Leave it off to keep
   uploading English audio by hand.

## Phase 4 — Wrap up

- In the repo: tick task 6.5 in `openspec/changes/switch-narration-to-voicestudio/tasks.md`, then
  `openspec archive switch-narration-to-voicestudio` (merges the specs into `openspec/specs/`),
  and commit.
- On the VPS, after about a week of good episodes: delete the `ELEVENLABS_*` lines from `.env` and
  the `.env.bak-voicestudio-*` backups. Cancel any ElevenLabs plan.
- The OmniVoice weights are **CC-BY-NC (non-commercial)**. Before any commercial use of the
  narration (ads, sponsorships, paid products), switch the engine to VoxCPM2 (Apache-2.0); see
  `deploy/DEPLOY.md` → Licensing.

---

## Rollback

**Home worker only (fastest, no VPS change).** Go back to F5 from the worktree:

```bash
cd /c/BoosterDigital/projects/boosternews-voicestudio/deploy
sed -i 's/^TTS_ENGINE=.*/TTS_ENGINE=f5/' ../.env
docker compose --env-file ../.env -f compose.home.yml up -d sound-worker
```

Or restart the old worker from the main checkout, exactly as before:

```bash
cd /c/BoosterDigital/projects/boosternews/deploy
docker compose --env-file ../.env -f compose.home.yml up -d --build sound-worker
```

(VoiceStudio can stay running; it is only idle GPU memory.)

**VPS.** Revert the merge on GitHub (a "Revert" PR into `main`), then on the server:

```bash
cd /root/vaccaricode_podcast
cp .env.bak-voicestudio-<timestamp> .env    # only if the script changed NARRATION_PROVIDER
bash deploy/redeploy.sh
```

The old VPS code works with both the old and the new home worker.
