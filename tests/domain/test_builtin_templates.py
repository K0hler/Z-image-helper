from string import Formatter

import pytest
from pydantic import ValidationError

from zprompt_helper.domain.models import BlockDefinition, TemplateDefinition
from zprompt_helper.templates.builtin import load_builtin_templates


def _placeholders(formula: str) -> list[str]:
    return [field_name for _, field_name, _, _ in Formatter().parse(formula) if field_name]


def test_builtin_catalog_contains_expected_templates() -> None:
    templates = load_builtin_templates()
    names = {template.name for template in templates}

    assert len(templates) == 7
    assert names == {
        "Universal",
        "Cinematic",
        "Photorealism",
        "Art / Illustration",
        "Character",
        "Scenes / Environment",
        "Text In Image",
    }
    assert all(template.origin == "built_in" for template in templates)


def test_text_in_image_template_contains_text_blocks() -> None:
    template = next(template for template in load_builtin_templates() if template.id == "text_in_image")

    assert set(template.blocks) >= {"headline", "subheadline", "cta", "layout"}
    assert isinstance(template.blocks["headline"], BlockDefinition)


def test_builtin_templates_satisfy_catalog_invariants() -> None:
    for template in load_builtin_templates():
        assert len(template.block_order) == len(set(template.block_order))
        assert set(template.block_order) == set(template.blocks)
        assert all(block_id == block.id for block_id, block in template.blocks.items())
        assert _placeholders(template.assembly_formula) == template.block_order


def test_template_definition_rejects_invalid_catalog_invariants() -> None:
    with pytest.raises(ValidationError):
        TemplateDefinition(
            id="broken",
            name="Broken",
            description="Invalid template",
            origin="built_in",
            block_order=["subject"],
            blocks={"scene": BlockDefinition(id="different", label="Scene")},
            assembly_formula="{subject}, {missing}",
            template_system_prompt="Return JSON",
        )


def test_template_definition_rejects_duplicate_block_order_ids() -> None:
    with pytest.raises(ValidationError):
        TemplateDefinition(
            id="duplicate-order",
            name="Duplicate Order",
            description="Invalid template",
            origin="built_in",
            block_order=["subject", "subject"],
            blocks={"subject": BlockDefinition(id="subject", label="Subject")},
            assembly_formula="{subject}",
            template_system_prompt="Return JSON",
        )


def test_template_definition_rejects_formula_that_omits_declared_block() -> None:
    with pytest.raises(ValidationError):
        TemplateDefinition(
            id="missing-placeholder",
            name="Missing Placeholder",
            description="Invalid template",
            origin="built_in",
            block_order=["subject", "style"],
            blocks={
                "subject": BlockDefinition(id="subject", label="Subject"),
                "style": BlockDefinition(id="style", label="Style"),
            },
            assembly_formula="{subject}",
            template_system_prompt="Return JSON",
        )


def test_template_definition_rejects_reordered_formula_placeholders() -> None:
    with pytest.raises(ValidationError):
        TemplateDefinition(
            id="reordered-placeholder",
            name="Reordered Placeholder",
            description="Invalid template",
            origin="built_in",
            block_order=["subject", "style"],
            blocks={
                "subject": BlockDefinition(id="subject", label="Subject"),
                "style": BlockDefinition(id="style", label="Style"),
            },
            assembly_formula="{style}, {subject}",
            template_system_prompt="Return JSON",
        )
