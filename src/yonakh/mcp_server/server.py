from __future__ import annotations

import sqlite3

from mcp.server.fastmcp import FastMCP

from yonakh.config import get_settings
from yonakh.db.engine import init_db
from yonakh.embedding.pipeline import EmbeddingPipeline, get_embedding_provider
from yonakh.store.entity_store import EntityStore
from yonakh.store.event_store import EventStore
from yonakh.store.fts_store import FTSStore
from yonakh.store.provenance_store import ProvenanceStore
from yonakh.store.relationship_store import RelationshipStore
from yonakh.store.vector_store import VectorStore
from yonakh.search.hybrid import HybridSearch

mcp = FastMCP("yonakh")

# Module-level state initialized lazily
_conn: sqlite3.Connection | None = None
_stores: dict = {}

def _init():
    global _conn, _stores
    if _conn is not None:
        return
    settings = get_settings()
    _conn = init_db(settings.db_path)
    provider = get_embedding_provider()
    entity_store = EntityStore(_conn)
    fts_store = FTSStore(_conn)
    vector_store = VectorStore(_conn)
    pipeline = EmbeddingPipeline(provider, vector_store)
    _stores.update(
        event_store=EventStore(_conn),
        entity_store=entity_store,
        relationship_store=RelationshipStore(_conn),
        fts_store=fts_store,
        vector_store=vector_store,
        provenance_store=ProvenanceStore(_conn),
        pipeline=pipeline,
        hybrid_search=HybridSearch(
            entity_store=entity_store,
            fts_store=fts_store,
            pipeline=pipeline,
            relationship_store=RelationshipStore(_conn),
        ),
    )

# Import tools to register them
from yonakh.mcp_server import tools  # noqa: E402, F401
