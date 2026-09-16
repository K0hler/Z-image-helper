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


def render_history_panel(
    entries: list[dict],
    history_store=None,
    *,
    show_heading: bool = True,
    page_size: int | None = None,
) -> None:
    import streamlit as st

    summary = build_history_summary(entries)

    if show_heading:
        getattr(st, "subheader", lambda *_args, **_kwargs: None)("История")
    with _container(st):
        st.caption(_build_summary_line(summary))
        if _button(st, "Очистить историю", key="clear_history"):
            _handle_clear_history_request(st, history_store)

    ordered_entries = summarize_history_entries(entries)
    visible_count = len(ordered_entries)
    if page_size is not None:
        visible_count = max(
            page_size,
            int(st.session_state.get("_workbench_history_visible_count", page_size)),
        )
    visible_entries = ordered_entries[:visible_count]

    for entry in visible_entries:
        with _container(st, border=True):
            st.caption(f"Сохранено {_format_created_at(entry['created_at'])}")
            if _button(st, "Копировать", key=f"copy-history-{entry['id']}"):
                st.session_state["copied_prompt"] = entry["prompt_text"]
                st.success("Промт подготовлен для копирования.")
            if _button(st, "Удалить", key=f"delete-history-{entry['id']}"):
                if history_store is None:
                    st.error("Хранилище истории не настроено.")
                else:
                    delete_history_entry(history_store, entry)
                    st.success("Запись удалена.")
                    st.rerun()
            st.code(entry["prompt_text"])

    if page_size is not None and visible_count < len(ordered_entries):
        st.caption(f"Показано {len(visible_entries)} из {len(ordered_entries)}")
        if _button(st, "Показать ещё", key="show-more-history"):
            st.session_state["_workbench_history_visible_count"] = visible_count + page_size
            st.rerun()


def _handle_clear_history_request(st, history_store) -> None:
    dialog = getattr(st, "dialog", None)
    if callable(dialog):
        @dialog("Очистить историю")
        def confirm_clear_history() -> None:
            st.caption("Все сохранённые промты будут удалены из локальной истории.")
            if _button(st, "Очистить", key="confirm-clear-history"):
                _clear_history_with_feedback(st, history_store)
            _button(st, "Отмена", key="cancel-clear-history")

        confirm_clear_history()
        return

    _clear_history_with_feedback(st, history_store)


def _clear_history_with_feedback(st, history_store) -> None:
    if history_store is None:
        st.error("Хранилище истории не настроено.")
    else:
        clear_history(history_store)
        st.success("История очищена.")
        st.rerun()


def _build_summary_line(summary: HistorySummary) -> str:
    if summary.total_entries == 0:
        return "Сохранённых промтов пока нет"
    if summary.latest_created_at is None:
        return f"Сохранено промтов: {summary.total_entries}"
    return f"Сохранено: {summary.total_entries} · последний {summary.latest_created_at}"


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
