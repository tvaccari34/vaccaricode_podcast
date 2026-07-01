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
| Amazon SES | ⬜ | production |
| Resend | ⬜ | production alternative |

**Switching provider = flip `enabled`** on the desired server (UI, or the `settings` row) — no code
change. For production, disable Mailpit, fill the SES *or* Resend host/username/password, enable
it, and set the From address.

### Domain auth (production, DNS)

Before sending from `tiagovaccari.com`, add these DNS records for the chosen provider:

- **SPF:** `TXT @  "v=spf1 include:amazonses.com ~all"` (SES) or the Resend-provided include.
- **DKIM:** the CNAME/TXT records the provider gives you (SES: 3 CNAMEs; Resend: provided records).
- **DMARC:** `TXT _dmarc  "v=DMARC1; p=none; rua=mailto:dmarc@tiagovaccari.com"`.

Verify the domain in the provider console before enabling the server.

## Campaign sending (pipeline → Listmonk API)

Publishing creates a Listmonk **campaign** from an approved newsletter draft
(`boosternews.listmonk.create_campaign`). It needs an API user token:

1. Listmonk → **Admin → Users → New** → type **API** → assign a role with campaign + list
   permissions → copy the generated **token**.
2. Put it in `.env`:
   ```
   LISTMONK_API_USER=<api username>
   LISTMONK_API_TOKEN=<token>
   LISTMONK_LIST_ID=2
   ```
3. Restart the pipeline. `publish` will now create campaigns; start/send them from the Listmonk
   UI (or enable auto-start later).

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
