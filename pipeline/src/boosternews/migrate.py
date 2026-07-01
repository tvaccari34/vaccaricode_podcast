"""Minimal forward-only SQL migration runner.

Applies every ``*.sql`` file in the migrations directory, in lexical order, that has not yet
been recorded in the ``schema_migrations`` table. Each migration runs in its own transaction,
so a failure leaves earlier migrations applied and the failing one rolled back.

Run with:  python -m boosternews.migrate   (or the `boosternews-migrate` console script)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

from .config import get_settings


def find_migrations_dir() -> Path:
    """Locate the migrations directory via $MIGRATIONS_DIR or known relative locations."""
    env = os.environ.get("MIGRATIONS_DIR")
    candidates = [
        Path(env) if env else None,
        Path("/app/db/migrations"),  # inside the container image
        Path(__file__).resolve().parents[3] / "db" / "migrations",  # repo checkout
        Path.cwd() / "db" / "migrations",
    ]
    for c in candidates:
        if c and c.is_dir():
            return c
    raise FileNotFoundError(
        "Could not locate db/migrations. Set MIGRATIONS_DIR to its absolute path."
    )


def _ensure_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version    text PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """)
    conn.commit()


def _applied(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def main() -> int:
    settings = get_settings()
    migrations_dir = find_migrations_dir()
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print(f"No migrations found in {migrations_dir}")
        return 0

    with psycopg.connect(settings.database_url) as conn:
        _ensure_table(conn)
        done = _applied(conn)

        pending = [f for f in files if f.name not in done]
        if not pending:
            print(f"Up to date — {len(done)} migration(s) already applied.")
            return 0

        for path in pending:
            sql = path.read_text(encoding="utf-8")
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s)",
                        (path.name,),
                    )
                conn.commit()
                print(f"applied  {path.name}")
            except Exception as exc:  # noqa: BLE001 — surface and stop
                conn.rollback()
                print(f"FAILED   {path.name}: {exc}", file=sys.stderr)
                return 1

    print(f"Done — applied {len(pending)} migration(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
