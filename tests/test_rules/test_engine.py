from engram.models.base import EntityType, RelationType
from engram.models.entities import EntityCreate
from engram.rules.engine import RulesEngine
from engram.rules.git_rule import GitRule
from engram.rules.validator import ThresholdValidator
from engram.store.entity_store import EntityStore
from engram.store.provenance_store import ProvenanceStore
from engram.store.relationship_store import RelationshipStore


def _make_engine(db_conn, threshold=0.85):
    return RulesEngine(
        rules=[GitRule()],
        validator=ThresholdValidator(threshold=threshold),
        entity_store=EntityStore(db_conn),
        relationship_store=RelationshipStore(db_conn),
        provenance_store=ProvenanceStore(db_conn),
    )


class TestEngine:
    def test_end_to_end(self, db_conn):
        entity_store = EntityStore(db_conn)

        decision = entity_store.create(EntityCreate(
            entity_type=EntityType.DECISION,
            title="Use JWT for auth",
            files=["src/auth/jwt.py", "src/auth/tokens.py"],
        ))

        commit = entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title="feat(auth): refactor JWT parser",
            files=["src/auth/jwt.py", "src/auth/tokens.py"],
        ))

        engine = _make_engine(db_conn)
        result = engine.process(commit)

        assert len(result.findings) > 0
        assert len(result.proposals) == 1
        assert result.proposals[0].target_entity_id == decision.id

        # Full overlap → confidence = 0.9, above 0.85 threshold
        assert len(result.accepted) == 1
        assert result.relationships_created == 1

        # Verify relationship was created
        rel_store = RelationshipStore(db_conn)
        rels = rel_store.get_for_entity(decision.id)
        assert len(rels) == 1
        assert rels[0].relation_type == RelationType.REFERENCES
        assert rels[0].source_id == commit.id

        # Verify provenance was recorded
        prov_store = ProvenanceStore(db_conn)
        records = prov_store.get_for_entity(decision.id)
        assert len(records) == 1
        assert records[0].related_entity_id == commit.id

    def test_below_threshold_rejected(self, db_conn):
        entity_store = EntityStore(db_conn)

        entity_store.create(EntityCreate(
            entity_type=EntityType.DECISION,
            title="Database strategy",
            files=["src/db/engine.py", "src/db/pool.py", "src/db/models.py",
                   "src/db/migrations.py", "src/db/config.py"],
        ))

        commit = entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title="fix db config",
            files=["src/db/config.py"],
        ))

        # 1/5 file overlap → confidence = 0.5 + 0.2*0.4 = 0.58, below 0.85
        engine = _make_engine(db_conn, threshold=0.85)
        result = engine.process(commit)

        assert len(result.proposals) == 1
        assert result.proposals[0].confidence < 0.85
        assert len(result.accepted) == 0
        assert result.relationships_created == 0

    def test_no_candidates(self, db_conn):
        entity_store = EntityStore(db_conn)

        commit = entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title="bump version",
            files=["pyproject.toml"],
        ))

        engine = _make_engine(db_conn)
        result = engine.process(commit)

        assert len(result.proposals) == 0
        assert len(result.accepted) == 0
        assert result.relationships_created == 0

    def test_ignores_non_commit(self, db_conn):
        entity_store = EntityStore(db_conn)

        decision = entity_store.create(EntityCreate(
            entity_type=EntityType.DECISION,
            title="Use PostgreSQL",
        ))

        engine = _make_engine(db_conn)
        result = engine.process(decision)

        assert len(result.findings) == 0
        assert len(result.proposals) == 0

    def test_duplicate_relationship_handled(self, db_conn):
        entity_store = EntityStore(db_conn)
        rel_store = RelationshipStore(db_conn)

        decision = entity_store.create(EntityCreate(
            entity_type=EntityType.DECISION,
            title="Auth strategy",
            files=["src/auth/jwt.py"],
        ))

        commit = entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title="update jwt",
            files=["src/auth/jwt.py"],
        ))

        engine = _make_engine(db_conn)

        result1 = engine.process(commit)
        assert result1.relationships_created == 1

        result2 = engine.process(commit)
        assert result2.relationships_created == 0

        rels = rel_store.get_for_entity(decision.id)
        assert len(rels) == 1


class TestValidator:
    def test_threshold_filtering(self):
        from engram.models.base import RelationType
        from engram.rules.proposals import Proposal

        validator = ThresholdValidator(threshold=0.8)
        proposals = [
            Proposal("a", "b", RelationType.REFERENCES, 0.95, "high"),
            Proposal("a", "c", RelationType.REFERENCES, 0.5, "low"),
            Proposal("a", "d", RelationType.REFERENCES, 0.8, "boundary"),
        ]
        accepted = validator.accept(proposals)
        assert len(accepted) == 2
        assert all(p.confidence >= 0.8 for p in accepted)


class TestFindByFilePaths:
    def test_finds_matching_entities(self, db_conn):
        store = EntityStore(db_conn)

        d = store.create(EntityCreate(
            entity_type=EntityType.DECISION,
            title="JWT auth",
            files=["src/auth/jwt.py"],
        ))

        results = store.find_by_file_paths(["src/auth/jwt.py"])
        assert len(results) == 1
        assert results[0].id == d.id

    def test_excludes_by_id(self, db_conn):
        store = EntityStore(db_conn)

        d = store.create(EntityCreate(
            entity_type=EntityType.DECISION,
            title="JWT auth",
            files=["src/auth/jwt.py"],
        ))

        results = store.find_by_file_paths(["src/auth/jwt.py"], exclude_id=d.id)
        assert len(results) == 0

    def test_excludes_by_type(self, db_conn):
        store = EntityStore(db_conn)

        store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title="a commit",
            files=["src/auth/jwt.py"],
        ))

        results = store.find_by_file_paths(
            ["src/auth/jwt.py"],
            exclude_types=[EntityType.COMMIT],
        )
        assert len(results) == 0

    def test_empty_paths_returns_empty(self, db_conn):
        store = EntityStore(db_conn)
        results = store.find_by_file_paths([])
        assert results == []
