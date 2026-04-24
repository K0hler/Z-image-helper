from zprompt_helper.ui.history_panel import (
    clear_history,
    delete_history_entry,
    summarize_history_entries,
)


class FakeHistoryStore:
    def __init__(self) -> None:
        self.deleted: list[tuple[str, str]] = []
        self.clear_count = 0

    def delete_entry(self, date_key: str, entry_id: str) -> None:
        self.deleted.append((date_key, entry_id))

    def clear_all(self) -> None:
        self.clear_count += 1


def test_summarize_history_entries_returns_latest_first() -> None:
    items = [
        {"id": "1", "prompt_text": "first", "created_at": "2026-04-24T10:00:00+00:00"},
        {"id": "2", "prompt_text": "second", "created_at": "2026-04-24T12:00:00+00:00"},
    ]

    summary = summarize_history_entries(items)

    assert summary[0]["id"] == "2"


def test_summarize_history_entries_handles_iso_strings_with_timezone() -> None:
    items = [
        {"id": "utc", "prompt_text": "first", "created_at": "2026-04-24T10:00:00+00:00"},
        {"id": "yekaterinburg", "prompt_text": "second", "created_at": "2026-04-24T15:00:00+05:00"},
        {"id": "later", "prompt_text": "third", "created_at": "2026-04-24T10:30:00+00:00"},
    ]

    summary = summarize_history_entries(items)

    assert [item["id"] for item in summary] == ["later", "utc", "yekaterinburg"]


def test_summarize_history_entries_handles_mixed_naive_and_aware_iso_strings() -> None:
    items = [
        {"id": "naive", "prompt_text": "first", "created_at": "2026-04-24T10:00:00"},
        {"id": "aware", "prompt_text": "second", "created_at": "2026-04-24T12:00:00+00:00"},
    ]

    summary = summarize_history_entries(items)

    assert [item["id"] for item in summary] == ["aware", "naive"]


def test_delete_history_entry_derives_date_key_from_created_at() -> None:
    store = FakeHistoryStore()

    delete_history_entry(
        store,
        {"id": "entry-1", "prompt_text": "prompt", "created_at": "2026-04-24T23:30:00+05:00"},
    )

    assert store.deleted == [("2026-04-24", "entry-1")]


def test_clear_history_calls_store() -> None:
    store = FakeHistoryStore()

    clear_history(store)

    assert store.clear_count == 1
