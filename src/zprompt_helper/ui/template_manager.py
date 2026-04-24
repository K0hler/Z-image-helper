from datetime import UTC, datetime
from uuid import uuid4

from zprompt_helper.domain.models import TemplateDefinition


def build_custom_copy(template: TemplateDefinition) -> TemplateDefinition:
    duplicated = template.model_copy(deep=True)
    duplicated.id = f"{template.id}-{uuid4().hex[:8]}"
    duplicated.name = f"{template.name} Copy"
    duplicated.origin = "custom"
    timestamp = datetime.now(UTC)
    duplicated.created_at = timestamp
    duplicated.updated_at = timestamp
    return duplicated


def render_template_manager(
    custom_templates: list[TemplateDefinition],
    built_in_templates: list[TemplateDefinition],
) -> None:
    import streamlit as st

    st.header("Шаблоны")

    st.subheader("Встроенные")
    for template in built_in_templates:
        st.button(f"Создать копию: {template.name}", key=f"copy-{template.id}")

    st.subheader("Пользовательские")
    if st.button("Экспортировать шаблоны", key="export-custom-templates"):
        st.session_state["template_export_requested"] = True
    if st.button("Импортировать шаблоны", key="import-custom-templates"):
        st.session_state["template_import_requested"] = True

    for template in custom_templates:
        with st.expander(template.name):
            st.text_input("Название", value=template.name, key=f"name-{template.id}")
            st.text_area(
                "Системный промт шаблона",
                value=template.template_system_prompt,
                key=f"system-{template.id}",
            )
            st.text_area(
                "Формула сборки",
                value=template.assembly_formula,
                key=f"formula-{template.id}",
            )
