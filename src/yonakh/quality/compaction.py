"""Background compaction task that orchestrates all quality operations.

Walks every active entity, recomputes decay and importance scores, persists
the updated values, and archives entities whose effective score drops below
a configurable threshold.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone

from yonakh.models.base import EntityStatus
from yonakh.models.entities import EntityFilter
from yonakh.quality.decay import compute_decay
from yonakh.quality.importance import compute_importance
from yonakh.store.entity_store import EntityStore
from yonakh.store.relationship_store import RelationshipStore

logger = logging.getLogger(__name__)


def run_compaction(
    conn: sqlite3.Connection,
    entity_store: EntityStore,
    relationship_store: RelationshipStore,
    archive_threshold: float = 0.05,
) -> dict[str, int]:
    """Run a full compaction pass over all active entities.

    Parameters
    ----------
    conn:
        Database connection used for bulk updates.
    entity_store:
        Store for reading entities.
    relationship_store:
        Store for counting relationships per entity.
    archive_threshold:
        Entities whose ``importance * decay_factor`` falls below this value
        are archived.

    Returns
    -------
    dict
        ``{"updated": N, "archived": M}`` with counts of affected entities.
    """
    now = datetime.now(timezone.utc)
    active_filter = EntityFilter(status=EntityStatus.ACTIVE, limit=1000)
    entities = entity_store.list(active_filter)

    updated = 0
    archived = 0

    for entity in entities:
        rel_count = relationship_store.count(entity.id)
        new_importance = compute_importance(entity, relationship_count=rel_count)
        new_decay = compute_decay(entity, now=now)

        effective_score = new_importance * new_decay

        new_status = EntityStatus.ARCHIVED if effective_score < archive_threshold else None

        conn.execute(
            "UPDATE entities SET importance = ?, decay_factor = ?, "
            "status = COALESCE(?, status), updated_at = ? WHERE id = ?",
            (
                new_importance,
                new_decay,
                new_status.value if new_status else None,
                now.isoformat(),
                entity.id,
            ),
        )
        updated += 1
        if new_status == EntityStatus.ARCHIVED:
            archived += 1
            logger.info("Archived entity %s (score=%.4f)", entity.id, effective_score)

    conn.commit()
    logger.info("Compaction complete: updated=%d, archived=%d", updated, archived)
    return {"updated": updated, "archived": archived}
