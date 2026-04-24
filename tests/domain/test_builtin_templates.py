from zprompt_helper.domain.models import BlockDefinition
from zprompt_helper.templates.builtin import load_builtin_templates


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
