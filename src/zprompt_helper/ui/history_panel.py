from dataclasses import dataclass
from datetime import UTC, datetime
from contextlib import nullcontext
from typing import Any


@dataclass(frozen=True)
class HistorySummary:
    total_entries: int
    latest_created_at: str | None = None


def build_history_summary(entries: list[dict]) -> HistorySummary:
    ordered_entries = summarize_history_entries(entries)
    latest_created_at = None
    if ordered_entries:
        latest_created_at = _format_created_at(ordered_entries[0]["created_at"])
    return HistorySummary(
        total_entries=len(entries),
        latest_created_at=latest_created_at,
    )


def summarize_history_entries(entries: list[dict]) -> list[dict]:
    return sorted(entries, key=_created_at_sort_key, reverse=True)


def delete_history_entry(history_store, entry: dict) -> None:
    created_at = _parse_created_at(entry["created_at"])
    history_store.delete_entry(created_at.date().isoformat(), entry["id"])


def clear_history(history_store) -> None:
    history_store.clear_all()


def render_history_panel(entries: list[dict], history_store=None) -> None:
    import streamlit as st

    summary = build_history_summary(entries)

    getattr(st, "subheader", lambda *_args, **_kwargs: None)("History")
    with _container(st, border=True):
        st.caption(_build_summary_line(summary))
        if _button(st, "Clear history", key="clear_history", use_container_width=True):
            _handle_clear_history_request(st, history_store)

    for entry in summarize_history_entries(entries):
        with _container(st, border=True):
            st.caption(f"Saved {_format_created_at(entry['created_at'])}")
            st.caption(f"Entry {entry['id']}")
            if _button(st, "Copy prompt", key=f"copy-history-{entry['id']}", use_container_width=True):
                st.session_state["copied_prompt"] = entry["prompt_text"]
                st.success("Prompt prepared for copying.")
            if _button(st, "Delete", key=f"delete-history-{entry['id']}", use_container_width=True):
                if history_store is None:
                    st.error("HistoryStore is not configured.")
                else:
                    delete_history_entry(history_store, entry)
                    st.success("History entry deleted.")
                    st.rerun()
            st.code(entry["prompt_text"])


def _handle_clear_history_request(st, history_store) -> None:
    dialog = getattr(st, "dialog", None)
    if callable(dialog):
        @dialog("Clear history")
        def confirm_clear_history() -> None:
            st.caption("This removes every saved prompt from local history.")
            if _button(st, "Confirm clear", key="confirm-clear-history", use_container_width=True):
                _clear_history_with_feedback(st, history_store)
            _button(st, "Keep history", key="cancel-clear-history", use_container_width=True)

        confirm_clear_history()
        return

    _clear_history_with_feedback(st, history_store)


def _clear_history_with_feedback(st, history_store) -> None:
    if history_store is None:
        st.error("HistoryStore is not configured.")
    else:
        clear_history(history_store)
        st.success("History cleared.")
        st.rerun()


def _build_summary_line(summary: HistorySummary) -> str:
    if summary.total_entries == 0:
        return "Saved 0 prompts"
    if summary.latest_created_at is None:
        return f"Saved {summary.total_entries} prompts"
    return f"Saved {summary.total_entries} prompts. Latest: {summary.latest_created_at}"


def _format_created_at(created_at: Any) -> str:
    return _parse_created_at(created_at).astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _container(st_module, **kwargs: object):
    container_fn = getattr(st_module, "container", None)
    if callable(container_fn):
        try:
            return container_fn(**kwargs)
        except TypeError:
            return container_fn()
    return nullcontext()


def _button(st_module, label: str, **kwargs: object) -> bool:
    button_fn = getattr(st_module, "button")
    try:
        return bool(button_fn(label, **kwargs))
    except TypeError:
        safe_kwargs = {key: value for key, value in kwargs.items() if key == "key"}
        return bool(button_fn(label, **safe_kwargs))


def _created_at_sort_key(entry: dict[str, Any]) -> float:
    parsed = _parse_created_at(entry["created_at"])
    return parsed.astimezone(UTC).timestamp()


def _parse_created_at(created_at: Any) -> datetime:
    if isinstance(created_at, datetime):
        parsed = created_at
    else:
        parsed = datetime.fromisoformat(str(created_at))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed
