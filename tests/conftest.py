import sqlite3

import pytest

from yonakh.db.engine import _set_pragmas, _load_vec_extension, _read_schema_sql
from yonakh.config import get_settings


@pytest.fixture
def db_conn():
    """In-memory SQLite database with full schema and sqlite-vec if available."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _set_pragmas(conn)
    vec_loaded = _load_vec_extension(conn)
    conn.executescript(_read_schema_sql())
    if vec_loaded:
        dims = get_settings().embedding_dimensions
        conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS entity_embeddings "
            f"USING vec0(entity_id TEXT PRIMARY KEY, embedding float[{dims}])"
        )
    conn.commit()
    yield conn
    conn.close()
