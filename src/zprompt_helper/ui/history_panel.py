from datetime import UTC, datetime
from typing import Any


def summarize_history_entries(entries: list[dict]) -> list[dict]:
    return sorted(entries, key=_created_at_sort_key, reverse=True)


def delete_history_entry(history_store, entry: dict) -> None:
    created_at = _parse_created_at(entry["created_at"])
    history_store.delete_entry(created_at.date().isoformat(), entry["id"])


def clear_history(history_store) -> None:
    history_store.clear_all()


def render_history_panel(entries: list[dict], history_store=None) -> None:
    import streamlit as st

    st.subheader("История")
    for entry in summarize_history_entries(entries):
        with st.expander(str(entry["created_at"])):
            st.code(entry["prompt_text"])
            if st.button("Скопировать", key=f"copy-history-{entry['id']}"):
                st.session_state["copied_prompt"] = entry["prompt_text"]
                st.success("Промт подготовлен к копированию.")
            if st.button("Удалить", key=f"delete-history-{entry['id']}"):
                if history_store is None:
                    st.error("HistoryStore is not configured.")
                else:
                    delete_history_entry(history_store, entry)
                    st.success("Запись удалена.")
                    st.rerun()
    if st.button("Очистить историю", key="clear_history"):
        if history_store is None:
            st.error("HistoryStore is not configured.")
        else:
            clear_history(history_store)
            st.success("История очищена.")
            st.rerun()


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
