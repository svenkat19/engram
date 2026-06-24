"""Simple schema version tracking."""

from __future__ import annotations

import logging
import sqlite3

from yonakh.db.engine import _read_schema_sql

logger = logging.getLogger(__name__)

CURRENT_VERSION = 1


def get_current_version(conn: sqlite3.Connection) -> int:
    """Return the current schema version, or 0 if uninitialized."""
    try:
        row = conn.execute(
            "SELECT MAX(version) FROM schema_version"
        ).fetchone()
        return row[0] if row and row[0] is not None else 0
    except sqlite3.OperationalError:
        return 0


def apply_schema(conn: sqlite3.Connection) -> None:
    """Apply schema.sql and record version 1 if not already applied."""
    version = get_current_version(conn)
    if version >= CURRENT_VERSION:
        logger.debug("Schema already at version %d, skipping", version)
        return

    conn.executescript(_read_schema_sql())
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version, description) "
        "VALUES (?, ?)",
        (CURRENT_VERSION, "Initial schema"),
    )
    conn.commit()
    logger.info("Schema applied: version %d", CURRENT_VERSION)
