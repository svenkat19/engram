from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from engram.api.deps import AppState, get_state
from engram.ingest.registry import get_default_registry

router = APIRouter(tags=["ingest"])

_registry = None


def _get_registry():
    global _registry
    if _registry is None:
        _registry = get_default_registry()
    return _registry


class IngestRequest(BaseModel):
    plugin: str
    params: dict = Field(default_factory=dict)


@router.post("/ingest")
def run_ingest(body: IngestRequest, state: AppState = Depends(get_state)):
    registry = _get_registry()
    plugin = registry.get(body.plugin)
    if plugin is None:
        available = [p.name() for p in registry.list()]
        raise HTTPException(
            status_code=400,
            detail=f"Unknown plugin '{body.plugin}'. Available: {available}",
        )

    result = plugin.ingest(
        event_store=state.event_store,
        entity_store=state.entity_store,
        **body.params,
    )
    return {
        "plugin": body.plugin,
        "events_created": result.events_created,
        "entities_created": result.entities_created,
        "errors": result.errors,
    }


@router.get("/ingest/plugins")
def list_plugins():
    registry = _get_registry()
    return [
        {"name": p.name(), "description": p.description()}
        for p in registry.list()
    ]
