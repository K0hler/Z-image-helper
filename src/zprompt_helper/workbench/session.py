from dataclasses import dataclass, field

from zprompt_helper.domain.models import TemplateDefinition


@dataclass
class EditorSession:
    short_idea: str = ""
    block_values: dict[str, str] = field(default_factory=dict)
    locked_blocks: set[str] = field(default_factory=set)
    final_prompt: str = ""


def rebuild_prompt(template: TemplateDefinition, session: EditorSession) -> str:
    values = {
        block_id: session.block_values.get(block_id, "")
        for block_id in template.block_order
    }
    return template.assembly_formula.format(**values).strip(", ")


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
