from datetime import datetime, timezone

from engram.models.events import EventCreate, EventFilter
from engram.store.event_store import EventStore


def test_create_and_get(db_conn):
    store = EventStore(db_conn)
    event = store.create(EventCreate(
        event_type="commit",
        source="git",
        source_id="abc123",
        timestamp=datetime(2024, 6, 1, tzinfo=timezone.utc),
        payload={"message": "initial commit", "sha": "abc123"},
        project="test-project",
        actor="test-user",
    ))

    assert event.id is not None
    assert event.event_type == "commit"
    assert event.source == "git"
    assert event.payload["sha"] == "abc123"
    assert event.processed is False

    fetched = store.get(event.id)
    assert fetched is not None
    assert fetched.id == event.id
    assert fetched.checksum == event.checksum


def test_idempotent_create(db_conn):
    store = EventStore(db_conn)
    payload = {"message": "same event"}
    ev1 = store.create(EventCreate(
        event_type="test", source="manual", timestamp=datetime.now(timezone.utc),
        payload=payload,
    ))
    ev2 = store.create(EventCreate(
        event_type="test", source="manual", timestamp=datetime.now(timezone.utc),
        payload=payload,
    ))
    assert ev1.checksum == ev2.checksum
    assert store.count() == 1


def test_list_with_filter(db_conn):
    store = EventStore(db_conn)
    for i in range(5):
        store.create(EventCreate(
            event_type="commit" if i < 3 else "pr.opened",
            source="git",
            timestamp=datetime(2024, 6, 1 + i, tzinfo=timezone.utc),
            payload={"idx": i},
            project="proj-a",
        ))

    all_events = store.list(EventFilter(limit=100))
    assert len(all_events) == 5

    commits = store.list(EventFilter(event_type="commit"))
    assert len(commits) == 3

    prs = store.list(EventFilter(event_type="pr.opened"))
    assert len(prs) == 2


def test_mark_processed(db_conn):
    store = EventStore(db_conn)
    event = store.create(EventCreate(
        event_type="test", source="manual",
        timestamp=datetime.now(timezone.utc), payload={"x": 1},
    ))
    assert event.processed is False

    store.mark_processed(event.id)
    fetched = store.get(event.id)
    assert fetched is not None
    assert fetched.processed is True


def test_count_with_filter(db_conn):
    store = EventStore(db_conn)
    for i in range(3):
        store.create(EventCreate(
            event_type="commit", source="git",
            timestamp=datetime(2024, 1, 1 + i, tzinfo=timezone.utc),
            payload={"i": i}, project="proj-a",
        ))
    store.create(EventCreate(
        event_type="issue", source="github",
        timestamp=datetime.now(timezone.utc),
        payload={"title": "bug"}, project="proj-b",
    ))

    assert store.count() == 4
    assert store.count(EventFilter(project="proj-a")) == 3
    assert store.count(EventFilter(event_type="issue")) == 1
