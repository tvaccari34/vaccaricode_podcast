# Newsletter (Listmonk) — setup & runbook

The newsletter runs on self-hosted **Listmonk**. This covers local dev (working now) and what to
configure for production.

## Local dev (working)

- **Listmonk admin:** http://localhost:9000/ (super admin auto-provisioned from
  `LISTMONK_ADMIN_USER` / `LISTMONK_ADMIN_PASSWORD` in `.env`; an existing admin is kept).
- **Mailpit** (dev mail catcher): http://localhost:8025/ — Listmonk delivers all mail here, so you
  can see opt-in and campaign emails without a real provider.
- **List:** a public, **double opt-in** list ("Opt-in list", uuid `a61c3235-…`) is used by the
  subscribe page (`PUBLIC_LISTMONK_LIST_UUID`).
- **Subscribe flow (verified):** the site's `/subscribe` form posts to
  `…/subscription/form` → Listmonk creates the subscriber as *unconfirmed* and emails a
  "Confirm subscription" link (visible in Mailpit) → clicking confirm makes them *confirmed*.

## Pluggable SMTP (SES ↔ Resend)

Listmonk holds **multiple named SMTP servers** (Admin → Settings → SMTP). We ship three:

| Server | Enabled | Use |
|--------|---------|-----|
| Mailpit (dev) | ✅ | local testing — catches all mail |
| Amazon SES | ⬜ | production alternative |
| Resend | ✅ | production (chosen) |

**Switching provider = flip `enabled`** on the desired server (UI, or the `settings` row) — no code
change. For production, disable Mailpit, fill the SES *or* Resend host/username/password, enable
it, and set the From address. These SMTP settings live in Listmonk's DB via the admin UI — the
`SMTP_*` lines in `.env` are informational only and are **not** read by Listmonk.

### Resend (production — chosen provider)

Concrete Listmonk SMTP server settings (Admin → Settings → SMTP → add server):

| Field | Value |
|-------|-------|
| Host | `smtp.resend.com` |
| Port | `587` (STARTTLS) |
| Auth protocol | `LOGIN` |
| Username | `resend` |
| Password | a Resend **API key** (`re_…`) with *Sending* permission |
| From email | `news@tiagovaccari.com` (must be on the verified domain) |
| TLS | STARTTLS enabled |

Enable this server, disable Mailpit, send a test.

### Domain auth (production, DNS)

Verify `tiagovaccari.com` in the **Resend dashboard → Domains → Add Domain** *before* enabling the
server. Resend then shows the **exact** records to add at your DNS host — copy them verbatim (values
are generated per-domain). They are, in shape:

- **MX** + **SPF** on the sending subdomain — e.g. `send.tiagovaccari.com` MX →
  `feedback-smtp.<region>.amazonses.com`, and `TXT send  "v=spf1 include:amazonses.com ~all"`.
- **DKIM:** a `TXT resend._domainkey` record with the provided public key.
- **DMARC** (recommended): `TXT _dmarc  "v=DMARC1; p=none; rua=mailto:dmarc@tiagovaccari.com"`.

Wait for Resend to show the domain as **Verified** before sending.

## Campaign sending — weekly digest (pipeline → Listmonk API)

Subscribers get **one weekly digest**, not one email per post. Publishing a post does **not** create
a campaign; instead the weekly digest (`boosternews.digest`) aggregates the posts published in the
last 7 days into **one Listmonk campaign per language** (a "this week" intro + a section per post
with its blurb and a link). It needs an API user token:

1. Listmonk → **Admin → Users → New** → type **API** → assign a role with campaign + list
   permissions → copy the generated **token**.
2. Put it in `.env`:
   ```
   LISTMONK_API_USER=<api username>
   LISTMONK_API_TOKEN=<token>
   LISTMONK_LIST_ID=<pt id>
   LISTMONK_LIST_ID_EN=<en id>
   ```
3. The digest runs weekly via cron (`deploy/weekly-digest.sh`, Sundays 7:00 PM US Eastern by default) — or on demand:
   ```
   docker … run --rm pipeline python -m boosternews digest   # (or deploy/weekly-digest.sh)
   ```

**Draft vs. auto-send:** by default the digest is created as a **draft** — review it in the Listmonk
UI and click send. To send automatically, set `NEWSLETTER_DIGEST_AUTOSEND=true` in `.env`. Subjects
and the intro line are configurable (`NEWSLETTER_DIGEST_SUBJECT[_EN]`, `NEWSLETTER_DIGEST_INTRO[_EN]`).

Idempotent: each digest covers posts published since the previous digest (bounded to 7 days), so
posts are never included twice and a week with no new posts sends nothing.

> Note: API tokens are generated and verified internally by Listmonk and can't be seeded via SQL,
> so this is a one-time manual step.

## Unsubscribe & data rights (LGPD/GDPR)

- Every email includes an **unsubscribe** link (Listmonk built-in).
- Subscribers can **export** or **wipe** their data from the subscription-management page
  (`privacy.allow_export` / `privacy.allow_wipe` are enabled).
- Admins can delete a subscriber via Listmonk UI or `DELETE /api/subscribers/{id}`.

## Analytics

Listmonk records per-campaign **delivery, opens, and clicks** (Campaigns → view). Available once a
campaign is sent through a working SMTP server.
