from zprompt_helper.domain.models import BlockDefinition, TemplateDefinition
from zprompt_helper.workbench.session import (
    EditorSession,
    merge_generated_blocks,
    rebuild_prompt,
    set_block_value,
)


def make_template(block_order: list[str], assembly_formula: str) -> TemplateDefinition:
    return TemplateDefinition(
        id="universal",
        name="Universal",
        description="starter",
        origin="built_in",
        block_order=block_order,
        blocks={
            block_id: BlockDefinition(id=block_id, label=block_id.title())
            for block_id in block_order
        },
        assembly_formula=assembly_formula,
        template_system_prompt="Return JSON",
    )


def test_rebuild_prompt_uses_template_formula_and_overwrites_manual_prompt() -> None:
    template = make_template(["subject", "style"], "{subject}, {style}")
    session = EditorSession(
        short_idea="robot portrait",
        block_values={
            "subject": "portrait of a chrome robot",
            "style": "cinematic still",
        },
        final_prompt="manually edited prompt",
    )

    rebuilt = rebuild_prompt(template, session)

    assert rebuilt == "portrait of a chrome robot, cinematic still"
    assert rebuilt != session.final_prompt


def test_merge_generated_blocks_skips_locked_fields() -> None:
    session = EditorSession(
        block_values={"style": "oil painting", "subject": "cat"},
        locked_blocks={"style"},
    )

    result = merge_generated_blocks(
        session,
        generated_blocks={"style": "photorealistic", "subject": "tiger"},
        block_ids=["subject", "style"],
    )

    assert result is session
    assert session.block_values["style"] == "oil painting"
    assert session.block_values["subject"] == "tiger"


def test_rebuild_prompt_missing_blocks_render_empty_and_strip_trailing_separators() -> None:
    template = make_template(
        ["subject", "style", "details"],
        "{subject}, {style}, {details}",
    )
    session = EditorSession(block_values={"subject": "portrait of a chrome robot"})

    rebuilt = rebuild_prompt(template, session)

    assert rebuilt == "portrait of a chrome robot"


def test_rebuild_prompt_collapses_missing_middle_segments() -> None:
    template = make_template(
        ["subject", "style", "details"],
        "{subject}, {style}, {details}",
    )
    session = EditorSession(
        block_values={"subject": "cat", "details": "blue background"}
    )

    rebuilt = rebuild_prompt(template, session)

    assert rebuilt == "cat, blue background"


def test_set_block_value_updates_block_values() -> None:
    session = EditorSession(block_values={"subject": "cat"})

    result = set_block_value(session, "subject", "tiger")

    assert result is session
    assert session.block_values["subject"] == "tiger"
