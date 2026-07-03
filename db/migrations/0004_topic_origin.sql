-- 0004_topic_origin.sql
-- Distinguish manually authored content from pipeline-discovered topics. Manual entries create a
-- synthetic topic (origin='manual') so hand-written posts/episodes flow through the same
-- review/publish/site path, while the automated pipeline (extract/generate/scoring) skips them.
-- Existing rows default to 'auto'.

ALTER TABLE topics ADD COLUMN IF NOT EXISTS origin text NOT NULL DEFAULT 'auto';
