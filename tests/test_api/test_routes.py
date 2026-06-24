"""Integration tests for the REST API."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from yonakh.api.deps import init_app_state
from yonakh.api.routes import admin, entities, events, ingest, relationships, search
from yonakh.db.engine import _set_pragmas, _load_vec_extension, _read_schema_sql
from tests.fake_embedding import FakeEmbeddingProvider


@pytest.fixture
def client():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _set_pragmas(conn)
    _load_vec_extension(conn)
    conn.executescript(_read_schema_sql())
    conn.commit()

    provider = FakeEmbeddingProvider()
    init_app_state(conn, provider)

    app = FastAPI()
    app.include_router(events.router, prefix="/api/v1")
    app.include_router(entities.router, prefix="/api/v1")
    app.include_router(relationships.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(ingest.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")

    with TestClient(app) as c:
        yield c

    conn.close()


class TestHealth:
    def test_health(self, client):
        r = client.get("/api/v1/admin/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_stats(self, client):
        r = client.get("/api/v1/admin/stats")
        assert r.status_code == 200
        data = r.json()
        assert "entities" in data
        assert "events" in data


class TestEvents:
    def test_create_and_get_event(self, client):
        r = client.post("/api/v1/events", json={
            "event_type": "commit",
            "source": "git",
            "source_id": "abc123",
            "timestamp": "2024-06-01T00:00:00Z",
            "payload": {"message": "initial commit"},
            "project": "test",
        })
        assert r.status_code == 200
        event = r.json()
        assert event["event_type"] == "commit"

        r2 = client.get(f"/api/v1/events/{event['id']}")
        assert r2.status_code == 200
        assert r2.json()["id"] == event["id"]

    def test_list_events(self, client):
        for i in range(3):
            client.post("/api/v1/events", json={
                "event_type": "commit",
                "source": "git",
                "timestamp": f"2024-06-0{i+1}T00:00:00Z",
                "payload": {"i": i},
            })

        r = client.get("/api/v1/events")
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_event_not_found(self, client):
        r = client.get("/api/v1/events/nonexistent")
        assert r.status_code == 404


class TestEntities:
    def test_create_and_get_entity(self, client):
        r = client.post("/api/v1/entities", json={
            "entity_type": "decision",
            "title": "Use SQLite",
            "content": "Local-first storage solution.",
            "project": "yonakh",
            "tags": ["architecture"],
            "files": ["db/engine.py"],
        })
        assert r.status_code == 200
        entity = r.json()
        assert entity["title"] == "Use SQLite"
        assert entity["tags"] == ["architecture"]

        r2 = client.get(f"/api/v1/entities/{entity['id']}")
        assert r2.status_code == 200

    def test_update_entity(self, client):
        r = client.post("/api/v1/entities", json={
            "entity_type": "bug_report",
            "title": "Login broken",
        })
        entity = r.json()

        r2 = client.put(f"/api/v1/entities/{entity['id']}", json={
            "title": "Login broken on Safari",
            "tags": ["bug", "safari"],
        })
        assert r2.status_code == 200
        assert r2.json()["title"] == "Login broken on Safari"

    def test_delete_entity(self, client):
        r = client.post("/api/v1/entities", json={
            "entity_type": "snippet",
            "title": "temp note",
        })
        entity = r.json()

        r2 = client.delete(f"/api/v1/entities/{entity['id']}")
        assert r2.status_code == 200
        assert r2.json()["deleted"] is True

    def test_list_entities(self, client):
        for i in range(3):
            client.post("/api/v1/entities", json={
                "entity_type": "commit",
                "title": f"Commit {i}",
                "project": "test",
            })

        r = client.get("/api/v1/entities", params={"project": "test"})
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_entity_not_found(self, client):
        r = client.get("/api/v1/entities/nonexistent")
        assert r.status_code == 404


class TestRelationships:
    def _make_entities(self, client):
        ids = []
        for i in range(2):
            r = client.post("/api/v1/entities", json={
                "entity_type": "decision",
                "title": f"Decision {i}",
            })
            ids.append(r.json()["id"])
        return ids

    def test_create_and_list(self, client):
        ids = self._make_entities(client)
        r = client.post("/api/v1/relationships", json={
            "source_id": ids[0],
            "target_id": ids[1],
            "relation_type": "related_to",
        })
        assert r.status_code == 200

        r2 = client.get("/api/v1/relationships", params={"source_id": ids[0]})
        assert r2.status_code == 200
        assert len(r2.json()) == 1

    def test_delete_relationship(self, client):
        ids = self._make_entities(client)
        r = client.post("/api/v1/relationships", json={
            "source_id": ids[0],
            "target_id": ids[1],
            "relation_type": "related_to",
        })
        rel_id = r.json()["id"]

        r2 = client.delete(f"/api/v1/relationships/{rel_id}")
        assert r2.status_code == 200


class TestSearch:
    def _seed(self, client):
        client.post("/api/v1/entities", json={
            "entity_type": "decision",
            "title": "Use SQLite for storage",
            "content": "SQLite is local-first.",
            "project": "yonakh",
        })
        client.post("/api/v1/entities", json={
            "entity_type": "bug_report",
            "title": "WAL mode not enabled",
            "content": "SQLite WAL mode was missing.",
            "project": "yonakh",
        })

    def test_hybrid_search(self, client):
        self._seed(client)
        r = client.post("/api/v1/search", json={
            "query": "SQLite",
            "limit": 10,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        assert len(data["results"]) > 0

    def test_search_by_file(self, client):
        client.post("/api/v1/entities", json={
            "entity_type": "decision",
            "title": "Auth design",
            "files": ["auth.py"],
        })
        r = client.get("/api/v1/search/file/auth.py")
        assert r.status_code == 200
        assert len(r.json()) >= 1


class TestProvenance:
    def test_create_records_provenance(self, client):
        r = client.post("/api/v1/entities", json={
            "entity_type": "decision",
            "title": "Test provenance",
        })
        entity_id = r.json()["id"]

        r2 = client.get(f"/api/v1/entities/{entity_id}/provenance")
        assert r2.status_code == 200
        records = r2.json()
        assert len(records) >= 1
        assert records[0]["action"] == "created"

    def test_update_creates_snapshot(self, client):
        r = client.post("/api/v1/entities", json={
            "entity_type": "decision",
            "title": "Original title",
        })
        entity_id = r.json()["id"]

        client.put(f"/api/v1/entities/{entity_id}", json={
            "title": "Updated title",
        })

        r2 = client.get(f"/api/v1/entities/{entity_id}/snapshots")
        assert r2.status_code == 200
        snapshots = r2.json()
        assert len(snapshots) >= 1
        assert snapshots[0]["title"] == "Original title"

    def test_snapshot_at(self, client):
        r = client.post("/api/v1/entities", json={
            "entity_type": "decision",
            "title": "Time travel test",
        })
        entity_id = r.json()["id"]

        client.put(f"/api/v1/entities/{entity_id}", json={
            "title": "After time travel",
        })

        r2 = client.get(
            f"/api/v1/entities/{entity_id}/snapshot-at",
            params={"at": "2099-01-01T00:00:00Z"},
        )
        assert r2.status_code == 200
        assert r2.json()["title"] == "Time travel test"


class TestCompaction:
    def test_compact(self, client):
        for i in range(3):
            client.post("/api/v1/entities", json={
                "entity_type": "message",
                "title": f"Message {i}",
            })

        r = client.post("/api/v1/admin/compact")
        assert r.status_code == 200
        data = r.json()
        assert "updated" in data
        assert "archived" in data


class TestIngest:
    def test_list_plugins(self, client):
        r = client.get("/api/v1/ingest/plugins")
        assert r.status_code == 200
        plugins = r.json()
        names = [p["name"] for p in plugins]
        assert "git" in names
        assert "manual" in names

    def test_unknown_plugin(self, client):
        r = client.post("/api/v1/ingest", json={
            "plugin": "nonexistent",
        })
        assert r.status_code == 400
