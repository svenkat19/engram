from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from yonakh.ingest.base import IngestPlugin, IngestResult
from yonakh.models.base import EntityType
from yonakh.models.entities import EntityCreate
from yonakh.models.events import EventCreate
from yonakh.store.entity_store import EntityStore
from yonakh.store.event_store import EventStore

_GIT_LOG_SEP = "|"
_GIT_LOG_FORMAT = _GIT_LOG_SEP.join(["%H", "%an", "%ae", "%aI", "%s"])


class GitIngestPlugin(IngestPlugin):
    def name(self) -> str:
        return "git"

    def description(self) -> str:
        return "Ingest commits from git history"

    def ingest(  # type: ignore[override]
        self,
        repo_path: str = ".",
        event_store: EventStore | None = None,
        entity_store: EntityStore | None = None,
        max_commits: int = 100,
        project: str | None = None,
        **kwargs: object,
    ) -> IngestResult:
        result = IngestResult()
        repo = Path(repo_path).resolve()

        try:
            proc = subprocess.run(
                [
                    "git", "log",
                    f"--format={_GIT_LOG_FORMAT}",
                    f"--max-count={max_commits}",
                ],
                cwd=str(repo),
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            result.errors.append("git executable not found")
            return result

        if proc.returncode != 0:
            result.errors.append(f"git log failed: {proc.stderr.strip()}")
            return result

        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        for line in lines:
            parts = line.split(_GIT_LOG_SEP, maxsplit=4)
            if len(parts) < 5:
                result.errors.append(f"Skipped malformed log line: {line!r}")
                continue

            sha, author_name, author_email, date_str, message = parts
            try:
                timestamp = datetime.fromisoformat(date_str)
            except ValueError:
                result.errors.append(f"Bad date for {sha[:8]}: {date_str}")
                continue

            changed_files = self._changed_files(sha, repo)

            if event_store is not None:
                event = EventCreate(
                    event_type="commit",
                    source="git",
                    source_id=sha,
                    timestamp=timestamp,
                    payload={
                        "sha": sha,
                        "author_name": author_name,
                        "author_email": author_email,
                        "message": message,
                        "files": changed_files,
                    },
                    project=project,
                    actor=author_name,
                )
                event_store.create(event)
                result.events_created += 1

            if entity_store is not None:
                entity = EntityCreate(
                    entity_type=EntityType.COMMIT,
                    title=message,
                    content=None,
                    properties={
                        "sha": sha,
                        "author_name": author_name,
                        "author_email": author_email,
                    },
                    project=project,
                    tags=["git"],
                    files=changed_files,
                    created_by=author_name,
                )
                created = entity_store.create(entity)
                result.entities_created += 1
                result.entity_ids.append(created.id)

        return result

    @staticmethod
    def _changed_files(sha: str, repo: Path) -> list[str]:
        proc = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return []
        return [f for f in proc.stdout.splitlines() if f.strip()]
