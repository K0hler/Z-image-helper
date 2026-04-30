from datetime import UTC, datetime

from zprompt_helper.storage.idea_history_store import IdeaHistoryStore
from zprompt_helper.storage.paths import ProjectPaths


def test_idea_history_store_writes_entries_to_date_named_files(tmp_path) -> None:
    store = IdeaHistoryStore(ProjectPaths.from_root(tmp_path))

    entry = store.append(
        idea_text="A rainy cyberpunk courier",
        created_at=datetime(2026, 4, 30, 10, 15, tzinfo=UTC),
    )

    history_file = tmp_path / "data" / "idea_history" / "2026-04-30.json"
    assert history_file.exists()
    assert entry.idea_text == "A rainy cyberpunk courier"


def test_idea_history_store_exports_entries_latest_first(tmp_path) -> None:
    store = IdeaHistoryStore(ProjectPaths.from_root(tmp_path))

    earlier = store.append("earlier", created_at=datetime(2026, 4, 29, 10, tzinfo=UTC))
    later = store.append("later", created_at=datetime(2026, 4, 30, 10, tzinfo=UTC))

    exported = store.export_all()

    assert [item["id"] for item in exported] == [later.id, earlier.id]


def test_idea_history_store_skips_blank_and_duplicate_ideas(tmp_path) -> None:
    store = IdeaHistoryStore(ProjectPaths.from_root(tmp_path))

    assert store.append_if_new("  ") is None
    first = store.append_if_new("  robot portrait  ")
    duplicate = store.append_if_new("robot portrait")

    assert first is not None
    assert duplicate is None
    assert [item["idea_text"] for item in store.export_all()] == ["robot portrait"]
