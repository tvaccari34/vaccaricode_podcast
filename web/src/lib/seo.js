// Shared SEO helpers + brand constants used by Base.astro (meta tags) and the
// sitemap, so canonical URLs, share images, and author info stay consistent.
import { safeMatter } from "./frontmatter.js";

export const SITE_NAME = "Vaccari's Code";
export const AUTHOR = "Tiago Vaccari";
// Default social-share image (square brand art in web/public). A dedicated
// 1200×630 image would render a touch better on X/Facebook, but square works.
export const DEFAULT_OG_IMAGE = "/cover-art-512.png";
// Open Graph locale codes per site language.
export const OG_LOCALE = { "pt-BR": "pt_BR", en: "en_US" };

/**
 * Absolute canonical URL for a path (or full URL). Directory routes are served
 * as `index.html`, so nginx 301s the no-slash form to the trailing-slash one;
 * we therefore canonicalize to the trailing-slash form (the 200 response) so
 * canonical / hreflang / sitemap / og:url never point at a redirect. Paths with
 * a file extension (e.g. /rss.xml) are left as-is.
 */
export function canonicalUrl(pathOrUrl, site) {
  const u = new URL((pathOrUrl ?? "/").toString(), site);
  if (!u.pathname.endsWith("/") && !/\.[^/]+$/.test(u.pathname)) u.pathname += "/";
  return u.href;
}

/**
 * Plain-text summary for a meta description: first real paragraph of a Markdown
 * body with the markup stripped, clamped to ~max chars.
 */
export function plainExcerpt(body, max = 160) {
  const { content } = safeMatter(body);
  const para = content.trim().split("\n\n").find((x) => x.trim() && !x.startsWith("#")) || content;
  const text = para.replace(/[#*`>_[\]()]/g, "").replace(/\s+/g, " ").trim();
  return text.length > max ? text.slice(0, max - 1).trimEnd() + "…" : text;
}
