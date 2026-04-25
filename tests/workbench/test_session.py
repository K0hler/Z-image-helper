from zprompt_helper.domain.models import BlockDefinition, TemplateDefinition
from zprompt_helper.workbench.session import (
    activate_template,
    capture_template_draft,
    current_template_has_meaningful_draft,
    EditorSession,
    merge_generated_blocks,
    rebuild_prompt,
    restore_template_draft,
    set_block_value,
    template_draft_has_meaningful_content,
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


def test_capture_and_restore_template_draft_roundtrip() -> None:
    session = EditorSession(
        block_values={"subject": "cat"},
        locked_blocks={"subject"},
        final_prompt="cat portrait",
        variation_index=2,
    )

    draft = capture_template_draft(session)
    restored = EditorSession()
    restore_template_draft(restored, draft)

    assert restored.block_values == {"subject": "cat"}
    assert restored.locked_blocks == {"subject"}
    assert restored.final_prompt == "cat portrait"
    assert restored.variation_index == 2


def test_activate_template_preserves_separate_drafts_per_template() -> None:
    session = EditorSession(short_idea="one idea")

    activate_template(session, "universal")
    session.block_values["subject"] = "robot"
    session.locked_blocks.add("subject")
    session.final_prompt = "robot prompt"
    session.variation_index = 1

    activate_template(session, "cinematic")
    assert session.block_values == {}
    assert session.locked_blocks == set()
    assert session.final_prompt == ""
    assert session.variation_index == 0

    session.block_values["subject"] = "detective"
    session.final_prompt = "cinematic detective"

    activate_template(session, "universal")
    assert session.block_values == {"subject": "robot"}
    assert session.locked_blocks == {"subject"}
    assert session.final_prompt == "robot prompt"
    assert session.variation_index == 1


def test_template_draft_has_meaningful_content_detects_real_saved_state() -> None:
    assert template_draft_has_meaningful_content({}) is False
    assert template_draft_has_meaningful_content({"block_values": {"subject": ""}}) is False
    assert template_draft_has_meaningful_content({"block_values": {"subject": "robot"}}) is True
    assert template_draft_has_meaningful_content({"locked_blocks": {"subject"}}) is True
    assert template_draft_has_meaningful_content({"final_prompt": "robot prompt"}) is True
    assert template_draft_has_meaningful_content({"variation_index": 1}) is True


def test_current_template_has_meaningful_draft_uses_active_template_state() -> None:
    session = EditorSession(active_template_id="universal")
    assert current_template_has_meaningful_draft(session) is False

    session.block_values["subject"] = "robot"
    assert current_template_has_meaningful_draft(session) is True
