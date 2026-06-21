from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    event_type: str
    source: str
    source_id: str | None = None
    timestamp: datetime
    payload: dict
    project: str | None = None
    actor: str | None = None


class Event(BaseModel):
    id: str
    event_type: str
    source: str
    source_id: str | None = None
    timestamp: datetime
    ingested_at: datetime
    payload: dict
    project: str | None = None
    actor: str | None = None
    checksum: str
    processed: bool = False

    model_config = ConfigDict(from_attributes=True)


class EventFilter(BaseModel):
    event_type: str | None = None
    source: str | None = None
    project: str | None = None
    after: datetime | None = None
    before: datetime | None = None
    processed: bool | None = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
