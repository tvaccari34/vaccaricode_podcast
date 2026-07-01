-- 0002_topic_base_score.sql
-- Store the pre-corroboration base score per topic so the final score can be recomputed
-- deterministically as sources merge in (see boosternews.scoring).

ALTER TABLE topics ADD COLUMN IF NOT EXISTS base_score double precision NOT NULL DEFAULT 0;
