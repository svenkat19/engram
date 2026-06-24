from yonakh.models.base import EntityType
from yonakh.models.entities import EntityCreate
from yonakh.store.entity_store import EntityStore
from yonakh.store.fts_store import FTSStore


def _seed(db_conn):
    store = EntityStore(db_conn)
    store.create(EntityCreate(
        entity_type=EntityType.DECISION,
        title="Use SQLite for storage",
        content="SQLite is local-first and has great performance for single-user workloads.",
        project="yonakh",
    ))
    store.create(EntityCreate(
        entity_type=EntityType.DECISION,
        title="Use React for dashboard",
        content="React ecosystem is mature and has good graph visualization libraries.",
        project="yonakh",
    ))
    store.create(EntityCreate(
        entity_type=EntityType.BUG_REPORT,
        title="SQLite WAL mode not enabled",
        content="Concurrent reads are blocking writes because WAL mode was not set.",
        project="yonakh",
    ))
    return store


def test_search_basic(db_conn):
    _seed(db_conn)
    fts = FTSStore(db_conn)

    results = fts.search("SQLite")
    assert len(results) >= 2


def test_search_by_type(db_conn):
    _seed(db_conn)
    fts = FTSStore(db_conn)

    decisions = fts.search("SQLite", entity_types=[EntityType.DECISION])
    bugs = fts.search("SQLite", entity_types=[EntityType.BUG_REPORT])

    assert len(decisions) >= 1
    assert len(bugs) >= 1

    for r in decisions:
        assert r.entity_id is not None


def test_search_by_project(db_conn):
    _seed(db_conn)
    fts = FTSStore(db_conn)

    results = fts.search("storage", project="yonakh")
    assert len(results) >= 1

    results = fts.search("storage", project="other")
    assert len(results) == 0


def test_search_empty_query(db_conn):
    _seed(db_conn)
    fts = FTSStore(db_conn)

    results = fts.search("")
    assert results == []
