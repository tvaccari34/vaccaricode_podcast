// Build-time data access. The Astro site queries Postgres while building the static pages.
// On the host use localhost; in a container on the compose network use host "postgres".
import pg from "pg";

const connectionString =
  process.env.DATABASE_URL ||
  "postgresql://boosternews:devpassword123@localhost:5432/boosternews";

const pool = new pg.Pool({ connectionString });

/** Published blog posts for a language (markdown body includes frontmatter). */
export async function getPublishedPosts(language = "pt-BR") {
  const { rows } = await pool.query(
    `SELECT topic_id, title, body, updated_at
       FROM drafts
      WHERE channel = 'blog' AND status = 'published' AND language = $1
      ORDER BY updated_at DESC`,
    [language]
  );
  return rows;
}

/** Published podcast episodes for a language. Set withAudioOnly for feeds. */
export async function getPublishedEpisodes(language = "pt-BR", { withAudioOnly = false } = {}) {
  const { rows } = await pool.query(
    `SELECT topic_id, title, show_notes, script, audio_url, duration_seconds,
            file_size_bytes, updated_at
       FROM episodes
      WHERE status = 'published' AND language = $1
        ${withAudioOnly ? "AND audio_url IS NOT NULL" : ""}
      ORDER BY updated_at DESC`,
    [language]
  );
  return rows;
}
