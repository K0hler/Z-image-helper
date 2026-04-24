from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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
