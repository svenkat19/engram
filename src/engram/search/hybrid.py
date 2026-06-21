from __future__ import annotations

import time

from engram.embedding.pipeline import EmbeddingPipeline
from engram.models.base import EntityType
from engram.models.entities import Entity
from engram.models.relationships import Relationship
from engram.models.search import SearchQuery, SearchResponse, SearchResult
from engram.store.entity_store import EntityStore
from engram.store.fts_store import FTSStore
from engram.store.relationship_store import RelationshipStore
from engram.store.vector_store import VectorStore


RRF_K = 60


class HybridSearch:

    def __init__(
        self,
        entity_store: EntityStore,
        fts_store: FTSStore,
        pipeline: EmbeddingPipeline,
        relationship_store: RelationshipStore | None = None,
    ) -> None:
        self.entity_store = entity_store
        self.fts_store = fts_store
        self.pipeline = pipeline
        self.relationship_store = relationship_store

    def search(self, query: SearchQuery) -> SearchResponse:
        start = time.monotonic()
        overfetch = query.limit * 3

        fts_results = self.fts_store.search(
            query.query,
            entity_types=query.entity_types,
            project=query.project,
            limit=overfetch,
        )

        semantic_results = []
        if self.pipeline.vector_store.available:
            embedding = self.pipeline.embed_query(query.query)
            semantic_results = self.pipeline.vector_store.search(
                embedding, limit=overfetch,
            )

        scores: dict[str, float] = {}
        for rank, result in enumerate(fts_results):
            scores[result.entity_id] = scores.get(result.entity_id, 0) + 1.0 / (RRF_K + rank + 1)
        for rank, result in enumerate(semantic_results):
            scores[result.entity_id] = scores.get(result.entity_id, 0) + 1.0 / (RRF_K + rank + 1)

        entity_cache: dict[str, Entity] = {}
        filtered_scores: dict[str, float] = {}

        for entity_id, rrf_score in scores.items():
            entity = self.entity_store.get(entity_id)
            if entity is None or entity.status.value == "deleted":
                continue

            if query.entity_types and entity.entity_type not in query.entity_types:
                continue
            if query.project and entity.project != query.project:
                continue
            if query.min_importance and entity.importance < query.min_importance:
                continue
            if query.after and entity.created_at < query.after:
                continue
            if query.before and entity.created_at > query.before:
                continue

            effective_score = rrf_score * entity.importance * entity.decay_factor
            filtered_scores[entity_id] = effective_score
            entity_cache[entity_id] = entity

            self.entity_store.record_access(entity_id)

        ranked = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)
        top = ranked[: query.limit]

        results = []
        for entity_id, score in top:
            entity = entity_cache[entity_id]
            relationships: list[Relationship] = []
            if query.include_relationships and self.relationship_store:
                relationships = self.relationship_store.get_for_entity(entity_id)
            results.append(SearchResult(
                entity=entity,
                score=score,
                relationships=relationships,
            ))

        duration_ms = (time.monotonic() - start) * 1000

        return SearchResponse(
            results=results,
            total=len(filtered_scores),
            query=query.query,
            duration_ms=round(duration_ms, 2),
        )
