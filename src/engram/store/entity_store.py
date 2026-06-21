from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from ulid import ULID

from engram.db import crypto_service
from engram.models.base import EntityStatus, EntityType
from engram.models.entities import Entity, EntityCreate, EntityFilter, EntityUpdate


def _row_to_entity(row: sqlite3.Row, tags: list[str], files: list[str]) -> Entity:
    return Entity(
        id=row["id"],
        entity_type=row["entity_type"],
        title=row["title"],
        content=crypto_service.decrypt(row["content"]),
        properties=json.loads(row["properties"]) if row["properties"] else {},
        project=row["project"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        importance=row["importance"],
        access_count=row["access_count"],
        last_accessed=(
            datetime.fromisoformat(row["last_accessed"])
            if row["last_accessed"]
            else None
        ),
        decay_factor=row["decay_factor"],
        source_event_id=row["source_event_id"],
        created_by=row["created_by"],
        confidence=row["confidence"],
        tags=tags,
        files=files,
    )


class EntityStore:
    """CRUD operations for knowledge graph entities backed by SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    def _fetch_tags(self, entity_id: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT tag FROM tags WHERE entity_id = ? ORDER BY tag",
            (entity_id,),
        ).fetchall()
        return [r["tag"] for r in rows]

    def _fetch_files(self, entity_id: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT file_path FROM entity_files WHERE entity_id = ? ORDER BY file_path",
            (entity_id,),
        ).fetchall()
        return [r["file_path"] for r in rows]

    def _insert_tags(self, entity_id: str, tags: list[str]) -> None:
        if tags:
            self.conn.executemany(
                "INSERT INTO tags (entity_id, tag) VALUES (?, ?)",
                [(entity_id, t) for t in tags],
            )

    def _insert_files(self, entity_id: str, files: list[str]) -> None:
        if files:
            self.conn.executemany(
                "INSERT INTO entity_files (entity_id, file_path) VALUES (?, ?)",
                [(entity_id, f) for f in files],
            )

    def create(self, entity: EntityCreate) -> Entity:
        entity_id = str(ULID())
        now = datetime.now(timezone.utc).isoformat()
        stored_content = crypto_service.encrypt(entity.content)
        self.conn.execute(
            """INSERT INTO entities
               (id, entity_type, title, content, properties, project, status,
                created_at, updated_at, importance, access_count, last_accessed,
                decay_factor, source_event_id, created_by, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entity_id,
                entity.entity_type.value,
                entity.title,
                stored_content,
                json.dumps(entity.properties),
                entity.project,
                EntityStatus.ACTIVE.value,
                now,
                now,
                entity.importance,
                0,
                None,
                1.0,
                entity.source_event_id,
                entity.created_by,
                entity.confidence,
            ),
        )
        self._insert_tags(entity_id, entity.tags)
        self._insert_files(entity_id, entity.files)
        self.conn.commit()
        return self.get(entity_id)  # type: ignore[return-value]

    def get(self, entity_id: str) -> Entity | None:
        row = self.conn.execute(
            "SELECT * FROM entities WHERE id = ?", (entity_id,)
        ).fetchone()
        if row is None:
            return None
        tags = self._fetch_tags(entity_id)
        files = self._fetch_files(entity_id)
        return _row_to_entity(row, tags, files)

    def update(self, entity_id: str, update: EntityUpdate) -> Entity | None:
        existing = self.get(entity_id)
        if existing is None:
            return None

        sets: list[str] = []
        params: list[object] = []
        now = datetime.now(timezone.utc).isoformat()

        if update.title is not None:
            sets.append("title = ?")
            params.append(update.title)
        if update.content is not None:
            sets.append("content = ?")
            params.append(crypto_service.encrypt(update.content))
        if update.properties is not None:
            sets.append("properties = ?")
            params.append(json.dumps(update.properties))
        if update.status is not None:
            sets.append("status = ?")
            params.append(update.status.value)
        if update.confidence is not None:
            sets.append("confidence = ?")
            params.append(update.confidence)
        if update.importance is not None:
            sets.append("importance = ?")
            params.append(update.importance)

        sets.append("updated_at = ?")
        params.append(now)
        params.append(entity_id)

        self.conn.execute(
            f"UPDATE entities SET {', '.join(sets)} WHERE id = ?", params
        )

        if update.tags is not None:
            self.conn.execute("DELETE FROM tags WHERE entity_id = ?", (entity_id,))
            self._insert_tags(entity_id, update.tags)

        if update.files is not None:
            self.conn.execute(
                "DELETE FROM entity_files WHERE entity_id = ?", (entity_id,)
            )
            self._insert_files(entity_id, update.files)

        self.conn.commit()
        return self.get(entity_id)

    def delete(self, entity_id: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.conn.execute(
            "UPDATE entities SET status = ?, updated_at = ? WHERE id = ?",
            (EntityStatus.DELETED.value, now, entity_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def list(self, filter: EntityFilter) -> list[Entity]:
        wheres, params, joins = self._build_filter(filter)
        join_clause = " ".join(joins)
        where_clause = f"WHERE {' AND '.join(wheres)}" if wheres else ""
        query = (
            f"SELECT DISTINCT e.* FROM entities e {join_clause} "
            f"{where_clause} ORDER BY e.created_at DESC LIMIT ? OFFSET ?"
        )
        params.extend([filter.limit, filter.offset])
        rows = self.conn.execute(query, params).fetchall()
        results: list[Entity] = []
        for row in rows:
            eid = row["id"]
            tags = self._fetch_tags(eid)
            files = self._fetch_files(eid)
            results.append(_row_to_entity(row, tags, files))
        return results

    def count(self, filter: EntityFilter | None = None) -> int:
        if filter is None:
            row = self.conn.execute("SELECT COUNT(*) AS cnt FROM entities").fetchone()
            return row["cnt"]  # type: ignore[index]
        wheres, params, joins = self._build_filter(filter)
        join_clause = " ".join(joins)
        where_clause = f"WHERE {' AND '.join(wheres)}" if wheres else ""
        query = (
            f"SELECT COUNT(DISTINCT e.id) AS cnt FROM entities e "
            f"{join_clause} {where_clause}"
        )
        row = self.conn.execute(query, params).fetchone()
        return row["cnt"]  # type: ignore[index]

    def record_access(self, entity_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE entities SET access_count = access_count + 1, last_accessed = ? "
            "WHERE id = ?",
            (now, entity_id),
        )
        self.conn.commit()

    def find_by_file_paths(
        self,
        paths: list[str],
        exclude_id: str | None = None,
        exclude_types: list[EntityType] | None = None,
    ) -> list[Entity]:
        if not paths:
            return []
        placeholders = ", ".join("?" for _ in paths)
        query = (
            f"SELECT DISTINCT ef.entity_id FROM entity_files ef "
            f"JOIN entities e ON e.id = ef.entity_id "
            f"WHERE ef.file_path IN ({placeholders}) "
            f"AND e.status != ?"
        )
        params: list[object] = [*paths, EntityStatus.DELETED.value]
        if exclude_id is not None:
            query += " AND ef.entity_id != ?"
            params.append(exclude_id)
        if exclude_types:
            type_placeholders = ", ".join("?" for _ in exclude_types)
            query += f" AND e.entity_type NOT IN ({type_placeholders})"
            params.extend(t.value for t in exclude_types)
        rows = self.conn.execute(query, params).fetchall()
        results: list[Entity] = []
        for row in rows:
            entity = self.get(row["entity_id"])
            if entity is not None:
                results.append(entity)
        return results

    def _build_filter(
        self, filter: EntityFilter
    ) -> tuple[list[str], list[object], list[str]]:
        wheres: list[str] = []
        params: list[object] = []
        joins: list[str] = []

        if filter.entity_type is not None:
            wheres.append("e.entity_type = ?")
            params.append(filter.entity_type.value)
        if filter.entity_types is not None:
            placeholders = ", ".join("?" for _ in filter.entity_types)
            wheres.append(f"e.entity_type IN ({placeholders})")
            params.extend(t.value for t in filter.entity_types)
        if filter.project is not None:
            wheres.append("e.project = ?")
            params.append(filter.project)
        if filter.status is not None:
            wheres.append("e.status = ?")
            params.append(filter.status.value)
        if filter.min_importance is not None:
            wheres.append("e.importance >= ?")
            params.append(filter.min_importance)
        if filter.created_by is not None:
            wheres.append("e.created_by = ?")
            params.append(filter.created_by)
        if filter.after is not None:
            wheres.append("e.created_at >= ?")
            params.append(filter.after.isoformat())
        if filter.before is not None:
            wheres.append("e.created_at <= ?")
            params.append(filter.before.isoformat())
        if filter.tag is not None:
            joins.append("JOIN tags t ON t.entity_id = e.id")
            wheres.append("t.tag = ?")
            params.append(filter.tag)
        if filter.file_path is not None:
            joins.append("JOIN entity_files ef ON ef.entity_id = e.id")
            wheres.append("ef.file_path = ?")
            params.append(filter.file_path)

        return wheres, params, joins
