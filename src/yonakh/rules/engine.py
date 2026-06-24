from __future__ import annotations

import logging
import sqlite3

from yonakh.models.base import ProvenanceAction, RelationType
from yonakh.models.entities import Entity
from yonakh.models.provenance import ProvenanceCreate
from yonakh.models.relationships import RelationshipCreate
from yonakh.rules.base import Rule
from yonakh.rules.proposals import ProcessResult, Proposal
from yonakh.rules.validator import ThresholdValidator
from yonakh.store.entity_store import EntityStore
from yonakh.store.provenance_store import ProvenanceStore
from yonakh.store.relationship_store import RelationshipStore

logger = logging.getLogger(__name__)

_RELATION_TO_PROVENANCE: dict[RelationType, ProvenanceAction] = {
    RelationType.REFERENCES: ProvenanceAction.REFERENCED,
    RelationType.REVERTS: ProvenanceAction.CONTRADICTED,
    RelationType.CONTRADICTS: ProvenanceAction.CONTRADICTED,
    RelationType.SUPERSEDES: ProvenanceAction.SUPERSEDED,
}


class RulesEngine:
    def __init__(
        self,
        rules: list[Rule],
        validator: ThresholdValidator,
        entity_store: EntityStore,
        relationship_store: RelationshipStore,
        provenance_store: ProvenanceStore,
    ) -> None:
        self._rules = rules
        self._validator = validator
        self._entity_store = entity_store
        self._relationship_store = relationship_store
        self._provenance_store = provenance_store

    def process(self, entity: Entity) -> ProcessResult:
        all_findings = []
        all_proposals = []

        for rule in self._rules:
            if not rule.observes(entity):
                continue

            findings = rule.extract(entity)
            all_findings.extend(findings)

            candidates = rule.candidates(
                entity, findings, self._entity_store, self._relationship_store,
            )
            proposals = rule.propose(entity, findings, candidates)
            all_proposals.extend(proposals)

        accepted = self._validator.accept(all_proposals)
        created = self._apply(accepted)

        return ProcessResult(
            findings=all_findings,
            proposals=all_proposals,
            accepted=accepted,
            relationships_created=created,
        )

    def process_batch(self, entities: list[Entity]) -> list[ProcessResult]:
        return [self.process(e) for e in entities]

    def _apply(self, proposals: list[Proposal]) -> int:
        created = 0
        for p in proposals:
            try:
                self._relationship_store.create(RelationshipCreate(
                    source_id=p.source_entity_id,
                    target_id=p.target_entity_id,
                    relation_type=p.relation_type,
                    weight=p.confidence,
                    properties={"reason": p.reason, "rule": p.rule_name},
                ))
                created += 1
            except sqlite3.IntegrityError:
                logger.debug(
                    "Relationship already exists: %s -> %s (%s)",
                    p.source_entity_id, p.target_entity_id, p.relation_type,
                )
                continue

            action = _RELATION_TO_PROVENANCE.get(
                p.relation_type, ProvenanceAction.REFERENCED,
            )
            self._provenance_store.record(ProvenanceCreate(
                entity_id=p.target_entity_id,
                action=action,
                actor=f"rules_engine:{p.rule_name}",
                related_entity_id=p.source_entity_id,
                details={"reason": p.reason, "confidence": p.confidence},
                confidence_delta=0.0,
            ))

        return created
