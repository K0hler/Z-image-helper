from datetime import UTC, datetime

from zprompt_helper.storage.history_store import HistoryStore
from zprompt_helper.storage.paths import ProjectPaths


def test_history_store_writes_entries_to_date_named_files(tmp_path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    store = HistoryStore(paths)

    entry = store.append(
        prompt_text="A cinematic still of a neon alley",
        created_at=datetime(2026, 4, 24, 10, 15, tzinfo=UTC),
    )

    history_file = tmp_path / "data" / "history" / "2026-04-24.json"
    assert history_file.exists()
    assert entry.prompt_text == "A cinematic still of a neon alley"


def test_history_store_exports_entries_sorted_by_date_file(tmp_path) -> None:
    store = HistoryStore(ProjectPaths.from_root(tmp_path))

    later = store.append("later", created_at=datetime(2026, 4, 25, 10, tzinfo=UTC))
    earlier = store.append("earlier", created_at=datetime(2026, 4, 24, 10, tzinfo=UTC))

    exported = store.export_all()

    assert [item["id"] for item in exported] == [earlier.id, later.id]


def test_history_store_deletes_entry_from_date_file(tmp_path) -> None:
    store = HistoryStore(ProjectPaths.from_root(tmp_path))
    keep = store.append("keep", created_at=datetime(2026, 4, 24, 10, tzinfo=UTC))
    remove = store.append("remove", created_at=datetime(2026, 4, 24, 11, tzinfo=UTC))

    store.delete_entry("2026-04-24", remove.id)

    exported = store.export_all()
    assert [item["id"] for item in exported] == [keep.id]


def test_history_store_clear_all_removes_history_files(tmp_path) -> None:
    store = HistoryStore(ProjectPaths.from_root(tmp_path))
    store.append("first", created_at=datetime(2026, 4, 24, 10, tzinfo=UTC))
    store.append("second", created_at=datetime(2026, 4, 25, 10, tzinfo=UTC))

    store.clear_all()

    assert store.export_all() == []
    assert not list((tmp_path / "data" / "history").glob("*.json"))


def test_history_store_import_many_skips_duplicate_ids_and_preserves_ids(tmp_path) -> None:
    store = HistoryStore(ProjectPaths.from_root(tmp_path))
    existing = store.append("existing", created_at=datetime(2026, 4, 24, 10, tzinfo=UTC))

    imported_items = [
        {
            "id": existing.id,
            "prompt_text": "duplicate",
            "created_at": "2026-04-24T12:00:00+00:00",
        },
        {
            "id": "imported-id",
            "prompt_text": "imported",
            "created_at": "2026-04-25T12:00:00+00:00",
        },
    ]

    count = store.import_many(imported_items)

    exported = store.export_all()
    assert count == 1
    assert [item["id"] for item in exported] == [existing.id, "imported-id"]
    assert exported[1]["created_at"] == "2026-04-25T12:00:00+00:00"
