from typing import Any

from zprompt_helper.domain.models import TemplateDefinition
from zprompt_helper.workbench.session import EditorSession, merge_generated_blocks


def build_generation_request(
    template: TemplateDefinition,
    session: EditorSession,
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
        },
        "locked_blocks": session.locked_blocks.intersection(active_blocks),
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

    col1, col2, col3 = st.columns(3)
    generate = col1.button("Сгенерировать", key="generate")
    regenerate = col2.button("Перегенерировать незаблокированные", key="regenerate_unlocked")
    rebuild = col3.button("Пересобрать промт", key="rebuild_prompt")

    if generate or regenerate:
        try:
            if settings_service is not None:
                settings = settings_service.load()
            service = generation_service or _build_generation_service(
                generation_factory,
                _setting(settings, "api_key", ""),
            )
            request = build_generation_request(template, session)
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
            if history_store is not None:
                record_prompt_if_present(history_store, session.final_prompt)
            st.success("Промт обновлен.")
        except Exception as error:
            st.error(f"Не удалось сгенерировать промт: {error}")

    if rebuild:
        apply_generated_result(
            session=session,
            generated_blocks={},
            block_ids=template.block_order,
            formula=template.assembly_formula,
        )
        if history_store is not None:
            record_prompt_if_present(history_store, session.final_prompt)
        st.success("Финальный промт пересобран.")

    session.final_prompt = st.text_area(
        "Финальный промт",
        value=session.final_prompt,
        key=f"final-prompt-{template.id}",
        height=160,
    )
    if session.final_prompt:
        st.code(session.final_prompt)
    if st.button("Скопировать промт", key="copy_prompt"):
        st.session_state["copied_prompt"] = session.final_prompt
        st.success("Промт подготовлен к копированию.")


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
