"""Minimal Listmonk client for creating newsletter campaigns.

Used by publishing to turn an approved newsletter draft into a Listmonk campaign. Actually
*sending* requires SMTP + a public list, which are configured in task group 7 — until then this
is a no-op when credentials/list aren't set (publishing still records the edition as published).
"""

from __future__ import annotations

import logging

import httpx

from .config import get_settings

log = logging.getLogger("boosternews.listmonk")


def build_campaign_payload(
    name: str,
    subject: str,
    body: str,
    list_ids: list[int],
    content_type: str = "markdown",
) -> dict:
    """Pure helper: the JSON body for POST /api/campaigns."""
    return {
        "name": name,
        "subject": subject,
        "lists": list_ids,
        "content_type": content_type,
        "type": "regular",
        "body": body,
    }


def is_configured() -> bool:
    s = get_settings()
    return bool(s.listmonk_api_user and s.listmonk_api_token and s.listmonk_list_id)


def list_id_for(language: str) -> int:
    """The Listmonk list id for a language (English → its own list; else the primary list)."""
    s = get_settings()
    if language == s.secondary_language_code and s.listmonk_list_id_en:
        return s.listmonk_list_id_en
    return s.listmonk_list_id


def create_campaign(
    *, name: str, subject: str, body: str, list_id: int | None = None
) -> int | None:
    """Create a Listmonk campaign (draft) targeting ``list_id``. None if Listmonk isn't configured."""
    s = get_settings()
    lid = list_id or s.listmonk_list_id
    if not (s.listmonk_api_user and s.listmonk_api_token and lid):
        log.info("Listmonk not configured (api creds / list %s); skipping campaign", lid)
        return None
    payload = build_campaign_payload(name, subject, body, [lid])
    headers = {"Authorization": f"token {s.listmonk_api_user}:{s.listmonk_api_token}"}
    resp = httpx.post(
        f"{s.listmonk_api_url.rstrip('/')}/api/campaigns",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("data", {}).get("id")


def start_campaign(campaign_id: int | None) -> bool:
    """Start (send) a draft campaign via PUT /api/campaigns/{id}/status. Best-effort."""
    s = get_settings()
    if not (s.listmonk_api_user and s.listmonk_api_token and campaign_id):
        return False
    headers = {"Authorization": f"token {s.listmonk_api_user}:{s.listmonk_api_token}"}
    resp = httpx.put(
        f"{s.listmonk_api_url.rstrip('/')}/api/campaigns/{campaign_id}/status",
        json={"status": "running"},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return True
