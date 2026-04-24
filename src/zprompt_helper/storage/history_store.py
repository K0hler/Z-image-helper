import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, field_serializer

from zprompt_helper.storage.paths import ProjectPaths


class HistoryEntry(BaseModel):
    id: str
    prompt_text: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime) -> str:
        return created_at.isoformat()


class HistoryStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def append(self, prompt_text: str, created_at: datetime | None = None) -> HistoryEntry:
        timestamp = created_at or datetime.now(UTC)
        entry = HistoryEntry(
            id=uuid4().hex,
            prompt_text=prompt_text,
            created_at=timestamp,
        )
        self._append_entry(entry)
        return entry

    def delete_entry(self, date_key: str, entry_id: str) -> None:
        target = self.paths.history_dir / f"{date_key}.json"
        if not target.exists():
            return

        kept = [
            item
            for item in self._read_file(target)
            if item["id"] != entry_id
        ]
        self._write_file(target, kept)

    def clear_all(self) -> None:
        for path in self.paths.history_dir.glob("*.json"):
            path.unlink()

    def export_all(self) -> list[dict]:
        payload: list[dict] = []
        for path in sorted(self.paths.history_dir.glob("*.json")):
            payload.extend(self._read_file(path))
        return payload

    def import_many(self, items: list[dict]) -> int:
        imported = 0
        seen_ids = {item["id"] for item in self.export_all()}

        for item in items:
            entry = HistoryEntry.model_validate(item)
            if entry.id in seen_ids:
                continue

            self._append_entry(entry)
            seen_ids.add(entry.id)
            imported += 1

        return imported

    def _append_entry(self, entry: HistoryEntry) -> None:
        target = self.paths.history_dir / f"{entry.created_at.date().isoformat()}.json"
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
