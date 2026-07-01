-- 0001_init.sql — initial schema for boosternews.
-- Idempotent-friendly where practical; applied once by the migration runner.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()

-- Shared updated_at trigger -------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Enums ---------------------------------------------------------------------
CREATE TYPE channel          AS ENUM ('blog', 'podcast', 'newsletter');
CREATE TYPE topic_status     AS ENUM ('new', 'selected', 'generating', 'drafted', 'rejected', 'published');
CREATE TYPE draft_status     AS ENUM ('pending_review', 'approved', 'rejected', 'needs_edit', 'published');
CREATE TYPE episode_status   AS ENUM ('script_ready', 'narrating', 'assembling', 'ready', 'approved', 'published', 'failed');
CREATE TYPE review_decision  AS ENUM ('approve', 'reject', 'request_edit');
CREATE TYPE narration_status AS ENUM ('queued', 'claimed', 'completed', 'failed');

-- sources: configured feeds / APIs and their cadence ------------------------
CREATE TABLE sources (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                   text NOT NULL,
  kind                   text NOT NULL,                       -- rss | hackernews | github_trending | ...
  url                    text,
  config                 jsonb NOT NULL DEFAULT '{}'::jsonb,
  enabled                boolean NOT NULL DEFAULT true,
  fetch_interval_minutes integer NOT NULL DEFAULT 60,
  last_fetched_at        timestamptz,
  created_at             timestamptz NOT NULL DEFAULT now(),
  updated_at             timestamptz NOT NULL DEFAULT now()
);

-- topics: deduped candidate trends ------------------------------------------
CREATE TABLE topics (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title          text NOT NULL,
  summary        text,
  urls           text[] NOT NULL DEFAULT '{}',
  source_ids     uuid[] NOT NULL DEFAULT '{}',
  extracted_text text,
  dedup_key      text UNIQUE,                                 -- merges the same story across sources
  score          double precision NOT NULL DEFAULT 0,
  status         topic_status NOT NULL DEFAULT 'new',
  first_seen_at  timestamptz NOT NULL DEFAULT now(),
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_topics_status_score ON topics (status, score DESC);

-- drafts: generated artifact per topic per channel --------------------------
CREATE TABLE drafts (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id   uuid NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  channel    channel NOT NULL,
  title      text,
  body       text NOT NULL,
  metadata   jsonb NOT NULL DEFAULT '{}'::jsonb,
  status     draft_status NOT NULL DEFAULT 'pending_review',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (topic_id, channel)
);
CREATE INDEX idx_drafts_status ON drafts (status);

-- episodes: podcast episode produced from a topic/script --------------------
CREATE TABLE episodes (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id         uuid NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  draft_id         uuid REFERENCES drafts(id) ON DELETE SET NULL,
  title            text NOT NULL,
  script           text NOT NULL,
  show_notes       text,
  voice_id         text,
  audio_url        text,
  duration_seconds integer,
  file_size_bytes  bigint,
  status           episode_status NOT NULL DEFAULT 'script_ready',
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_episodes_status ON episodes (status);

-- narration_jobs: queue drained by the home GPU sound-worker -----------------
CREATE TABLE narration_jobs (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  episode_id       uuid NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
  voice_id         text NOT NULL,
  text             text NOT NULL,
  status           narration_status NOT NULL DEFAULT 'queued',
  attempts         integer NOT NULL DEFAULT 0,
  max_attempts     integer NOT NULL DEFAULT 3,
  claimed_by       text,
  claimed_at       timestamptz,
  error            text,
  result_audio_key text,                                      -- object-storage key of the raw narration
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);
-- Drives "claim the oldest queued job" for the worker:
CREATE INDEX idx_narration_jobs_queue ON narration_jobs (status, created_at);

-- reviews: per-channel human decisions --------------------------------------
CREATE TABLE reviews (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id   uuid REFERENCES drafts(id) ON DELETE CASCADE,
  episode_id uuid REFERENCES episodes(id) ON DELETE CASCADE,
  channel    channel NOT NULL,
  decision   review_decision NOT NULL,
  reviewer   text NOT NULL,
  notes      text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (draft_id IS NOT NULL OR episode_id IS NOT NULL)
);
CREATE INDEX idx_reviews_draft   ON reviews (draft_id);
CREATE INDEX idx_reviews_episode ON reviews (episode_id);

-- publications: what was published where, and when --------------------------
CREATE TABLE publications (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id     uuid REFERENCES topics(id) ON DELETE SET NULL,
  channel      channel NOT NULL,
  ref_id       uuid,                                          -- draft or episode id
  url          text,
  external_id  text,                                          -- e.g. Listmonk campaign id
  published_at timestamptz NOT NULL DEFAULT now(),
  metadata     jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX idx_publications_topic ON publications (topic_id);

-- updated_at triggers -------------------------------------------------------
CREATE TRIGGER trg_sources_updated        BEFORE UPDATE ON sources        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_topics_updated         BEFORE UPDATE ON topics         FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_drafts_updated         BEFORE UPDATE ON drafts         FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_episodes_updated       BEFORE UPDATE ON episodes       FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_narration_jobs_updated BEFORE UPDATE ON narration_jobs FOR EACH ROW EXECUTE FUNCTION set_updated_at();
