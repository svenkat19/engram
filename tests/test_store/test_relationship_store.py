from yonakh.models.base import EntityType, RelationType
from yonakh.models.entities import EntityCreate
from yonakh.models.relationships import RelationshipCreate, RelationshipFilter
from yonakh.store.entity_store import EntityStore
from yonakh.store.relationship_store import RelationshipStore


def _make_entities(db_conn, count=3):
    store = EntityStore(db_conn)
    entities = []
    for i in range(count):
        e = store.create(EntityCreate(
            entity_type=EntityType.DECISION, title=f"Entity {i}",
        ))
        entities.append(e)
    return entities


def test_create_and_get(db_conn):
    entities = _make_entities(db_conn)
    store = RelationshipStore(db_conn)

    rel = store.create(RelationshipCreate(
        source_id=entities[0].id,
        target_id=entities[1].id,
        relation_type=RelationType.RELATED_TO,
        properties={"note": "test"},
    ))

    assert rel.id is not None
    assert rel.source_id == entities[0].id
    assert rel.target_id == entities[1].id
    assert rel.relation_type == RelationType.RELATED_TO

    fetched = store.get(rel.id)
    assert fetched is not None
    assert fetched.properties == {"note": "test"}


def test_get_for_entity(db_conn):
    entities = _make_entities(db_conn)
    store = RelationshipStore(db_conn)

    store.create(RelationshipCreate(
        source_id=entities[0].id, target_id=entities[1].id,
        relation_type=RelationType.CAUSED_BY,
    ))
    store.create(RelationshipCreate(
        source_id=entities[2].id, target_id=entities[0].id,
        relation_type=RelationType.RELATED_TO,
    ))

    rels = store.get_for_entity(entities[0].id)
    assert len(rels) == 2

    caused = store.get_for_entity(entities[0].id, RelationType.CAUSED_BY)
    assert len(caused) == 1


def test_get_neighbors(db_conn):
    entities = _make_entities(db_conn, 4)
    store = RelationshipStore(db_conn)

    # 0 -> 1 -> 2 -> 3
    store.create(RelationshipCreate(
        source_id=entities[0].id, target_id=entities[1].id,
        relation_type=RelationType.FOLLOWED_BY,
    ))
    store.create(RelationshipCreate(
        source_id=entities[1].id, target_id=entities[2].id,
        relation_type=RelationType.FOLLOWED_BY,
    ))
    store.create(RelationshipCreate(
        source_id=entities[2].id, target_id=entities[3].id,
        relation_type=RelationType.FOLLOWED_BY,
    ))

    depth1 = store.get_neighbors(entities[0].id, depth=1)
    assert len(depth1) == 1

    depth2 = store.get_neighbors(entities[0].id, depth=2)
    assert len(depth2) == 2

    depth3 = store.get_neighbors(entities[0].id, depth=3)
    assert len(depth3) == 3


def test_delete(db_conn):
    entities = _make_entities(db_conn)
    store = RelationshipStore(db_conn)

    rel = store.create(RelationshipCreate(
        source_id=entities[0].id, target_id=entities[1].id,
        relation_type=RelationType.RELATED_TO,
    ))

    assert store.delete(rel.id) is True
    assert store.get(rel.id) is None
    assert store.delete("nonexistent") is False


def test_list_with_filter(db_conn):
    entities = _make_entities(db_conn)
    store = RelationshipStore(db_conn)

    store.create(RelationshipCreate(
        source_id=entities[0].id, target_id=entities[1].id,
        relation_type=RelationType.CAUSED_BY,
    ))
    store.create(RelationshipCreate(
        source_id=entities[0].id, target_id=entities[2].id,
        relation_type=RelationType.RELATED_TO,
    ))

    all_rels = store.list(RelationshipFilter())
    assert len(all_rels) == 2

    caused = store.list(RelationshipFilter(relation_type=RelationType.CAUSED_BY))
    assert len(caused) == 1

    from_e0 = store.list(RelationshipFilter(source_id=entities[0].id))
    assert len(from_e0) == 2
