#!/usr/bin/env bash
# On-demand site rebuild watcher. Runs every minute via cron. Consumes pending rows in
# site_build_requests (queued by the dashboard's management actions and the "Rebuild now" button)
# and rebuilds the static site if any were pending. Lightweight when idle (one psql exec).
set -uo pipefail
REPO=/root/vaccaricode_podcast
PGC=$(docker ps -q -f name=postgres_postgres | head -1)
[ -z "$PGC" ] && exit 0
pending=$(docker exec "$PGC" psql -U postgres -d boosternews -tAc \
  "UPDATE site_build_requests SET consumed_at = now() WHERE consumed_at IS NULL RETURNING 1;" \
  2>/dev/null | grep -c 1)
if [ "${pending:-0}" -gt 0 ]; then
  echo "$(date -u +%FT%TZ) rebuild-watch: ${pending} request(s) pending -> rebuilding"
  bash "$REPO/deploy/publish-rebuild.sh" rebuild
fi
