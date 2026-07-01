-- 0003_language_variants.sql
-- Bilingual support: each topic can have content in multiple languages. The primary language
-- (pt-BR) is auto-narrated; secondary languages (en) get a generated script + manually-uploaded
-- audio. Existing rows default to 'pt-BR'.

-- Drafts: blog/newsletter/podcast now vary by language.
ALTER TABLE drafts ADD COLUMN IF NOT EXISTS language text NOT NULL DEFAULT 'pt-BR';
ALTER TABLE drafts DROP CONSTRAINT IF EXISTS drafts_topic_id_channel_key;
CREATE UNIQUE INDEX IF NOT EXISTS drafts_topic_channel_lang ON drafts (topic_id, channel, language);

-- Episodes: one per (topic, language).
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS language text NOT NULL DEFAULT 'pt-BR';
CREATE UNIQUE INDEX IF NOT EXISTS episodes_topic_lang ON episodes (topic_id, language);

-- Publications: track which language was published.
ALTER TABLE publications ADD COLUMN IF NOT EXISTS language text NOT NULL DEFAULT 'pt-BR';
