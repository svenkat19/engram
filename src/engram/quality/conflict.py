"""Contradiction detection between entities."""

from __future__ import annotations

from dataclasses import dataclass

from engram.models.base import RelationType
from engram.models.entities import Entity
from engram.store.relationship_store import RelationshipStore


@dataclass
class Conflict:
    """A detected conflict between two entities."""

    entity_a: Entity
    entity_b: Entity
    conflict_type: str  # "competing_decisions" | "potential_update" | "explicit_supersession"
    confidence: float


def detect_conflicts(
    entity: Entity,
    similar_entities: list[tuple[Entity, float]],
    relationship_store: RelationshipStore,
) -> list[Conflict]:
    """Detect conflicts between *entity* and a set of *similar_entities*.

    Parameters
    ----------
    entity:
        The entity to check for conflicts.
    similar_entities:
        A list of ``(entity, similarity_score)`` pairs that are textually
        similar to *entity*.
    relationship_store:
        Used to look up explicit supersession/revert relationships.
    """
    conflicts: list[Conflict] = []

    for other, similarity in similar_entities:
        if other.id == entity.id:
            continue

        # Check explicit supersession / revert relationships.
        rels = relationship_store.get_for_entity(entity.id)
        for rel in rels:
            peer_id = rel.target_id if rel.source_id == entity.id else rel.source_id
            if peer_id != other.id:
                continue
            if rel.relation_type in (RelationType.SUPERSEDES, RelationType.REVERTS):
                conflicts.append(
                    Conflict(
                        entity_a=entity,
                        entity_b=other,
                        conflict_type="explicit_supersession",
                        confidence=1.0,
                    )
                )
                break

        # Check for competing decisions on the same files.
        if (
            entity.entity_type.value == "decision"
            and other.entity_type.value == "decision"
            and entity.files
            and other.files
            and set(entity.files) & set(other.files)
        ):
            conflicts.append(
                Conflict(
                    entity_a=entity,
                    entity_b=other,
                    conflict_type="competing_decisions",
                    confidence=similarity,
                )
            )
            continue

        # Temporal ordering: newer entity about the same topic.
        if similarity >= 0.85 and entity.created_at != other.created_at:
            conflicts.append(
                Conflict(
                    entity_a=entity,
                    entity_b=other,
                    conflict_type="potential_update",
                    confidence=similarity * 0.8,
                )
            )

    return conflicts
