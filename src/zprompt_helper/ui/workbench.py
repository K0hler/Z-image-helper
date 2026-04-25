import subprocess
import sys
from typing import Any

from zprompt_helper.domain.models import TemplateDefinition
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
    session = view_model.get("session") or st.session_state.get("workbench_session")
    if session is None:
        session = EditorSession()
    st.session_state["workbench_session"] = session

    st.title("Z-Prompt-Helper")
    notice = pop_workbench_notice(st)
    if notice:
        st.success(notice)
    if not templates:
        template_names = view_model.get("template_names", [])
        if template_names:
            st.selectbox("Шаблон", options=template_names, key="selected_template_id")
        st.error("Нет доступных шаблонов.")
        return

    template_by_name = {template.name: template for template in templates}
    selected_name = st.selectbox(
        "Шаблон",
        options=list(template_by_name),
        key="selected_template_id",
    )
    template = template_by_name[selected_name]
    activate_template(session, template.id)
    apply_pending_workbench_widget_state(st)

    session.short_idea = st.text_area(
        "Кратко о том, что хотите создать",
        value=session.short_idea,
        key="short_idea",
        height=100,
    )

    for block_id in template.block_order:
        block = template.blocks[block_id]
        if not block.enabled:
            continue
        session.block_values[block_id] = st.text_area(
            block.label,
            value=session.block_values.get(block_id, ""),
            key=f"block-{template.id}-{block_id}",
        )
        locked = st.checkbox(
            "Зафиксировать блок",
            value=block_id in session.locked_blocks,
            key=f"lock-{template.id}-{block_id}",
        )
        if locked:
            session.locked_blocks.add(block_id)
        else:
            session.locked_blocks.discard(block_id)

    if current_template_has_meaningful_draft(session):
        st.caption("Черновик этого шаблона сохраняется автоматически.")
    else:
        st.caption("Новый черновик шаблона. Заполните поля или сгенерируйте промт.")

    col1, col2, col3 = st.columns(3)
    generate = col1.button("Сгенерировать", key="generate")
    regenerate = col2.button("Перегенерировать незаблокированные", key="regenerate_unlocked")
    rebuild = col3.button("Пересобрать промт", key="rebuild_prompt")
    col4, col5, col6 = st.columns(3)
    clear_unlocked = col4.button("Очистить незаблокированные", key="clear_unlocked")
    lock_all = col5.button("Заблокировать все блоки", key="lock_all")
    unlock_all = col6.button("Разблокировать все блоки", key="unlock_all")

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

    session.final_prompt = st.text_area(
        "Финальный промт",
        value=session.final_prompt,
        key=f"final-prompt-{template.id}",
        height=160,
    )
    if session.final_prompt:
        st.code(session.final_prompt)
    if st.button("Скопировать промт", key="copy_prompt"):
        if copy_text_to_clipboard(session.final_prompt):
            st.success("Промт скопирован в буфер обмена.")
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
