from datetime import datetime
from typing import Any


def summarize_history_entries(entries: list[dict]) -> list[dict]:
    return sorted(entries, key=_created_at_sort_key, reverse=True)


def render_history_panel(entries: list[dict]) -> None:
    import streamlit as st

    st.subheader("История")
    for entry in summarize_history_entries(entries):
        with st.expander(str(entry["created_at"])):
            st.code(entry["prompt_text"])
            st.button("Скопировать", key=f"copy-history-{entry['id']}")
            st.button("Удалить", key=f"delete-history-{entry['id']}")
    st.button("Очистить историю", key="clear_history")


def _created_at_sort_key(entry: dict[str, Any]) -> datetime:
    created_at = entry["created_at"]
    if isinstance(created_at, datetime):
        return created_at
    return datetime.fromisoformat(str(created_at))
