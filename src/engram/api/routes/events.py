from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from engram.api.deps import AppState, get_state
from engram.models.events import Event, EventCreate, EventFilter

router = APIRouter(tags=["events"])


@router.post("/events", response_model=Event)
def create_event(body: EventCreate, state: AppState = Depends(get_state)):
    event = state.event_store.create(body)
    return event


@router.get("/events", response_model=list[Event])
def list_events(
    event_type: str | None = None,
    source: str | None = None,
    project: str | None = None,
    limit: int = 50,
    offset: int = 0,
    state: AppState = Depends(get_state),
):
    filt = EventFilter(
        event_type=event_type,
        source=source,
        project=project,
        limit=limit,
        offset=offset,
    )
    return state.event_store.list(filt)


@router.get("/events/{event_id}", response_model=Event)
def get_event(event_id: str, state: AppState = Depends(get_state)):
    event = state.event_store.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
