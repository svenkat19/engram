from __future__ import annotations

from dataclasses import dataclass, field

from yonakh.models.base import RelationType
from yonakh.rules.findings import Finding


@dataclass
class Proposal:
    source_entity_id: str
    target_entity_id: str
    relation_type: RelationType
    confidence: float
    reason: str
    findings: list[Finding] = field(default_factory=list)
    rule_name: str = ""


@dataclass
class ProcessResult:
    findings: list[Finding] = field(default_factory=list)
    proposals: list[Proposal] = field(default_factory=list)
    accepted: list[Proposal] = field(default_factory=list)
    relationships_created: int = 0
