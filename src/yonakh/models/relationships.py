from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from yonakh.models.base import RelationType


class RelationshipCreate(BaseModel):
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: dict = Field(default_factory=dict)
    weight: float = Field(default=1.0, ge=0.0)
    source_event_id: str | None = None


class Relationship(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: dict = Field(default_factory=dict)
    weight: float = 1.0
    created_at: datetime
    source_event_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RelationshipFilter(BaseModel):
    source_id: str | None = None
    target_id: str | None = None
    relation_type: RelationType | None = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
