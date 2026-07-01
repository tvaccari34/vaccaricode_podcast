"""Tests for fail-fast configuration loading."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from boosternews.config import Settings, mask

REQUIRED_ENV = {
    "DATABASE_URL": "postgresql://u:p@localhost:5432/boosternews",
    "GEMINI_API_KEY": "test-gemini-key",
    "S3_ENDPOINT_URL": "http://localhost:9000",
    "S3_ACCESS_KEY_ID": "key",
    "S3_SECRET_ACCESS_KEY": "secret",
    "WORKER_AUTH_TOKEN": "token",
}


def test_loads_with_all_required(monkeypatch):
    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    s = Settings(_env_file=None)
    assert s.database_url == REQUIRED_ENV["DATABASE_URL"]
    assert s.gemini_model == "gemini-2.5-flash"  # default applied


def test_fails_fast_when_secret_missing(monkeypatch):
    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)
    assert "gemini_api_key" in str(exc.value)


def test_mask_hides_secret():
    assert mask("sk-ant-supersecret").startswith("sk-a")
    assert "supersecret" not in mask("sk-ant-supersecret")
