from __future__ import annotations

from pathlib import Path

from yonakh.ingest.base import IngestPlugin, IngestResult
from yonakh.models.base import EntityType
from yonakh.models.entities import EntityCreate
from yonakh.store.entity_store import EntityStore


class ManualIngestPlugin(IngestPlugin):
    def name(self) -> str:
        return "manual"

    def description(self) -> str:
        return "Ingest markdown files as documents"

    def ingest(  # type: ignore[override]
        self,
        file_path: str = "",
        entity_store: EntityStore | None = None,
        project: str | None = None,
        **kwargs: object,
    ) -> IngestResult:
        result = IngestResult()

        if not file_path:
            result.errors.append("file_path is required")
            return result

        path = Path(file_path)
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            result.errors.append(f"File not found: {file_path}")
            return result
        except OSError as exc:
            result.errors.append(f"Error reading {file_path}: {exc}")
            return result

        title = path.stem

        if entity_store is not None:
            entity = EntityCreate(
                entity_type=EntityType.DOCUMENT,
                title=title,
                content=content,
                project=project,
                tags=["manual"],
                files=[str(path.resolve())],
            )
            entity_store.create(entity)
            result.entities_created += 1

        return result
