"""Deterministic fake embedding provider for testing."""

from __future__ import annotations

import hashlib
import math

from engram.embedding.base import EmbeddingProvider

FAKE_DIM = 384


class FakeEmbeddingProvider(EmbeddingProvider):

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._text_to_vec(t) for t in texts]

    def dimension(self) -> int:
        return FAKE_DIM

    def model_name(self) -> str:
        return "fake-test"

    def _text_to_vec(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).digest()
        raw = []
        for i in range(FAKE_DIM):
            byte_val = h[i % len(h)]
            raw.append((byte_val / 255.0) * 2.0 - 1.0)
        norm = math.sqrt(sum(x * x for x in raw))
        if norm == 0:
            return raw
        return [x / norm for x in raw]
