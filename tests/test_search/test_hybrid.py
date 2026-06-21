"""Tests for the hybrid search engine."""

from __future__ import annotations

import sqlite3

import pytest

from engram.db.engine import _set_pragmas, _read_schema_sql
from engram.embedding.pipeline import EmbeddingPipeline
from engram.models.base import EntityType
from engram.models.entities import EntityCreate
from engram.models.search import SearchQuery
from engram.search.hybrid import HybridSearch
from engram.store.entity_store import EntityStore
from engram.store.fts_store import FTSStore
from engram.store.relationship_store import RelationshipStore
from engram.store.vector_store import VectorStore
from tests.fake_embedding import FakeEmbeddingProvider


@pytest.fixture
def search_env(db_conn):
    """Set up a full search environment with seeded data."""
    entity_store = EntityStore(db_conn)
    fts_store = FTSStore(db_conn)
    vector_store = VectorStore(db_conn)
    rel_store = RelationshipStore(db_conn)
    provider = FakeEmbeddingProvider()
    pipeline = EmbeddingPipeline(provider, vector_store)

    entities = [
        EntityCreate(
            entity_type=EntityType.DECISION,
            title="Use SQLite for storage",
            content="We chose SQLite for local-first storage with zero dependencies.",
            project="engram",
            importance=0.9,
        ),
        EntityCreate(
            entity_type=EntityType.DECISION,
            title="Use React for the dashboard",
            content="React has the best ecosystem for graph visualization components.",
            project="engram",
            importance=0.8,
        ),
        EntityCreate(
            entity_type=EntityType.BUG_REPORT,
            title="SQLite WAL mode not enabled",
            content="Concurrent reads are blocking writes because WAL mode was not set.",
            project="engram",
            importance=0.7,
        ),
        EntityCreate(
            entity_type=EntityType.FAILED_ATTEMPT,
            title="Tried Redis for caching",
            content="Redis added too much operational complexity for a local tool.",
            project="engram",
            importance=0.6,
        ),
        EntityCreate(
            entity_type=EntityType.COMMIT,
            title="Add authentication middleware",
            content="Added JWT-based auth with refresh tokens.",
            project="other-project",
            importance=0.4,
        ),
    ]

    created = []
    for ec in entities:
        e = entity_store.create(ec)
        pipeline.index_entity(e)
        created.append(e)

    search = HybridSearch(
        entity_store=entity_store,
        fts_store=fts_store,
        pipeline=pipeline,
        relationship_store=rel_store,
    )

    return search, created


def test_basic_search(search_env):
    search, _ = search_env
    response = search.search(SearchQuery(query="SQLite storage"))

    assert response.total > 0
    assert len(response.results) > 0
    assert response.duration_ms >= 0

    titles = [r.entity.title for r in response.results]
    assert "Use SQLite for storage" in titles


def test_search_filters_by_type(search_env):
    search, _ = search_env
    response = search.search(SearchQuery(
        query="SQLite",
        entity_types=[EntityType.BUG_REPORT],
    ))

    for r in response.results:
        assert r.entity.entity_type == EntityType.BUG_REPORT


def test_search_filters_by_project(search_env):
    search, _ = search_env
    response = search.search(SearchQuery(
        query="authentication middleware",
        project="engram",
    ))

    for r in response.results:
        assert r.entity.project == "engram"


def test_search_min_importance(search_env):
    search, _ = search_env
    response = search.search(SearchQuery(
        query="SQLite React Redis",
        min_importance=0.75,
    ))

    for r in response.results:
        assert r.entity.importance >= 0.75


def test_search_respects_limit(search_env):
    search, _ = search_env
    response = search.search(SearchQuery(query="engram project", limit=2))
    assert len(response.results) <= 2


def test_search_includes_relationships(search_env):
    search, created = search_env
    response = search.search(SearchQuery(
        query="SQLite",
        include_relationships=True,
    ))
    assert response.total > 0


def test_fts_only_search(search_env):
    search, _ = search_env
    response = search.search(SearchQuery(query="WAL mode"))
    assert response.total > 0
    titles = [r.entity.title for r in response.results]
    assert "SQLite WAL mode not enabled" in titles


def test_empty_query_returns_empty(search_env):
    search, _ = search_env
    response = search.search(SearchQuery(query=""))
    assert response.total == 0
