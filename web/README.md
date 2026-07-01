# web

The public **Astro** site for tiagovaccari.com: blog, podcast, about/bio, and the themed
newsletter subscribe page, plus an RSS feed and an iTunes-compatible podcast feed.

Per the chosen approach, the site **queries Postgres at build time** (no markdown files): each
page reads published `drafts` / `episodes` and renders static HTML. Publishing (task group 8)
just flips a draft's status to `published`, and the next build picks it up.

## Structure

```
src/
  lib/db.js                 pg queries (published posts + episodes)
  layouts/Base.astro        shell, nav, light/dark theme toggle, feed links
  styles/global.css         theme (CSS variables)
  pages/
    index.astro             home: latest posts + episodes + bio teaser
    blog/index.astro        blog list
    blog/[id].astro         post (markdown body → HTML via marked; frontmatter via gray-matter)
    podcast/index.astro     episode list
    podcast/[id].astro      episode (audio player when ready + show notes)
    about.astro             Tiago's bio
    subscribe.astro         themed Listmonk subscribe form
    rss.xml.js              blog RSS feed
    podcast/feed.xml.js     iTunes podcast feed
```

## Build / dev

The build needs the database. The simplest path uses the containerized build on the compose
network (no host DB port needed):

```bash
# from repo root
make web-build      # docker compose run --rm web-build  → writes web/dist (served by Caddy)
```

Then open http://localhost/ . Routes: `/`, `/blog`, `/podcast`, `/about`, `/subscribe`,
`/rss.xml`, `/podcast/feed.xml`.

For fast local iteration with live reload, run Astro on the host pointed at the DB (publish the
Postgres port or use a tunnel), then `cd web && npm install && npm run dev`.

## Build-time env

| Var | Purpose |
|-----|---------|
| `DATABASE_URL` | Postgres DSN (compose injects the in-network one) |
| `PUBLIC_SITE_URL` | absolute base URL used in feeds (default `http://localhost`) |
| `PUBLIC_LISTMONK_URL` | subscribe form target (default `http://localhost:9000`) |
| `PUBLIC_LISTMONK_LIST_UUID` | Listmonk list to subscribe to (wired in task group 7) |

## Pending

- Subscribe form needs the Listmonk public list UUID (task group 7).
- Episode pages show "audio coming soon" until the sound-worker produces audio (task group 4).
