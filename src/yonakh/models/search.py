from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from yonakh.models.base import EntityType
from yonakh.models.entities import Entity
from yonakh.models.relationships import Relationship


class SearchQuery(BaseModel):
    query: str
    entity_types: list[EntityType] | None = None
    project: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)
    after: datetime | None = None
    before: datetime | None = None
    include_relationships: bool = False
    boost_recent: bool = True


class SearchResult(BaseModel):
    entity: Entity
    score: float
    relationships: list[Relationship] = Field(default_factory=list)


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    query: str
    duration_ms: float
