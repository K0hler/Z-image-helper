# Loading Indicators Design

**Date:** 2026-04-27  
**Status:** Approved  
**Scope:** `src/zprompt_helper/ui/workbench.py`, `src/zprompt_helper/ui/workbench_panels.py`, `tests/ui/test_workbench_actions.py`

## Problem

When the user clicks «Сгенерировать» or «Перегенерировать», the app makes a blocking HTTP request to OpenRouter. During this time the UI is frozen with no visual feedback. The existing `_spinner` helper wraps the API call, but the spinner renders below both columns — outside the visible viewport — so the user never sees it.

## Goals

- Show a spinner **inside the output panel** (right column) in place of the final-prompt text area while generation is in progress.
- Disable only the **«Сгенерировать»** and **«Перегенерировать»** buttons during generation; all other buttons remain active.
- Fit naturally into the existing deferred-write pattern (`_workbench_notice`, `_workbench_pending_widget_state`).

## Non-Goals

- Progress bar tracking individual blocks.
- Disabling all buttons, not just generate/regenerate.
- Any CSS overlay or `st.empty()` placeholder approach.

## Approach

Add a new session-state flag `_workbench_generating` that stores the pending action (`"generate"` or `"regenerate"`), following the same pattern as `_workbench_notice`.

## State Machine (3 rerun cycles)

```
Rerun 1 — click detection
  generate or regenerate button returns True
  → session_state["_workbench_generating"] = "generate" | "regenerate"
  → rerun_workbench() (no API call yet)

Rerun 2 — generation
  _workbench_generating is set
  → panels render with generating=True
      - generate/regenerate buttons: disabled=True
      - output panel: st.spinner("Генерирую промт…") instead of text_area
  → service.generate_blocks() executes
  → flag cleared via pop_workbench_generating()
  → results written, _workbench_notice set, rerun

Rerun 3 — result display
  _workbench_generating = None (normal state)
  → buttons active, output panel shows filled prompt
  → toast "Промт обновлен."
```

## New Helpers (`workbench.py`)

```python
def set_workbench_generating(st_module: Any, action: str) -> None:
    st_module.session_state["_workbench_generating"] = action

def pop_workbench_generating(st_module: Any) -> str | None:
    return st_module.session_state.pop("_workbench_generating", None)
```

## Changes to `render_workbench`

Read the flag at the top of the function, before panels render:

```python
generating_action = st.session_state.get("_workbench_generating")
generating = bool(generating_action)
```

Pass `generating` to both panel functions:

```python
editor_actions = render_workbench_editor_panel(
    st, template=template, session=session, generating=generating
)
output_actions = render_workbench_output_panel(
    st, session=session, template=template, summary=summary, generating=generating
)
```

Replace the single `if generate or regenerate` block with two separate blocks:

**Block A — execute if flag is already set:**
```python
if generating_action:
    try:
        if generating_action == "regenerate":
            session.variation_index += 1
        else:
            session.variation_index = 0
        request = build_generation_request(...)
        with _spinner(st, "Генерирую промт…"):
            generated = service.generate_blocks(...)
        apply_generated_result(...)
        queue_workbench_widget_state(...)
        record_prompt_if_present(...)
        pop_workbench_generating(st)
        set_workbench_notice(st, "Промт обновлен.")
        rerun_workbench(st)
    except Exception as error:
        pop_workbench_generating(st)
        st.error(f"Не удалось сгенерировать промт: {error}")
    return
```

**Block B — set flag if button clicked:**
```python
if generate:
    set_workbench_generating(st, "generate")
    rerun_workbench(st)
    return
if regenerate:
    set_workbench_generating(st, "regenerate")
    rerun_workbench(st)
    return
```

All other actions (rebuild, clear_unlocked, lock_all, unlock_all, copy_prompt) remain unchanged below Block B.

## Changes to `workbench_panels.py`

### `render_workbench_editor_panel`

Add parameter `generating: bool = False`. Apply to generate/regenerate buttons only:

```python
generate = col1.button("Сгенерировать", key="generate", disabled=generating)
regenerate = col2.button(
    "Перегенерировать незаблокированные",
    key="regenerate_unlocked",
    disabled=generating,
)
```

Buttons «Очистить», «Заблокировать все», «Разблокировать все» — no change.

### `render_workbench_output_panel`

Add parameter `generating: bool = False`. Replace text area with spinner when generating:

```python
if generating:
    # Use st.spinner as a standalone display widget (no with-block needed here —
    # the actual blocking call happens in render_workbench, not in this panel).
    # Fallback to st.info if spinner is unavailable.
    spinner_fn = getattr(st_module, "spinner", None)
    if callable(spinner_fn):
        st_module.markdown("⏳ **Генерирую промт…**")
    else:
        st_module.info("Генерирую промт…")
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
        _markdown(st_module, '<div class="zp-empty">…</div>', unsafe_allow_html=True)
```

Buttons «Пересобрать» and «Скопировать» render in both states (not disabled).

## Error Handling

If `service.generate_blocks()` raises, `pop_workbench_generating(st)` is called **before** `st.error()`. This guarantees buttons never stay permanently disabled after a failed request.

## Testing

### `FakeStreamlit` addition

```python
def spinner(self, _message: str):
    from contextlib import nullcontext
    return nullcontext()
```

### Updated test

`test_render_workbench_updates_widget_state_after_generation_on_rerun` — updated to use three render calls:
1. First call with `generate` button pressed → sets flag, requests rerun (no generation yet).
2. Second call with flag set → generation executes, widget state queued, rerun requested.
3. Third call → widget state applied, results visible.

### New tests

| Test | Verifies |
|---|---|
| `test_generate_click_sets_generating_flag_and_reruns` | clicking «Сгенерировать» writes `_workbench_generating = "generate"` to session_state and requests rerun; `generate_blocks` is NOT called |
| `test_regenerate_click_sets_generating_flag` | clicking «Перегенерировать» writes `_workbench_generating = "regenerate"` |
| `test_generating_flag_executes_generation_and_clears_flag` | when flag is set, `generate_blocks` is called, flag is removed from session_state afterwards, results are written |
