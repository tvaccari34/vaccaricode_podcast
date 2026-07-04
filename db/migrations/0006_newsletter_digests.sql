-- 0006_newsletter_digests.sql
-- Weekly newsletter digest bookkeeping. Each row records one digest campaign for a language and the
-- time window it covered, so posts are never included twice and empty weeks are skipped.

CREATE TABLE IF NOT EXISTS newsletter_digests (
  id           bigserial PRIMARY KEY,
  language     text NOT NULL,
  campaign_id  integer,
  item_count   integer NOT NULL DEFAULT 0,
  window_start timestamptz,
  window_end   timestamptz NOT NULL DEFAULT now(),
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_newsletter_digests_lang ON newsletter_digests (language, window_end DESC);
