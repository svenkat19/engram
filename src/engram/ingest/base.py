from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class IngestResult:
    events_created: int = 0
    entities_created: int = 0
    errors: list[str] = field(default_factory=list)


class IngestPlugin(ABC):
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def ingest(self, **kwargs: object) -> IngestResult: ...
