from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

from ulid import ULID

from yonakh.db import crypto_service
from yonakh.models.events import Event, EventCreate, EventFilter


def _row_to_event(row: sqlite3.Row) -> Event:
    return Event(
        id=row["id"],
        event_type=row["event_type"],
        source=row["source"],
        source_id=row["source_id"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        ingested_at=datetime.fromisoformat(row["ingested_at"]),
        payload=json.loads(crypto_service.decrypt(row["payload"]) or "{}"),
        project=row["project"],
        actor=row["actor"],
        checksum=row["checksum"],
        processed=bool(row["processed"]),
    )


class EventStore:
    """Append-only event store backed by SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.row_factory = sqlite3.Row

    def create(self, event: EventCreate) -> Event:
        event_id = str(ULID())
        now = datetime.now(timezone.utc)
        payload_str = json.dumps(event.payload, sort_keys=True)
        checksum = hashlib.sha256(
            f"{event.event_type}{event.source}{event.source_id}{payload_str}".encode()
        ).hexdigest()
        stored_payload = crypto_service.encrypt(payload_str) or payload_str
        timestamp_str = event.timestamp.isoformat()
        ingested_str = now.isoformat()
        try:
            self._conn.execute(
                """INSERT INTO events
                   (id, event_type, source, source_id, timestamp, ingested_at,
                    payload, project, actor, checksum, processed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (
                    event_id,
                    event.event_type,
                    event.source,
                    event.source_id,
                    timestamp_str,
                    ingested_str,
                    stored_payload,
                    event.project,
                    event.actor,
                    checksum,
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            row = self._conn.execute(
                "SELECT * FROM events WHERE checksum = ?", (checksum,)
            ).fetchone()
            if row is not None:
                return _row_to_event(row)
            raise
        return Event(
            id=event_id,
            event_type=event.event_type,
            source=event.source,
            source_id=event.source_id,
            timestamp=event.timestamp,
            ingested_at=now,
            payload=event.payload,
            project=event.project,
            actor=event.actor,
            checksum=checksum,
            processed=False,
        )

    def get(self, event_id: str) -> Event | None:
        row = self._conn.execute(
            "SELECT * FROM events WHERE id = ?", (event_id,)
        ).fetchone()
        return _row_to_event(row) if row else None

    def list(self, filter: EventFilter) -> list[Event]:
        clauses: list[str] = []
        params: list[object] = []
        if filter.event_type is not None:
            clauses.append("event_type = ?")
            params.append(filter.event_type)
        if filter.source is not None:
            clauses.append("source = ?")
            params.append(filter.source)
        if filter.project is not None:
            clauses.append("project = ?")
            params.append(filter.project)
        if filter.after is not None:
            clauses.append("timestamp > ?")
            params.append(filter.after.isoformat())
        if filter.before is not None:
            clauses.append("timestamp < ?")
            params.append(filter.before.isoformat())
        if filter.processed is not None:
            clauses.append("processed = ?")
            params.append(int(filter.processed))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"SELECT * FROM events{where} ORDER BY timestamp ASC LIMIT ? OFFSET ?"
        params.extend([filter.limit, filter.offset])
        rows = self._conn.execute(query, params).fetchall()
        return [_row_to_event(r) for r in rows]

    def mark_processed(self, event_id: str) -> None:
        self._conn.execute(
            "UPDATE events SET processed = 1 WHERE id = ?", (event_id,)
        )
        self._conn.commit()

    def count(self, filter: EventFilter | None = None) -> int:
        clauses: list[str] = []
        params: list[object] = []
        if filter is not None:
            if filter.event_type is not None:
                clauses.append("event_type = ?")
                params.append(filter.event_type)
            if filter.source is not None:
                clauses.append("source = ?")
                params.append(filter.source)
            if filter.project is not None:
                clauses.append("project = ?")
                params.append(filter.project)
            if filter.after is not None:
                clauses.append("timestamp > ?")
                params.append(filter.after.isoformat())
            if filter.before is not None:
                clauses.append("timestamp < ?")
                params.append(filter.before.isoformat())
            if filter.processed is not None:
                clauses.append("processed = ?")
                params.append(int(filter.processed))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        row = self._conn.execute(
            f"SELECT COUNT(*) FROM events{where}", params
        ).fetchone()
        return row[0]
