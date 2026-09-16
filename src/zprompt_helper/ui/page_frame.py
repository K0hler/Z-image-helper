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
        label="Студия промтов",
        eyebrow="Рабочая область",
        summary="Превращайте идеи в точные и управляемые промты.",
    ),
    "template_manager": PageSpec(
        label="Шаблоны",
        eyebrow="Каталог",
        summary="Используйте встроенные шаблоны и настраивайте свои.",
    ),
    "settings": PageSpec(
        label="Настройки",
        eyebrow="Приложение",
        summary="Управляйте API, моделью и параметрами генерации.",
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

    with st.sidebar:
        st.markdown("## Z · PROMPT")
        st.caption("Локальная студия")
        selected_page = st.radio(
            "Навигация",
            options=page_options,
            index=page_options.index(initial_state.page_id),
            format_func=lambda page_id: page_labels[page_id],
            key="active_page_radio",
            label_visibility="collapsed",
        )
        toggled = st.button(
            "Светлая тема" if initial_state.theme_mode == "dark" else "Тёмная тема",
            key="theme_toggle",
            icon=":material/light_mode:" if initial_state.theme_mode == "dark" else ":material/dark_mode:",
            use_container_width=True,
        )
        st.caption("Готов к работе")

    selected_theme = toggle_theme_mode(initial_state.theme_mode) if toggled else initial_state.theme_mode
    current_state = build_page_shell_state(selected_page, selected_theme)
    st.session_state["active_page"] = current_state.page_id
    st.session_state["theme_mode"] = current_state.theme_mode
    if settings_service is not None and current_state.theme_mode != initial_state.theme_mode:
        settings_service.save_theme_mode(current_state.theme_mode)
    if toggled:
        st.rerun()

    st.title(current_state.spec.label)
    st.caption(current_state.spec.summary)

    return current_state.page_id, current_state.theme_mode
