"""sqlite-vec vector store operations."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass


@dataclass
class VectorResult:
    entity_id: str
    distance: float
    similarity: float


class VectorStore:
    """Manages entity embeddings via sqlite-vec."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self._available = self._check_available()

    def _check_available(self) -> bool:
        try:
            self.conn.execute(
                "SELECT * FROM entity_embeddings LIMIT 0"
            )
            return True
        except sqlite3.OperationalError:
            return False

    @property
    def available(self) -> bool:
        return self._available

    def upsert(self, entity_id: str, embedding: list[float]) -> None:
        if not self._available:
            return
        vec_json = json.dumps(embedding)
        self.conn.execute(
            "INSERT OR REPLACE INTO entity_embeddings (entity_id, embedding) "
            "VALUES (?, ?)",
            (entity_id, vec_json),
        )

    def batch_upsert(self, items: list[tuple[str, list[float]]]) -> None:
        if not self._available:
            return
        for entity_id, embedding in items:
            self.upsert(entity_id, embedding)

    def search(
        self,
        embedding: list[float],
        limit: int = 20,
    ) -> list[VectorResult]:
        if not self._available:
            return []
        vec_json = json.dumps(embedding)
        rows = self.conn.execute(
            "SELECT entity_id, distance "
            "FROM entity_embeddings "
            "WHERE embedding MATCH ? "
            "ORDER BY distance "
            "LIMIT ?",
            (vec_json, limit),
        ).fetchall()

        results = []
        for row in rows:
            distance = row[1] if isinstance(row[1], float) else float(row[1])
            similarity = 1.0 / (1.0 + distance)
            results.append(VectorResult(
                entity_id=row[0],
                distance=distance,
                similarity=similarity,
            ))
        return results

    def delete(self, entity_id: str) -> None:
        if not self._available:
            return
        self.conn.execute(
            "DELETE FROM entity_embeddings WHERE entity_id = ?",
            (entity_id,),
        )

    def count(self) -> int:
        if not self._available:
            return 0
        row = self.conn.execute(
            "SELECT COUNT(*) FROM entity_embeddings"
        ).fetchone()
        return row[0] if row else 0
