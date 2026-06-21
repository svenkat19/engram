from __future__ import annotations

import logging
import sqlite3

from engram.config import get_settings
from engram.embedding.base import EmbeddingProvider
from engram.models.entities import Entity
from engram.store.vector_store import VectorStore

logger = logging.getLogger(__name__)


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "openai":
        from engram.embedding.openai import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider(
            dimensions=settings.embedding_dimensions,
            api_key=settings.openai_api_key,
        )
    from engram.embedding.local import LocalEmbeddingProvider
    return LocalEmbeddingProvider(model_id=settings.embedding_model)


def build_embed_text(entity: Entity) -> str:
    text = f"[{entity.entity_type.value}] {entity.title}"
    if entity.content:
        text += f"\n{entity.content[:500]}"
    return text


class EmbeddingPipeline:

    def __init__(
        self,
        provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self.provider = provider
        self.vector_store = vector_store

    def index_entity(self, entity: Entity) -> list[float]:
        text = build_embed_text(entity)
        [embedding] = self.provider.embed([text])
        self.vector_store.upsert(entity.id, embedding)
        return embedding

    def batch_index(self, entities: list[Entity], batch_size: int = 64) -> None:
        for i in range(0, len(entities), batch_size):
            batch = entities[i : i + batch_size]
            texts = [build_embed_text(e) for e in batch]
            embeddings = self.provider.embed(texts)
            items = [(e.id, emb) for e, emb in zip(batch, embeddings)]
            self.vector_store.batch_upsert(items)
            logger.info("Indexed %d/%d entities", min(i + batch_size, len(entities)), len(entities))

    def embed_query(self, query: str) -> list[float]:
        [embedding] = self.provider.embed([query])
        return embedding
