// Shared RSS / iTunes podcast feed builders, per language.
import matter from "gray-matter";
import { getPublishedEpisodes, getPublishedPosts } from "./db.js";
import { STRINGS } from "./i18n.js";

const esc = (s) =>
  String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function siteBase(lang, siteUrl) {
  const root = (siteUrl || "http://localhost/").toString().replace(/\/$/, "");
  return root + STRINGS[lang].base; // "" for pt-BR, "/en" for en
}

export async function blogRss(lang, siteUrl) {
  const base = siteBase(lang, siteUrl);
  const posts = await getPublishedPosts(lang);
  const items = posts
    .map((p) => {
      const link = `${base}/blog/${p.topic_id}`;
      const { content } = matter(p.body);
      const desc = content.replace(/[#*`>]/g, "").trim().slice(0, 300);
      return `<item><title>${esc(p.title)}</title><link>${link}</link><guid>${link}</guid><pubDate>${new Date(p.updated_at).toUTCString()}</pubDate><description>${esc(desc)}</description></item>`;
    })
    .join("");
  const langLabel = lang === "en" ? " (EN)" : "";
  return `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Vaccari's Code Podcast${langLabel}</title><link>${base}/</link><description>${lang === "en" ? "Automated trends in software development and AI." : "Tendências automatizadas em desenvolvimento de software e IA."}</description>${items}</channel></rss>`;
}

export async function podcastFeed(lang, siteUrl) {
  const base = siteBase(lang, siteUrl);
  const episodes = await getPublishedEpisodes(lang, { withAudioOnly: true });
  const items = episodes
    .map((e) => {
      const link = `${base}/podcast/${e.topic_id}`;
      const enclosure = `<enclosure url="${esc(e.audio_url)}" type="audio/mpeg" length="${e.file_size_bytes || 0}" />`;
      const duration = e.duration_seconds ? `<itunes:duration>${e.duration_seconds}</itunes:duration>` : "";
      return `<item><title>${esc(e.title)}</title><link>${link}</link><guid>${link}</guid><pubDate>${new Date(e.updated_at).toUTCString()}</pubDate><description>${esc(e.show_notes)}</description>${enclosure}${duration}</item>`;
    })
    .join("");
  const langLabel = lang === "en" ? " (EN)" : "";
  return `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><channel><title>Vaccari's Code Podcast${langLabel}</title><link>${base}/</link><description>${lang === "en" ? "Narrated trends in software development and AI." : "Tendências narradas em desenvolvimento de software e IA."}</description><language>${lang}</language><itunes:author>Tiago Vaccari</itunes:author>${items}</channel></rss>`;
}
