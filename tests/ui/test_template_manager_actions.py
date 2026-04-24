import pytest

from zprompt_helper.domain.models import TemplateDefinition
from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.template_manager import (
    build_custom_copy,
    copy_builtin_template,
    save_custom_template,
)


class FakeTemplateStore:
    def __init__(self) -> None:
        self.saved: list[TemplateDefinition] = []

    def save(self, template: TemplateDefinition) -> None:
        self.saved.append(template)


def test_build_custom_copy_marks_builtin_cinematic_as_custom() -> None:
    original = next(
        template
        for template in load_builtin_templates()
        if template.name == "Cinematic"
    )

    duplicated = build_custom_copy(original)

    assert duplicated.origin == "custom"
    assert duplicated.id != original.id
    assert duplicated.id.startswith("cinematic-")
    assert duplicated.name == "Cinematic Copy"
    assert duplicated.created_at is not None
    assert duplicated.updated_at is not None


def test_build_custom_copy_deep_copies_blocks() -> None:
    original = next(
        template
        for template in load_builtin_templates()
        if template.name == "Cinematic"
    )

    duplicated = build_custom_copy(original)
    duplicated.blocks["subject"].label = "Changed"

    assert original.blocks["subject"].label != "Changed"


def test_copy_builtin_template_saves_custom_copy() -> None:
    store = FakeTemplateStore()
    original = next(template for template in load_builtin_templates() if template.name == "Cinematic")

    copied = copy_builtin_template(store, original)

    assert store.saved == [copied]
    assert copied.origin == "custom"
    assert copied.id != original.id


def test_save_custom_template_updates_editable_fields_and_timestamp() -> None:
    store = FakeTemplateStore()
    template = build_custom_copy(
        next(template for template in load_builtin_templates() if template.name == "Cinematic")
    )

    saved = save_custom_template(
        store,
        template,
        name="Cinematic v2",
        system_prompt="Updated system prompt",
        formula=template.assembly_formula,
    )

    assert store.saved == [saved]
    assert saved.id == template.id
    assert saved.name == "Cinematic v2"
    assert saved.template_system_prompt == "Updated system prompt"
    assert saved.updated_at is not None


def test_save_custom_template_rejects_invalid_formula() -> None:
    store = FakeTemplateStore()
    template = build_custom_copy(
        next(template for template in load_builtin_templates() if template.name == "Cinematic")
    )

    with pytest.raises(ValueError, match="assembly_formula"):
        save_custom_template(
            store,
            template,
            name=template.name,
            system_prompt=template.template_system_prompt,
            formula="{subject}",
        )

    assert store.saved == []
