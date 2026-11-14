#!/usr/bin/env bash
# VPS side of the VoiceStudio narration cutover (openspec: switch-narration-to-voicestudio).
# Run ON THE SERVER after the feat/voicestudio-narration PR is merged into main:
#
#   bash /root/vaccaricode_podcast/deploy/voicestudio-cutover.sh            # check, fix .env, redeploy
#   bash /root/vaccaricode_podcast/deploy/voicestudio-cutover.sh --check    # preflight only, no changes
#
# What it does:
#   1. preflight: merged code is on origin/main, the checkout is clean, .env exists
#   2. backs up .env, then makes NARRATION_PROVIDER valid for the new code (elevenlabs -> local)
#   3. runs deploy/redeploy.sh (pull, build, migrate, redeploy stack, rebuild site)
#   4. verifies: the new image accepts .env, services converged, the API answers, no startup errors
# Safe to re-run. Full runbook (home PC side, verification, rollback): deploy/VOICESTUDIO_CUTOVER.md
# NOTE: no `set -e` — redeploy.sh / swarm_run rely on that.
set -uo pipefail
REPO=/root/vaccaricode_podcast
IMG=boosternews/pipeline:local
API_HEALTH=https://tiagovaccari.com/api/health
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

ok()   { echo "    ok: $*"; }
warn() { echo "    WARN: $*"; }
die()  { echo "    FAIL: $*" >&2; exit 1; }

cd "$REPO" || die "no repo at $REPO"

echo "==> [1/4] preflight"
git fetch -q origin main || die "git fetch failed"
git cat-file -e origin/main:sound-worker/src/sound_worker/voicestudio.py 2>/dev/null \
  || die "origin/main has no VoiceStudio code yet — merge the feat/voicestudio-narration PR first"
if git cat-file -e origin/main:pipeline/src/boosternews/tts/elevenlabs.py 2>/dev/null; then
  die "origin/main still has tts/elevenlabs.py — unexpected; is the right PR merged?"
fi
ok "origin/main is $(git rev-parse --short origin/main) and contains the VoiceStudio change"
[ -z "$(git status --porcelain --untracked-files=no)" ] \
  || die "tracked files have local changes (redeploy.sh would refuse to pull): $(git status --short --untracked-files=no | head -3 | tr '\n' ' ')"
ok "checkout is clean (at $(git rev-parse --short HEAD))"
[ -f .env ] || die ".env missing"

current=$(grep -E '^NARRATION_PROVIDER=' .env | tail -1 | cut -d= -f2- | tr -d "\"' \r" | tr '[:upper:]' '[:lower:]')
echo "    NARRATION_PROVIDER in .env: ${current:-<unset, defaults to local>}"
case "$current" in
  ""|local|custom) ok "valid for the new code" ; FIX=0 ;;
  elevenlabs)      warn "elevenlabs is rejected by the new code — will set it to local"; FIX=1 ;;
  *)               die "unknown NARRATION_PROVIDER '$current' — fix .env by hand (local|custom)" ;;
esac
if grep -qE '^ELEVENLABS_' .env; then
  warn "ELEVENLABS_* lines are still in .env — harmless (ignored); delete them once the cutover is confirmed"
fi
if [ "$CHECK_ONLY" = 1 ]; then echo "==> --check: preflight passed, nothing changed"; exit 0; fi

echo "==> [2/4] .env"
backup=".env.bak-voicestudio-$(date +%Y%m%d-%H%M%S)"
cp -p .env "$backup" && ok "backed up to $REPO/$backup"
if [ "$FIX" = 1 ]; then
  sed -i -E 's/^NARRATION_PROVIDER=.*/NARRATION_PROVIDER=local/' .env && ok "NARRATION_PROVIDER=local"
  warn "this VPS was narrating with ElevenLabs — from now on the home PC must be running the VoiceStudio worker"
else
  ok "no .env change needed"
fi

echo "==> [3/4] redeploy"
bash deploy/redeploy.sh || die "redeploy.sh failed — see its output above (rollback: deploy/VOICESTUDIO_CUTOVER.md)"

echo "==> [4/4] verify"
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] && ok "deployed $(git rev-parse --short HEAD)" \
  || warn "HEAD $(git rev-parse --short HEAD) != origin/main $(git rev-parse --short origin/main)"
provider=$(docker run --rm --env-file "$REPO/.env" "$IMG" \
  python -c "from boosternews.config import get_settings; print(get_settings().narration_provider)" 2>&1 | tail -1)
case "$provider" in
  local|custom) ok "new image loads .env (NARRATION_PROVIDER=$provider)" ;;
  *) warn "could not confirm NARRATION_PROVIDER with the new image: $provider" ;;
esac
for s in narration-api scheduler dashboard; do
  reps=$(docker service ls --filter "name=boosternews_$s" --format '{{.Replicas}}' | head -1)
  case "$reps" in
    1/1) ok "boosternews_$s $reps" ;;
    *) warn "boosternews_$s replicas: ${reps:-?} — check: docker service ps boosternews_$s --no-trunc" ;;
  esac
done
code=000
for i in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$API_HEALTH" || true)
  [ "$code" = 200 ] && break
  sleep 3
done
[ "$code" = 200 ] && ok "narration API answers ($API_HEALTH)" || warn "narration API health returned $code"
errs=$(docker service logs --since 10m boosternews_narration-api 2>&1 | grep -E "Traceback|ValidationError|NARRATION_PROVIDER" | tail -5)
[ -z "$errs" ] && ok "no startup errors in narration-api logs" || { warn "narration-api log errors:"; echo "$errs" | sed 's/^/      /'; }

echo "==> VPS done. Next: switch the home PC worker (deploy/VOICESTUDIO_CUTOVER.md, Phase 2)."
