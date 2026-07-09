// Dynamic robots.txt so the Sitemap directive always points at the current
// build's site URL. Regenerated on every rebuild alongside the sitemap.
export async function GET(context) {
  const root = (context.site?.toString() || "http://localhost/").replace(/\/$/, "");
  const body = `User-agent: *\nAllow: /\n\nSitemap: ${root}/sitemap.xml\n`;
  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
}
