from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from engram.models.base import ProvenanceAction


class ProvenanceCreate(BaseModel):
    entity_id: str
    action: ProvenanceAction
    actor: str
    source_event_id: str | None = None
    related_entity_id: str | None = None
    details: dict = Field(default_factory=dict)
    confidence_delta: float = 0.0


class ProvenanceRecord(BaseModel):
    id: str
    entity_id: str
    action: ProvenanceAction
    actor: str
    timestamp: datetime
    source_event_id: str | None = None
    related_entity_id: str | None = None
    details: dict = Field(default_factory=dict)
    confidence_delta: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class EntitySnapshot(BaseModel):
    id: str
    entity_id: str
    snapshot_at: datetime
    title: str
    content: str | None = None
    properties: dict = Field(default_factory=dict)
    status: str
    importance: float
    confidence: float
    provenance_id: str | None = None

    model_config = ConfigDict(from_attributes=True)
