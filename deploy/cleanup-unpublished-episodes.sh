#!/usr/bin/env bash
# Delete every UNPUBLISHED podcast episode on the VPS, the same way the dashboard's "delete" does:
# the episode row, its paired podcast draft, its narration jobs (cascade) and its audio objects
# (podcast/<id>.mp3, narration/<id>/raw.wav), then one site rebuild.
#
#   bash deploy/cleanup-unpublished-episodes.sh                      # dry run: list, change nothing
#   bash deploy/cleanup-unpublished-episodes.sh --yes                # full DB backup to /root, then delete
#   bash deploy/cleanup-unpublished-episodes.sh --include-approved [--yes]
#
# Kept: every episode with status 'published'; any episode whose podcast draft is 'published' (a live
# episode in the middle of a re-narration is briefly 'script_ready'); and, unless --include-approved,
# any episode whose podcast draft is 'approved' (approved and waiting for the publish job).
# Topics, blog posts, newsletters and subscribers are not touched.
set -uo pipefail
YES=0; KEEP="'published', 'approved'"
for a in "$@"; do
  case "$a" in
    --yes) YES=1 ;;
    --include-approved) KEEP="'published'" ;;
    *) echo "unknown option: $a"; exit 2 ;;
  esac
done
DC=$(docker ps -q -f name=boosternews_dashboard | head -1)
PGC=$(docker ps -q -f name=postgres_postgres | head -1)
[ -n "$DC" ] || { echo "FAIL: boosternews_dashboard container not running"; exit 1; }
[ -n "$PGC" ] || { echo "FAIL: postgres_postgres container not running"; exit 1; }
psqlc() { docker exec "$PGC" psql -U postgres -d boosternews "$@"; }

TARGETS="SELECT e.id FROM episodes e WHERE e.status <> 'published' AND NOT EXISTS (
  SELECT 1 FROM drafts d WHERE d.topic_id = e.topic_id AND d.language = e.language
  AND d.channel = 'podcast' AND d.status IN ($KEEP))"

echo "==> unpublished episodes"
psqlc -c "SELECT left(e.id::text,8) AS id, e.language AS lang, e.status, d.status AS draft,
  (e.audio_url IS NOT NULL) AS audio, e.updated_at::date AS updated, left(e.title,55) AS title
  FROM episodes e LEFT JOIN drafts d ON d.topic_id = e.topic_id AND d.language = e.language
  AND d.channel = 'podcast' WHERE e.id IN ($TARGETS) ORDER BY e.updated_at"
n=$(psqlc -tAc "SELECT count(*) FROM ($TARGETS) x")
kept=$(psqlc -tAc "SELECT count(*) FROM episodes WHERE id NOT IN ($TARGETS)")
echo "==> $n episode(s) would be deleted; $kept episode(s) kept (podcast draft in: $KEEP)."
[ "$YES" = 1 ] || { echo "Dry run, nothing changed. Re-run with --yes to delete."; exit 0; }
[ "$n" -gt 0 ] || { echo "Nothing to delete."; exit 0; }

ts=$(date +%Y%m%d-%H%M%S)
bk=/root/boosternews-before-episode-cleanup-$ts.dump
echo "==> backup"
docker exec "$PGC" pg_dump -U postgres -Fc boosternews > "$bk"
[ -s "$bk" ] || { echo "FAIL: backup is empty — nothing deleted"; rm -f "$bk"; exit 1; }
echo "    $bk ($(du -h "$bk" | cut -f1)). Restore: docker exec -i $PGC pg_restore -U postgres -d boosternews --clean < $bk"

echo "==> delete"
docker exec -i "$DC" python - <<PY
from boosternews import repository as repo, storage
from boosternews.db import get_conn

with get_conn() as conn:
    with conn.cursor() as cur:
        cur.execute("""$TARGETS""")
        ids = [str(r[0]) for r in cur.fetchall()]
    keys = []
    for i in ids:
        keys += repo.delete_episode(conn, i)
    repo.request_site_rebuild(conn)
    conn.commit()
print(f"    deleted {len(ids)} episode(s) and their podcast drafts / narration jobs")
for k in keys:
    storage.delete_object(k)  # ignores missing objects
print(f"    purged {len(keys)} audio object key(s)")
PY
rc=$?
[ $rc -eq 0 ] || { echo "FAIL: delete step exited $rc — DB changes roll back on error; backup: $bk"; exit 1; }
left=$(psqlc -tAc "SELECT count(*) FROM ($TARGETS) x")
echo "==> done. Unpublished episodes left: $left. Published kept: $(psqlc -tAc "SELECT count(*) FROM episodes WHERE status='published'")."
echo "    The site rebuild runs within ~1 min (rebuild-watch)."
