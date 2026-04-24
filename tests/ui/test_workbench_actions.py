from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.workbench import (
    apply_generated_result,
    build_generation_request,
    record_prompt_if_present,
)
from zprompt_helper.workbench.session import EditorSession


class FakeHistoryStore:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def append(self, prompt_text: str) -> None:
        self.prompts.append(prompt_text)


def test_apply_generated_result_rebuilds_the_final_prompt() -> None:
    session = EditorSession(block_values={"subject": "robot"})
    next_session = apply_generated_result(
        session=session,
        generated_blocks={"style": "cinematic still"},
        block_ids=["subject", "style"],
        formula="{subject}, {style}",
    )

    assert next_session.final_prompt == "robot, cinematic still"


def test_build_generation_request_maps_template_and_session() -> None:
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    session = EditorSession(
        short_idea="robot portrait",
        block_values={"subject": "old robot"},
        locked_blocks={"shot"},
    )

    request = build_generation_request(template, session)

    assert request["short_idea"] == "robot portrait"
    assert request["active_blocks"] == template.block_order
    assert request["template_prompt"] == template.template_system_prompt
    assert request["current_values"]["subject"] == "old robot"
    assert request["locked_blocks"] == {"shot"}
    assert request["block_instructions"]["subject"] == template.blocks["subject"].instruction


def test_record_prompt_if_present_appends_only_non_empty_prompts() -> None:
    store = FakeHistoryStore()

    assert record_prompt_if_present(store, "  ") is None
    record = record_prompt_if_present(store, "  robot, cinematic  ")

    assert store.prompts == ["robot, cinematic"]
    assert record is None
