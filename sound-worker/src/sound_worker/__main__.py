"""Entry point for the home GPU sound-worker."""

from __future__ import annotations

import sys

from .config import get_worker_settings
from .worker import run


def main() -> int:
    try:
        get_worker_settings()  # fail fast on missing config
    except Exception as exc:  # noqa: BLE001
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
