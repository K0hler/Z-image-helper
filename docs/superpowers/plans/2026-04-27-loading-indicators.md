# Loading Indicators Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show a spinner inside the output panel and disable generate/regenerate buttons while the API call is in progress, so the user gets clear visual feedback instead of a frozen UI.

**Architecture:** A new session-state flag `_workbench_generating` ("generate" | "regenerate") follows the same deferred-write pattern as `_workbench_notice`. On click, the flag is set and the page reruns; on the next rerun the panels see the flag, render disabled buttons / spinner placeholder, and then the action loop executes the API call and clears the flag before requesting a final rerun.

**Tech Stack:** Python 3.12, Streamlit, pytest

---

## File Map

| File | Change |
|---|---|
| `src/zprompt_helper/ui/workbench.py` | Add `set_workbench_generating` / `pop_workbench_generating`; refactor `render_workbench` action loop |
| `src/zprompt_helper/ui/workbench_panels.py` | Add `generating: bool` param to editor + output panel; disable buttons; show loading text |
| `tests/ui/test_workbench_actions.py` | Add `spinner` + `disabled`-aware `button` to `FakeStreamlit`; add 3 new tests; update existing three-rerun test |

---

## Task 1: New session-state helpers and FakeStreamlit additions

**Files:**
- Modify: `src/zprompt_helper/ui/workbench.py`
- Modify: `tests/ui/test_workbench_actions.py`

- [ ] **Step 1: Add imports to test file**

Open `tests/ui/test_workbench_actions.py`. Add `set_workbench_generating` and `pop_workbench_generating` to the existing import block from `zprompt_helper.ui.workbench`:

```python
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
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/ui/test_workbench_actions.py`:

```python
def test_workbench_generating_helpers_roundtrip() -> None:
    fake_st = FakeStreamlit()
    set_workbench_generating(fake_st, "generate")
    assert pop_workbench_generating(fake_st) == "generate"
    assert pop_workbench_generating(fake_st) is None


def test_workbench_generating_helpers_store_regenerate() -> None:
    fake_st = FakeStreamlit()
    set_workbench_generating(fake_st, "regenerate")
    assert pop_workbench_generating(fake_st) == "regenerate"
```

- [ ] **Step 3: Run tests to verify they fail**

```
python -m pytest tests/ui/test_workbench_actions.py::test_workbench_generating_helpers_roundtrip tests/ui/test_workbench_actions.py::test_workbench_generating_helpers_store_regenerate -v
```

Expected: `ImportError` — `pop_workbench_generating` not found.

- [ ] **Step 4: Add helpers to workbench.py**

In `src/zprompt_helper/ui/workbench.py`, after the `pop_workbench_notice` function (around line 139), insert:

```python
def set_workbench_generating(st_module: Any, action: str) -> None:
    st_module.session_state["_workbench_generating"] = action


def pop_workbench_generating(st_module: Any) -> str | None:
    return st_module.session_state.pop("_workbench_generating", None)
```

- [ ] **Step 5: Add `spinner` method to FakeStreamlit**

In `tests/ui/test_workbench_actions.py`, inside the `FakeStreamlit` class (after the `rerun` method, around line 106), add:

```python
def spinner(self, _message: str):
    from contextlib import nullcontext
    return nullcontext()
```

- [ ] **Step 6: Run tests to verify they pass**

```
python -m pytest tests/ui/test_workbench_actions.py::test_workbench_generating_helpers_roundtrip tests/ui/test_workbench_actions.py::test_workbench_generating_helpers_store_regenerate -v
```

Expected: `2 passed`.

- [ ] **Step 7: Run the full test suite to check for regressions**

```
python -m pytest -v
```

Expected: all existing tests pass.

- [ ] **Step 8: Commit**

```bash
git add src/zprompt_helper/ui/workbench.py tests/ui/test_workbench_actions.py
git commit -m "feat(ui): add set/pop_workbench_generating helpers"
```

---

## Task 2: Disable generate/regenerate buttons when generating

**Files:**
- Modify: `src/zprompt_helper/ui/workbench_panels.py`
- Modify: `tests/ui/test_workbench_actions.py`

- [ ] **Step 1: Update `FakeStreamlit.button` to accept `disabled`**

In `tests/ui/test_workbench_actions.py`, replace the existing `button` method in `FakeStreamlit`:

```python
def button(self, _: str, *, key: str, disabled: bool = False) -> bool:
    if disabled:
        return False
    return self._button_presses.get(key, False)
```

- [ ] **Step 2: Add panel import to test file**

Add to the imports at the top of `tests/ui/test_workbench_actions.py`:

```python
from zprompt_helper.ui.workbench_panels import (
    build_workbench_summary,
    render_workbench_editor_panel,
    render_workbench_output_panel,
)
```

- [ ] **Step 3: Write the failing test**

Append to `tests/ui/test_workbench_actions.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it fails**

```
python -m pytest tests/ui/test_workbench_actions.py::test_editor_panel_disables_generate_buttons_when_generating -v
```

Expected: `TypeError` — `render_workbench_editor_panel() got an unexpected keyword argument 'generating'`.

- [ ] **Step 5: Add `generating` param to `render_workbench_editor_panel`**

In `src/zprompt_helper/ui/workbench_panels.py`, update the signature and the two button calls:

```python
def render_workbench_editor_panel(
    st_module: Any,
    *,
    template: TemplateDefinition,
    session: EditorSession,
    generating: bool = False,
) -> dict[str, bool]:
```

Inside the function, update the generate and regenerate button lines:

```python
generate = col1.button("Сгенерировать", key="generate", disabled=generating)
regenerate = col2.button(
    "Перегенерировать незаблокированные",
    key="regenerate_unlocked",
    disabled=generating,
)
```

The other three buttons (`clear_unlocked`, `lock_all`, `unlock_all`) stay unchanged — no `disabled` argument.

- [ ] **Step 6: Run test to verify it passes**

```
python -m pytest tests/ui/test_workbench_actions.py::test_editor_panel_disables_generate_buttons_when_generating -v
```

Expected: `1 passed`.

- [ ] **Step 7: Run full test suite**

```
python -m pytest -v
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add src/zprompt_helper/ui/workbench_panels.py tests/ui/test_workbench_actions.py
git commit -m "feat(ui): disable generate buttons during generation"
```

---

## Task 3: Show loading indicator in output panel

**Files:**
- Modify: `src/zprompt_helper/ui/workbench_panels.py`
- Modify: `tests/ui/test_workbench_actions.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/ui/test_workbench_actions.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```
python -m pytest tests/ui/test_workbench_actions.py::test_output_panel_does_not_render_prompt_text_area_when_generating -v
```

Expected: `TypeError` — `render_workbench_output_panel() got an unexpected keyword argument 'generating'`.

- [ ] **Step 3: Add `generating` param to `render_workbench_output_panel`**

In `src/zprompt_helper/ui/workbench_panels.py`, update the signature:

```python
def render_workbench_output_panel(
    st_module: Any,
    *,
    session: EditorSession,
    template: TemplateDefinition,
    summary: WorkbenchSummary,
    generating: bool = False,
) -> dict[str, bool]:
```

Inside the function, wrap the text area + code block with an `if/else` on `generating`. Replace this existing block:

```python
session.final_prompt = st_module.text_area(
    "Финальный промт",
    value=session.final_prompt,
    key=f"final-prompt-{template.id}",
    height=180,
)
if session.final_prompt:
    st_module.code(session.final_prompt)
else:
    _markdown(
        st_module,
        '<div class="zp-empty">Generate or rebuild to see the final prompt here.</div>',
        unsafe_allow_html=True,
    )
```

with:

```python
if generating:
    _markdown(st_module, "⏳ **Генерирую промт…**")
else:
    session.final_prompt = st_module.text_area(
        "Финальный промт",
        value=session.final_prompt,
        key=f"final-prompt-{template.id}",
        height=180,
    )
    if session.final_prompt:
        st_module.code(session.final_prompt)
    else:
        _markdown(
            st_module,
            '<div class="zp-empty">Generate or rebuild to see the final prompt here.</div>',
            unsafe_allow_html=True,
        )
```

The `rebuild` and `copy_prompt` buttons below this block remain unchanged.

- [ ] **Step 4: Run test to verify it passes**

```
python -m pytest tests/ui/test_workbench_actions.py::test_output_panel_does_not_render_prompt_text_area_when_generating -v
```

Expected: `1 passed`.

- [ ] **Step 5: Run full test suite**

```
python -m pytest -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/zprompt_helper/ui/workbench_panels.py tests/ui/test_workbench_actions.py
git commit -m "feat(ui): show loading indicator in output panel during generation"
```

---

## Task 4: Refactor render_workbench action loop (Block A + Block B)

**Files:**
- Modify: `src/zprompt_helper/ui/workbench.py`
- Modify: `tests/ui/test_workbench_actions.py`

- [ ] **Step 1: Write three new failing tests**

Append to `tests/ui/test_workbench_actions.py`:

```python
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
```

- [ ] **Step 2: Run the three new tests to verify they fail**

```
python -m pytest tests/ui/test_workbench_actions.py::test_generate_click_sets_generating_flag_and_reruns tests/ui/test_workbench_actions.py::test_regenerate_click_sets_generating_flag tests/ui/test_workbench_actions.py::test_generating_flag_executes_generation_and_clears_flag -v
```

Expected: all three `FAILED` — `generate_click` test fails because generation is called immediately (no flag set yet), others fail due to assertion errors.

- [ ] **Step 3: Update `test_render_workbench_updates_widget_state_after_generation_on_rerun` to three reruns**

Replace the entire existing function `test_render_workbench_updates_widget_state_after_generation_on_rerun` in `tests/ui/test_workbench_actions.py` with:

```python
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
```

- [ ] **Step 4: Refactor `render_workbench` in workbench.py**

In `src/zprompt_helper/ui/workbench.py`, make the following changes:

**4a.** After the second `apply_pending_workbench_widget_state(st)` call (around line 228), add:

```python
    generating_action = st.session_state.get("_workbench_generating")
    generating = bool(generating_action)
```

**4b.** Pass `generating=generating` to both panel calls:

```python
    with _column_scope(left_col):
        editor_actions = render_workbench_editor_panel(
            st,
            template=template,
            session=session,
            generating=generating,
        )
    summary = build_workbench_summary(session, active_block_count=len(active_blocks))
    with _column_scope(right_col):
        output_actions = render_workbench_output_panel(
            st,
            session=session,
            template=template,
            summary=summary,
            generating=generating,
        )
```

**4c.** Replace the entire `if generate or regenerate:` block (and the `generate`/`regenerate` variable declarations) with Block A + Block B. The full replacement (starting from `actions = ...`) is:

```python
    actions = editor_actions | output_actions
    generate = bool(actions.get("generate"))
    regenerate = bool(actions.get("regenerate"))
    rebuild = bool(actions.get("rebuild"))
    clear_unlocked = bool(actions.get("clear_unlocked"))
    lock_all = bool(actions.get("lock_all"))
    unlock_all = bool(actions.get("unlock_all"))
    copy_prompt = bool(actions.get("copy_prompt"))

    if generating_action:
        try:
            if settings_service is not None:
                settings = settings_service.load()
            service = generation_service or _build_generation_service(
                generation_factory,
                _setting(settings, "api_key", ""),
            )
            if generating_action == "regenerate":
                session.variation_index += 1
            else:
                session.variation_index = 0
            request = build_generation_request(
                template,
                session,
                regenerate_unlocked=(generating_action == "regenerate"),
                variation_index=session.variation_index,
            )
            with _spinner(st, "Генерирую промт…"):
                generated = service.generate_blocks(
                    model=_setting(settings, "model", ""),
                    temperature=float(_setting(settings, "temperature", 0.2)),
                    top_p=float(_setting(settings, "top_p", 0.9)),
                    max_tokens=int(_setting(settings, "max_tokens", 700)),
                    **request,
                )
            apply_generated_result(
                session=session,
                generated_blocks=generated,
                block_ids=request["active_blocks"],
                formula=template.assembly_formula,
            )
            queue_workbench_widget_state(st, template, session, request["active_blocks"])
            if history_store is not None:
                record_prompt_if_present(history_store, session.final_prompt)
            pop_workbench_generating(st)
            set_workbench_notice(st, "Промт обновлен.")
            rerun_workbench(st)
            return
        except Exception as error:
            pop_workbench_generating(st)
            st.error(f"Не удалось сгенерировать промт: {error}")
        return

    if generate:
        set_workbench_generating(st, "generate")
        rerun_workbench(st)
        return
    if regenerate:
        set_workbench_generating(st, "regenerate")
        rerun_workbench(st)
        return

    if rebuild:
```

The `if rebuild:`, `if clear_unlocked:`, `if lock_all:`, `if unlock_all:`, `if copy_prompt:` blocks below stay exactly as they are.

- [ ] **Step 5: Run the four new/updated tests**

```
python -m pytest tests/ui/test_workbench_actions.py::test_generate_click_sets_generating_flag_and_reruns tests/ui/test_workbench_actions.py::test_regenerate_click_sets_generating_flag tests/ui/test_workbench_actions.py::test_generating_flag_executes_generation_and_clears_flag tests/ui/test_workbench_actions.py::test_render_workbench_updates_widget_state_after_generation_on_rerun -v
```

Expected: `4 passed`.

- [ ] **Step 6: Run the full test suite**

```
python -m pytest -v
```

Expected: all pass. If `test_render_workbench_regenerate_passes_variation_controls` fails, check that `fake_st._button_presses = {"regenerate_unlocked": True}` now only sets the flag and that the test needs a second render call with the flag in session state. Update analogously to the three-rerun pattern if needed.

- [ ] **Step 7: Commit**

```bash
git add src/zprompt_helper/ui/workbench.py tests/ui/test_workbench_actions.py
git commit -m "feat(ui): add generating state flag to action loop"
```

---

## Task 5: Verify regenerate variation controls still work

The existing test `test_render_workbench_regenerate_passes_variation_controls` presses `regenerate_unlocked` and checks that `generation_service.calls[0]["regenerate_unlocked"] is True`. After Task 4 this test will need a second render call to actually trigger generation (same as the three-rerun pattern).

**Files:**
- Modify: `tests/ui/test_workbench_actions.py`

- [ ] **Step 1: Run the test to check if it still passes**

```
python -m pytest tests/ui/test_workbench_actions.py::test_render_workbench_regenerate_passes_variation_controls -v
```

If it passes, skip to Step 3. If it fails, proceed to Step 2.

- [ ] **Step 2: Update the test to use the two-step rerun**

Replace `test_render_workbench_regenerate_passes_variation_controls` in `tests/ui/test_workbench_actions.py` with:

```python
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

    # Rerun 1: sets flag
    render_workbench(view_model)
    assert fake_st.session_state["_workbench_generating"] == "regenerate"

    # Rerun 2: executes generation
    fake_st._button_presses = {}
    fake_st.rerun_requested = False
    fake_st.instantiated_keys.clear()
    render_workbench(view_model)

    assert generation_service.calls[0]["regenerate_unlocked"] is True
    assert generation_service.calls[0]["variation_index"] == 1
    assert generation_service.calls[0]["avoid_values"]["subject"] == "old robot"
    assert generation_service.calls[0]["avoid_values"]["scene"] == "studio"
    assert "shot" not in generation_service.calls[0]["avoid_values"]
```

- [ ] **Step 3: Check `test_render_workbench_generate_does_not_send_old_unlocked_values`**

Run:

```
python -m pytest tests/ui/test_workbench_actions.py::test_render_workbench_generate_does_not_send_old_unlocked_values -v
```

If it passes, skip to Step 5. If it fails (because generation no longer fires on Rerun 1), replace the function with:

```python
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

    # Rerun 1: sets flag
    render_workbench(view_model)
    assert fake_st.session_state["_workbench_generating"] == "generate"

    # Rerun 2: executes generation
    fake_st._button_presses = {}
    fake_st.rerun_requested = False
    fake_st.instantiated_keys.clear()
    render_workbench(view_model)

    assert generation_service.calls[0]["current_values"] == {"shot": "close-up"}
    assert generation_service.calls[0]["locked_blocks"] == {"shot"}
```

- [ ] **Step 4: Run full test suite**

```
python -m pytest -v
```

Expected: all pass.

- [ ] **Step 5: Commit if changes were needed**

```bash
git add tests/ui/test_workbench_actions.py
git commit -m "test(ui): update generate/regenerate tests for three-rerun flow"
```

---

## Verification

After all tasks are complete:

```
python -m pytest -v
streamlit run app.py
```

Manual check:
1. Enter a short idea, click «Сгенерировать».
2. Observe: «Сгенерировать» and «Перегенерировать незаблокированные» buttons are greyed out; output panel shows «⏳ Генерирую промт…».
3. After response arrives: buttons re-enable, output panel shows the filled prompt.
4. Toast «Промт обновлен.» appears.
5. Click «Перегенерировать незаблокированные» — same behaviour; `variation_index` increments.
6. If API call fails (e.g., wrong key): buttons re-enable, error message shown, no permanent disabled state.
