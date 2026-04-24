from zprompt_helper.ui.workbench import apply_generated_result
from zprompt_helper.workbench.session import EditorSession


def test_apply_generated_result_rebuilds_the_final_prompt() -> None:
    session = EditorSession(block_values={"subject": "robot"})
    next_session = apply_generated_result(
        session=session,
        generated_blocks={"style": "cinematic still"},
        block_ids=["subject", "style"],
        formula="{subject}, {style}",
    )

    assert next_session.final_prompt == "robot, cinematic still"
