"""Temporal decay with a sigmoid curve and per-type half-lives."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from yonakh.models.entities import Entity

HALF_LIFE_DAYS: dict[str, int] = {
    "decision": 365,
    "design_rationale": 365,
    "document": 365,
    "failed_attempt": 180,
    "bug_report": 120,
    "commit": 90,
    "benchmark": 90,
    "experiment": 90,
    "conversation": 60,
    "pull_request": 60,
    "code_review": 60,
    "issue": 90,
    "meeting_note": 60,
    "message": 30,
    "slack_thread": 30,
    "snippet": 90,
}

_DEFAULT_HALF_LIFE_DAYS = 90


def compute_decay(entity: Entity, now: datetime | None = None) -> float:
    """Return a decay factor in [0.01, 1.0] for *entity*.

    The decay follows a sigmoid curve centred at the entity type's half-life.
    Entities that have been accessed or updated recently decay more slowly
    because the reference timestamp is the most recent of ``last_accessed``
    and ``updated_at``.

    Parameters
    ----------
    entity:
        The entity whose decay to compute.
    now:
        The current time.  Defaults to ``datetime.now(timezone.utc)``.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Use the most recent activity timestamp.
    reference = entity.updated_at
    if entity.last_accessed is not None and entity.last_accessed > reference:
        reference = entity.last_accessed

    # Ensure both timestamps are offset-aware for subtraction.
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    age_days = (now - reference).total_seconds() / 86400.0
    half_life = HALF_LIFE_DAYS.get(entity.entity_type.value, _DEFAULT_HALF_LIFE_DAYS)
    steepness = half_life / 5.0

    decay = 1.0 / (1.0 + math.exp((age_days - half_life) / steepness))
    return max(0.01, min(1.0, decay))
