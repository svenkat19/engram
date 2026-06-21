"""SQLite connection factory with WAL mode, sqlite-vec, and FTS5."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path
from typing import Iterator

from engram.config import get_settings

logger = logging.getLogger(__name__)

_VEC_AVAILABLE = False


def get_db_path() -> Path:
    """Return the configured database path, creating parent directories."""
    db_path = get_settings().db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def _set_pragmas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = -64000")
    conn.execute("PRAGMA mmap_size = 268435456")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA foreign_keys = ON")


def _load_vec_extension(conn: sqlite3.Connection) -> bool:
    """Try to load sqlite-vec. Returns True on success."""
    global _VEC_AVAILABLE  # noqa: PLW0603
    try:
        import sqlite_vec  # type: ignore[import-untyped]

        sqlite_vec.load(conn)
        _VEC_AVAILABLE = True
        logger.debug("sqlite-vec extension loaded")
        return True
    except ImportError:
        logger.info("sqlite-vec not installed; vector search disabled")
        return False
    except Exception:
        logger.warning("Failed to load sqlite-vec extension", exc_info=True)
        return False


def _read_schema_sql() -> str:
    return (
        files("engram.db").joinpath("schema.sql").read_text(encoding="utf-8")
    )


def init_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Create and initialise the database, returning the connection."""
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    _set_pragmas(conn)
    _load_vec_extension(conn)

    conn.executescript(_read_schema_sql())

    if _VEC_AVAILABLE:
        dims = get_settings().embedding_dimensions
        conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS entity_embeddings "
            f"USING vec0(entity_id TEXT PRIMARY KEY, embedding float[{dims}])"
        )

    conn.commit()
    logger.info("Database initialised at %s", db_path)
    return conn


@contextmanager
def get_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a configured SQLite connection with Row factory."""
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    _set_pragmas(conn)
    _load_vec_extension(conn)

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
