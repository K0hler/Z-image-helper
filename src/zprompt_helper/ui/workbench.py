import subprocess
import sys
from contextlib import nullcontext
from typing import Any

from zprompt_helper.domain.models import TemplateDefinition
from zprompt_helper.ui.workbench_panels import (
    build_workbench_summary,
    render_workbench_editor_panel,
    render_workbench_header_panel,
    render_workbench_output_panel,
)
from zprompt_helper.workbench.session import (
    EditorSession,
    activate_template,
    current_template_has_meaningful_draft,
    merge_generated_blocks,
    rebuild_prompt,
)


def build_generation_request(
    template: TemplateDefinition,
    session: EditorSession,
    regenerate_unlocked: bool = False,
    variation_index: int = 0,
) -> dict[str, Any]:
    active_blocks = [
        block_id
        for block_id in template.block_order
        if template.blocks[block_id].enabled
    ]
    return {
        "short_idea": session.short_idea,
        "active_blocks": active_blocks,
        "template_prompt": template.template_system_prompt,
        "block_instructions": {
            block_id: template.blocks[block_id].instruction
            for block_id in active_blocks
        },
        "current_values": {
            block_id: session.block_values.get(block_id, "")
            for block_id in active_blocks
            if block_id in session.locked_blocks and session.block_values.get(block_id, "").strip()
        },
        "locked_blocks": session.locked_blocks.intersection(active_blocks),
        "regenerate_unlocked": regenerate_unlocked,
        "variation_index": variation_index,
        "avoid_values": {
            block_id: session.block_values.get(block_id, "")
            for block_id in active_blocks
            if regenerate_unlocked
            and block_id not in session.locked_blocks
            and session.block_values.get(block_id, "").strip()
        },
    }


def record_prompt_if_present(history_store: Any, prompt_text: str) -> Any | None:
    normalized = prompt_text.strip()
    if not normalized:
        return None
    return history_store.append(normalized)


def apply_generated_result(
    session: EditorSession,
    generated_blocks: dict[str, str],
    block_ids: list[str],
    formula: str,
) -> EditorSession:
    updated = merge_generated_blocks(session, generated_blocks, block_ids)
    values = {block_id: updated.block_values.get(block_id, "") for block_id in block_ids}
    prompt = formula.format(**values)
    segments = [segment.strip() for segment in prompt.split(",")]
    updated.final_prompt = ", ".join(segment for segment in segments if segment).strip(", ")
    return updated


def clear_unlocked_blocks(
    template: TemplateDefinition,
    session: EditorSession,
) -> EditorSession:
    next_values = dict(session.block_values)
    for block_id in template.block_order:
        if block_id in session.locked_blocks:
            continue
        next_values[block_id] = ""
    session.block_values = next_values
    session.final_prompt = rebuild_prompt(template, session)
    return session


def lock_all_blocks(
    template: TemplateDefinition,
    session: EditorSession,
) -> EditorSession:
    session.locked_blocks = {
        block_id
        for block_id in template.block_order
        if template.blocks[block_id].enabled
    }
    return session


def unlock_all_blocks(session: EditorSession) -> EditorSession:
    session.locked_blocks = set()
    return session


def queue_workbench_widget_state(
    streamlit_module: Any,
    template: TemplateDefinition,
    session: EditorSession,
    block_ids: list[str],
    extra_state: dict[str, Any] | None = None,
) -> None:
    streamlit_module.session_state["_workbench_pending_widget_state"] = {
        f"block-{template.id}-{block_id}": session.block_values.get(block_id, "")
        for block_id in block_ids
    } | {
        f"final-prompt-{template.id}": session.final_prompt,
    } | (extra_state or {})


def apply_pending_workbench_widget_state(streamlit_module: Any) -> None:
    pending_state = streamlit_module.session_state.pop("_workbench_pending_widget_state", None)
    if not pending_state:
        return
    for key, value in pending_state.items():
        streamlit_module.session_state[key] = value


def set_workbench_notice(streamlit_module: Any, message: str) -> None:
    streamlit_module.session_state["_workbench_notice"] = message


def pop_workbench_notice(streamlit_module: Any) -> str | None:
    return streamlit_module.session_state.pop("_workbench_notice", None)


def rerun_workbench(streamlit_module: Any) -> None:
    rerun = getattr(streamlit_module, "rerun", None)
    if callable(rerun):
        rerun()


def copy_text_to_clipboard(
    text: str,
    runner: Any = subprocess.run,
) -> bool:
    normalized = text.strip()
    if not normalized:
        return False

    command: list[str] | None = None
    if sys.platform == "win32":
        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            "[Console]::In.ReadToEnd() | Set-Clipboard",
        ]
    elif sys.platform == "darwin":
        command = ["pbcopy"]
    else:
        return False

    try:
        runner(command, input=normalized, text=True, check=True)
    except (OSError, subprocess.SubprocessError):
        return False
    return True


def render_workbench(view_model: dict) -> None:
    import streamlit as st

    templates: list[TemplateDefinition] = view_model.get("templates", [])
    settings = view_model.get("settings", {})
    settings_service = view_model.get("settings_service")
    generation_service = view_model.get("generation_service")
    generation_factory = view_model.get("generation_factory")
    history_store = view_model.get("history_store")
    history_entries = view_model.get("history_entries", [])
    session = view_model.get("session") or st.session_state.get("workbench_session")
    if session is None:
        session = EditorSession()
    st.session_state["workbench_session"] = session

    st.title("Z-Prompt-Helper")
    notice = pop_workbench_notice(st)
    if notice:
        _notify_success(st, notice)
    if not templates:
        template_names = view_model.get("template_names", [])
        if template_names:
            st.selectbox("Шаблон", options=template_names, key="selected_template_id")
        st.error("Нет доступных шаблонов.")
        return

    template_by_name = {template.name: template for template in templates}
    selected_name = st.session_state.get("selected_template_id", next(iter(template_by_name)))
    template = template_by_name.get(selected_name, next(iter(template_by_name.values())))
    activate_template(session, template.id)
    apply_pending_workbench_widget_state(st)
    active_blocks = [
        block_id
        for block_id in template.block_order
        if template.blocks[block_id].enabled
    ]
    summary = build_workbench_summary(session, active_block_count=len(active_blocks))
    selected_name = render_workbench_header_panel(
        st,
        template_names=list(template_by_name),
        selected_name=template.name,
        summary=summary,
        short_idea=session.short_idea,
    )
    template = template_by_name[selected_name]
    activate_template(session, template.id)
    apply_pending_workbench_widget_state(st)

    if current_template_has_meaningful_draft(session):
        st.caption("Черновик этого шаблона сохраняется автоматически.")
    else:
        st.caption("Новый черновик шаблона. Заполните поля или сгенерируйте промт.")

    left_col, right_col = _columns(st, [1.45, 1.0])
    with _column_scope(left_col):
        render_workbench_editor_panel(
            st,
            template=template,
            session=session,
        )
    summary = build_workbench_summary(session, active_block_count=len(active_blocks))
    with _column_scope(right_col):
        render_workbench_output_panel(
            st,
            session=session,
            template=template,
            summary=summary,
            history_entries=history_entries,
            history_store=history_store,
        )

    actions = st.session_state.get("_workbench_actions", {})
    generate = bool(actions.get("generate"))
    regenerate = bool(actions.get("regenerate"))
    rebuild = bool(actions.get("rebuild"))
    clear_unlocked = bool(actions.get("clear_unlocked"))
    lock_all = bool(actions.get("lock_all"))
    unlock_all = bool(actions.get("unlock_all"))
    copy_prompt = bool(actions.get("copy_prompt"))

    if generate or regenerate:
        try:
            if settings_service is not None:
                settings = settings_service.load()
            service = generation_service or _build_generation_service(
                generation_factory,
                _setting(settings, "api_key", ""),
            )
            if regenerate:
                session.variation_index += 1
            else:
                session.variation_index = 0
            request = build_generation_request(
                template,
                session,
                regenerate_unlocked=regenerate,
                variation_index=session.variation_index,
            )
            with _spinner(st, "Generating prompt..."):
                generated = service.generate_blocks(
                    model=_setting(settings, "model", ""),
                    temperature=float(_setting(settings, "temperature", 0.2)),
                    top_p=float(_setting(settings, "top_p", 0.9)),
                    max_tokens=int(_setting(settings, "max_tokens", 700)),
                    **request,
                )
            apply_generated_result(
                session=session,
                generated_blocks=generated,
                block_ids=request["active_blocks"],
                formula=template.assembly_formula,
            )
            queue_workbench_widget_state(st, template, session, request["active_blocks"])
            if history_store is not None:
                record_prompt_if_present(history_store, session.final_prompt)
            set_workbench_notice(st, "Промт обновлен.")
            rerun_workbench(st)
            return
        except Exception as error:
            st.error(f"Не удалось сгенерировать промт: {error}")

    if rebuild:
        apply_generated_result(
            session=session,
            generated_blocks={},
            block_ids=template.block_order,
            formula=template.assembly_formula,
        )
        queue_workbench_widget_state(st, template, session, template.block_order)
        if history_store is not None:
            record_prompt_if_present(history_store, session.final_prompt)
        set_workbench_notice(st, "Финальный промт пересобран.")
        rerun_workbench(st)
        return

    if clear_unlocked:
        clear_unlocked_blocks(template, session)
        queue_workbench_widget_state(st, template, session, template.block_order)
        set_workbench_notice(st, "Незаблокированные блоки очищены.")
        rerun_workbench(st)
        return

    if lock_all:
        lock_all_blocks(template, session)
        queue_workbench_widget_state(
            st,
            template,
            session,
            [],
            extra_state={
                f"lock-{template.id}-{block_id}": True
                for block_id in template.block_order
                if template.blocks[block_id].enabled
            },
        )
        set_workbench_notice(st, "Все блоки заблокированы.")
        rerun_workbench(st)
        return

    if unlock_all:
        unlock_all_blocks(session)
        queue_workbench_widget_state(
            st,
            template,
            session,
            [],
            extra_state={
                f"lock-{template.id}-{block_id}": False
                for block_id in template.block_order
                if template.blocks[block_id].enabled
            },
        )
        set_workbench_notice(st, "Все блоки разблокированы.")
        rerun_workbench(st)
        return

    if copy_prompt:
        if copy_text_to_clipboard(session.final_prompt):
            _notify_success(st, "Промт скопирован в буфер обмена.")
        else:
            st.error("Не удалось скопировать промт в буфер обмена.")


def _build_generation_service(generation_factory: Any, api_key: str) -> Any:
    normalized_key = api_key.strip()
    if generation_factory is None:
        raise ValueError("generation_factory is not configured")
    if not normalized_key:
        raise ValueError("OpenRouter API key is required in Settings")
    return generation_factory(normalized_key)


def _setting(settings: Any, name: str, default: Any) -> Any:
    if isinstance(settings, dict):
        return settings.get(name, default)
    return getattr(settings, name, default)


def _columns(st_module: Any, spec: list[float]) -> list[Any]:
    columns_fn = getattr(st_module, "columns")
    try:
        return list(columns_fn(spec, gap="large"))
    except TypeError:
        return list(columns_fn(len(spec)))


def _spinner(st_module: Any, message: str):
    spinner = getattr(st_module, "spinner", None)
    if callable(spinner):
        return spinner(message)
    return nullcontext()


def _notify_success(st_module: Any, message: str) -> None:
    toast = getattr(st_module, "toast", None)
    if callable(toast):
        toast(message, icon=":material/check_circle:")
        return
    st_module.success(message)


def _column_scope(column: Any):
    if hasattr(column, "__enter__") and hasattr(column, "__exit__"):
        return column
    return nullcontext()
