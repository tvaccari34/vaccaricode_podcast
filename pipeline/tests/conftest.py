"""Shared test fixtures: provide a fake but complete config for every test.

Several modules call ``get_settings()`` at runtime (e.g. generation reads the author name). This
autouse fixture injects valid env vars and clears the settings cache around each test so those
calls succeed without real secrets and without leaking state between tests.
"""

from __future__ import annotations

import pytest

from boosternews.config import get_settings

FAKE_ENV = {
    "DATABASE_URL": "postgresql://u:p@localhost:5432/boosternews",
    "GEMINI_API_KEY": "test-gemini-key",
    "S3_ENDPOINT_URL": "http://localhost:9000",
    "S3_ACCESS_KEY_ID": "key",
    "S3_SECRET_ACCESS_KEY": "secret",
    "WORKER_AUTH_TOKEN": "token",
}


@pytest.fixture(autouse=True)
def _fake_settings(monkeypatch):
    for k, v in FAKE_ENV.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
