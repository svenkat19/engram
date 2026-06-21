"""Provenance and snapshot tracking."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from ulid import ULID

from engram.models.base import ProvenanceAction
from engram.models.provenance import EntitySnapshot, ProvenanceCreate, ProvenanceRecord


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _row_to_record(row: sqlite3.Row) -> ProvenanceRecord:
    return ProvenanceRecord(
        id=row["id"],
        entity_id=row["entity_id"],
        action=ProvenanceAction(row["action"]),
        actor=row["actor"],
        timestamp=_parse_dt(row["timestamp"]),
        source_event_id=row["source_event_id"],
        related_entity_id=row["related_entity_id"],
        details=json.loads(row["details"]),
        confidence_delta=row["confidence_delta"],
    )


def _row_to_snapshot(row: sqlite3.Row) -> EntitySnapshot:
    return EntitySnapshot(
        id=row["id"],
        entity_id=row["entity_id"],
        snapshot_at=_parse_dt(row["snapshot_at"]),
        title=row["title"],
        content=row["content"],
        properties=json.loads(row["properties"]) if row["properties"] else {},
        status=row["status"],
        importance=row["importance"],
        confidence=row["confidence"],
        provenance_id=row["provenance_id"],
    )


class ProvenanceStore:
    """Track provenance and entity snapshots."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def record(self, prov: ProvenanceCreate) -> ProvenanceRecord:
        prov_id = str(ULID())
        now = _now_iso()
        self.conn.execute(
            "INSERT INTO provenance (id, entity_id, action, actor, timestamp, "
            "source_event_id, related_entity_id, details, confidence_delta) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                prov_id,
                prov.entity_id,
                prov.action.value,
                prov.actor,
                now,
                prov.source_event_id,
                prov.related_entity_id,
                json.dumps(prov.details),
                prov.confidence_delta,
            ),
        )
        return self.get(prov_id)  # type: ignore[return-value]

    def get(self, prov_id: str) -> ProvenanceRecord | None:
        row = self.conn.execute(
            "SELECT * FROM provenance WHERE id = ?", (prov_id,)
        ).fetchone()
        return _row_to_record(row) if row else None

    def get_for_entity(self, entity_id: str) -> list[ProvenanceRecord]:
        rows = self.conn.execute(
            "SELECT * FROM provenance WHERE entity_id = ? ORDER BY timestamp ASC",
            (entity_id,),
        ).fetchall()
        return [_row_to_record(r) for r in rows]

    def create_snapshot(self, entity_id: str, provenance_id: str | None = None) -> EntitySnapshot:
        entity = self.conn.execute(
            "SELECT * FROM entities WHERE id = ?", (entity_id,)
        ).fetchone()
        if entity is None:
            raise ValueError(f"Entity {entity_id} not found")

        snap_id = str(ULID())
        self.conn.execute(
            "INSERT INTO entity_snapshots (id, entity_id, title, content, "
            "properties, status, importance, confidence, provenance_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                snap_id,
                entity_id,
                entity["title"],
                entity["content"],
                entity["properties"],
                entity["status"],
                entity["importance"],
                entity["confidence"],
                provenance_id,
            ),
        )
        return self.get_snapshot(snap_id)  # type: ignore[return-value]

    def get_snapshot(self, snap_id: str) -> EntitySnapshot | None:
        row = self.conn.execute(
            "SELECT * FROM entity_snapshots WHERE id = ?", (snap_id,)
        ).fetchone()
        return _row_to_snapshot(row) if row else None

    def get_snapshots(self, entity_id: str) -> list[EntitySnapshot]:
        rows = self.conn.execute(
            "SELECT * FROM entity_snapshots WHERE entity_id = ? ORDER BY snapshot_at ASC",
            (entity_id,),
        ).fetchall()
        return [_row_to_snapshot(r) for r in rows]

    def get_snapshot_at(self, entity_id: str, at: datetime) -> EntitySnapshot | None:
        row = self.conn.execute(
            "SELECT * FROM entity_snapshots WHERE entity_id = ? AND snapshot_at <= ? "
            "ORDER BY snapshot_at DESC LIMIT 1",
            (entity_id, at.isoformat()),
        ).fetchone()
        return _row_to_snapshot(row) if row else None
