-- 0005_site_build_requests.sql
-- On-demand site rebuild queue. The dashboard's management actions (and the "Rebuild now" button)
-- insert a request; a 1-minute host watcher (deploy/rebuild-watch.sh) consumes pending requests and
-- runs the Astro rebuild, so unpublish/delete/edit/publish reflect on the live site within ~1 min.

CREATE TABLE IF NOT EXISTS site_build_requests (
  id           bigserial PRIMARY KEY,
  requested_at timestamptz NOT NULL DEFAULT now(),
  consumed_at  timestamptz
);
CREATE INDEX IF NOT EXISTS idx_site_build_requests_pending
  ON site_build_requests (id) WHERE consumed_at IS NULL;
