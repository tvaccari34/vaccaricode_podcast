"""Entry point — dispatches to the CLI.

python -m boosternews                 # config + connectivity check (default)
python -m boosternews seed-sources
python -m boosternews ingest --all
python -m boosternews extract --limit 5
python -m boosternews list-topics
"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
