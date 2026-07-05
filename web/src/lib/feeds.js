// Shared RSS / iTunes podcast feed builders, per language.
import { safeMatter } from "./frontmatter.js";
import { getPublishedEpisodes, getPublishedPosts } from "./db.js";
import { STRINGS } from "./i18n.js";

const esc = (s) =>
  String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function rootUrl(siteUrl) {
  return (siteUrl || "http://localhost/").toString().replace(/\/$/, "");
}
function siteBase(lang, siteUrl) {
  return rootUrl(siteUrl) + STRINGS[lang].base; // "" for pt-BR, "/en" for en
}

// Podcast channel metadata (Apple Podcasts + PSP-1 requirements).
const OWNER_NAME = "Tiago Vaccari";
// Used by Apple only to verify feed ownership at submission; a role address on the owned domain.
const OWNER_EMAIL = process.env.PUBLIC_PODCAST_OWNER_EMAIL || "podcast@tiagovaccari.com";
const ITUNES_CATEGORY = "Technology";
const COVER_PATH = "/cover-art.png"; // 1536² square brand art in web/public
// Stable per-feed GUID = uuidv5(feed URL w/o scheme) under the Podcast Namespace GUID namespace.
// Must never change even if the feed URL moves, so it is pinned here rather than derived at build.
const PODCAST_GUID = {
  "pt-BR": "df50c829-3b44-5181-a850-973fb67e2190",
  en: "1bad3296-1fea-5eef-8e20-d357226d94c8",
};
const CHANNEL_DESC = {
  "pt-BR":
    "Vaccari's Code é um podcast sobre tendências em tecnologia, programação e Inteligência " +
    "Artificial. Cada episódio traz as histórias mais relevantes do desenvolvimento de software, " +
    "narradas por Tiago Vaccari — engenheiro de software sênior — a partir de fontes reais.",
  en:
    "Vaccari's Code is a podcast on trends in technology, programming, and Artificial " +
    "Intelligence. Each episode covers the most relevant stories in software development, " +
    "narrated by Tiago Vaccari — a senior software engineer — from real sources.",
};

export async function blogRss(lang, siteUrl) {
  const base = siteBase(lang, siteUrl);
  const posts = await getPublishedPosts(lang);
  const items = posts
    .map((p) => {
      const link = `${base}/blog/${p.topic_id}`;
      const { content } = safeMatter(p.body);
      const desc = content.replace(/[#*`>]/g, "").trim().slice(0, 300);
      return `<item><title>${esc(p.title)}</title><link>${link}</link><guid>${link}</guid><pubDate>${new Date(p.updated_at).toUTCString()}</pubDate><description>${esc(desc)}</description></item>`;
    })
    .join("");
  const langLabel = lang === "en" ? " (EN)" : "";
  return `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Vaccari's Code Podcast${langLabel}</title><link>${base}/</link><description>${lang === "en" ? "Automated trends in software development and AI." : "Tendências automatizadas em desenvolvimento de software e IA."}</description>${items}</channel></rss>`;
}

export async function podcastFeed(lang, siteUrl) {
  const base = siteBase(lang, siteUrl);
  const cover = `${rootUrl(siteUrl)}${COVER_PATH}`;
  const feedUrl = `${base}/podcast/feed.xml`;
  const langLabel = lang === "en" ? " (EN)" : "";
  const title = `Vaccari's Code Podcast${langLabel}`;
  const desc = CHANNEL_DESC[lang] || CHANNEL_DESC["pt-BR"];

  const episodes = await getPublishedEpisodes(lang, { withAudioOnly: true });
  const items = episodes
    .map((e) => {
      const link = `${base}/podcast/${e.topic_id}`;
      const enclosure = `<enclosure url="${esc(e.audio_url)}" type="audio/mpeg" length="${e.file_size_bytes || 0}" />`;
      const duration = e.duration_seconds ? `<itunes:duration>${e.duration_seconds}</itunes:duration>` : "";
      return (
        `<item><title>${esc(e.title)}</title><link>${link}</link>` +
        `<guid isPermaLink="true">${link}</guid>` +
        `<pubDate>${new Date(e.updated_at).toUTCString()}</pubDate>` +
        `<description>${esc(e.show_notes)}</description>` +
        `<itunes:summary>${esc(e.show_notes)}</itunes:summary>` +
        `<itunes:image href="${esc(cover)}" />` +
        `<itunes:explicit>false</itunes:explicit>` +
        `${enclosure}${duration}</item>`
      );
    })
    .join("");

  return (
    `<?xml version="1.0" encoding="UTF-8"?>` +
    `<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"` +
    ` xmlns:podcast="https://podcastindex.org/namespace/1.0"` +
    ` xmlns:atom="http://www.w3.org/2005/Atom">` +
    `<channel>` +
    `<title>${title}</title>` +
    `<link>${base}/</link>` +
    `<atom:link href="${esc(feedUrl)}" rel="self" type="application/rss+xml" />` +
    `<description>${esc(desc)}</description>` +
    `<language>${lang}</language>` +
    `<copyright>© ${new Date().getFullYear()} Tiago Vaccari</copyright>` +
    `<itunes:author>${OWNER_NAME}</itunes:author>` +
    `<itunes:summary>${esc(desc)}</itunes:summary>` +
    `<itunes:type>episodic</itunes:type>` +
    `<itunes:explicit>false</itunes:explicit>` +
    `<itunes:category text="${ITUNES_CATEGORY}" />` +
    `<itunes:image href="${esc(cover)}" />` +
    `<itunes:owner><itunes:name>${OWNER_NAME}</itunes:name><itunes:email>${OWNER_EMAIL}</itunes:email></itunes:owner>` +
    `<image><url>${esc(cover)}</url><title>${title}</title><link>${base}/</link></image>` +
    `<podcast:locked owner="${OWNER_EMAIL}">no</podcast:locked>` +
    `<podcast:guid>${PODCAST_GUID[lang] || PODCAST_GUID["pt-BR"]}</podcast:guid>` +
    `${items}</channel></rss>`
  );
}
