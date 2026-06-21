from __future__ import annotations

import logging

from engram.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):

    def __init__(
        self,
        model_id: str = "text-embedding-3-small",
        dimensions: int = 384,
        api_key: str | None = None,
    ) -> None:
        self._model_id = model_id
        self._dimensions = dimensions
        self._client = None
        self._api_key = api_key

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def embed(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        response = client.embeddings.create(
            input=texts,
            model=self._model_id,
            dimensions=self._dimensions,
        )
        return [item.embedding for item in response.data]

    def dimension(self) -> int:
        return self._dimensions

    def model_name(self) -> str:
        return f"{self._model_id}@{self._dimensions}d"
