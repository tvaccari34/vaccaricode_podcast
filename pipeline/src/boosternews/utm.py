"""UTM tagging for links delivered through *external* channels (newsletter email, podcast show
notes) that point back to the site, so analytics attributes visits to their source.

On-site links are intentionally left untagged to avoid self-referral noise. `with_utm` is pure and
idempotent: existing `utm_*` params are replaced, any other query params are preserved.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .config import get_settings


def with_utm(url: str, *, source: str, medium: str, campaign: str | None = None) -> str:
    """Return ``url`` with utm_source/medium[/campaign] appended (no-op if UTM is disabled)."""
    if not url or not get_settings().utm_enabled:
        return url
    parts = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.startswith("utm_")]
    query.append(("utm_source", source))
    query.append(("utm_medium", medium))
    if campaign:
        query.append(("utm_campaign", campaign))
    return urlunparse(parts._replace(query=urlencode(query)))
