from boosternews.config import get_settings
from boosternews.utm import with_utm


def test_with_utm_appends_params():
    u = with_utm("https://x.com/subscribe", source="podcast", medium="podcast", campaign="episode-1")
    assert "utm_source=podcast" in u
    assert "utm_medium=podcast" in u
    assert "utm_campaign=episode-1" in u


def test_with_utm_preserves_other_query():
    u = with_utm("https://x.com/p?ref=abc", source="newsletter", medium="email")
    assert "ref=abc" in u
    assert "utm_source=newsletter" in u


def test_with_utm_is_idempotent():
    once = with_utm("https://x.com/p", source="newsletter", medium="email", campaign="w1")
    twice = with_utm(once, source="newsletter", medium="email", campaign="w2")
    assert twice.count("utm_source=") == 1  # replaced, not duplicated
    assert "utm_campaign=w2" in twice and "utm_campaign=w1" not in twice


def test_with_utm_disabled(monkeypatch):
    monkeypatch.setenv("UTM_ENABLED", "false")
    get_settings.cache_clear()
    assert with_utm("https://x.com/p", source="podcast", medium="podcast") == "https://x.com/p"
    get_settings.cache_clear()
