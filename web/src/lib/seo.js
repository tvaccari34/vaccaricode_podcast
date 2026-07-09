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
 * Absolute canonical URL for a path (or full URL), with any trailing slash
 * removed except on the root — matching the site's no-trailing-slash internal
 * links so canonical / hreflang / sitemap all agree.
 */
export function canonicalUrl(pathOrUrl, site) {
  let p = (pathOrUrl ?? "/").toString();
  if (p.length > 1) p = p.replace(/\/+$/, "");
  return new URL(p || "/", site).href;
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
