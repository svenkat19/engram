from engram.models.base import EntityStatus, EntityType
from engram.models.entities import EntityCreate, EntityFilter, EntityUpdate
from engram.store.entity_store import EntityStore


def test_create_and_get(db_conn):
    store = EntityStore(db_conn)
    entity = store.create(EntityCreate(
        entity_type=EntityType.DECISION,
        title="Use SQLite for storage",
        content="We chose SQLite because it's local-first and zero-dependency.",
        properties={"status": "accepted"},
        project="engram",
        tags=["architecture", "storage"],
        files=["src/engram/db/engine.py"],
        created_by="test-user",
        confidence=0.9,
    ))

    assert entity.id is not None
    assert entity.entity_type == EntityType.DECISION
    assert entity.title == "Use SQLite for storage"
    assert entity.tags == ["architecture", "storage"]
    assert entity.files == ["src/engram/db/engine.py"]
    assert entity.confidence == 0.9
    assert entity.status == EntityStatus.ACTIVE

    fetched = store.get(entity.id)
    assert fetched is not None
    assert fetched.title == entity.title
    assert fetched.tags == entity.tags


def test_update(db_conn):
    store = EntityStore(db_conn)
    entity = store.create(EntityCreate(
        entity_type=EntityType.BUG_REPORT,
        title="Login fails on Safari",
        tags=["bug", "auth"],
    ))

    updated = store.update(entity.id, EntityUpdate(
        title="Login fails on Safari 17+",
        tags=["bug", "auth", "safari"],
        confidence=0.8,
    ))

    assert updated is not None
    assert updated.title == "Login fails on Safari 17+"
    assert updated.tags == ["auth", "bug", "safari"]  # sorted
    assert updated.confidence == 0.8
    assert updated.updated_at > entity.updated_at


def test_soft_delete(db_conn):
    store = EntityStore(db_conn)
    entity = store.create(EntityCreate(
        entity_type=EntityType.SNIPPET, title="test snippet",
    ))

    assert store.delete(entity.id) is True

    deleted = store.get(entity.id)
    assert deleted is not None
    assert deleted.status == EntityStatus.DELETED


def test_list_with_filter(db_conn):
    store = EntityStore(db_conn)
    store.create(EntityCreate(
        entity_type=EntityType.DECISION, title="Decision 1",
        project="proj-a", tags=["arch"],
    ))
    store.create(EntityCreate(
        entity_type=EntityType.DECISION, title="Decision 2",
        project="proj-a",
    ))
    store.create(EntityCreate(
        entity_type=EntityType.BUG_REPORT, title="Bug 1",
        project="proj-b",
    ))

    decisions = store.list(EntityFilter(entity_type=EntityType.DECISION))
    assert len(decisions) == 2

    proj_a = store.list(EntityFilter(project="proj-a"))
    assert len(proj_a) == 2

    tagged = store.list(EntityFilter(tag="arch"))
    assert len(tagged) == 1
    assert tagged[0].title == "Decision 1"


def test_list_by_file(db_conn):
    store = EntityStore(db_conn)
    store.create(EntityCreate(
        entity_type=EntityType.COMMIT, title="Fix auth",
        files=["auth.py", "tests/test_auth.py"],
    ))
    store.create(EntityCreate(
        entity_type=EntityType.DECISION, title="Use JWT",
        files=["auth.py"],
    ))
    store.create(EntityCreate(
        entity_type=EntityType.SNIPPET, title="Unrelated",
        files=["utils.py"],
    ))

    results = store.list(EntityFilter(file_path="auth.py"))
    assert len(results) == 2


def test_record_access(db_conn):
    store = EntityStore(db_conn)
    entity = store.create(EntityCreate(
        entity_type=EntityType.DOCUMENT, title="API docs",
    ))
    assert entity.access_count == 0
    assert entity.last_accessed is None

    store.record_access(entity.id)
    updated = store.get(entity.id)
    assert updated is not None
    assert updated.access_count == 1
    assert updated.last_accessed is not None


def test_count(db_conn):
    store = EntityStore(db_conn)
    for i in range(4):
        store.create(EntityCreate(
            entity_type=EntityType.COMMIT, title=f"Commit {i}",
        ))
    assert store.count() == 4
    assert store.count(EntityFilter(entity_type=EntityType.COMMIT)) == 4
    assert store.count(EntityFilter(entity_type=EntityType.DECISION)) == 0
