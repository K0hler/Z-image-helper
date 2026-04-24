from zprompt_helper.workbench.session import EditorSession, merge_generated_blocks


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

    st.title("Z-Prompt-Helper")
    st.selectbox("Шаблон", options=view_model["template_names"], key="selected_template_id")
    st.text_area("Кратко о том, что хотите создать", key="short_idea", height=100)
    col1, col2, col3 = st.columns(3)
    col1.button("Сгенерировать", key="generate")
    col2.button("Перегенерировать незаблокированные", key="regenerate_unlocked")
    col3.button("Скопировать промт", key="copy_prompt")
