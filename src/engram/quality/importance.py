"""Importance scoring engine.

Computes a [0.0, 1.0] score as a weighted sum of signals:
  - type_weight:    base importance by entity type
  - connectivity:   how many relationships the entity has
  - access:         how often the entity has been accessed
  - richness:       how much content the entity contains
  - explicit:       the entity's current importance value
"""

from __future__ import annotations

from engram.models.entities import Entity

TYPE_WEIGHTS: dict[str, float] = {
    "decision": 0.9,
    "design_rationale": 0.85,
    "failed_attempt": 0.8,
    "bug_report": 0.7,
    "code_review": 0.6,
    "pull_request": 0.5,
    "issue": 0.5,
    "conversation": 0.4,
    "document": 0.7,
    "experiment": 0.6,
    "benchmark": 0.6,
    "commit": 0.3,
    "message": 0.2,
    "snippet": 0.4,
    "meeting_note": 0.5,
    "slack_thread": 0.3,
    "branch": 0.2,
    "person": 0.5,
    "project": 0.5,
    "component": 0.5,
    "concept": 0.6,
}

# Signal weights (must sum to 1.0).
_W_TYPE = 0.30
_W_CONNECTIVITY = 0.15
_W_ACCESS = 0.15
_W_RICHNESS = 0.10
_W_EXPLICIT = 0.30


def compute_importance(entity: Entity, relationship_count: int = 0) -> float:
    """Return an importance score in [0.0, 1.0] for *entity*.

    Parameters
    ----------
    entity:
        The entity to score.
    relationship_count:
        Number of relationships (edges) involving this entity.
    """
    type_signal = TYPE_WEIGHTS.get(entity.entity_type.value, 0.5)
    connectivity_signal = min(1.0, relationship_count / 10)
    access_signal = min(1.0, entity.access_count / 20)
    content_len = len(entity.content) if entity.content else 0
    richness_signal = min(1.0, content_len / 1000)
    explicit_signal = entity.importance

    raw = (
        _W_TYPE * type_signal
        + _W_CONNECTIVITY * connectivity_signal
        + _W_ACCESS * access_signal
        + _W_RICHNESS * richness_signal
        + _W_EXPLICIT * explicit_signal
    )
    return max(0.0, min(1.0, raw))
