from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns list of float vectors."""

    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""

    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier for provenance tracking."""
