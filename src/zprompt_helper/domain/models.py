from datetime import datetime
from string import Formatter
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BlockDefinition(BaseModel):
    id: str
    label: str
    instruction: str = ""
    enabled: bool = True


class TemplateDefinition(BaseModel):
    id: str
    name: str
    description: str
    origin: Literal["built_in", "custom"]
    block_order: list[str]
    blocks: dict[str, BlockDefinition]
    assembly_formula: str
    template_system_prompt: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_block_catalog(self) -> "TemplateDefinition":
        ordered_blocks = set(self.block_order)
        block_keys = set(self.blocks)
        if len(self.block_order) != len(ordered_blocks):
            raise ValueError("block_order must not contain duplicate block ids")

        if ordered_blocks != block_keys:
            raise ValueError("block_order must contain exactly the same block ids as blocks")

        mismatched_ids = [
            block_key
            for block_key, block in self.blocks.items()
            if block_key != block.id
        ]
        if mismatched_ids:
            raise ValueError(f"block keys must match nested block ids: {mismatched_ids}")

        placeholders = {
            field_name
            for _, field_name, _, _ in Formatter().parse(self.assembly_formula)
            if field_name
        }
        if placeholders != block_keys:
            raise ValueError("assembly_formula placeholders must match defined block ids exactly")

        return self
