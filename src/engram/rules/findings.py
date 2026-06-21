from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FindingType(str, Enum):
    TOUCHES_PATH = "touches_path"
    TOUCHES_COMPONENT = "touches_component"
    REFERENCES_ISSUE = "references_issue"
    REFERENCES_ADR = "references_adr"
    CONTAINS_KEYWORD = "contains_keyword"
    IS_REVERT = "is_revert"


@dataclass(frozen=True)
class Finding:
    finding_type: FindingType
    value: str
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
