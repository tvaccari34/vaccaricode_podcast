# Tasks — site analytics (Umami) + UTM convention

## 1. Deploy Umami (infra)
- [x] 1.1 Create a `umami` DB + role on the shared `postgres_postgres` (one-off SQL); store password in `.env`.
- [x] 1.2 Add a `umami` service to `deploy/stack.boosternews.yml` (image `ghcr.io/umami-software/umami:postgresql-latest`, `DATABASE_URL` → `postgres_postgres/umami`, `APP_SECRET`, `BoosterBot_Network`).
- [x] 1.3 Traefik router `Host(\`umami.tiagovaccari.com\`)` → port 3000, TLS `letsencryptresolver`, `bn-sec-headers` (NO Basic Auth — collection endpoints must stay public).
- [ ] 1.4 DNS A record for `umami.tiagovaccari.com`; deploy; confirm Umami is up and its login works.

## 2. Register the site + config
- [x] 2.1 In the Umami dashboard: set admin password, add website `tiagovaccari.com` → copy the **website id**.
- [x] 2.2 `.env`: `UMAMI_DB_PASSWORD`, `UMAMI_APP_SECRET`, `PUBLIC_UMAMI_SRC`, `PUBLIC_UMAMI_WEBSITE_ID`; `.env.example` documents them.

## 3. Tracker + CSP
- [x] 3.1 `Base.astro`: inject the tracker `<script>` in `<head>`, gated on `import.meta.env.PUBLIC_UMAMI_WEBSITE_ID` (dev/off builds emit nothing).
- [x] 3.2 Widen `bn-csp`: add the Umami origin to `script-src` and `connect-src` (nothing else changed).

## 4. UTM convention (pipeline)
- [x] 4.1 `with_utm(url, *, source, medium, campaign)` pure helper (idempotent; preserves existing query); unit-tested.
- [x] 4.2 Config `UTM_ENABLED` (default true) + the source/medium taxonomy; document the table.
- [x] 4.3 Tag **newsletter digest** links (`digest.py`) → `utm_source=newsletter,utm_medium=email,utm_campaign=weekly-digest-<YYYY-Www>`.
- [x] 4.4 Tag **podcast show-notes** subscribe CTA (`generate.py`) → `utm_source=podcast,utm_medium=podcast,utm_campaign=episode-<topic_id>`.
- [x] 4.5 Leave on-site (blog) CTA links **untagged** to avoid self-referral noise.

## 5. Privacy note
- [x] 5.1 Add one line to the site's privacy/about copy: anonymous, cookieless analytics, no PII / cross-site tracking.

## 6. Verify end-to-end
- [ ] 6.1 Umami dashboard reachable + login works; `/script.js` and `/api/send` are publicly reachable (no auth).
- [ ] 6.2 Load a site page → a **pageview appears in Umami**, with **no CSP violation** in the browser console.
- [ ] 6.3 Visit a UTM-tagged link → Umami records the expected source/medium/campaign.
- [ ] 6.4 Unset `PUBLIC_UMAMI_WEBSITE_ID` + rebuild → tracker absent (kill switch works).
- [x] 6.5 `with_utm` unit tests: idempotency, existing-query preservation, encoding.

## 7. Docs
- [x] 7.1 `deploy/DEPLOY.md`: two-phase Umami rollout (deploy → website id → CSP + rebuild), the kill switch, and the UTM taxonomy table.
