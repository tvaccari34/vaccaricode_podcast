"""Pure job-lifecycle logic for narration jobs (testable without DB)."""

from __future__ import annotations


def next_status_after_failure(attempts: int, max_attempts: int) -> str:
    """A failed job requeues until it has used up its attempts, then it's failed for good.

    ``attempts`` is the number already made (incremented when the job is claimed).
    """
    return "queued" if attempts < max_attempts else "failed"
