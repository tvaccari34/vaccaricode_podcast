// Build-time sitemap for the static site. Regenerated on every `astro build`
// (i.e. every rebuild), so newly published posts/episodes appear automatically
// with no separate cron — the same way the RSS/podcast feeds work.
import { getPublishedEpisodes, getPublishedPosts } from "./db.js";
import { STRINGS } from "./i18n.js";

const LANGS = ["pt-BR", "en"];

const esc = (s) =>
  String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function rootUrl(siteUrl) {
  return (siteUrl || "http://localhost/").toString().replace(/\/$/, "");
}

// One <url> entry. lastmod (W3C / ISO 8601) is omitted when we have no date.
function urlEntry(loc, lastmod) {
  const mod = lastmod ? `<lastmod>${new Date(lastmod).toISOString()}</lastmod>` : "";
  return `<url><loc>${esc(loc)}</loc>${mod}</url>`;
}

function newest(...dates) {
  const ts = dates.filter(Boolean).map((d) => new Date(d).getTime());
  return ts.length ? new Date(Math.max(...ts)) : undefined;
}

/**
 * Full sitemap covering both locales (PT at the root, EN under /en): the static
 * pages plus every published blog post and podcast episode. Mirrors the routes
 * built by the [id] pages, so the sitemap can't list URLs that don't exist.
 */
export async function sitemapXml(siteUrl) {
  const root = rootUrl(siteUrl);
  const entries = [];
  for (const lang of LANGS) {
    const base = root + STRINGS[lang].base; // "" for pt-BR, "/en" for en
    // Both arrive sorted updated_at DESC, so [0] is the freshest.
    const posts = await getPublishedPosts(lang);
    const episodes = await getPublishedEpisodes(lang);
    const newestPost = posts[0]?.updated_at;
    const newestEpisode = episodes[0]?.updated_at;

    // Static pages — listing pages carry their freshest child's date.
    entries.push(urlEntry(`${base}/`, newest(newestPost, newestEpisode)));
    entries.push(urlEntry(`${base}/blog`, newestPost));
    entries.push(urlEntry(`${base}/podcast`, newestEpisode));
    entries.push(urlEntry(`${base}/about`));
    entries.push(urlEntry(`${base}/subscribe`));

    // Per-post and per-episode pages.
    for (const p of posts) entries.push(urlEntry(`${base}/blog/${p.topic_id}`, p.updated_at));
    for (const e of episodes) entries.push(urlEntry(`${base}/podcast/${e.topic_id}`, e.updated_at));
  }
  return (
    `<?xml version="1.0" encoding="UTF-8"?>` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">` +
    entries.join("") +
    `</urlset>`
  );
}
