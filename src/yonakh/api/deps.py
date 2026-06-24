"""Dependency injection for FastAPI routes."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from yonakh.embedding.base import EmbeddingProvider
from yonakh.embedding.pipeline import EmbeddingPipeline
from yonakh.search.hybrid import HybridSearch
from yonakh.store.entity_store import EntityStore
from yonakh.store.event_store import EventStore
from yonakh.store.fts_store import FTSStore
from yonakh.store.provenance_store import ProvenanceStore
from yonakh.store.relationship_store import RelationshipStore
from yonakh.store.vector_store import VectorStore


@dataclass
class AppState:
    conn: sqlite3.Connection
    event_store: EventStore
    entity_store: EntityStore
    relationship_store: RelationshipStore
    fts_store: FTSStore
    vector_store: VectorStore
    provenance_store: ProvenanceStore
    embedding_provider: EmbeddingProvider
    pipeline: EmbeddingPipeline
    hybrid_search: HybridSearch


_state: AppState | None = None


def init_app_state(conn: sqlite3.Connection, provider: EmbeddingProvider) -> AppState:
    global _state
    event_store = EventStore(conn)
    entity_store = EntityStore(conn)
    relationship_store = RelationshipStore(conn)
    fts_store = FTSStore(conn)
    vector_store = VectorStore(conn)
    provenance_store = ProvenanceStore(conn)
    pipeline = EmbeddingPipeline(provider, vector_store)
    hybrid_search = HybridSearch(
        entity_store=entity_store,
        fts_store=fts_store,
        pipeline=pipeline,
        relationship_store=relationship_store,
    )
    _state = AppState(
        conn=conn,
        event_store=event_store,
        entity_store=entity_store,
        relationship_store=relationship_store,
        fts_store=fts_store,
        vector_store=vector_store,
        provenance_store=provenance_store,
        embedding_provider=provider,
        pipeline=pipeline,
        hybrid_search=hybrid_search,
    )
    return _state


def get_state() -> AppState:
    if _state is None:
        raise RuntimeError("App state not initialized. Call init_app_state first.")
    return _state
