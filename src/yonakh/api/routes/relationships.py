from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from yonakh.api.deps import AppState, get_state
from yonakh.models.base import RelationType
from yonakh.models.relationships import (
    Relationship,
    RelationshipCreate,
    RelationshipFilter,
)

router = APIRouter(tags=["relationships"])


@router.post("/relationships", response_model=Relationship)
def create_relationship(
    body: RelationshipCreate, state: AppState = Depends(get_state)
):
    relationship = state.relationship_store.create(body)
    return relationship


@router.get("/relationships", response_model=list[Relationship])
def list_relationships(
    source_id: str | None = None,
    target_id: str | None = None,
    relation_type: RelationType | None = None,
    limit: int = 50,
    offset: int = 0,
    state: AppState = Depends(get_state),
):
    filt = RelationshipFilter(
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type,
        limit=limit,
        offset=offset,
    )
    return state.relationship_store.list(filt)


@router.delete("/relationships/{rel_id}")
def delete_relationship(rel_id: str, state: AppState = Depends(get_state)):
    existing = state.relationship_store.get(rel_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    state.relationship_store.delete(rel_id)
    return {"deleted": True}
