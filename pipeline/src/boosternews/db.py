"""PostgreSQL connection helpers (psycopg 3)."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator

import psycopg

from .config import get_settings


@contextmanager
def get_conn(*, autocommit: bool = False) -> Iterator[psycopg.Connection]:
    """Yield a database connection, closed on exit.

    With ``autocommit=False`` (default) the connection commits on clean exit and rolls back on
    exception, courtesy of psycopg's context manager.
    """
    settings = get_settings()
    with psycopg.connect(settings.database_url, autocommit=autocommit) as conn:
        yield conn


def ping() -> bool:
    """Return True if the database answers ``SELECT 1``."""
    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1")
        return cur.fetchone() == (1,)
