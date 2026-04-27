import subprocess

from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.workbench import (
    apply_pending_workbench_widget_state,
    apply_generated_result,
    build_generation_request,
    clear_unlocked_blocks,
    copy_text_to_clipboard,
    lock_all_blocks,
    pop_workbench_notice,
    pop_workbench_generating,
    queue_workbench_widget_state,
    record_prompt_if_present,
    render_workbench,
    set_workbench_generating,
    set_workbench_notice,
    unlock_all_blocks,
)
from zprompt_helper.ui.workbench_panels import (
    build_workbench_summary,
    render_workbench_editor_panel,
    render_workbench_output_panel,
)
from zprompt_helper.workbench.session import EditorSession


class FakeHistoryStore:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def append(self, prompt_text: str) -> None:
        self.prompts.append(prompt_text)


class FakeGenerationService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate_blocks(self, **_: object) -> dict[str, str]:
        self.calls.append(_)
        return {
            "subject": "android courier",
            "scene": "rainy neon street",
        }


class FakeColumn:
    def __init__(self, streamlit: "FakeStreamlit") -> None:
        self._streamlit = streamlit

    def button(self, label: str, *, key: str, disabled: bool = False) -> bool:
        return self._streamlit.button(label, key=key, disabled=disabled)


class FakeStreamlit:
    def __init__(self) -> None:
        self.session_state = FakeSessionState()
        self._button_presses = {"generate": True}
        self.success_messages: list[str] = []
        self.caption_messages: list[str] = []
        self.instantiated_keys: set[str] = set()
        self.rerun_requested = False

    def title(self, _: str) -> None:
        return None

    def error(self, message: str) -> None:
        raise AssertionError(message)

    def success(self, message: str) -> None:
        self.success_messages.append(message)

    def caption(self, message: str) -> None:
        self.caption_messages.append(message)

    def selectbox(self, _: str, *, options: list[str], key: str) -> str:
        value = self.session_state.get(key, options[0])
        self.session_state[key] = value
        self.instantiated_keys.add(key)
        return str(value)

    def text_area(
        self,
        _: str,
        *,
        value: str = "",
        key: str,
        height: int | None = None,
    ) -> str:
        del height
        if key not in self.session_state:
            self.session_state[key] = value
        self.instantiated_keys.add(key)
        return str(self.session_state[key])

    def checkbox(self, _: str, *, value: bool = False, key: str) -> bool:
        if key not in self.session_state:
            self.session_state[key] = value
        self.instantiated_keys.add(key)
        return bool(self.session_state[key])

    def columns(self, count: int) -> list[FakeColumn]:
        return [FakeColumn(self) for _ in range(count)]

    def button(self, _: str, *, key: str, disabled: bool = False) -> bool:
        if disabled:
            return False
        return self._button_presses.get(key, False)

    def code(self, _: str) -> None:
        return None

    def rerun(self) -> None:
        self.rerun_requested = True

    def spinner(self, _message: str):
        from contextlib import nullcontext
        return nullcontext()


class FakeSessionState(dict[str, object]):
    def __init__(self) -> None:
        super().__init__()
        self.instantiated_keys: set[str] | None = None

    def __setitem__(self, key: str, value: object) -> None:
        if self.instantiated_keys is not None and key in self.instantiated_keys:
            raise RuntimeError(f"{key} cannot be modified after the widget is instantiated")
        super().__setitem__(key, value)


def test_apply_generated_result_rebuilds_the_final_prompt() -> None:
    session = EditorSession(block_values={"subject": "robot"})
    next_session = apply_generated_result(
        session=session,
        generated_blocks={"style": "cinematic still"},
        block_ids=["subject", "style"],
        formula="{subject}, {style}",
    )

    assert next_session.final_prompt == "robot, cinematic still"


def test_build_generation_request_maps_template_and_session() -> None:
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    session = EditorSession(
        short_idea="robot portrait",
        block_values={"subject": "old robot"},
        locked_blocks={"shot"},
    )

    request = build_generation_request(template, session)

    assert request["short_idea"] == "robot portrait"
    assert request["active_blocks"] == template.block_order
    assert request["template_prompt"] == template.template_system_prompt
    assert request["current_values"] == {}
    assert request["locked_blocks"] == {"shot"}
    assert request["regenerate_unlocked"] is False
    assert request["variation_index"] == 0
    assert request["avoid_values"] == {}
    assert request["block_instructions"]["subject"] == template.blocks["subject"].instruction


def test_record_prompt_if_present_appends_only_non_empty_prompts() -> None:
    store = FakeHistoryStore()

    assert record_prompt_if_present(store, "  ") is None
    record = record_prompt_if_present(store, "  robot, cinematic  ")

    assert store.prompts == ["robot, cinematic"]
    assert record is None


def test_pending_workbench_widget_state_applies_before_widget_instantiation() -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    session = EditorSession(
        block_values={"subject": "android courier", "scene": "rainy neon street"},
        final_prompt="cinematic film still, android courier, rainy neon street",
    )

    queue_workbench_widget_state(fake_st, template, session, ["subject", "scene"])
    apply_pending_workbench_widget_state(fake_st)

    assert fake_st.session_state[f"block-{template.id}-subject"] == "android courier"
    assert fake_st.session_state[f"block-{template.id}-scene"] == "rainy neon street"
    assert fake_st.session_state[f"final-prompt-{template.id}"] == session.final_prompt


def test_pending_widget_state_can_apply_lock_checkboxes() -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st.session_state["_workbench_pending_widget_state"] = {
        "lock-universal-subject": True,
        "lock-universal-scene": False,
    }

    apply_pending_workbench_widget_state(fake_st)

    assert fake_st.session_state["lock-universal-subject"] is True
    assert fake_st.session_state["lock-universal-scene"] is False


def test_notice_roundtrip_uses_flash_slot() -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys

    set_workbench_notice(fake_st, "Промт обновлен.")

    assert pop_workbench_notice(fake_st) == "Промт обновлен."
    assert pop_workbench_notice(fake_st) is None


def test_copy_text_to_clipboard_uses_local_os_clipboard(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args[0], 0)

    monkeypatch.setattr("sys.platform", "win32")

    assert copy_text_to_clipboard("robot prompt", runner=fake_run) is True
    assert captured["args"][0] == [
        "powershell",
        "-NoProfile",
        "-Command",
        "[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false); "
        "[Console]::In.ReadToEnd() | Set-Clipboard",
    ]
    assert captured["kwargs"]["input"] == "robot prompt"
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["encoding"] == "utf-8"
    assert captured["kwargs"]["check"] is True


def test_copy_text_to_clipboard_accepts_unicode_prompt_text(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args[0], 0)

    monkeypatch.setattr("sys.platform", "win32")
    prompt_text = "robot with non-breaking hyphen \u2011 test"

    assert copy_text_to_clipboard(prompt_text, runner=fake_run) is True
    assert captured["kwargs"]["input"] == prompt_text
    assert captured["kwargs"]["encoding"] == "utf-8"


def test_build_generation_request_for_regenerate_excludes_locked_values_from_avoid_list() -> None:
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    session = EditorSession(
        short_idea="robot portrait",
        block_values={"subject": "old robot", "scene": "studio", "shot": "close-up"},
        locked_blocks={"shot"},
    )

    request = build_generation_request(
        template,
        session,
        regenerate_unlocked=True,
        variation_index=2,
    )

    assert request["regenerate_unlocked"] is True
    assert request["variation_index"] == 2
    assert request["avoid_values"]["subject"] == "old robot"
    assert request["avoid_values"]["scene"] == "studio"
    assert "shot" not in request["avoid_values"]


def test_build_generation_request_keeps_only_locked_current_values_for_regular_generate() -> None:
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    session = EditorSession(
        short_idea="new idea",
        block_values={"subject": "old robot", "scene": "studio", "shot": "close-up"},
        locked_blocks={"shot"},
    )

    request = build_generation_request(template, session)

    assert request["current_values"] == {"shot": "close-up"}
    assert request["locked_blocks"] == {"shot"}


def test_clear_unlocked_blocks_clears_only_unlocked_values_and_rebuilds_prompt() -> None:
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    session = EditorSession(
        block_values={"subject": "old robot", "scene": "studio", "shot": "close-up"},
        locked_blocks={"shot"},
        final_prompt="old final prompt",
    )

    clear_unlocked_blocks(template, session)

    assert session.block_values["subject"] == ""
    assert session.block_values["scene"] == ""
    assert session.block_values["shot"] == "close-up"
    assert session.final_prompt == "cinematic film still, close-up"


def test_lock_all_blocks_locks_every_enabled_block() -> None:
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    session = EditorSession(locked_blocks={"shot"})

    lock_all_blocks(template, session)

    assert session.locked_blocks == set(template.block_order)


def test_unlock_all_blocks_clears_all_locks() -> None:
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    session = EditorSession(locked_blocks=set(template.block_order))

    unlock_all_blocks(session)

    assert session.locked_blocks == set()


def test_render_workbench_updates_widget_state_after_generation_on_rerun(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    fake_st.session_state["selected_template_id"] = template.name
    fake_st.session_state["short_idea"] = "short idea"
    fake_st.session_state[f"block-{template.id}-subject"] = ""
    fake_st.session_state[f"block-{template.id}-scene"] = ""

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    history_store = FakeHistoryStore()
    view_model = {
        "templates": [template],
        "generation_service": FakeGenerationService(),
        "history_store": history_store,
        "settings": {
            "model": "openai/gpt-4o-mini",
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 700,
        },
    }

    # Rerun 1: generate button pressed → flag set, no generation yet
    fake_st._button_presses = {"generate": True}
    render_workbench(view_model)

    assert fake_st.session_state["_workbench_generating"] == "generate"
    assert fake_st.rerun_requested is True
    assert history_store.prompts == []

    # Rerun 2: flag set → generation executes → widget state queued
    fake_st._button_presses = {}
    fake_st.rerun_requested = False
    fake_st.instantiated_keys.clear()
    render_workbench(view_model)

    assert fake_st.rerun_requested is True
    assert history_store.prompts == ["cinematic film still, android courier, rainy neon street"]
    assert "_workbench_generating" not in fake_st.session_state
    assert "_workbench_pending_widget_state" in fake_st.session_state
    assert fake_st.session_state[f"block-{template.id}-subject"] == ""

    # Rerun 3: widget state applied → results visible in session state
    fake_st.rerun_requested = False
    fake_st.instantiated_keys.clear()
    render_workbench(view_model)

    assert fake_st.session_state[f"block-{template.id}-subject"] == "android courier"
    assert fake_st.session_state[f"block-{template.id}-scene"] == "rainy neon street"
    assert fake_st.session_state[f"final-prompt-{template.id}"] == history_store.prompts[0]
    assert fake_st.success_messages == ["Промт обновлен."]


def test_render_workbench_regenerate_passes_variation_controls(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {"regenerate_unlocked": True}
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    fake_st.session_state["selected_template_id"] = template.name
    fake_st.session_state["short_idea"] = "short idea"
    fake_st.session_state[f"block-{template.id}-subject"] = "old robot"
    fake_st.session_state[f"block-{template.id}-scene"] = "studio"
    fake_st.session_state[f"block-{template.id}-shot"] = "close-up"
    fake_st.session_state[f"lock-{template.id}-shot"] = True

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    history_store = FakeHistoryStore()
    generation_service = FakeGenerationService()
    view_model = {
        "templates": [template],
        "generation_service": generation_service,
        "history_store": history_store,
        "settings": {
            "model": "openai/gpt-4o-mini",
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 700,
        },
    }

    # Rerun 1: button click → flag set, no generation
    render_workbench(view_model)
    assert fake_st.session_state["_workbench_generating"] == "regenerate"
    assert generation_service.calls == []

    # Rerun 2: flag set → generation executes
    fake_st._button_presses = {}
    fake_st.rerun_requested = False
    fake_st.instantiated_keys.clear()
    render_workbench(view_model)

    assert generation_service.calls[0]["regenerate_unlocked"] is True
    assert generation_service.calls[0]["variation_index"] == 1
    assert generation_service.calls[0]["avoid_values"]["subject"] == "old robot"
    assert generation_service.calls[0]["avoid_values"]["scene"] == "studio"
    assert "shot" not in generation_service.calls[0]["avoid_values"]


def test_render_workbench_generate_does_not_send_old_unlocked_values(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {"generate": True}
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    fake_st.session_state["selected_template_id"] = template.name
    fake_st.session_state["short_idea"] = "fresh prompt"
    fake_st.session_state[f"block-{template.id}-subject"] = "old robot"
    fake_st.session_state[f"block-{template.id}-scene"] = "studio"
    fake_st.session_state[f"block-{template.id}-shot"] = "close-up"
    fake_st.session_state[f"lock-{template.id}-shot"] = True

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    generation_service = FakeGenerationService()
    view_model = {
        "templates": [template],
        "generation_service": generation_service,
        "history_store": FakeHistoryStore(),
        "settings": {
            "model": "openai/gpt-4o-mini",
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 700,
        },
    }

    # Rerun 1: button click → flag set, no generation
    render_workbench(view_model)
    assert fake_st.session_state["_workbench_generating"] == "generate"
    assert generation_service.calls == []

    # Rerun 2: flag set → generation executes
    fake_st._button_presses = {}
    fake_st.rerun_requested = False
    fake_st.instantiated_keys.clear()
    render_workbench(view_model)

    assert generation_service.calls[0]["current_values"] == {"shot": "close-up"}
    assert generation_service.calls[0]["locked_blocks"] == {"shot"}


def test_render_workbench_clear_unlocked_updates_fields_and_keeps_locked(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {"clear_unlocked": True}
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    fake_st.session_state["selected_template_id"] = template.name
    fake_st.session_state[f"block-{template.id}-subject"] = "old robot"
    fake_st.session_state[f"block-{template.id}-scene"] = "studio"
    fake_st.session_state[f"block-{template.id}-shot"] = "close-up"
    fake_st.session_state[f"lock-{template.id}-shot"] = True

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    history_store = FakeHistoryStore()
    render_workbench(
        {
            "templates": [template],
            "history_store": history_store,
            "settings": {},
        }
    )

    assert fake_st.rerun_requested is True
    pending = fake_st.session_state["_workbench_pending_widget_state"]
    assert pending[f"block-{template.id}-subject"] == ""
    assert pending[f"block-{template.id}-scene"] == ""
    assert pending[f"block-{template.id}-shot"] == "close-up"
    assert pending[f"final-prompt-{template.id}"] == "cinematic film still, close-up"


def test_render_workbench_lock_all_sets_all_checkbox_states(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {"lock_all": True}
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    fake_st.session_state["selected_template_id"] = template.name

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    render_workbench(
        {
            "templates": [template],
            "history_store": FakeHistoryStore(),
            "settings": {},
        }
    )

    pending = fake_st.session_state["_workbench_pending_widget_state"]
    for block_id in template.block_order:
        assert pending[f"lock-{template.id}-{block_id}"] is True


def test_render_workbench_unlock_all_clears_all_checkbox_states(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {"unlock_all": True}
    template = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    fake_st.session_state["selected_template_id"] = template.name
    for block_id in template.block_order:
        fake_st.session_state[f"lock-{template.id}-{block_id}"] = True

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    render_workbench(
        {
            "templates": [template],
            "history_store": FakeHistoryStore(),
            "settings": {},
        }
    )

    pending = fake_st.session_state["_workbench_pending_widget_state"]
    for block_id in template.block_order:
        assert pending[f"lock-{template.id}-{block_id}"] is False


def test_render_workbench_switching_templates_keeps_separate_drafts(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {}
    templates = load_builtin_templates()
    universal = next(template for template in templates if template.name == "Universal")
    cinematic = next(template for template in templates if template.name == "Cinematic")
    fake_st.session_state["selected_template_id"] = universal.name
    fake_st.session_state["short_idea"] = "shared idea"
    fake_st.session_state[f"block-{universal.id}-subject"] = "robot"
    fake_st.session_state[f"lock-{universal.id}-subject"] = True
    fake_st.session_state[f"final-prompt-{universal.id}"] = "robot prompt"

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    render_workbench(
        {
            "templates": [universal, cinematic],
            "history_store": FakeHistoryStore(),
            "settings": {},
        }
    )

    session = fake_st.session_state["workbench_session"]
    session.final_prompt = "robot prompt"
    fake_st.instantiated_keys.clear()
    fake_st.session_state["selected_template_id"] = cinematic.name

    render_workbench(
        {
            "templates": [universal, cinematic],
            "history_store": FakeHistoryStore(),
            "settings": {},
        }
    )

    session = fake_st.session_state["workbench_session"]
    assert session.block_values.get("subject", "") == ""
    assert "robot" not in session.block_values.values()
    assert session.locked_blocks == set()
    assert session.final_prompt == ""

    session.block_values["subject"] = "detective"
    session.final_prompt = "cinematic detective"
    fake_st.instantiated_keys.clear()
    fake_st.session_state[f"block-{cinematic.id}-subject"] = "detective"
    fake_st.session_state[f"final-prompt-{cinematic.id}"] = "cinematic detective"
    fake_st.instantiated_keys.clear()
    fake_st.session_state["selected_template_id"] = universal.name

    render_workbench(
        {
            "templates": [universal, cinematic],
            "history_store": FakeHistoryStore(),
            "settings": {},
        }
    )

    session = fake_st.session_state["workbench_session"]
    assert session.block_values["subject"] == "robot"
    assert session.locked_blocks == {"subject"}
    assert session.final_prompt == "robot prompt"


def test_render_workbench_shows_new_draft_indicator_for_empty_template(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {}
    template = next(template for template in load_builtin_templates() if template.name == "Universal")

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    render_workbench(
        {
            "templates": [template],
            "history_store": FakeHistoryStore(),
            "settings": {},
        }
    )

    assert fake_st.caption_messages == ["Новый черновик шаблона. Заполните поля или сгенерируйте промт."]


def test_render_workbench_shows_saved_draft_indicator_when_template_has_content(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {}
    template = next(template for template in load_builtin_templates() if template.name == "Universal")
    fake_st.session_state["selected_template_id"] = template.name
    session = EditorSession(
        active_template_id=template.id,
        block_values={"subject": "robot"},
    )

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    render_workbench(
        {
            "templates": [template],
            "session": session,
            "history_store": FakeHistoryStore(),
            "settings": {},
        }
    )

    assert fake_st.caption_messages == ["Черновик этого шаблона сохраняется автоматически."]


def test_workbench_generating_helpers_roundtrip() -> None:
    fake_st = FakeStreamlit()
    set_workbench_generating(fake_st, "generate")
    assert pop_workbench_generating(fake_st) == "generate"
    assert pop_workbench_generating(fake_st) is None


def test_workbench_generating_helpers_store_regenerate() -> None:
    fake_st = FakeStreamlit()
    set_workbench_generating(fake_st, "regenerate")
    assert pop_workbench_generating(fake_st) == "regenerate"


def test_editor_panel_disables_generate_buttons_when_generating() -> None:
    fake_st = FakeStreamlit()
    fake_st._button_presses = {"generate": True, "regenerate_unlocked": True}
    template = next(t for t in load_builtin_templates() if t.name == "Cinematic")
    session = EditorSession()

    actions = render_workbench_editor_panel(
        fake_st, template=template, session=session, generating=True
    )

    assert actions["generate"] is False
    assert actions["regenerate"] is False


def test_output_panel_does_not_render_prompt_text_area_when_generating() -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    template = next(t for t in load_builtin_templates() if t.name == "Cinematic")
    session = EditorSession()
    summary = build_workbench_summary(session, active_block_count=len(template.block_order))

    render_workbench_output_panel(
        fake_st, session=session, template=template, summary=summary, generating=True
    )

    assert f"final-prompt-{template.id}" not in fake_st.instantiated_keys


def test_generate_click_sets_generating_flag_and_reruns(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {"generate": True}
    template = next(t for t in load_builtin_templates() if t.name == "Cinematic")
    fake_st.session_state["selected_template_id"] = template.name
    fake_st.session_state["short_idea"] = "short idea"

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)
    generation_service = FakeGenerationService()

    render_workbench(
        {
            "templates": [template],
            "generation_service": generation_service,
            "history_store": FakeHistoryStore(),
            "settings": {
                "model": "openai/gpt-4o-mini",
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": 700,
            },
        }
    )

    assert fake_st.session_state["_workbench_generating"] == "generate"
    assert fake_st.rerun_requested is True
    assert generation_service.calls == []


def test_regenerate_click_sets_generating_flag(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {"regenerate_unlocked": True}
    template = next(t for t in load_builtin_templates() if t.name == "Cinematic")
    fake_st.session_state["selected_template_id"] = template.name
    fake_st.session_state["short_idea"] = "short idea"

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    render_workbench(
        {
            "templates": [template],
            "generation_service": FakeGenerationService(),
            "history_store": FakeHistoryStore(),
            "settings": {},
        }
    )

    assert fake_st.session_state["_workbench_generating"] == "regenerate"
    assert fake_st.rerun_requested is True


def test_generating_flag_executes_generation_and_clears_flag(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.instantiated_keys = fake_st.instantiated_keys
    fake_st._button_presses = {}
    fake_st.session_state["_workbench_generating"] = "generate"
    template = next(t for t in load_builtin_templates() if t.name == "Cinematic")
    fake_st.session_state["selected_template_id"] = template.name
    fake_st.session_state["short_idea"] = "short idea"
    fake_st.session_state[f"block-{template.id}-subject"] = ""
    fake_st.session_state[f"block-{template.id}-scene"] = ""

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)
    generation_service = FakeGenerationService()

    render_workbench(
        {
            "templates": [template],
            "generation_service": generation_service,
            "history_store": FakeHistoryStore(),
            "settings": {
                "model": "openai/gpt-4o-mini",
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": 700,
            },
        }
    )

    assert "_workbench_generating" not in fake_st.session_state
    assert len(generation_service.calls) == 1
    assert fake_st.rerun_requested is True
