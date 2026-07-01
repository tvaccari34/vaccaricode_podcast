# sound-worker

Runs on the **home computer** (NVIDIA RTX 4060 Ti). It is the only boosternews component that
runs at home. It pulls narration jobs from the VPS, synthesizes speech in Tiago's cloned voice
with **XTTS-v2**, and uploads the audio back — all over **outbound HTTPS**. No inbound ports
are opened; the home network needs no static IP.

## How it connects

```
home worker  ──POST /narration/claim──▶  VPS   (claim next queued job)
             ◀──────── job (text) ──────
             ──POST /narration/{id}/complete (audio) ──▶  VPS
```

If the VPS is unreachable or no jobs are queued, the worker backs off and retries. If the home
PC is asleep, jobs simply wait in the VPS queue.

## Config (home `.env`)

| Var | Meaning |
|-----|---------|
| `VPS_API_URL` | Base URL of the VPS narration API (e.g. `https://tiagovaccari.com/api`) |
| `WORKER_AUTH_TOKEN` | Shared bearer token (must match the VPS) |
| `VOICE_ID` | Cloned voice id (default `tiago`) |
| `REFERENCE_SAMPLE_PATH` | Path to the private voice reference WAV (mounted into the container) |

## Run

```bash
cd deploy
docker compose -f compose.home.yml up -d
docker compose -f compose.home.yml logs -f sound-worker
```

## Status

Implemented: the job-lifecycle loop, the HTTP contract, and **XTTS-v2 synthesis**
(`synthesize()` in `worker.py` — zero-shot voice cloning from `reference.wav`). The matching
VPS-side narration API (`boosternews.narration.app`) assembles + stores the episode audio. Place
the voice sample per `deploy/voice/README.md`, then run on the GPU host.

The VPS-side path (claim → assemble → store → update episode) is verified; only the GPU synthesis
itself requires the home machine (NVIDIA Container Toolkit + the model download on first run).
