"""Tests for the embedding pipeline."""

from __future__ import annotations

import sqlite3

import pytest

from engram.embedding.pipeline import EmbeddingPipeline, build_embed_text
from engram.models.base import EntityType
from engram.models.entities import EntityCreate
from engram.store.entity_store import EntityStore
from engram.store.vector_store import VectorStore
from tests.fake_embedding import FakeEmbeddingProvider


def _vec_available() -> bool:
    try:
        conn = sqlite3.connect(":memory:")
        conn.enable_load_extension(True)
        import sqlite_vec
        sqlite_vec.load(conn)
        conn.close()
        return True
    except (AttributeError, ImportError, Exception):
        return False


def test_build_embed_text():
    from engram.models.entities import Entity
    from datetime import datetime, timezone

    entity = Entity(
        id="test",
        entity_type=EntityType.DECISION,
        title="Use SQLite",
        content="Long explanation " * 100,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    text = build_embed_text(entity)
    assert text.startswith("[decision] Use SQLite")
    assert len(text) < 600


def test_index_entity_returns_embedding(db_conn):
    entity_store = EntityStore(db_conn)
    vector_store = VectorStore(db_conn)
    provider = FakeEmbeddingProvider()
    pipeline = EmbeddingPipeline(provider, vector_store)

    entity = entity_store.create(EntityCreate(
        entity_type=EntityType.DECISION,
        title="Use PostgreSQL for production",
        content="PostgreSQL supports concurrent writes better than SQLite.",
    ))

    embedding = pipeline.index_entity(entity)
    assert len(embedding) == 384


@pytest.mark.skipif(
    not _vec_available(),
    reason="sqlite-vec extension not available in this Python build",
)
def test_index_and_vector_search(db_conn):
    entity_store = EntityStore(db_conn)
    vector_store = VectorStore(db_conn)
    provider = FakeEmbeddingProvider()
    pipeline = EmbeddingPipeline(provider, vector_store)

    entity = entity_store.create(EntityCreate(
        entity_type=EntityType.DECISION,
        title="Use PostgreSQL for production",
        content="PostgreSQL supports concurrent writes better than SQLite.",
    ))

    pipeline.index_entity(entity)

    query_emb = pipeline.embed_query("PostgreSQL database")
    results = vector_store.search(query_emb, limit=5)
    assert len(results) >= 1
    assert results[0].entity_id == entity.id


@pytest.mark.skipif(
    not _vec_available(),
    reason="sqlite-vec extension not available in this Python build",
)
def test_batch_index(db_conn):
    entity_store = EntityStore(db_conn)
    vector_store = VectorStore(db_conn)
    provider = FakeEmbeddingProvider()
    pipeline = EmbeddingPipeline(provider, vector_store)

    entities = []
    for i in range(10):
        e = entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title=f"Commit #{i}: fix bug {i}",
        ))
        entities.append(e)

    pipeline.batch_index(entities, batch_size=4)
    assert vector_store.count() == 10
