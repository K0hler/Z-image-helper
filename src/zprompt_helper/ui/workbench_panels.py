from dataclasses import dataclass
from typing import Any

from zprompt_helper.domain.models import TemplateDefinition
from zprompt_helper.workbench.session import EditorSession


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


def render_workbench_header_panel(
    st_module: Any,
    *,
    template_names: list[str],
    selected_name: str,
    summary: WorkbenchSummary,
    short_idea: str,
) -> str:
    with _container(st_module, border=True, key="workbench_header_panel"):
        _caption(st_module, "Prompt studio")
        selected_name = st_module.selectbox(
            "Шаблон",
            options=template_names,
            key="selected_template_id",
        )
        _status_chip(
            st_module,
            "Saved draft" if summary.filled_count or summary.has_final_prompt else "New draft",
            tone="accent" if summary.filled_count or summary.has_final_prompt else "muted",
            icon="✦" if summary.filled_count or summary.has_final_prompt else "○",
        )
        _caption(st_module, f"Shared idea: {short_idea.strip() or 'Not set yet'}")
    return selected_name


def render_workbench_editor_panel(
    st_module: Any,
    *,
    template: TemplateDefinition,
    session: EditorSession,
    generating: bool = False,
) -> dict[str, bool]:
    with _container(st_module, border=True, key="workbench_editor_panel"):
        _subheader(st_module, "Block editor")

        with _container(st_module, key="editor_gen_row"):
            col1, col2 = _columns(st_module, [1, 1])
            generate = col1.button("Сгенерировать", key="generate", disabled=generating)
            regenerate = col2.button(
                "Перегенерировать незаблокированные",
                key="regenerate_unlocked",
                disabled=generating,
            )

        with _container(st_module, key="editor_ctrl_row"):
            col3, col4, col5 = _columns(st_module, [1, 1, 1])
            clear_unlocked = col3.button("Очистить незаблокированные", key="clear_unlocked")
            lock_all = col4.button("Заблокировать все блоки", key="lock_all")
            unlock_all = col5.button("Разблокировать все блоки", key="unlock_all")

        with _container(st_module, key="short_idea_section"):
            _markdown(
                st_module,
                '<p class="zp-idea-label">✦ Ваша идея</p>',
                unsafe_allow_html=True,
            )
            if "short_idea" not in st_module.session_state:
                st_module.session_state["short_idea"] = session.short_idea
            session.short_idea = st_module.text_area(
                "Кратко о том, что хотите создать",
                key="short_idea",
                height=100,
                label_visibility="collapsed",
            )
        divider_fn = getattr(st_module, "divider", None)
        if callable(divider_fn):
            divider_fn()
        for block_id in template.block_order:
            block = template.blocks[block_id]
            if not block.enabled:
                continue
            locked = st_module.checkbox(
                block.label,
                value=block_id in session.locked_blocks,
                key=f"lock-{template.id}-{block_id}",
                help="Зафиксировать блок",
            )
            block_key = f"block-{template.id}-{block_id}"
            if block_key not in st_module.session_state:
                st_module.session_state[block_key] = session.block_values.get(block_id, "")
            session.block_values[block_id] = st_module.text_area(
                block.label,
                key=block_key,
                label_visibility="collapsed",
            )
            if locked:
                session.locked_blocks.add(block_id)
            else:
                session.locked_blocks.discard(block_id)

    return {
        "generate": generate,
        "regenerate": regenerate,
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
) -> dict[str, bool]:
    with _container(st_module, border=True, key="workbench_output_panel"):
        _subheader(st_module, "Prompt output")
        _status_chip(
            st_module,
            f"Variation {summary.variation_index}",
            tone="accent" if summary.variation_index else "muted",
            icon="◌" if summary.variation_index else "—",
        )
        with _container(st_module):
            if generating:
                _markdown(st_module, "⏳ **Генерирую промт…**")
            else:
                final_prompt_key = f"final-prompt-{template.id}"
                if final_prompt_key not in st_module.session_state:
                    st_module.session_state[final_prompt_key] = session.final_prompt
                session.final_prompt = st_module.text_area(
                    "Финальный промт",
                    key=final_prompt_key,
                    height=180,
                )

        with _container(st_module):
            col1, col2 = _columns(st_module, [1, 1])
            rebuild = col1.button("Пересобрать промт", key="rebuild_prompt")
            copy_prompt = col2.button("Скопировать промт", key="copy_prompt")

    return {
        "rebuild": rebuild,
        "copy_prompt": copy_prompt,
    }


def _columns(st_module: Any, spec: list[float]) -> list[Any]:
    columns_fn = getattr(st_module, "columns")
    try:
        return list(columns_fn(spec, gap="small"))
    except TypeError:
        return list(columns_fn(len(spec)))


def _container(st_module: Any, **kwargs: object):
    container_fn = getattr(st_module, "container", None)
    if callable(container_fn):
        try:
            return container_fn(**kwargs)
        except TypeError:
            return container_fn()
    from contextlib import nullcontext

    return nullcontext()


def _subheader(st_module: Any, label: str) -> None:
    getattr(st_module, "subheader", lambda *_args, **_kwargs: None)(label)


def _caption(st_module: Any, label: str) -> None:
    markdown_fn = getattr(st_module, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(label)
        return
    write_fn = getattr(st_module, "write", None)
    if callable(write_fn):
        write_fn(label)


def _markdown(st_module: Any, body: str, **kwargs: object) -> None:
    markdown_fn = getattr(st_module, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(body, **kwargs)
        return
    _caption(st_module, body)


def _status_chip(st_module: Any, label: str, *, tone: str, icon: str) -> None:
    safe_tone = tone if tone in {"accent", "muted"} else "muted"
    _markdown(
        st_module,
        (
            f'<div class="zp-status-chip zp-status-chip--{safe_tone}">'
            f'<span class="zp-status-chip__icon">{icon}</span>'
            f"<span>{label}</span>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
