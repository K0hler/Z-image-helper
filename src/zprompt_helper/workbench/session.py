from dataclasses import dataclass, field
from typing import Any

from zprompt_helper.domain.models import TemplateDefinition


@dataclass
class EditorSession:
    short_idea: str = ""
    block_values: dict[str, str] = field(default_factory=dict)
    locked_blocks: set[str] = field(default_factory=set)
    final_prompt: str = ""
    variation_index: int = 0
    active_template_id: str | None = None
    template_drafts: dict[str, dict[str, Any]] = field(default_factory=dict)


def capture_template_draft(session: EditorSession) -> dict[str, Any]:
    return {
        "block_values": dict(session.block_values),
        "locked_blocks": set(session.locked_blocks),
        "final_prompt": session.final_prompt,
        "variation_index": session.variation_index,
    }


def restore_template_draft(
    session: EditorSession,
    draft: dict[str, Any] | None,
) -> EditorSession:
    draft = draft or {}
    session.block_values = dict(draft.get("block_values", {}))
    session.locked_blocks = set(draft.get("locked_blocks", set()))
    session.final_prompt = str(draft.get("final_prompt", ""))
    session.variation_index = int(draft.get("variation_index", 0))
    return session


def activate_template(
    session: EditorSession,
    template_id: str,
) -> EditorSession:
    if session.active_template_id == template_id:
        return session

    if session.active_template_id is not None:
        session.template_drafts[session.active_template_id] = capture_template_draft(session)

    restore_template_draft(session, session.template_drafts.get(template_id))
    session.active_template_id = template_id
    return session


def template_draft_has_meaningful_content(draft: dict[str, Any] | None) -> bool:
    draft = draft or {}
    block_values = draft.get("block_values", {})
    if any(str(value).strip() for value in block_values.values()):
        return True
    if draft.get("locked_blocks"):
        return True
    if str(draft.get("final_prompt", "")).strip():
        return True
    if int(draft.get("variation_index", 0)) > 0:
        return True
    return False


def current_template_has_meaningful_draft(session: EditorSession) -> bool:
    return template_draft_has_meaningful_content(capture_template_draft(session))


def rebuild_prompt(template: TemplateDefinition, session: EditorSession) -> str:
    values = {
        block_id: session.block_values.get(block_id, "")
        for block_id in template.block_order
    }
    prompt = template.assembly_formula.format(**values)
    segments = [segment.strip() for segment in prompt.split(",")]
    return ", ".join(segment for segment in segments if segment).strip(", ")


def merge_generated_blocks(
    session: EditorSession,
    generated_blocks: dict[str, str],
    block_ids: list[str],
) -> EditorSession:
    next_values = dict(session.block_values)
    for block_id in block_ids:
        if block_id in session.locked_blocks:
            continue
        if block_id in generated_blocks:
            next_values[block_id] = generated_blocks[block_id]
    session.block_values = next_values
    return session


def set_block_value(
    session: EditorSession,
    block_id: str,
    value: str,
) -> EditorSession:
    session.block_values[block_id] = value
    return session
