import pytest

from zprompt_helper.domain.models import TemplateDefinition
from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.template_manager import (
    build_custom_copy,
    copy_builtin_template,
    render_template_manager,
    save_custom_template,
    split_template_groups,
)


class FakeTemplateStore:
    def __init__(self) -> None:
        self.saved: list[TemplateDefinition] = []

    def save(self, template: TemplateDefinition) -> None:
        self.saved.append(template)


class FakeContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class FakeForm(FakeContext):
    def __init__(self, streamlit: "FakeStreamlit", key: str) -> None:
        self.streamlit = streamlit
        self.key = key


class FakeContainer(FakeContext):
    def __init__(self, streamlit: "FakeStreamlit") -> None:
        self.streamlit = streamlit

    def button(self, label: str, *, key: str, type: str | None = None) -> bool:
        del type
        return self.streamlit.button(label, key=key)


class FakePopover(FakeContainer):
    pass


class FakeColumn(FakeContainer):
    pass


class FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.button_presses: dict[str, bool] = {}
        self.form_submits: dict[str, bool] = {}
        self.forms: list[str] = []
        self.popovers: list[str] = []
        self.columns_specs: list[object] = []
        self.container_borders: list[bool] = []
        self.errors: list[str] = []
        self.successes: list[str] = []
        self.captions: list[str] = []

    def header(self, _: str) -> None:
        return None

    def subheader(self, _: str) -> None:
        return None

    def write(self, _: str) -> None:
        return None

    def markdown(self, _: str) -> None:
        return None

    def caption(self, message: str) -> None:
        self.captions.append(message)

    def success(self, message: str) -> None:
        self.successes.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def columns(self, spec, **_: object) -> list[FakeColumn]:
        self.columns_specs.append(spec)
        count = spec if isinstance(spec, int) else len(spec)
        return [FakeColumn(self) for _ in range(count)]

    def container(self, *, border: bool = False, **_: object) -> FakeContainer:
        self.container_borders.append(border)
        return FakeContainer(self)

    def popover(self, label: str, **_: object) -> FakePopover:
        self.popovers.append(label)
        return FakePopover(self)

    def form(self, key: str, **_: object) -> FakeForm:
        self.forms.append(key)
        return FakeForm(self, key)

    def text_input(self, _: str, *, value: str = "", key: str, **__: object) -> str:
        return str(self.session_state.get(key, value))

    def text_area(self, _: str, *, value: str = "", key: str, **__: object) -> str:
        return str(self.session_state.get(key, value))

    def button(self, _: str, *, key: str, **__: object) -> bool:
        return self.button_presses.get(key, False)

    def form_submit_button(self, _: str, *, key: str | None = None, **__: object) -> bool:
        submit_key = key or self.forms[-1]
        return self.form_submits.get(submit_key, False)


def test_build_custom_copy_marks_builtin_cinematic_as_custom() -> None:
    original = next(
        template
        for template in load_builtin_templates()
        if template.name == "Cinematic"
    )

    duplicated = build_custom_copy(original)

    assert duplicated.origin == "custom"
    assert duplicated.id != original.id
    assert duplicated.id.startswith("cinematic-")
    assert duplicated.name == "Cinematic Copy"
    assert duplicated.created_at is not None
    assert duplicated.updated_at is not None


def test_build_custom_copy_deep_copies_blocks() -> None:
    original = next(
        template
        for template in load_builtin_templates()
        if template.name == "Cinematic"
    )

    duplicated = build_custom_copy(original)
    duplicated.blocks["subject"].label = "Changed"

    assert original.blocks["subject"].label != "Changed"


def test_copy_builtin_template_saves_custom_copy() -> None:
    store = FakeTemplateStore()
    original = next(template for template in load_builtin_templates() if template.name == "Cinematic")

    copied = copy_builtin_template(store, original)

    assert store.saved == [copied]
    assert copied.origin == "custom"
    assert copied.id != original.id


def test_save_custom_template_updates_editable_fields_and_timestamp() -> None:
    store = FakeTemplateStore()
    template = build_custom_copy(
        next(template for template in load_builtin_templates() if template.name == "Cinematic")
    )

    saved = save_custom_template(
        store,
        template,
        name="Cinematic v2",
        system_prompt="Updated system prompt",
        formula=template.assembly_formula,
    )

    assert store.saved == [saved]
    assert saved.id == template.id
    assert saved.name == "Cinematic v2"
    assert saved.template_system_prompt == "Updated system prompt"
    assert saved.updated_at is not None


def test_save_custom_template_rejects_invalid_formula() -> None:
    store = FakeTemplateStore()
    template = build_custom_copy(
        next(template for template in load_builtin_templates() if template.name == "Cinematic")
    )

    with pytest.raises(ValueError, match="assembly_formula"):
        save_custom_template(
            store,
            template,
            name=template.name,
            system_prompt=template.template_system_prompt,
            formula="{subject}",
        )

    assert store.saved == []


def test_split_template_groups_separates_builtin_and_custom() -> None:
    built_in = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    custom = build_custom_copy(built_in)

    groups = split_template_groups([built_in, custom])

    assert groups["built_in"] == [built_in]
    assert groups["custom"] == [custom]


def test_render_template_manager_uses_catalog_layout_and_custom_form(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    built_in = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    custom = build_custom_copy(built_in)
    fake_st.session_state[f"name-{custom.id}"] = "Updated custom"
    fake_st.session_state[f"system-{custom.id}"] = "Updated system"
    fake_st.session_state[f"formula-{custom.id}"] = custom.assembly_formula
    fake_st.form_submits[f"custom-template-form-{custom.id}"] = True

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    store = FakeTemplateStore()
    render_template_manager(
        custom_templates=[custom],
        built_in_templates=[built_in],
        template_store=store,
    )

    assert fake_st.forms == [f"custom-template-form-{custom.id}"]
    assert fake_st.popovers == ["More actions"]
    assert any(border is True for border in fake_st.container_borders)
    assert store.saved[0].name == "Updated custom"
    assert fake_st.successes == ["Шаблон сохранен."]


def test_render_template_manager_preserves_copy_import_and_export_actions(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    built_in = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    fake_st.button_presses = {
        f"copy-{built_in.id}": True,
        "export-custom-templates": True,
        "import-custom-templates": True,
    }

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    store = FakeTemplateStore()
    render_template_manager(
        custom_templates=[],
        built_in_templates=[built_in],
        template_store=store,
    )

    assert len(store.saved) == 1
    assert store.saved[0].origin == "custom"
    assert fake_st.session_state["template_export_requested"] is True
    assert fake_st.session_state["template_import_requested"] is True
