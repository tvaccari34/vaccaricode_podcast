"""Orchestration scheduler.

A single long-running loop that runs the pipeline's recurring jobs at configurable intervals:

  ingest   → discover trends from sources (respects per-source fetch intervals)
  extract  → backfill article text for new topics
  generate → (optional) draft the top new topic into the review queue
  publish  → release approved drafts (gate-enforced) and record publications

Each job is isolated: a failure is logged and the job simply retries on its next due tick — one
bad run never aborts the loop or the other jobs. Publishing only ever releases *approved* drafts,
so automating it is safe; the human review gate is untouched.

Note: the static site rebuild (`web-build`) runs separately (a short cron on the host) since it's
a Node build — see deploy/DEPLOY.md.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from .config import get_settings

log = logging.getLogger("boosternews.scheduler")


def is_due(last_run: float, interval_seconds: int, now: float) -> bool:
    """True if a job with the given interval is due. interval <= 0 disables the job."""
    if interval_seconds <= 0:
        return False
    return (now - last_run) >= interval_seconds


@dataclass
class Job:
    name: str
    interval_seconds: int
    fn: Callable[[], object]
    last_run: float = float("-inf")  # due on the first cycle


def run_cycle(jobs: list[Job], now: float) -> None:
    """Run every due job once, isolating failures, and advance its last_run."""
    for job in jobs:
        if not is_due(job.last_run, job.interval_seconds, now):
            continue
        try:
            result = job.fn()
            log.info("job %s ok: %s", job.name, _summarize(result))
        except Exception as exc:  # noqa: BLE001 — isolate; retry next due tick
            log.warning("job %s failed (retry next tick): %s", job.name, exc)
        job.last_run = now


def default_jobs() -> list[Job]:
    s = get_settings()
    from .ingest import run_extraction, run_ingest

    jobs = [
        Job("ingest", s.sched_ingest_minutes * 60, lambda: run_ingest(only_due=True)),
        Job("extract", s.sched_extract_minutes * 60, lambda: run_extraction(limit=10)),
    ]
    if s.sched_generate_minutes > 0:
        from .generate import generate_top

        jobs.append(Job("generate", s.sched_generate_minutes * 60, generate_top))
    jobs.append(Job("publish", s.sched_publish_minutes * 60, _publish))
    return jobs


def _publish():
    from .publish import publish_all

    return publish_all()


def _summarize(result) -> str:
    if result is None:
        return "no-op"
    if isinstance(result, list):
        return f"{len(result)} item(s)"
    if isinstance(result, dict):
        return f"{len(result)} key(s)"
    return str(result)[:120]


def run_scheduler(
    jobs: list[Job] | None = None,
    *,
    tick: int | None = None,
    max_cycles: int = 0,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    s = get_settings()
    jobs = default_jobs() if jobs is None else jobs
    tick = tick or s.sched_tick_seconds
    log.info(
        "scheduler up (tick=%ss): %s",
        tick,
        ", ".join(f"{j.name}@{j.interval_seconds // 60}m" for j in jobs),
    )
    cycle = 0
    while True:
        run_cycle(jobs, clock())
        cycle += 1
        if max_cycles and cycle >= max_cycles:
            break
        sleep(tick)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_scheduler(max_cycles=get_settings().sched_max_cycles)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
