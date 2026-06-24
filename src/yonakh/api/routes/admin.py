from __future__ import annotations

from fastapi import APIRouter, Depends

from yonakh.api.deps import AppState, get_state
from yonakh.quality.compaction import run_compaction

router = APIRouter(tags=["admin"])


@router.get("/admin/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@router.get("/admin/stats")
def stats(state: AppState = Depends(get_state)):
    return {
        "events": state.event_store.count(),
        "entities": state.entity_store.count(),
        "relationships": state.relationship_store.count(),
        "vector_embeddings": state.vector_store.count(),
    }


@router.post("/admin/reindex")
def reindex(state: AppState = Depends(get_state)):
    state.fts_store.rebuild()
    return {"reindexed": True}


@router.post("/admin/compact")
def compact(state: AppState = Depends(get_state)):
    result = run_compaction(
        conn=state.conn,
        entity_store=state.entity_store,
        relationship_store=state.relationship_store,
    )
    return result
