"""The narration claim carries the episode language so the worker can pick the right voice."""

from __future__ import annotations

from boosternews import repository as repo


class _Cursor:
    def __init__(self, row):
        self.row = row
        self.executed: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.executed.append(sql)

    def fetchone(self):
        return self.row


class _Conn:
    def __init__(self, row):
        self.cur = _Cursor(row)

    def cursor(self):
        return self.cur


def test_claim_includes_episode_language():
    conn = _Conn(("j1", "e1", "narrator", "Hello there.", "en"))
    job = repo.claim_next_job(conn, "worker-01")
    assert job == {
        "id": "j1",
        "episode_id": "e1",
        "voice_id": "narrator",
        "text": "Hello there.",
        "language": "en",
    }
    assert "JOIN episodes" in conn.cur.executed[0]


def test_claim_falls_back_to_primary_language():
    conn = _Conn(("j1", "e1", "narrator", "Olá.", None))
    assert repo.claim_next_job(conn, "worker-01")["language"] == "pt-BR"


def test_claim_returns_none_when_queue_empty():
    assert repo.claim_next_job(_Conn(None), "worker-01") is None
