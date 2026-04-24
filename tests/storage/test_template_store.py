import pytest

from zprompt_helper.domain.models import BlockDefinition, TemplateDefinition
from zprompt_helper.storage.paths import ProjectPaths
from zprompt_helper.storage.template_store import TemplateStore


def _template(
    template_id: str,
    name: str = "Custom Universal",
    origin: str = "custom",
) -> TemplateDefinition:
    return TemplateDefinition(
        id=template_id,
        name=name,
        description="editable",
        origin=origin,
        block_order=["subject"],
        blocks={"subject": BlockDefinition(id="subject", label="Subject")},
        assembly_formula="{subject}",
        template_system_prompt="Return JSON",
    )


def test_template_store_exports_and_imports_custom_templates(tmp_path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    store = TemplateStore(paths)
    template = _template("custom-universal")

    store.save(template)
    exported = store.export_all()

    assert exported[0]["id"] == "custom-universal"


def test_template_store_loads_json_templates_sorted_by_filename(tmp_path) -> None:
    store = TemplateStore(ProjectPaths.from_root(tmp_path))
    second = _template("second")
    first = _template("first")

    store.save(second)
    store.save(first)

    assert [template.id for template in store.load_all()] == ["first", "second"]


def test_template_store_duplicate_deep_copies_as_custom_with_new_name(tmp_path) -> None:
    store = TemplateStore(ProjectPaths.from_root(tmp_path))
    original = _template("built-in", name="Original", origin="built_in")

    duplicate = store.duplicate(original, "Custom Copy")

    assert duplicate.id.startswith("built-in-")
    assert duplicate.id != original.id
    assert duplicate.name == "Custom Copy"
    assert duplicate.origin == "custom"
    assert duplicate.blocks is not original.blocks


def test_template_store_import_many_skips_existing_and_non_custom_templates(tmp_path) -> None:
    store = TemplateStore(ProjectPaths.from_root(tmp_path))
    store.save(_template("existing"))

    count = store.import_many(
        [
            _template("existing").model_dump(mode="json"),
            _template("built-in", origin="built_in").model_dump(mode="json"),
            _template("new-custom").model_dump(mode="json"),
        ]
    )

    assert count == 1
    assert [template.id for template in store.load_all()] == ["existing", "new-custom"]


def test_template_store_save_rejects_unsafe_template_id_without_writing_outside_templates_dir(tmp_path) -> None:
    store = TemplateStore(ProjectPaths.from_root(tmp_path))

    with pytest.raises(ValueError, match="template id"):
        store.save(_template("../settings"))

    assert not (tmp_path / "data" / "settings.json").exists()
    assert store.load_all() == []


def test_template_store_import_many_rejects_unsafe_template_id_without_writing_outside_templates_dir(tmp_path) -> None:
    store = TemplateStore(ProjectPaths.from_root(tmp_path))

    with pytest.raises(ValueError, match="template id"):
        store.import_many([_template("../settings").model_dump(mode="json")])

    assert not (tmp_path / "data" / "settings.json").exists()
    assert store.load_all() == []
