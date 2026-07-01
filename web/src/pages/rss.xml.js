import { blogRss } from "../lib/feeds.js";

export async function GET(context) {
  const xml = await blogRss("pt-BR", context.site);
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8" } });
}
