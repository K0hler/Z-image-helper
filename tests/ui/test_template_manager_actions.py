from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.template_manager import build_custom_copy


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
