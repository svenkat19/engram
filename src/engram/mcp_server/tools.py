from __future__ import annotations

from engram.mcp_server.server import mcp, _init, _stores
from engram.models.base import EntityType, ProvenanceAction, RelationType
from engram.models.entities import EntityCreate, EntityFilter
from engram.models.provenance import ProvenanceCreate
from engram.models.relationships import RelationshipCreate
from engram.models.search import SearchQuery


@mcp.tool()
def remember(
    content: str,
    entity_type: str = "snippet",
    title: str | None = None,
    project: str | None = None,
    tags: list[str] | None = None,
    related_files: list[str] | None = None,
    importance: float = 0.5,
) -> dict:
    """Store knowledge in engram's memory. Use for architecture decisions, bug context, design rationale, failed attempts, or any engineering knowledge worth preserving."""
    _init()
    if title is None:
        title = content[:80]
    entity = _stores["entity_store"].create(
        EntityCreate(
            entity_type=EntityType(entity_type),
            title=title,
            content=content,
            project=project,
            tags=tags or [],
            files=related_files or [],
            importance=importance,
        )
    )
    _stores["pipeline"].index_entity(entity)
    return entity.model_dump(mode="json")


@mcp.tool()
def recall(
    query: str,
    entity_types: list[str] | None = None,
    project: str | None = None,
    limit: int = 10,
    min_importance: float = 0.0,
) -> list[dict]:
    """Search engram's memory for relevant knowledge. Returns semantically similar memories ranked by relevance and importance."""
    _init()
    search_query = SearchQuery(
        query=query,
        entity_types=[EntityType(t) for t in entity_types] if entity_types else None,
        project=project,
        limit=limit,
        min_importance=min_importance,
    )
    response = _stores["hybrid_search"].search(search_query)
    return [
        {**r.entity.model_dump(mode="json"), "score": r.score}
        for r in response.results
    ]


@mcp.tool()
def recall_about_file(file_path: str, limit: int = 10) -> list[dict]:
    """Find all knowledge related to a specific file."""
    _init()
    entities = _stores["entity_store"].list(
        EntityFilter(file_path=file_path, limit=limit)
    )
    return [e.model_dump(mode="json") for e in entities]


@mcp.tool()
def record_decision(
    title: str,
    context: str,
    decision: str,
    consequences: list[str] | None = None,
    alternatives: list[dict] | None = None,
    related_files: list[str] | None = None,
) -> dict:
    """Record an architecture or design decision (ADR). High-importance memory that persists long-term."""
    _init()
    entity = _stores["entity_store"].create(
        EntityCreate(
            entity_type=EntityType.DECISION,
            title=title,
            content=decision,
            properties={
                "context": context,
                "decision": decision,
                "consequences": consequences or [],
                "alternatives": alternatives or [],
            },
            files=related_files or [],
            importance=0.9,
            confidence=0.8,
        )
    )
    _stores["pipeline"].index_entity(entity)
    return entity.model_dump(mode="json")


@mcp.tool()
def record_failed_attempt(
    what_was_tried: str,
    why_it_failed: str,
    lessons_learned: str,
    related_files: list[str] | None = None,
) -> dict:
    """Record something that was tried and didn't work. Prevents other developers or AI agents from repeating mistakes."""
    _init()
    entity = _stores["entity_store"].create(
        EntityCreate(
            entity_type=EntityType.FAILED_ATTEMPT,
            title=what_was_tried[:80],
            content=f"{what_was_tried}\n\nWhy it failed: {why_it_failed}\n\nLessons learned: {lessons_learned}",
            properties={
                "what_was_tried": what_was_tried,
                "why_it_failed": why_it_failed,
                "lessons_learned": lessons_learned,
            },
            files=related_files or [],
            importance=0.8,
        )
    )
    _stores["pipeline"].index_entity(entity)
    return entity.model_dump(mode="json")


@mcp.tool()
def get_context(
    file_paths: list[str] | None = None,
    project: str | None = None,
) -> dict:
    """Get a comprehensive context bundle: recent decisions, active bugs, and relevant knowledge for the given files or project. Call at the start of a coding session."""
    _init()
    store = _stores["entity_store"]

    recent_decisions = store.list(
        EntityFilter(
            entity_type=EntityType.DECISION,
            project=project,
            limit=10,
        )
    )
    recent_bugs = store.list(
        EntityFilter(
            entity_type=EntityType.BUG_REPORT,
            project=project,
            limit=10,
        )
    )
    file_knowledge: list[dict] = []
    if file_paths:
        for fp in file_paths:
            entities = store.list(EntityFilter(file_path=fp, limit=5))
            file_knowledge.extend(e.model_dump(mode="json") for e in entities)

    return {
        "recent_decisions": [e.model_dump(mode="json") for e in recent_decisions],
        "recent_bugs": [e.model_dump(mode="json") for e in recent_bugs],
        "file_knowledge": file_knowledge,
    }


@mcp.tool()
def get_entity_history(entity_id: str) -> dict:
    """Get the full provenance chain for an entity."""
    _init()
    records = _stores["provenance_store"].get_for_entity(entity_id)
    return {
        "entity_id": entity_id,
        "history": [r.model_dump(mode="json") for r in records],
    }


@mcp.tool()
def link_entities(
    source_id: str,
    target_id: str,
    relation_type: str = "related_to",
    weight: float = 1.0,
) -> dict:
    """Create a relationship between two entities in the knowledge graph."""
    _init()
    rel = _stores["relationship_store"].create(
        RelationshipCreate(
            source_id=source_id,
            target_id=target_id,
            relation_type=RelationType(relation_type),
            weight=weight,
        )
    )
    return rel.model_dump(mode="json")


@mcp.tool()
def find_contradictions(
    entity_id: str | None = None,
    project: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Find entities that may contradict each other — competing decisions, superseded knowledge, or potential updates."""
    _init()
    from engram.quality.conflict import detect_conflicts

    if entity_id:
        entity = _stores["entity_store"].get(entity_id)
        if entity is None:
            return [{"error": f"Entity {entity_id} not found"}]
        query = SearchQuery(query=entity.title, project=project, limit=limit)
        response = _stores["hybrid_search"].search(query)
        similar = [(r.entity, r.score) for r in response.results if r.entity.id != entity_id]
        conflicts = detect_conflicts(entity, similar, _stores["relationship_store"])
        return [
            {
                "entity_a": c.entity_a.model_dump(mode="json"),
                "entity_b": c.entity_b.model_dump(mode="json"),
                "conflict_type": c.conflict_type,
                "confidence": c.confidence,
            }
            for c in conflicts
        ]

    decisions = _stores["entity_store"].list(
        EntityFilter(entity_type=EntityType.DECISION, project=project, limit=limit)
    )
    all_conflicts = []
    for decision in decisions:
        query = SearchQuery(query=decision.title, project=project, limit=5)
        response = _stores["hybrid_search"].search(query)
        similar = [(r.entity, r.score) for r in response.results if r.entity.id != decision.id]
        conflicts = detect_conflicts(decision, similar, _stores["relationship_store"])
        all_conflicts.extend(
            {
                "entity_a": c.entity_a.model_dump(mode="json"),
                "entity_b": c.entity_b.model_dump(mode="json"),
                "conflict_type": c.conflict_type,
                "confidence": c.confidence,
            }
            for c in conflicts
        )
    return all_conflicts


@mcp.tool()
def run_quality_check() -> dict:
    """Run the memory quality engine: recompute importance scores, apply temporal decay, and archive stale memories."""
    _init()
    from engram.quality.compaction import run_compaction

    return run_compaction(
        conn=_stores["entity_store"].conn,
        entity_store=_stores["entity_store"],
        relationship_store=_stores["relationship_store"],
    )
