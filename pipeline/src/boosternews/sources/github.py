"""GitHub 'trending' source fetcher (official Search API).

GitHub has no official trending endpoint, so we approximate it with the Search API: repositories
created in the last N days, ordered by stars. This stays within GitHub's ToS (no scraping) and
returns clean JSON. An optional token raises the rate limit.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from ..config import get_settings
from ..models import SourceItem, SourceRow

SEARCH_ENDPOINT = "https://api.github.com/search/repositories"


def items_from_github(payload: dict) -> list[SourceItem]:
    """Pure transform of a Search API response into SourceItems."""
    items: list[SourceItem] = []
    for repo in payload.get("items", []):
        full_name = repo.get("full_name")
        html_url = repo.get("html_url")
        if not full_name or not html_url:
            continue
        description = (repo.get("description") or "").strip() or None
        title = f"{full_name}: {description}" if description else full_name
        published = None
        if repo.get("created_at"):
            published = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
        items.append(
            SourceItem(
                title=title,
                url=html_url,
                external_id=f"gh-{repo.get('id')}",
                summary=description,
                engagement=int(repo.get("stargazers_count") or 0),
                published_at=published,
                extra={"language": repo.get("language")},
            )
        )
    return items


def _since(days: int) -> str:
    return (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()


def fetch_github_trending(source: SourceRow) -> list[SourceItem]:
    cfg = source.config
    q = f"created:>={_since(int(cfg.get('since_days', 7)))} stars:>={int(cfg.get('min_stars', 50))}"
    if cfg.get("language"):
        q += f" language:{cfg['language']}"
    headers = {"Accept": "application/vnd.github+json"}
    token = get_settings().github_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = httpx.get(
        SEARCH_ENDPOINT,
        params={
            "q": q,
            "sort": "stars",
            "order": "desc",
            "per_page": int(cfg.get("limit", 30)),
        },
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return items_from_github(resp.json())
