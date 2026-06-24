from __future__ import annotations

from yonakh.rules.proposals import Proposal


class ThresholdValidator:
    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold

    def accept(self, proposals: list[Proposal]) -> list[Proposal]:
        return [p for p in proposals if p.confidence >= self.threshold]
