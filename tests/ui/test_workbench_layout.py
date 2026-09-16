from zprompt_helper.ui.workbench_panels import block_display_label, build_workbench_summary
from zprompt_helper.workbench.session import EditorSession


def test_build_workbench_summary_counts_locks_and_variations() -> None:
    session = EditorSession(
        block_values={"subject": "robot"},
        locked_blocks={"subject", "scene"},
        variation_index=2,
        final_prompt="robot prompt",
    )

    summary = build_workbench_summary(session, active_block_count=5)

    assert summary.locked_count == 2
    assert summary.filled_count == 1
    assert summary.active_block_count == 5
    assert summary.variation_index == 2
    assert summary.has_final_prompt is True


def test_block_display_label_localizes_known_blocks_and_keeps_custom_labels() -> None:
    assert block_display_label("subject", "Subject") == "Объект"
    assert block_display_label("custom", "Custom field") == "Custom field"
