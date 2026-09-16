from contextlib import nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from zprompt_helper.domain.models import TemplateDefinition
from zprompt_helper.ui.history_panel import render_history_panel
from zprompt_helper.workbench.session import EditorSession


BLOCK_LABELS = {
    "subject": "Объект",
    "scene": "Сцена",
    "composition": "Композиция",
    "lighting": "Свет",
    "style": "Стиль",
    "details": "Детали",
    "constraints": "Ограничения",
    "shot": "Камера",
    "color_grade": "Цвет",
    "environment": "Окружение",
    "camera": "Камера",
    "materials": "Материалы",
    "concept": "Концепция",
    "medium": "Техника",
    "palette": "Палитра",
    "identity": "Персонаж",
    "appearance": "Внешность",
    "pose": "Поза",
    "wardrobe": "Одежда",
    "location": "Локация",
    "time_weather": "Время и погода",
    "architecture_nature": "Архитектура и природа",
    "atmosphere": "Атмосфера",
    "headline": "Заголовок",
    "subheadline": "Подзаголовок",
    "cta": "Призыв к действию",
    "layout": "Макет",
}


@dataclass(frozen=True)
class WorkbenchSummary:
    active_block_count: int
    filled_count: int
    locked_count: int
    variation_index: int
    has_final_prompt: bool


def build_workbench_summary(
    session: EditorSession,
    active_block_count: int,
) -> WorkbenchSummary:
    filled_count = sum(1 for value in session.block_values.values() if str(value).strip())
    return WorkbenchSummary(
        active_block_count=active_block_count,
        filled_count=filled_count,
        locked_count=len(session.locked_blocks),
        variation_index=session.variation_index,
        has_final_prompt=bool(session.final_prompt.strip()),
    )


def block_display_label(block_id: str, fallback: str) -> str:
    return BLOCK_LABELS.get(block_id, fallback)


def render_workbench_header_panel(
    st_module: Any,
    *,
    template_names: list[str],
    selected_name: str,
    summary: WorkbenchSummary,
    short_idea: str,
    generating: bool = False,
    idea_history_entries: list[dict] | None = None,
) -> dict[str, Any]:
    with _container(st_module, border=True, key="workbench_composer_panel"):
        _subheader(st_module, "Начните с идеи")
        _caption(st_module, "Опишите замысел своими словами — блоки можно уточнить позже.")
        if "short_idea" not in st_module.session_state:
            st_module.session_state["short_idea"] = short_idea
        idea_text = st_module.text_area(
            "Идея",
            key="short_idea",
            height=116,
            placeholder="Например: футуристический город на скалах на закате…",
        )
        selected_name = st_module.selectbox(
            "Шаблон",
            options=template_names,
            index=template_names.index(selected_name),
            key="selected_template_id",
        )
        generate = _button(
            st_module,
            "Сгенерировать",
            key="generate",
            type="primary",
            icon=":material/auto_awesome:",
            use_container_width=True,
            disabled=generating,
        )

        selected_idea_id = ""
        use_idea_history = False
        with _container(st_module, horizontal=True, key="composer_secondary_actions"):
            save_idea = _button(
                st_module,
                "Сохранить идею",
                key="save_idea_history",
                icon=":material/bookmark_add:",
                disabled=generating,
            )
            entries = idea_history_entries or []
            if entries:
                with _popover(
                    st_module,
                    "История идей",
                    icon=":material/history:",
                    disabled=generating,
                ):
                    for entry in entries:
                        entry_id = str(entry["id"])
                        if _button(
                            st_module,
                            _format_idea_option(entry_id, entries),
                            key=f"use-idea-history-{entry_id}",
                            disabled=generating,
                        ):
                            selected_idea_id = entry_id
                            use_idea_history = True

        draft_label = "Сохранено" if summary.filled_count or summary.has_final_prompt else "Новый черновик"
        _caption(
            st_module,
            f"{draft_label} · заполнено {summary.filled_count} из {summary.active_block_count} блоков",
        )

    return {
        "selected_name": selected_name,
        "short_idea": idea_text,
        "generate": generate,
        "save_idea": save_idea,
        "use_idea_history": use_idea_history,
        "selected_idea_id": selected_idea_id,
    }


def render_workbench_editor_panel(
    st_module: Any,
    *,
    template: TemplateDefinition,
    session: EditorSession,
    generating: bool = False,
    idea_history_entries: list[dict] | None = None,
) -> dict[str, bool]:
    del idea_history_entries
    with _container(st_module, border=True, key="workbench_editor_panel"):
        _subheader(st_module, "Блоки промта")
        _caption(st_module, "Откройте только тот блок, который хотите уточнить.")

        with _popover(st_module, "Действия с блоками", icon=":material/tune:"):
            clear_unlocked = _button(
                st_module,
                "Очистить незакреплённые",
                key="clear_unlocked",
                disabled=generating,
            )
            lock_all = _button(
                st_module,
                "Закрепить все",
                key="lock_all",
                disabled=generating,
            )
            unlock_all = _button(
                st_module,
                "Открепить все",
                key="unlock_all",
                disabled=generating,
            )

        visible_index = 0
        for block_id in template.block_order:
            block = template.blocks[block_id]
            if not block.enabled:
                continue
            block_key = f"block-{template.id}-{block_id}"
            if block_key not in st_module.session_state:
                st_module.session_state[block_key] = session.block_values.get(block_id, "")
            current_value = str(st_module.session_state.get(block_key, ""))
            label = block_display_label(block_id, block.label)
            preview = _block_preview(current_value)
            expander_label = f"{label}  ·  {preview}" if preview else label
            locked_by_default = block_id in session.locked_blocks
            with _expander(
                st_module,
                expander_label,
                expanded=visible_index == 0,
                icon=":material/lock:" if locked_by_default else ":material/edit_note:",
            ):
                locked = _toggle(
                    st_module,
                    "Закрепить блок",
                    value=locked_by_default,
                    key=f"lock-{template.id}-{block_id}",
                    help="Закреплённый блок не изменится при следующей генерации.",
                )
                session.block_values[block_id] = st_module.text_area(
                    label,
                    key=block_key,
                    height=96,
                    placeholder=block.instruction,
                    label_visibility="collapsed",
                )
                if locked:
                    session.locked_blocks.add(block_id)
                else:
                    session.locked_blocks.discard(block_id)
            visible_index += 1

    return {
        "clear_unlocked": clear_unlocked,
        "lock_all": lock_all,
        "unlock_all": unlock_all,
    }


def render_workbench_output_panel(
    st_module: Any,
    *,
    session: EditorSession,
    template: TemplateDefinition,
    summary: WorkbenchSummary,
    generating: bool = False,
    history_entries: list[dict] | None = None,
    history_store: Any = None,
) -> dict[str, bool]:
    with _container(st_module, border=True, key="workbench_output_panel"):
        prompt_tab, history_tab = _tabs(st_module, ["Финальный промт", "История"])
        with prompt_tab:
            _caption(
                st_module,
                f"Заполнено {summary.filled_count} из {summary.active_block_count} блоков"
                + (f" · вариант {summary.variation_index}" if summary.variation_index else ""),
            )
            if generating:
                _markdown(st_module, "**Генерирую промт…**")
            else:
                final_prompt_key = f"final-prompt-{template.id}"
                if final_prompt_key not in st_module.session_state:
                    st_module.session_state[final_prompt_key] = session.final_prompt
                session.final_prompt = st_module.text_area(
                    "Финальный промт",
                    key=final_prompt_key,
                    height=330,
                    placeholder="Готовый промт появится здесь.",
                    label_visibility="collapsed",
                )

            with _container(st_module, horizontal=True, key="output_action_row"):
                copy_prompt = _button(
                    st_module,
                    "Копировать",
                    key="copy_prompt",
                    icon=":material/content_copy:",
                    disabled=generating or not summary.has_final_prompt,
                )
                regenerate = _button(
                    st_module,
                    "Новая версия",
                    key="regenerate_unlocked",
                    icon=":material/refresh:",
                    disabled=generating,
                )
                with _popover(st_module, "Ещё", icon=":material/more_horiz:"):
                    rebuild = _button(
                        st_module,
                        "Пересобрать из блоков",
                        key="rebuild_prompt",
                        disabled=generating,
                    )

        with history_tab:
            render_history_panel(
                history_entries or [],
                history_store=history_store,
                show_heading=False,
                page_size=8,
            )

    return {
        "regenerate": regenerate,
        "rebuild": rebuild,
        "copy_prompt": copy_prompt,
    }


def _block_preview(value: str, limit: int = 52) -> str:
    preview = " ".join(value.split())
    if len(preview) <= limit:
        return preview
    return f"{preview[: limit - 1].rstrip()}…"


def _container(st_module: Any, **kwargs: object):
    container_fn = getattr(st_module, "container", None)
    if callable(container_fn):
        try:
            return container_fn(**kwargs)
        except TypeError:
            return container_fn()
    return nullcontext()


def _popover(st_module: Any, label: str, **kwargs: object):
    popover_fn = getattr(st_module, "popover", None)
    if callable(popover_fn):
        try:
            return popover_fn(label, **kwargs)
        except TypeError:
            return popover_fn(label)
    return _container(st_module)


def _expander(st_module: Any, label: str, **kwargs: object):
    expander_fn = getattr(st_module, "expander", None)
    if callable(expander_fn):
        try:
            return expander_fn(label, **kwargs)
        except TypeError:
            return expander_fn(label)
    return _container(st_module)


def _tabs(st_module: Any, labels: list[str]) -> list[Any]:
    tabs_fn = getattr(st_module, "tabs", None)
    if callable(tabs_fn):
        return list(tabs_fn(labels))
    return [nullcontext() for _ in labels]


def _button(st_module: Any, label: str, **kwargs: object) -> bool:
    button_fn = getattr(st_module, "button")
    try:
        return bool(button_fn(label, **kwargs))
    except TypeError:
        safe_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key in {"key", "disabled"}
        }
        return bool(button_fn(label, **safe_kwargs))


def _toggle(
    st_module: Any,
    label: str,
    *,
    value: bool,
    key: str,
    help: str,
) -> bool:
    toggle_fn = getattr(st_module, "toggle", None)
    if callable(toggle_fn):
        try:
            return bool(toggle_fn(label, value=value, key=key, help=help))
        except TypeError:
            pass
    return bool(st_module.checkbox(label, value=value, key=key, help=help))


def _subheader(st_module: Any, label: str) -> None:
    getattr(st_module, "subheader", lambda *_args, **_kwargs: None)(label)


def _caption(st_module: Any, label: str) -> None:
    caption_fn = getattr(st_module, "caption", None)
    if callable(caption_fn):
        caption_fn(label)
        return
    _markdown(st_module, label)


def _markdown(st_module: Any, body: str, **kwargs: object) -> None:
    markdown_fn = getattr(st_module, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(body, **kwargs)
        return
    write_fn = getattr(st_module, "write", None)
    if callable(write_fn):
        write_fn(body)


def _format_idea_option(entry_id: str, entries: list[dict]) -> str:
    if not entry_id:
        return "Выберите идею из истории"
    entry = next((item for item in entries if item["id"] == entry_id), None)
    if entry is None:
        return entry_id
    created_at = _format_created_at(entry.get("created_at"))
    preview = str(entry.get("idea_text", "")).strip().replace("\n", " ")
    if len(preview) > 72:
        preview = f"{preview[:69]}..."
    return f"{created_at} — {preview}"


def _format_created_at(created_at: Any) -> str:
    try:
        parsed = datetime.fromisoformat(str(created_at))
    except ValueError:
        return "Сохранено"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
