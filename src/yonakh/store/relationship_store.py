"""CRUD for knowledge graph edges."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from ulid import ULID

from yonakh.models.base import RelationType
from yonakh.models.relationships import Relationship, RelationshipCreate, RelationshipFilter


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_dt(s: str | None) -> datetime | None:
    if s is None:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _row_to_relationship(row: sqlite3.Row) -> Relationship:
    return Relationship(
        id=row["id"],
        source_id=row["source_id"],
        target_id=row["target_id"],
        relation_type=RelationType(row["relation_type"]),
        properties=json.loads(row["properties"]),
        weight=row["weight"],
        created_at=_parse_dt(row["created_at"]),  # type: ignore[arg-type]
        source_event_id=row["source_event_id"],
    )


class RelationshipStore:
    """Manages knowledge graph edges in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, rel: RelationshipCreate) -> Relationship:
        rel_id = str(ULID())
        now = _now_iso()
        self.conn.execute(
            "INSERT INTO relationships (id, source_id, target_id, relation_type, "
            "properties, weight, created_at, source_event_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rel_id,
                rel.source_id,
                rel.target_id,
                rel.relation_type.value,
                json.dumps(rel.properties),
                rel.weight,
                now,
                rel.source_event_id,
            ),
        )
        return self.get(rel_id)  # type: ignore[return-value]

    def get(self, rel_id: str) -> Relationship | None:
        row = self.conn.execute(
            "SELECT * FROM relationships WHERE id = ?", (rel_id,)
        ).fetchone()
        return _row_to_relationship(row) if row else None

    def list(self, filter: RelationshipFilter) -> list[Relationship]:
        clauses: list[str] = []
        params: list[str | float] = []

        if filter.source_id:
            clauses.append("source_id = ?")
            params.append(filter.source_id)
        if filter.target_id:
            clauses.append("target_id = ?")
            params.append(filter.target_id)
        if filter.relation_type:
            clauses.append("relation_type = ?")
            params.append(filter.relation_type.value)

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM relationships{where} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([filter.limit, filter.offset])

        rows = self.conn.execute(sql, params).fetchall()
        return [_row_to_relationship(r) for r in rows]

    def get_for_entity(
        self, entity_id: str, relation_type: RelationType | None = None
    ) -> list[Relationship]:
        if relation_type:
            rows = self.conn.execute(
                "SELECT * FROM relationships "
                "WHERE (source_id = ? OR target_id = ?) AND relation_type = ? "
                "ORDER BY created_at DESC",
                (entity_id, entity_id, relation_type.value),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM relationships "
                "WHERE source_id = ? OR target_id = ? "
                "ORDER BY created_at DESC",
                (entity_id, entity_id),
            ).fetchall()
        return [_row_to_relationship(r) for r in rows]

    def get_neighbors(self, entity_id: str, depth: int = 1) -> list[str]:
        visited: set[str] = {entity_id}
        frontier: set[str] = {entity_id}

        for _ in range(depth):
            next_frontier: set[str] = set()
            for node_id in frontier:
                rows = self.conn.execute(
                    "SELECT source_id, target_id FROM relationships "
                    "WHERE source_id = ? OR target_id = ?",
                    (node_id, node_id),
                ).fetchall()
                for row in rows:
                    for col in ("source_id", "target_id"):
                        nid = row[col]
                        if nid not in visited:
                            visited.add(nid)
                            next_frontier.add(nid)
            frontier = next_frontier
            if not frontier:
                break

        visited.discard(entity_id)
        return list(visited)

    def delete(self, rel_id: str) -> bool:
        cursor = self.conn.execute(
            "DELETE FROM relationships WHERE id = ?", (rel_id,)
        )
        return cursor.rowcount > 0

    def count(self, entity_id: str | None = None) -> int:
        if entity_id:
            row = self.conn.execute(
                "SELECT COUNT(*) FROM relationships WHERE source_id = ? OR target_id = ?",
                (entity_id, entity_id),
            ).fetchone()
        else:
            row = self.conn.execute("SELECT COUNT(*) FROM relationships").fetchone()
        return row[0] if row else 0
