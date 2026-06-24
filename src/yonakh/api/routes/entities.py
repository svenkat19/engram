from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from yonakh.api.deps import AppState, get_state
from yonakh.models.base import EntityStatus, EntityType, ProvenanceAction
from yonakh.models.entities import Entity, EntityCreate, EntityFilter, EntityUpdate
from yonakh.models.provenance import ProvenanceCreate

router = APIRouter(tags=["entities"])


@router.post("/entities", response_model=Entity)
def create_entity(body: EntityCreate, state: AppState = Depends(get_state)):
    entity = state.entity_store.create(body)
    state.pipeline.index_entity(entity)
    state.provenance_store.record(ProvenanceCreate(
        entity_id=entity.id,
        action=ProvenanceAction.CREATED,
        actor=body.created_by or "api",
        source_event_id=body.source_event_id,
    ))
    return entity


@router.get("/entities", response_model=list[Entity])
def list_entities(
    entity_type: EntityType | None = None,
    project: str | None = None,
    status: EntityStatus | None = None,
    min_importance: float | None = None,
    tag: str | None = None,
    file_path: str | None = None,
    limit: int = 50,
    offset: int = 0,
    state: AppState = Depends(get_state),
):
    filt = EntityFilter(
        entity_type=entity_type,
        project=project,
        status=status,
        min_importance=min_importance,
        tag=tag,
        file_path=file_path,
        limit=limit,
        offset=offset,
    )
    return state.entity_store.list(filt)


@router.get("/entities/{entity_id}", response_model=Entity)
def get_entity(entity_id: str, state: AppState = Depends(get_state)):
    entity = state.entity_store.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    state.entity_store.record_access(entity_id)
    return entity


@router.put("/entities/{entity_id}", response_model=Entity)
def update_entity(
    entity_id: str, body: EntityUpdate, state: AppState = Depends(get_state)
):
    existing = state.entity_store.get(entity_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    prov = state.provenance_store.record(ProvenanceCreate(
        entity_id=entity_id,
        action=ProvenanceAction.UPDATED,
        actor="api",
        details=body.model_dump(exclude_none=True),
    ))
    state.provenance_store.create_snapshot(entity_id, provenance_id=prov.id)
    entity = state.entity_store.update(entity_id, body)
    if body.title is not None or body.content is not None:
        state.pipeline.index_entity(entity)
    return entity


@router.delete("/entities/{entity_id}")
def delete_entity(entity_id: str, state: AppState = Depends(get_state)):
    existing = state.entity_store.get(entity_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    state.provenance_store.record(ProvenanceCreate(
        entity_id=entity_id,
        action=ProvenanceAction.UPDATED,
        actor="api",
        details={"action": "soft_delete"},
    ))
    state.entity_store.delete(entity_id)
    return {"deleted": True}


@router.get("/entities/{entity_id}/provenance")
def get_entity_provenance(entity_id: str, state: AppState = Depends(get_state)):
    existing = state.entity_store.get(entity_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return state.provenance_store.get_for_entity(entity_id)


@router.get("/entities/{entity_id}/snapshots")
def get_entity_snapshots(entity_id: str, state: AppState = Depends(get_state)):
    existing = state.entity_store.get(entity_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return state.provenance_store.get_snapshots(entity_id)


@router.get("/entities/{entity_id}/snapshot-at")
def get_entity_snapshot_at(
    entity_id: str,
    at: str = Query(..., description="ISO 8601 datetime"),
    state: AppState = Depends(get_state),
):
    try:
        at_dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")
    snapshot = state.provenance_store.get_snapshot_at(entity_id, at_dt)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="No snapshot found at that time")
    return snapshot
