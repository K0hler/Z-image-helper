from typing import Any

from zprompt_helper.ui.shadcn import normalize_nav_items


PAGE_SPECS = {
    "workbench": {
        "label": "Workbench",
        "eyebrow": "Prompt studio",
        "description": "Shape, lock, and regenerate prompt blocks without losing stable session flow.",
    },
    "template_manager": {
        "label": "Template Manager",
        "eyebrow": "Template catalog",
        "description": "Browse built-in structures, clone them, and maintain local custom templates.",
    },
    "settings": {
        "label": "Settings",
        "eyebrow": "OpenRouter and app defaults",
        "description": "Store the API key safely and tune default generation behavior for the workbench.",
    },
}


def normalize_page_id(page_id: str | None) -> str:
    if page_id in PAGE_SPECS:
        return str(page_id)
    return "workbench"


def render_page_shell(active_page: str | None) -> str:
    import streamlit as st

    normalized = normalize_page_id(active_page or st.session_state.get("active_page"))
    st.session_state["active_page"] = normalized
    spec = PAGE_SPECS[normalized]
    nav_items = normalize_nav_items(
        [{"id": page_id, "label": item["label"]} for page_id, item in PAGE_SPECS.items()]
    )

    with st.container(border=True, key="zp-page-shell"):
        st.markdown(
            "\n".join(
                [
                    '<div class="zp-shell">',
                    f'<div class="zp-shell__eyebrow">{spec["eyebrow"]}</div>',
                    f'<div class="zp-shell__title">{spec["label"]}</div>',
                    f'<div class="zp-shell__lede">{spec["description"]}</div>',
                    "</div>",
                ]
            ),
            unsafe_allow_html=True,
        )

        labels = [item["label"] for item in nav_items]
        page_by_label = {item["label"]: item["id"] for item in nav_items}
        selector = _select_page(st, labels, spec["label"])
        normalized = normalize_page_id(page_by_label.get(selector))
        st.session_state["active_page"] = normalized

    return normalized


def _select_page(st_module: Any, labels: list[str], current_label: str) -> str:
    segmented_control = getattr(st_module, "segmented_control", None)
    if callable(segmented_control):
        return str(
            segmented_control(
                "Section",
                options=labels,
                default=current_label,
                key="active_page_control",
            )
        )

    radio = getattr(st_module, "radio", None)
    if callable(radio):
        try:
            return str(
                radio(
                    "Section",
                    options=labels,
                    key="active_page_control",
                    horizontal=True,
                    label_visibility="collapsed",
                )
            )
        except TypeError:
            return str(radio("Section", options=labels, key="active_page_control"))

    return current_label
