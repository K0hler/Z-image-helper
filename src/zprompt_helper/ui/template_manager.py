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


def copy_builtin_template(template_store, template: TemplateDefinition) -> TemplateDefinition:
    duplicated = build_custom_copy(template)
    template_store.save(duplicated)
    return duplicated


def save_custom_template(
    template_store,
    template: TemplateDefinition,
    name: str,
    system_prompt: str,
    formula: str,
) -> TemplateDefinition:
    payload = template.model_dump()
    payload.update(
        {
            "name": name.strip(),
            "template_system_prompt": system_prompt,
            "assembly_formula": formula,
            "updated_at": datetime.now(UTC),
        }
    )
    updated = TemplateDefinition.model_validate(payload)
    template_store.save(updated)
    return updated


def render_template_manager(
    custom_templates: list[TemplateDefinition],
    built_in_templates: list[TemplateDefinition],
    template_store=None,
) -> None:
    import streamlit as st

    st.header("Шаблоны")

    st.subheader("Встроенные")
    for template in built_in_templates:
        if st.button(f"Создать копию: {template.name}", key=f"copy-{template.id}"):
            if template_store is None:
                st.error("TemplateStore is not configured.")
            else:
                try:
                    copy_builtin_template(template_store, template)
                    st.success("Копия шаблона сохранена.")
                except Exception as error:
                    st.error(f"Не удалось сохранить копию: {error}")

    st.subheader("Пользовательские")
    if st.button("Экспортировать шаблоны", key="export-custom-templates"):
        st.session_state["template_export_requested"] = True
    if st.button("Импортировать шаблоны", key="import-custom-templates"):
        st.session_state["template_import_requested"] = True

    for template in custom_templates:
        with st.expander(template.name):
            name = st.text_input("Название", value=template.name, key=f"name-{template.id}")
            system_prompt = st.text_area(
                "Системный промт шаблона",
                value=template.template_system_prompt,
                key=f"system-{template.id}",
            )
            formula = st.text_area(
                "Формула сборки",
                value=template.assembly_formula,
                key=f"formula-{template.id}",
            )
            if st.button("Сохранить шаблон", key=f"save-{template.id}"):
                if template_store is None:
                    st.error("TemplateStore is not configured.")
                else:
                    try:
                        save_custom_template(
                            template_store,
                            template,
                            name=name,
                            system_prompt=system_prompt,
                            formula=formula,
                        )
                        st.success("Шаблон сохранен.")
                    except Exception as error:
                        st.error(f"Не удалось сохранить шаблон: {error}")
