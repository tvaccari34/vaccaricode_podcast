"""Review decisions and the publish gate (pure logic).

Kept free of DB/IO so the state-transition rules and the approval gate are unit-testable. The
repository layer applies these to Postgres; the publishing step (task group 8) calls the gate
before anything goes live.
"""

from __future__ import annotations

# A per-channel review decision maps a draft to its next status.
DECISION_STATUS: dict[str, str] = {
    "approve": "approved",
    "reject": "rejected",
    "request_edit": "needs_edit",
}

VALID_DECISIONS = frozenset(DECISION_STATUS)


class PublishGateError(Exception):
    """Raised when something not approved is asked to publish."""


def decision_to_status(decision: str) -> str:
    """Map a review decision to the draft status it produces. Raises KeyError if unknown."""
    return DECISION_STATUS[decision]


def assert_publishable(status: str) -> None:
    """Enforce the approval gate: only an 'approved' draft may be published."""
    if status != "approved":
        raise PublishGateError(f"draft is not approved (status={status!r}); cannot publish")
