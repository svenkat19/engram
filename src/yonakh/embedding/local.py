from __future__ import annotations

import logging

from yonakh.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class LocalEmbeddingProvider(EmbeddingProvider):

    def __init__(self, model_id: str = "all-MiniLM-L6-v2") -> None:
        self._model_id = model_id
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s", self._model_id)
            self._model = SentenceTransformer(self._model_id)
            logger.info("Embedding model loaded (dim=%d)", self.dimension())
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return [e.tolist() for e in embeddings]

    def dimension(self) -> int:
        model = self._load_model()
        return model.get_sentence_embedding_dimension()

    def model_name(self) -> str:
        return self._model_id
