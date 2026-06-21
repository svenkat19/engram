from __future__ import annotations

from typing import Protocol

from engram.models.entities import Entity
from engram.rules.findings import Finding
from engram.rules.proposals import Proposal
from engram.store.entity_store import EntityStore
from engram.store.relationship_store import RelationshipStore


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
