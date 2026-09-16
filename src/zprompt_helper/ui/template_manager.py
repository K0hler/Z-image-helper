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


def split_template_groups(templates: list[TemplateDefinition]) -> dict[str, list[TemplateDefinition]]:
    return {
        "built_in": [template for template in templates if template.origin == "built_in"],
        "custom": [template for template in templates if template.origin == "custom"],
    }


def render_template_manager(
    custom_templates: list[TemplateDefinition],
    built_in_templates: list[TemplateDefinition],
    template_store=None,
) -> None:
    import streamlit as st

    groups = split_template_groups([*built_in_templates, *custom_templates])
    built_in_catalog = groups["built_in"]
    custom_catalog = groups["custom"]

    st.subheader("Каталог встроенных шаблонов")
    if built_in_catalog:
        for index in range(0, len(built_in_catalog), 2):
            row = st.columns(2)
            for column, template in zip(row, built_in_catalog[index : index + 2]):
                with _column_container(st, column, border=True):
                    st.write(template.name)
                    st.caption(template.description)
                    st.caption(f"Блоков: {len(template.block_order)}")
                    if st.button("Создать копию", key=f"copy-{template.id}"):
                        if template_store is None:
                            st.error("TemplateStore is not configured.")
                        else:
                            try:
                                copy_builtin_template(template_store, template)
                                st.success("Копия шаблона сохранена.")
                            except Exception as error:
                                st.error(f"Не удалось сохранить копию: {error}")

    st.subheader("Пользовательские шаблоны")
    with st.popover("More actions"):
        if st.button("Экспортировать шаблоны", key="export-custom-templates"):
            st.session_state["template_export_requested"] = True
        if st.button("Импортировать шаблоны", key="import-custom-templates"):
            st.session_state["template_import_requested"] = True

    if not custom_catalog:
        st.caption("Пользовательские шаблоны появятся здесь после создания копии.")
        return

    selected_template_id = st.session_state.get("selected_custom_template_id")
    if selected_template_id not in {template.id for template in custom_catalog}:
        selected_template_id = custom_catalog[0].id
        st.session_state["selected_custom_template_id"] = selected_template_id

    list_column, detail_column = st.columns([1, 2])
    for template in custom_catalog:
        with _column_container(st, list_column, border=template.id == selected_template_id):
            if st.button(template.name, key=f"select-{template.id}"):
                selected_template_id = template.id
                st.session_state["selected_custom_template_id"] = template.id

    selected_template = next(
        template for template in custom_catalog if template.id == selected_template_id
    )
    with _column_container(st, detail_column, border=True):
        st.write(selected_template.name)
        st.caption(selected_template.description)
        with st.form(f"custom-template-form-{selected_template.id}"):
            name = st.text_input(
                "Название",
                value=selected_template.name,
                key=f"name-{selected_template.id}",
            )
            system_prompt = st.text_area(
                "Системный промт шаблона",
                value=selected_template.template_system_prompt,
                key=f"system-{selected_template.id}",
            )
            formula = st.text_area(
                "Формула сборки",
                value=selected_template.assembly_formula,
                key=f"formula-{selected_template.id}",
            )
            if st.form_submit_button("Сохранить шаблон"):
                if template_store is None:
                    st.error("TemplateStore is not configured.")
                else:
                    try:
                        save_custom_template(
                            template_store,
                            selected_template,
                            name=name,
                            system_prompt=system_prompt,
                            formula=formula,
                        )
                        st.success("Шаблон сохранен.")
                    except Exception as error:
                        st.error(f"Не удалось сохранить шаблон: {error}")


def _column_container(st_module, column, *, border: bool):
    container = getattr(column, "container", None)
    if callable(container):
        return container(border=border)
    return st_module.container(border=border)
