from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from engram.models.base import EntityStatus, EntityType


class EntityCreate(BaseModel):
    entity_type: EntityType
    title: str
    content: str | None = None
    properties: dict = Field(default_factory=dict)
    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    created_by: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    source_event_id: str | None = None


class EntityUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    properties: dict | None = None
    status: EntityStatus | None = None
    tags: list[str] | None = None
    files: list[str] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    importance: float | None = Field(default=None, ge=0.0, le=1.0)


class Entity(BaseModel):
    id: str
    entity_type: EntityType
    title: str
    content: str | None = None
    properties: dict = Field(default_factory=dict)
    project: str | None = None
    status: EntityStatus = EntityStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    importance: float = 0.5
    access_count: int = 0
    last_accessed: datetime | None = None
    decay_factor: float = 1.0
    source_event_id: str | None = None
    created_by: str | None = None
    confidence: float = 1.0
    tags: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class EntityFilter(BaseModel):
    entity_type: EntityType | None = None
    entity_types: list[EntityType] | None = None
    project: str | None = None
    status: EntityStatus | None = None
    min_importance: float | None = Field(default=None, ge=0.0, le=1.0)
    created_by: str | None = None
    tag: str | None = None
    file_path: str | None = None
    after: datetime | None = None
    before: datetime | None = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
