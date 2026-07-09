import { sitemapXml } from "../lib/sitemap.js";

export async function GET(context) {
  const xml = await sitemapXml(context.site);
  return new Response(xml, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
}
