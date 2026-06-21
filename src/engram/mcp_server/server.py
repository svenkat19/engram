from __future__ import annotations

import sqlite3

from mcp.server.fastmcp import FastMCP

from engram.config import get_settings
from engram.db.engine import init_db
from engram.embedding.pipeline import EmbeddingPipeline, get_embedding_provider
from engram.store.entity_store import EntityStore
from engram.store.event_store import EventStore
from engram.store.fts_store import FTSStore
from engram.store.provenance_store import ProvenanceStore
from engram.store.relationship_store import RelationshipStore
from engram.store.vector_store import VectorStore
from engram.search.hybrid import HybridSearch

mcp = FastMCP("engram")

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
from engram.mcp_server import tools  # noqa: E402, F401
