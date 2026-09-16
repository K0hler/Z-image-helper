import sys
from contextlib import contextmanager

from zprompt_helper.ui.history_panel import (
    build_history_summary,
    clear_history,
    delete_history_entry,
    render_history_panel,
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


def test_build_history_summary_counts_entries() -> None:
    summary = build_history_summary(
        [
            {"id": "1", "prompt_text": "one", "created_at": "2026-04-24T10:00:00+00:00"},
            {"id": "2", "prompt_text": "two", "created_at": "2026-04-24T12:00:00+00:00"},
        ]
    )

    assert summary.total_entries == 2


class FakeStreamlit:
    def __init__(self, button_presses: dict[str, bool] | None = None) -> None:
        self.session_state: dict[str, object] = {}
        self.button_presses = button_presses or {}
        self.events: list[str] = []
        self.success_messages: list[str] = []
        self.error_messages: list[str] = []
        self.rerun_requested = False
        self.dialog_calls: list[str] = []

    def subheader(self, label: str) -> None:
        self.events.append(f"subheader:{label}")

    def caption(self, message: str) -> None:
        self.events.append(f"caption:{message}")

    def markdown(self, body: str) -> None:
        self.events.append(f"markdown:{body}")

    def code(self, body: str) -> None:
        self.events.append(f"code:{body}")

    def success(self, message: str) -> None:
        self.success_messages.append(message)

    def error(self, message: str) -> None:
        self.error_messages.append(message)

    def button(self, label: str, *, key: str, **_: object) -> bool:
        self.events.append(f"button:{label}:{key}")
        return self.button_presses.get(key, False)

    def container(self, **_: object):
        return _nullcontext()

    def columns(self, spec: int | list[float], **_: object):
        count = spec if isinstance(spec, int) else len(spec)
        return [self for _ in range(count)]

    def rerun(self) -> None:
        self.rerun_requested = True

    def dialog(self, title: str, **_: object):
        def decorator(func):
            def wrapper(*args, **kwargs):
                self.dialog_calls.append(title)
                return func(*args, **kwargs)

            return wrapper

        return decorator


@contextmanager
def _nullcontext():
    yield


def test_render_history_panel_shows_metadata_before_prompt_content(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)

    render_history_panel(
        [{"id": "1", "prompt_text": "robot prompt", "created_at": "2026-04-24T10:00:00+00:00"}]
    )

    metadata_index = next(
        i
        for i, event in enumerate(fake_st.events)
        if event.startswith("caption:Сохранено ")
    )
    prompt_index = fake_st.events.index("code:robot prompt")
    assert metadata_index < prompt_index


def test_render_history_panel_delete_flow_uses_store_and_requests_rerun(monkeypatch) -> None:
    fake_st = FakeStreamlit(button_presses={"delete-history-entry-1": True})
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    store = FakeHistoryStore()

    render_history_panel(
        [{"id": "entry-1", "prompt_text": "robot prompt", "created_at": "2026-04-24T10:00:00+00:00"}],
        history_store=store,
    )

    assert store.deleted == [("2026-04-24", "entry-1")]
    assert fake_st.rerun_requested is True


def test_render_history_panel_clear_flow_uses_confirmation_dialog_when_available(monkeypatch) -> None:
    fake_st = FakeStreamlit(
        button_presses={
            "clear_history": True,
            "confirm-clear-history": True,
        }
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    store = FakeHistoryStore()

    render_history_panel(
        [{"id": "entry-1", "prompt_text": "robot prompt", "created_at": "2026-04-24T10:00:00+00:00"}],
        history_store=store,
    )

    assert fake_st.dialog_calls == ["Очистить историю"]
    assert store.clear_count == 1
    assert fake_st.rerun_requested is True


def test_render_history_panel_limits_initial_workbench_history(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    entries = [
        {
            "id": str(index),
            "prompt_text": f"prompt {index}",
            "created_at": f"2026-04-{index + 1:02d}T10:00:00+00:00",
        }
        for index in range(10)
    ]

    render_history_panel(entries, page_size=3)

    assert len([event for event in fake_st.events if event.startswith("code:")]) == 3
    assert "button:Показать ещё:show-more-history" in fake_st.events
