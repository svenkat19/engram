"""FTS5 full-text search operations."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from engram.models.base import EntityType


@dataclass
class FTSResult:
    entity_id: str
    rank: float


class FTSStore:
    """Full-text search using SQLite FTS5."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def search(
        self,
        query: str,
        entity_types: list[EntityType] | None = None,
        project: str | None = None,
        limit: int = 50,
    ) -> list[FTSResult]:
        fts_query = _sanitize_fts_query(query)
        if not fts_query:
            return []

        clauses = ["entities_fts MATCH ?"]
        params: list[str | int] = [fts_query]

        if entity_types:
            placeholders = ",".join("?" for _ in entity_types)
            clauses.append(f"e.entity_type IN ({placeholders})")
            params.extend(t.value for t in entity_types)

        if project:
            clauses.append("e.project = ?")
            params.append(project)

        where = " AND ".join(clauses)
        sql = (
            f"SELECT e.id, entities_fts.rank "
            f"FROM entities_fts "
            f"JOIN entities e ON e.rowid = entities_fts.rowid "
            f"WHERE {where} AND e.status != 'deleted' "
            f"ORDER BY entities_fts.rank "
            f"LIMIT ?"
        )
        params.append(limit)

        rows = self.conn.execute(sql, params).fetchall()
        return [FTSResult(entity_id=row[0], rank=row[1]) for row in rows]

    def rebuild(self) -> None:
        self.conn.execute("INSERT INTO entities_fts(entities_fts) VALUES('rebuild')")


def _sanitize_fts_query(query: str) -> str:
    cleaned = query.replace('"', "").replace("'", "").strip()
    if not cleaned:
        return ""
    words = cleaned.split()
    return " ".join(f'"{w}"' for w in words if w)
