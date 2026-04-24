from zprompt_helper.ui.history_panel import summarize_history_entries


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
