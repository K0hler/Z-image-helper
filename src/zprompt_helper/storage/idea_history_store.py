import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, field_serializer

from zprompt_helper.storage.paths import ProjectPaths


class IdeaHistoryEntry(BaseModel):
    id: str
    idea_text: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime) -> str:
        return created_at.isoformat()


class IdeaHistoryStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def append(
        self,
        idea_text: str,
        created_at: datetime | None = None,
    ) -> IdeaHistoryEntry:
        timestamp = created_at or datetime.now(UTC)
        entry = IdeaHistoryEntry(
            id=uuid4().hex,
            idea_text=idea_text.strip(),
            created_at=timestamp,
        )
        self._append_entry(entry)
        return entry

    def append_if_new(
        self,
        idea_text: str,
        created_at: datetime | None = None,
    ) -> IdeaHistoryEntry | None:
        normalized = idea_text.strip()
        if not normalized:
            return None
        if any(item["idea_text"].strip() == normalized for item in self.export_all()):
            return None
        return self.append(normalized, created_at=created_at)

    def export_all(self) -> list[dict]:
        payload: list[dict] = []
        for path in sorted(self.paths.idea_history_dir.glob("*.json"), reverse=True):
            payload.extend(self._read_file(path))
        return sorted(payload, key=lambda item: item["created_at"], reverse=True)

    def _append_entry(self, entry: IdeaHistoryEntry) -> None:
        target = self.paths.idea_history_dir / f"{entry.created_at.date().isoformat()}.json"
        entries = self._read_file(target) if target.exists() else []
        entries.append(entry.model_dump(mode="json"))
        self._write_file(target, entries)

    @staticmethod
    def _read_file(path: Path) -> list[dict]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_file(path: Path, entries: list[dict]) -> None:
        path.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
