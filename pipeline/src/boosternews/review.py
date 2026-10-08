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


# ── Narration policy ────────────────────────────────────────────────────────
# Narration is enqueued when a podcast draft is APPROVED, not when it is generated. Generating
# audio up front spent the whole TTS quota on drafts that were never reviewed (83 topics queued vs
# 22 published), so the expensive step now waits for a human yes.
def should_narrate_on_approval(
    *,
    channel: str,
    decision: str,
    language: str,
    primary_language: str,
    secondary_enabled: bool,
) -> bool:
    """Whether approving this draft should queue narration.

    Only an approved podcast draft narrates. The primary language always does; the secondary
    (translated) language only when ``narration_secondary_enabled`` is set, since it doubles the
    per-episode TTS spend.
    """
    if channel != "podcast" or decision != "approve":
        return False
    if language == primary_language:
        return True
    return secondary_enabled


def episode_audio_ready(audio_url: str | None) -> bool:
    """Whether an episode has narration audio and may therefore go live."""
    return bool(audio_url and audio_url.strip())


def assert_audio_present(audio_url: str | None) -> None:
    """Enforce the audio gate: a silent episode must never reach the feed."""
    if not episode_audio_ready(audio_url):
        raise PublishGateError("episode has no narration audio yet; cannot publish")
