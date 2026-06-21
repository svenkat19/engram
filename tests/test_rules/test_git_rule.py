from datetime import UTC, datetime

from engram.models.base import EntityType, RelationType
from engram.models.entities import Entity, EntityCreate
from engram.rules.findings import FindingType
from engram.rules.git_rule import GitRule
from engram.store.entity_store import EntityStore
from engram.store.relationship_store import RelationshipStore


def _make_entity(
    entity_type: EntityType = EntityType.COMMIT,
    title: str = "test commit",
    files: list[str] | None = None,
    **kwargs: object,
) -> Entity:
    now = datetime.now(UTC)
    return Entity(
        id="test-entity-id",
        entity_type=entity_type,
        title=title,
        created_at=now,
        updated_at=now,
        files=files or [],
        **kwargs,  # type: ignore[arg-type]
    )


class TestObserves:
    def test_observes_commit(self):
        rule = GitRule()
        entity = _make_entity(EntityType.COMMIT)
        assert rule.observes(entity) is True

    def test_ignores_decision(self):
        rule = GitRule()
        entity = _make_entity(EntityType.DECISION)
        assert rule.observes(entity) is False


class TestExtract:
    def test_touches_path(self):
        rule = GitRule()
        entity = _make_entity(files=["src/auth/jwt.py", "tests/test_auth.py"])
        findings = rule.extract(entity)
        paths = [f for f in findings if f.finding_type == FindingType.TOUCHES_PATH]
        assert len(paths) == 2
        assert {f.value for f in paths} == {"src/auth/jwt.py", "tests/test_auth.py"}

    def test_touches_component(self):
        rule = GitRule()
        entity = _make_entity(files=["src/auth/jwt.py", "src/auth/tokens.py"])
        findings = rule.extract(entity)
        components = [f for f in findings if f.finding_type == FindingType.TOUCHES_COMPONENT]
        assert any(f.value == "auth" for f in components)

    def test_conventional_commit_scope(self):
        rule = GitRule()
        entity = _make_entity(title="feat(auth): migrate JWT parser", files=[])
        findings = rule.extract(entity)
        components = [f for f in findings if f.finding_type == FindingType.TOUCHES_COMPONENT]
        assert any(f.value == "auth" for f in components)

    def test_references_issue(self):
        rule = GitRule()
        entity = _make_entity(title="Fix login bug Fixes #321", files=[])
        findings = rule.extract(entity)
        issues = [f for f in findings if f.finding_type == FindingType.REFERENCES_ISSUE]
        assert len(issues) == 1
        assert issues[0].value == "321"

    def test_references_issue_bare_hash(self):
        rule = GitRule()
        entity = _make_entity(title="Related to #42", files=[])
        findings = rule.extract(entity)
        issues = [f for f in findings if f.finding_type == FindingType.REFERENCES_ISSUE]
        assert any(f.value == "42" for f in issues)

    def test_references_adr(self):
        rule = GitRule()
        entity = _make_entity(title="Supersedes ADR-4", files=[])
        findings = rule.extract(entity)
        adrs = [f for f in findings if f.finding_type == FindingType.REFERENCES_ADR]
        assert len(adrs) == 1
        assert adrs[0].value == "4"

    def test_is_revert(self):
        rule = GitRule()
        entity = _make_entity(title='Revert "Enable async auth"', files=[])
        findings = rule.extract(entity)
        reverts = [f for f in findings if f.finding_type == FindingType.IS_REVERT]
        assert len(reverts) == 1

    def test_contains_keyword(self):
        rule = GitRule()
        entity = _make_entity(title="Deprecate old auth handler", files=[])
        findings = rule.extract(entity)
        keywords = [f for f in findings if f.finding_type == FindingType.CONTAINS_KEYWORD]
        assert any(f.value == "deprecat" for f in keywords)

    def test_no_findings_on_empty(self):
        rule = GitRule()
        entity = _make_entity(title="bump version", files=[])
        findings = rule.extract(entity)
        assert all(f.finding_type != FindingType.IS_REVERT for f in findings)
        assert all(f.finding_type != FindingType.REFERENCES_ISSUE for f in findings)


class TestCandidates:
    def test_finds_entities_with_shared_files(self, db_conn):
        entity_store = EntityStore(db_conn)
        rel_store = RelationshipStore(db_conn)
        rule = GitRule()

        decision = entity_store.create(EntityCreate(
            entity_type=EntityType.DECISION,
            title="Use JWT for auth",
            files=["src/auth/jwt.py", "src/auth/tokens.py"],
        ))

        commit = entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title="feat(auth): migrate JWT parser",
            files=["src/auth/jwt.py", "docs/auth.md"],
        ))

        findings = rule.extract(commit)
        candidates = rule.candidates(commit, findings, entity_store, rel_store)

        assert len(candidates) == 1
        assert candidates[0].id == decision.id

    def test_excludes_commit_entities(self, db_conn):
        entity_store = EntityStore(db_conn)
        rel_store = RelationshipStore(db_conn)
        rule = GitRule()

        entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title="earlier commit",
            files=["src/auth/jwt.py"],
        ))

        commit = entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title="later commit",
            files=["src/auth/jwt.py"],
        ))

        findings = rule.extract(commit)
        candidates = rule.candidates(commit, findings, entity_store, rel_store)
        assert len(candidates) == 0

    def test_no_candidates_when_no_file_overlap(self, db_conn):
        entity_store = EntityStore(db_conn)
        rel_store = RelationshipStore(db_conn)
        rule = GitRule()

        entity_store.create(EntityCreate(
            entity_type=EntityType.DECISION,
            title="Use PostgreSQL",
            files=["src/db/engine.py"],
        ))

        commit = entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title="update readme",
            files=["README.md"],
        ))

        findings = rule.extract(commit)
        candidates = rule.candidates(commit, findings, entity_store, rel_store)
        assert len(candidates) == 0


class TestPropose:
    def test_file_overlap_proposal(self, db_conn):
        entity_store = EntityStore(db_conn)
        rule = GitRule()

        decision = entity_store.create(EntityCreate(
            entity_type=EntityType.DECISION,
            title="Use JWT for auth",
            files=["src/auth/jwt.py", "src/auth/tokens.py"],
        ))

        commit = entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title="update auth module",
            files=["src/auth/jwt.py", "docs/auth.md"],
        ))

        findings = rule.extract(commit)
        proposals = rule.propose(commit, findings, [decision])

        assert len(proposals) == 1
        p = proposals[0]
        assert p.source_entity_id == commit.id
        assert p.target_entity_id == decision.id
        assert p.relation_type == RelationType.REFERENCES
        assert 0.5 <= p.confidence <= 0.95
        assert p.rule_name == "git"

    def test_revert_proposal(self, db_conn):
        entity_store = EntityStore(db_conn)
        rule = GitRule()

        decision = entity_store.create(EntityCreate(
            entity_type=EntityType.DECISION,
            title="Enable async auth",
            files=["src/auth/handler.py"],
        ))

        commit = entity_store.create(EntityCreate(
            entity_type=EntityType.COMMIT,
            title='Revert "Enable async auth"',
            files=["src/auth/handler.py"],
        ))

        findings = rule.extract(commit)
        proposals = rule.propose(commit, findings, [decision])

        assert len(proposals) == 1
        assert proposals[0].relation_type == RelationType.REVERTS
        assert proposals[0].confidence == 0.9

    def test_full_overlap_high_confidence(self, db_conn):
        entity_store = EntityStore(db_conn)
        rule = GitRule()

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

        findings = rule.extract(commit)
        proposals = rule.propose(commit, findings, [decision])

        assert len(proposals) == 1
        assert proposals[0].confidence == 0.9  # 0.5 + 1.0 * 0.4
