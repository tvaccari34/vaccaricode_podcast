import { podcastFeed } from "../../../lib/feeds.js";

export async function GET(context) {
  const xml = await podcastFeed("en", context.site);
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8" } });
}
