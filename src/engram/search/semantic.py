from __future__ import annotations

from dataclasses import dataclass

from engram.embedding.base import EmbeddingProvider
from engram.embedding.pipeline import EmbeddingPipeline
from engram.store.vector_store import VectorResult, VectorStore


@dataclass
class SemanticResult:
    entity_id: str
    similarity: float


class SemanticSearch:

    def __init__(self, pipeline: EmbeddingPipeline) -> None:
        self.pipeline = pipeline

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[SemanticResult]:
        embedding = self.pipeline.embed_query(query)
        results = self.pipeline.vector_store.search(embedding, limit=limit)
        return [
            SemanticResult(entity_id=r.entity_id, similarity=r.similarity)
            for r in results
        ]
