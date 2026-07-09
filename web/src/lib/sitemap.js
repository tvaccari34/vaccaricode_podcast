// Build-time sitemap for the static site. Regenerated on every `astro build`
// (i.e. every rebuild), so newly published posts/episodes appear automatically
// with no separate cron — the same way the RSS/podcast feeds work.
//
// Each page that exists in both locales carries reciprocal, self-referential
// hreflang alternates (PT ⇄ EN + x-default → PT) per Google's guidelines;
// content that exists in only one language gets no alternates.
import { getPublishedEpisodes, getPublishedPosts } from "./db.js";
import { STRINGS } from "./i18n.js";
import { canonicalUrl } from "./seo.js";

const LANGS = ["pt-BR", "en"];
const DEFAULT_LANG = "pt-BR"; // x-default target

const esc = (s) =>
  String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function rootUrl(siteUrl) {
  return (siteUrl || "http://localhost/").toString().replace(/\/$/, "");
}

function newest(...dates) {
  const ts = dates.filter(Boolean).map((d) => new Date(d).getTime());
  return ts.length ? new Date(Math.max(...ts)) : undefined;
}

/**
 * Emit one <url> per language for a logical page.
 * @param {Object<string,{href:string, lastmod?:*}>} perLang - lang → { href, lastmod }
 * When more than one language is present, every emitted <url> gets the same set
 * of alternate links (reciprocal + self-referential) plus an x-default.
 */
function pageEntries(perLang) {
  const langs = Object.keys(perLang);
  let alts = "";
  if (langs.length > 1) {
    const links = langs.map(
      (l) => `<xhtml:link rel="alternate" hreflang="${STRINGS[l].htmlLang}" href="${esc(perLang[l].href)}"/>`
    );
    const def = perLang[DEFAULT_LANG] || perLang[langs[0]];
    links.push(`<xhtml:link rel="alternate" hreflang="x-default" href="${esc(def.href)}"/>`);
    alts = links.join("");
  }
  return langs.map((l) => {
    const { href, lastmod } = perLang[l];
    const mod = lastmod ? `<lastmod>${new Date(lastmod).toISOString()}</lastmod>` : "";
    return `<url><loc>${esc(href)}</loc>${mod}${alts}</url>`;
  });
}

/**
 * Full sitemap covering both locales (PT at the root, EN under /en): the static
 * pages plus every published blog post and podcast episode. Mirrors the routes
 * built by the [id] pages, so the sitemap can't list URLs that don't exist.
 */
export async function sitemapXml(siteUrl) {
  const root = rootUrl(siteUrl);
  const base = Object.fromEntries(LANGS.map((l) => [l, root + STRINGS[l].base])); // "" / "/en"

  // Fetch both locales up front so we can pair alternates by topic_id.
  const posts = Object.fromEntries(await Promise.all(LANGS.map(async (l) => [l, await getPublishedPosts(l)])));
  const episodes = Object.fromEntries(await Promise.all(LANGS.map(async (l) => [l, await getPublishedEpisodes(l)])));

  const entries = [];

  // ---- static pages (always exist in both locales) ----
  // canonicalUrl() drops trailing slashes (except root) so these match the
  // <link rel="canonical"> / hreflang tags emitted by Base.astro.
  const staticPage = (suffix, lastmodByLang = {}) =>
    pageEntries(
      Object.fromEntries(LANGS.map((l) => [l, { href: canonicalUrl(base[l] + suffix, siteUrl), lastmod: lastmodByLang[l] }]))
    );

  const newestPost = Object.fromEntries(LANGS.map((l) => [l, posts[l][0]?.updated_at]));
  const newestEp = Object.fromEntries(LANGS.map((l) => [l, episodes[l][0]?.updated_at]));
  const newestAny = Object.fromEntries(LANGS.map((l) => [l, newest(newestPost[l], newestEp[l])]));

  entries.push(...staticPage("/", newestAny));
  entries.push(...staticPage("/blog", newestPost));
  entries.push(...staticPage("/podcast", newestEp));
  entries.push(...staticPage("/about"));
  entries.push(...staticPage("/subscribe"));

  // ---- content pages, paired across locales by topic_id ----
  const contentEntries = (rows, seg) => {
    const byId = Object.fromEntries(LANGS.map((l) => [l, new Map(rows[l].map((r) => [r.topic_id, r]))]));
    for (const [l, other] of [["pt-BR", "en"], ["en", "pt-BR"]]) {
      for (const r of rows[l]) {
        // A row whose id also exists in the other locale is emitted only once,
        // as part of the primary (pt-BR) pass, with both alternates.
        if (l !== DEFAULT_LANG && byId[other].has(r.topic_id)) continue;
        const perLang = { [l]: { href: canonicalUrl(`${base[l]}/${seg}/${r.topic_id}`, siteUrl), lastmod: r.updated_at } };
        const twin = byId[other].get(r.topic_id);
        if (twin) perLang[other] = { href: canonicalUrl(`${base[other]}/${seg}/${r.topic_id}`, siteUrl), lastmod: twin.updated_at };
        entries.push(...pageEntries(perLang));
      }
    }
  };
  contentEntries(posts, "blog");
  contentEntries(episodes, "podcast");

  return (
    `<?xml version="1.0" encoding="UTF-8"?>` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"` +
    ` xmlns:xhtml="http://www.w3.org/1999/xhtml">` +
    entries.join("") +
    `</urlset>`
  );
}
