from __future__ import annotations

import re

from yonakh.models.base import EntityType, RelationType
from yonakh.models.entities import Entity
from yonakh.rules.findings import Finding, FindingType
from yonakh.rules.proposals import Proposal
from yonakh.store.entity_store import EntityStore
from yonakh.store.relationship_store import RelationshipStore

_ISSUE_RE = re.compile(r"(?:[Ff]ixes|[Cc]loses|[Rr]esolves)?\s*#(\d+)")
_ADR_RE = re.compile(r"ADR-?(\d+)", re.IGNORECASE)
_REVERT_RE = re.compile(r'^(?:Revert\s+"|revert:)', re.IGNORECASE)
_SCOPE_RE = re.compile(r"^\w+\(([^)]+)\):")
_KEYWORDS = ("deprecat", "remov", "replac", "migrat")

_SKIP_DIRS = frozenset({"src", "lib", "pkg", "internal", "cmd", "app", "apps"})


def _infer_component(path: str) -> str | None:
    parts = path.replace("\\", "/").split("/")
    for part in parts:
        if part and part not in _SKIP_DIRS and not part.startswith("."):
            return part
    return None


class GitRule:
    @property
    def name(self) -> str:
        return "git"

    def observes(self, entity: Entity) -> bool:
        return entity.entity_type == EntityType.COMMIT

    def extract(self, entity: Entity) -> list[Finding]:
        findings: list[Finding] = []
        title = entity.title or ""

        for path in entity.files:
            findings.append(Finding(FindingType.TOUCHES_PATH, path))

        seen_components: set[str] = set()
        for path in entity.files:
            comp = _infer_component(path)
            if comp and comp not in seen_components:
                seen_components.add(comp)
                findings.append(Finding(FindingType.TOUCHES_COMPONENT, comp))

        scope_match = _SCOPE_RE.match(title)
        if scope_match:
            scope = scope_match.group(1)
            if scope not in seen_components:
                findings.append(Finding(FindingType.TOUCHES_COMPONENT, scope))

        for m in _ISSUE_RE.finditer(title):
            findings.append(Finding(FindingType.REFERENCES_ISSUE, m.group(1)))

        for m in _ADR_RE.finditer(title):
            findings.append(Finding(FindingType.REFERENCES_ADR, m.group(1)))

        if _REVERT_RE.match(title):
            findings.append(Finding(FindingType.IS_REVERT, title))

        title_lower = title.lower()
        for kw in _KEYWORDS:
            if kw in title_lower:
                findings.append(Finding(FindingType.CONTAINS_KEYWORD, kw))

        return findings

    def candidates(
        self,
        entity: Entity,
        findings: list[Finding],
        entity_store: EntityStore,
        relationship_store: RelationshipStore,
    ) -> list[Entity]:
        paths = [f.value for f in findings if f.finding_type == FindingType.TOUCHES_PATH]
        if not paths:
            return []
        return entity_store.find_by_file_paths(
            paths,
            exclude_id=entity.id,
            exclude_types=[EntityType.COMMIT],
        )

    def propose(
        self,
        entity: Entity,
        findings: list[Finding],
        candidates: list[Entity],
    ) -> list[Proposal]:
        proposals: list[Proposal] = []
        is_revert = any(f.finding_type == FindingType.IS_REVERT for f in findings)
        commit_paths = {f.value for f in findings if f.finding_type == FindingType.TOUCHES_PATH}
        adr_refs = {f.value for f in findings if f.finding_type == FindingType.REFERENCES_ADR}

        for candidate in candidates:
            candidate_paths = set(candidate.files)
            if not candidate_paths:
                continue

            shared = commit_paths & candidate_paths
            if not shared:
                continue

            overlap_ratio = len(shared) / len(candidate_paths)

            if is_revert:
                proposals.append(Proposal(
                    source_entity_id=entity.id,
                    target_entity_id=candidate.id,
                    relation_type=RelationType.REVERTS,
                    confidence=0.9,
                    reason=f"Revert commit touches {len(shared)} shared file(s)",
                    findings=[f for f in findings if f.finding_type == FindingType.IS_REVERT],
                    rule_name=self.name,
                ))
                continue

            title_upper = (candidate.title or "").upper()
            for adr_num in adr_refs:
                if f"ADR-{adr_num}" in title_upper or f"ADR {adr_num}" in title_upper:
                    adr_findings = [
                        f for f in findings
                        if f.finding_type == FindingType.REFERENCES_ADR
                        and f.value == adr_num
                    ]
                    proposals.append(Proposal(
                        source_entity_id=entity.id,
                        target_entity_id=candidate.id,
                        relation_type=RelationType.REFERENCES,
                        confidence=0.95,
                        reason=f"Commit references ADR-{adr_num}",
                        findings=adr_findings,
                        rule_name=self.name,
                    ))
                    break
            else:
                confidence = min(0.95, 0.5 + overlap_ratio * 0.4)
                path_findings = [
                    f for f in findings
                    if f.finding_type == FindingType.TOUCHES_PATH
                    and f.value in shared
                ]
                proposals.append(Proposal(
                    source_entity_id=entity.id,
                    target_entity_id=candidate.id,
                    relation_type=RelationType.REFERENCES,
                    confidence=confidence,
                    reason=f"Shares {len(shared)}/{len(candidate_paths)} file(s)",
                    findings=path_findings,
                    rule_name=self.name,
                ))

        return proposals
