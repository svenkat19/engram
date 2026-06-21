"""Near-duplicate detection using cosine similarity."""

from __future__ import annotations

from dataclasses import dataclass

from engram.models.entities import Entity
from engram.store.entity_store import EntityStore
from engram.store.vector_store import VectorStore


@dataclass
class DuplicateCandidate:
    """An entity that is a near-duplicate of the query entity."""

    entity: Entity
    similarity: float


def find_near_duplicates(
    entity_id: str,
    embedding: list[float],
    vector_store: VectorStore,
    entity_store: EntityStore,
    threshold: float = 0.92,
    limit: int = 5,
) -> list[DuplicateCandidate]:
    """Search for entities whose embeddings are very similar to *embedding*.

    Parameters
    ----------
    entity_id:
        ID of the query entity (excluded from results).
    embedding:
        The embedding vector of the query entity.
    vector_store:
        Vector store used for similarity search.
    entity_store:
        Entity store used to hydrate full entity objects.
    threshold:
        Minimum similarity score to consider a match.
    limit:
        Maximum number of candidates to return.
    """
    # Fetch more candidates than needed so we can filter.
    results = vector_store.search(embedding, limit=limit + 1)

    candidates: list[DuplicateCandidate] = []
    for result in results:
        if result.entity_id == entity_id:
            continue
        if result.similarity < threshold:
            continue
        entity = entity_store.get(result.entity_id)
        if entity is None:
            continue
        candidates.append(DuplicateCandidate(entity=entity, similarity=result.similarity))
        if len(candidates) >= limit:
            break

    return candidates


def should_supersede(new_entity: Entity, existing: Entity) -> bool:
    """Return ``True`` if *new_entity* should supersede *existing*.

    A newer entity supersedes an older one when it was created more recently
    **and** has equal or higher confidence.
    """
    if new_entity.created_at <= existing.created_at:
        return False
    return new_entity.confidence >= existing.confidence
