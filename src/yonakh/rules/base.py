from __future__ import annotations

from typing import Protocol

from yonakh.models.entities import Entity
from yonakh.rules.findings import Finding
from yonakh.rules.proposals import Proposal
from yonakh.store.entity_store import EntityStore
from yonakh.store.relationship_store import RelationshipStore


class Rule(Protocol):
    @property
    def name(self) -> str: ...

    def observes(self, entity: Entity) -> bool: ...

    def extract(self, entity: Entity) -> list[Finding]: ...

    def candidates(
        self,
        entity: Entity,
        findings: list[Finding],
        entity_store: EntityStore,
        relationship_store: RelationshipStore,
    ) -> list[Entity]: ...

    def propose(
        self,
        entity: Entity,
        findings: list[Finding],
        candidates: list[Entity],
    ) -> list[Proposal]: ...
