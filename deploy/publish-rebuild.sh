#!/usr/bin/env bash
# publish-rebuild.sh — publish approved content to the DB, then rebuild the static site.
#
#   publish  : renders approved blog/newsletter/episodes into the DB + pushes newsletter campaigns
#   rebuild  : regenerates web/dist from the DB (Astro); nginx serves it live, no restart needed
#
# One-off jobs run as ephemeral Swarm services because BoosterBot_Network is not attachable.
# Usage:  bash deploy/publish-rebuild.sh            (publish + rebuild)
#         bash deploy/publish-rebuild.sh rebuild    (rebuild only)
#         bash deploy/publish-rebuild.sh publish    (publish only)
# NOTE: no `set -e` — the swarm_run helper intentionally runs commands that may return
# non-zero (e.g. removing a not-yet-existing service); it reports failures via its return code,
# which we check explicitly below.
set -uo pipefail
REPO=/root/vaccaricode_podcast
cd "$REPO"
source deploy/swarm-run.sh

STEP="${1:-all}"
IMG=boosternews/pipeline:local

do_publish() {
  echo "==> publish --all"
  swarm_run bn-publish -- --env-file "$REPO/.env" "$IMG" python -m boosternews publish --all
}

do_rebuild() {
  echo "==> rebuild static site (Astro -> web/dist)"
  swarm_run bn-webbuild -- \
    --env-file "$REPO/.env" \
    --mount type=bind,src="$REPO/web",dst=/web \
    --workdir /web \
    node:22-alpine sh -c "npm install --no-audit --no-fund && npm run build"
}

case "$STEP" in
  publish) do_publish ;;
  rebuild) do_rebuild ;;
  all)     do_publish || { echo "publish failed — skipping rebuild" >&2; exit 1; }; do_rebuild ;;
  *) echo "usage: $0 [all|publish|rebuild]" >&2; exit 2 ;;
esac
rc=$?
[ $rc -eq 0 ] && echo "==> done ($STEP). Live at https://tiagovaccari.com" || echo "==> FAILED ($STEP), exit $rc" >&2
exit $rc
