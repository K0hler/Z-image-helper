from dataclasses import dataclass
from typing import Literal

from zprompt_helper.ui.shadcn import normalize_nav_items
from zprompt_helper.ui.theme import normalize_theme_mode


@dataclass(frozen=True)
class PageSpec:
    label: str
    eyebrow: str
    summary: str


@dataclass(frozen=True)
class PageShellState:
    page_id: str
    theme_mode: Literal["light", "dark"]
    spec: PageSpec


PAGE_SPECS: dict[str, PageSpec] = {
    "workbench": PageSpec(
        label="Workbench",
        eyebrow="Prompt Studio",
        summary="Build, regenerate, and polish prompts without leaving the editor flow.",
    ),
    "template_manager": PageSpec(
        label="Template Manager",
        eyebrow="Template Catalog",
        summary="Browse built-ins and manage your local custom prompt templates.",
    ),
    "settings": PageSpec(
        label="Settings",
        eyebrow="API And App Defaults",
        summary="Control model defaults, generation settings, and API access.",
    ),
}


def normalize_page_id(page_id: str | None) -> str:
    if page_id in PAGE_SPECS:
        return str(page_id)
    return "workbench"


def build_page_shell_state(
    page_id: str | None,
    theme_mode: str | None,
) -> PageShellState:
    normalized_page = normalize_page_id(page_id)
    normalized_theme = normalize_theme_mode(theme_mode)
    return PageShellState(
        page_id=normalized_page,
        theme_mode=normalized_theme,
        spec=PAGE_SPECS[normalized_page],
    )


def page_nav_items() -> list[dict[str, str]]:
    return normalize_nav_items(
        {"id": page_id, "label": spec.label} for page_id, spec in PAGE_SPECS.items()
    )


def toggle_theme_mode(theme_mode: str | None) -> Literal["light", "dark"]:
    if normalize_theme_mode(theme_mode) == "dark":
        return "light"
    return "dark"


def render_page_shell(
    active_page: str | None,
    theme_mode: str | None,
    settings_service=None,
) -> tuple[str, Literal["light", "dark"]]:
    import streamlit as st

    initial_state = build_page_shell_state(active_page, theme_mode)
    nav_items = page_nav_items()
    page_options = [item["id"] for item in nav_items]
    page_labels = {item["id"]: item["label"] for item in nav_items}

    with st.container():
        st.markdown('<div class="zp-toolbar">', unsafe_allow_html=True)
        nav_col, theme_col = st.columns([1.0, 0.2], gap="small")
        with nav_col:
            st.markdown('<div class="zp-toolbar__nav">', unsafe_allow_html=True)
            selected_page = st.radio(
                "Page",
                options=page_options,
                index=page_options.index(initial_state.page_id),
                format_func=lambda page_id: page_labels[page_id],
                key="active_page_radio",
                horizontal=True,
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)
        with theme_col:
            st.markdown('<div class="zp-toolbar__theme">', unsafe_allow_html=True)
            toggled = st.button(
                "Toggle theme",
                key="theme_toggle",
                use_container_width=True,
            )
            selected_theme = toggle_theme_mode(initial_state.theme_mode) if toggled else initial_state.theme_mode
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        current_state = build_page_shell_state(selected_page, selected_theme)
        st.session_state["active_page"] = current_state.page_id
        st.session_state["theme_mode"] = current_state.theme_mode
        if settings_service is not None and current_state.theme_mode != initial_state.theme_mode:
            settings_service.save_theme_mode(current_state.theme_mode)
        st.markdown(
            (
                '<section class="zp-page-shell">'
                f'<p class="zp-page-shell__eyebrow">{current_state.spec.eyebrow}</p>'
                f'<h1 class="zp-page-shell__title">{current_state.spec.label}</h1>'
                f'<p class="zp-page-shell__summary">{current_state.spec.summary}</p>'
                "</section>"
            ),
            unsafe_allow_html=True,
        )

    return current_state.page_id, current_state.theme_mode
