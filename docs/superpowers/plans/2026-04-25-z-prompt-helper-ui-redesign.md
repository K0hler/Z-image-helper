# Z-Prompt-Helper UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the Streamlit UI so `Z-Prompt-Helper` looks modern and intentional, integrates `streamlit-shadcn-ui`, and improves layout clarity without regressing the stable workbench state flow.

**Architecture:** Keep the rerun-sensitive editing core on native Streamlit widgets where the current tests already prove correctness, and add a dedicated presentation layer for theme tokens, shell layout, cards, tabs, badges, dialogs, and feedback. Isolate `streamlit-shadcn-ui` behind small adapter helpers so the app can keep a consistent look while limiting third-party API spread across the codebase. Split large UI functions into shell and panel modules so layout work does not tangle with generation and session-state logic.

**Tech Stack:** Python 3.12, Streamlit 1.44+, `streamlit-shadcn-ui`, CSS theme injection, pytest, manual localhost verification

---

## Planned File Structure

- `pyproject.toml`: add the `streamlit-shadcn-ui` runtime dependency.
- `.streamlit/config.toml`: base Streamlit theme values for the redesigned app shell.
- `app.py`: call the global theme and render the new page shell before individual screens.
- `src/zprompt_helper/ui/theme.py`: design tokens, CSS generation, and app-wide visual helpers.
- `src/zprompt_helper/ui/shadcn.py`: wrapper functions around `streamlit-shadcn-ui` plus native fallbacks.
- `src/zprompt_helper/ui/page_frame.py`: top-level shell, section navigation, page headers, and shared action bars.
- `src/zprompt_helper/ui/workbench.py`: keep action/state logic, but delegate panel rendering and feedback helpers.
- `src/zprompt_helper/ui/workbench_panels.py`: workbench header, editor column, output column, and status summary.
- `src/zprompt_helper/ui/history_panel.py`: render history as a secondary surface that can live inside the redesigned workbench.
- `src/zprompt_helper/ui/template_manager.py`: move to a card-and-editor layout with forms and clearer hierarchy.
- `src/zprompt_helper/ui/settings_page.py`: move to grouped forms, cards, and explicit validation feedback.
- `tests/ui/test_theme.py`: verify token and CSS helpers.
- `tests/ui/test_shadcn.py`: verify wrapper fallback behavior and normalized component configuration.
- `tests/ui/test_page_frame.py`: verify page identity normalization and shell metadata.
- `tests/ui/test_workbench_layout.py`: verify derived workbench summary/state helpers used by the new layout.
- `tests/ui/test_template_manager_actions.py`: extend with layout-safe helper coverage where needed.
- `tests/ui/test_settings_page_actions.py`: extend with grouped settings/form helper coverage where needed.

## Visual Direction Resolved In This Plan

- Use a light editorial workspace instead of Streamlit defaults.
- Use warm neutral surfaces with a copper accent, not purple and not generic blue-on-white.
- Use `Manrope` for UI text and `IBM Plex Mono` for prompt/code surfaces through injected CSS.
- Give the app one clear visual system: soft canvas background, surfaced cards, thin borders, large headings, compact badges, and consistent spacing.
- Keep animation minimal. Use subtle hover and focus states only; do not add decorative motion that fights Streamlit reruns.

## Integration Decisions Resolved In This Plan

- `streamlit-shadcn-ui` is part of the redesign and should be used for high-visibility surfaces: cards, tabs, badges, dialogs, popovers, and progress/alert affordances.
- Do **not** replace the core block text editors and checkbox-driven lock controls in the first pass. The current rerun-safe workbench behavior depends on native widget semantics and existing tests.
- Use a hybrid shell: native Streamlit remains responsible for page execution and stateful editors; the shadcn layer is responsible for modern surfaces and visual hierarchy.
- Move history out of the bottom-of-page flow and into the workbench secondary surface.
- Use `st.form()` for `Settings` and custom template editing to reduce rerun noise while typing.
- Use `st.spinner()` for generation and key validation. Use `st.toast()` for transient success feedback with a safe fallback to `st.success()` if needed.
- Keep every redesign task shippable on its own so the UI can be integrated gradually.

## Acceptance Criteria For The Redesign

- The app still opens with `streamlit run app.py` and keeps all current functional flows working.
- Template switching still preserves separate drafts per template.
- Generation, regenerate-unlocked, rebuild, clear-unlocked, lock-all, unlock-all, and copy prompt still behave as before.
- The workbench no longer reads like one long vertical form; the editor and output areas are visually separated.
- `Template Manager` and `Settings` no longer look like raw widget stacks.
- Success, error, loading, and destructive-action states are visually distinct and easy to understand.
- The UI has a deliberate aesthetic direction, not default Streamlit styling with minor tweaks.

### Task 1: Add The Theme And Shadcn Foundation

**Files:**
- Modify: `pyproject.toml`
- Create: `.streamlit/config.toml`
- Create: `src/zprompt_helper/ui/theme.py`
- Create: `src/zprompt_helper/ui/shadcn.py`
- Create: `tests/ui/test_theme.py`
- Create: `tests/ui/test_shadcn.py`

- [ ] **Step 1: Write the failing tests for theme and wrapper helpers**

```python
from zprompt_helper.ui.theme import ThemeTokens, build_theme_css
from zprompt_helper.ui.shadcn import normalize_nav_items, shadcn_available


def test_build_theme_css_contains_core_tokens() -> None:
    css = build_theme_css(ThemeTokens())
    assert "--zp-surface" in css
    assert "Manrope" in css
    assert "IBM Plex Mono" in css


def test_normalize_nav_items_keeps_declared_order() -> None:
    items = normalize_nav_items(
        [
            {"id": "workbench", "label": "Workbench"},
            {"id": "template_manager", "label": "Template Manager"},
            {"id": "settings", "label": "Settings"},
        ]
    )
    assert [item["id"] for item in items] == ["workbench", "template_manager", "settings"]


def test_shadcn_available_returns_bool() -> None:
    assert isinstance(shadcn_available(), bool)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python -m pytest tests/ui/test_theme.py tests/ui/test_shadcn.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.ui.theme'
```

- [ ] **Step 3: Add the dependency and base Streamlit theme**

```toml
[project]
dependencies = [
  "streamlit>=1.44,<2.0",
  "streamlit-shadcn-ui>=0.1.19,<0.2",
  "httpx>=0.27,<1.0",
  "pydantic>=2.7,<3.0",
  "keyring>=25.2,<26.0",
]
```

```toml
[theme]
base = "light"
primaryColor = "#a35b2f"
backgroundColor = "#f5efe6"
secondaryBackgroundColor = "#fffaf3"
textColor = "#201a17"
font = "sans serif"
```

- [ ] **Step 4: Implement the theme tokens and shadcn adapter layer**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    canvas: str = "#f5efe6"
    surface: str = "#fffaf3"
    surface_alt: str = "#f0e6d8"
    ink: str = "#201a17"
    muted: str = "#6e6258"
    accent: str = "#a35b2f"
    accent_soft: str = "#ead3bf"
    border: str = "#dbcbbc"
    success: str = "#2f6f4f"
    danger: str = "#9b3d2f"


def build_theme_css(tokens: ThemeTokens = ThemeTokens()) -> str:
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Manrope:wght@400;500;600;700&display=swap');
    :root {{
      --zp-canvas: {tokens.canvas};
      --zp-surface: {tokens.surface};
      --zp-ink: {tokens.ink};
      --zp-accent: {tokens.accent};
      --zp-border: {tokens.border};
    }}
    html, body, [data-testid="stAppViewContainer"] {{
      font-family: "Manrope", sans-serif;
      background: var(--zp-canvas);
    }}
    code, pre, textarea {{
      font-family: "IBM Plex Mono", monospace;
    }}
    </style>
    """
```

```python
def shadcn_available() -> bool:
    try:
        import streamlit_shadcn_ui  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def normalize_nav_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {"id": str(item["id"]), "label": str(item["label"])}
        for item in items
    ]
```

```python
def apply_theme() -> None:
    import streamlit as st

    st.markdown(build_theme_css(), unsafe_allow_html=True)
```

- [ ] **Step 5: Run the targeted tests**

Run:

```bash
python -m pytest tests/ui/test_theme.py tests/ui/test_shadcn.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .streamlit/config.toml src/zprompt_helper/ui/theme.py src/zprompt_helper/ui/shadcn.py tests/ui/test_theme.py tests/ui/test_shadcn.py
git commit -m "feat: add ui theme foundation"
```

### Task 2: Build The Shared Page Shell

**Files:**
- Modify: `app.py`
- Create: `src/zprompt_helper/ui/page_frame.py`
- Create: `tests/ui/test_page_frame.py`

- [ ] **Step 1: Write the failing shell helper tests**

```python
from zprompt_helper.ui.page_frame import normalize_page_id, PAGE_SPECS


def test_normalize_page_id_defaults_to_workbench() -> None:
    assert normalize_page_id(None) == "workbench"
    assert normalize_page_id("unknown") == "workbench"


def test_page_specs_cover_all_sections() -> None:
    assert set(PAGE_SPECS) == {"workbench", "template_manager", "settings"}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python -m pytest tests/ui/test_page_frame.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.ui.page_frame'
```

- [ ] **Step 3: Implement the shell metadata and rendering helpers**

```python
PAGE_SPECS = {
    "workbench": {"label": "Workbench", "eyebrow": "Prompt Studio"},
    "template_manager": {"label": "Template Manager", "eyebrow": "Template Catalog"},
    "settings": {"label": "Settings", "eyebrow": "OpenRouter And App Defaults"},
}


def normalize_page_id(page_id: str | None) -> str:
    if page_id in PAGE_SPECS:
        return str(page_id)
    return "workbench"
```

```python
def render_page_shell(active_page: str) -> str:
    normalized = normalize_page_id(active_page)
    return normalized
```

- [ ] **Step 4: Update `app.py` to apply the theme and use the shell**

```python
import streamlit as st

from zprompt_helper.ui.page_frame import normalize_page_id, render_page_shell
from zprompt_helper.ui.theme import apply_theme


st.set_page_config(page_title="Z-Prompt-Helper", layout="wide")
apply_theme()
page = render_page_shell(
    normalize_page_id(st.session_state.get("active_page"))
)
```

- [ ] **Step 5: Run the shell tests and the smoke import test**

Run:

```bash
python -m pytest tests/ui/test_page_frame.py tests/smoke/test_import.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 6: Run a manual shell smoke check**

Run:

```bash
streamlit run app.py
```

Expected:

```text
Local URL: http://localhost:8501
```

Manual check:

- The app loads with the new global theme.
- The top of the app has a deliberate page shell instead of a plain sidebar-only entry point.
- Section switching still reaches `Workbench`, `Template Manager`, and `Settings`.

- [ ] **Step 7: Commit**

```bash
git add app.py src/zprompt_helper/ui/page_frame.py tests/ui/test_page_frame.py
git commit -m "feat: add redesigned app shell"
```

### Task 3: Refactor Workbench Into A Two-Column Studio

**Files:**
- Modify: `src/zprompt_helper/ui/workbench.py`
- Create: `src/zprompt_helper/ui/workbench_panels.py`
- Create: `tests/ui/test_workbench_layout.py`
- Modify: `tests/ui/test_workbench_actions.py`

- [ ] **Step 1: Write failing tests for workbench summary helpers**

```python
from zprompt_helper.workbench.session import EditorSession
from zprompt_helper.ui.workbench_panels import build_workbench_summary


def test_build_workbench_summary_counts_locks_and_variations() -> None:
    session = EditorSession(
        block_values={"subject": "robot"},
        locked_blocks={"subject", "scene"},
        variation_index=2,
        final_prompt="robot prompt",
    )

    summary = build_workbench_summary(session, active_block_count=5)

    assert summary.locked_count == 2
    assert summary.filled_count == 1
    assert summary.active_block_count == 5
    assert summary.variation_index == 2
    assert summary.has_final_prompt is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python -m pytest tests/ui/test_workbench_layout.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.ui.workbench_panels'
```

- [ ] **Step 3: Implement derived summary and split the workbench renderer**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkbenchSummary:
    active_block_count: int
    filled_count: int
    locked_count: int
    variation_index: int
    has_final_prompt: bool
```

```python
def build_workbench_summary(session, active_block_count: int) -> WorkbenchSummary:
    filled_count = sum(1 for value in session.block_values.values() if str(value).strip())
    return WorkbenchSummary(
        active_block_count=active_block_count,
        filled_count=filled_count,
        locked_count=len(session.locked_blocks),
        variation_index=session.variation_index,
        has_final_prompt=bool(session.final_prompt.strip()),
    )
```

- [ ] **Step 4: Redesign the workbench layout around stable native editors**

Implement this structure:

- Header card with template select, short idea, and draft-status badge.
- Left column for block editors using native `st.text_area()` and `st.checkbox()`.
- Right column for final prompt, primary actions, stats, and history tabs.
- Use shadcn cards/tabs/badges/popovers where they do not own the critical editor state.
- Keep `queue_workbench_widget_state()` and `apply_pending_workbench_widget_state()` behavior unchanged.

Use this shell shape:

```python
left_col, right_col = st.columns([1.45, 1.0], gap="large")

with left_col:
    render_workbench_editor_panel(...)

with right_col:
    render_workbench_output_panel(...)
```

- [ ] **Step 5: Add loading and transient feedback**

Use:

```python
with st.spinner("Generating prompt..."):
    generated = service.generate_blocks(...)
```

And for success:

```python
st.toast("Prompt updated.", icon=":material/check_circle:")
```

Fallback:

```python
st.success("Prompt updated.")
```

- [ ] **Step 6: Run the workbench tests**

Run:

```bash
python -m pytest tests/ui/test_workbench_layout.py tests/ui/test_workbench_actions.py -v
```

Expected:

```text
all passed
```

- [ ] **Step 7: Run manual browser verification for the workbench**

Run:

```bash
streamlit run app.py
```

Manual check:

- The workbench reads as two coordinated surfaces, not one long stack.
- Template switching still restores per-template drafts.
- Generate, regenerate, rebuild, clear, lock-all, unlock-all, and copy prompt still work.
- No `cannot be modified after the widget is instantiated` error appears.
- History is visible inside the workbench secondary surface, not only below the fold.

- [ ] **Step 8: Commit**

```bash
git add src/zprompt_helper/ui/workbench.py src/zprompt_helper/ui/workbench_panels.py tests/ui/test_workbench_layout.py tests/ui/test_workbench_actions.py
git commit -m "feat: redesign workbench layout"
```

### Task 4: Redesign History As A Secondary Surface

**Files:**
- Modify: `src/zprompt_helper/ui/history_panel.py`
- Modify: `tests/ui/test_history_panel.py`

- [ ] **Step 1: Extend history tests for display metadata helpers**

```python
from zprompt_helper.ui.history_panel import build_history_summary


def test_build_history_summary_counts_entries() -> None:
    summary = build_history_summary(
        [
            {"id": "1", "prompt_text": "one", "created_at": "2026-04-24T10:00:00+00:00"},
            {"id": "2", "prompt_text": "two", "created_at": "2026-04-24T12:00:00+00:00"},
        ]
    )

    assert summary.total_entries == 2
```

- [ ] **Step 2: Run the history tests to verify they fail**

Run:

```bash
python -m pytest tests/ui/test_history_panel.py -v
```

Expected:

```text
E   ImportError: cannot import name 'build_history_summary'
```

- [ ] **Step 3: Implement the history summary and card-oriented renderer**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class HistorySummary:
    total_entries: int


def build_history_summary(entries: list[dict]) -> HistorySummary:
    return HistorySummary(total_entries=len(entries))
```

Render rules:

- Put history inside a bordered surface suitable for the workbench right rail.
- Show compact metadata first, expanded prompt second.
- Move destructive actions into a secondary control cluster.
- Use a confirmation dialog for `Clear history`.

- [ ] **Step 4: Run the history tests**

Run:

```bash
python -m pytest tests/ui/test_history_panel.py -v
```

Expected:

```text
all passed
```

- [ ] **Step 5: Commit**

```bash
git add src/zprompt_helper/ui/history_panel.py tests/ui/test_history_panel.py
git commit -m "feat: redesign history surface"
```

### Task 5: Redesign Template Manager As A Catalog Plus Editor

**Files:**
- Modify: `src/zprompt_helper/ui/template_manager.py`
- Modify: `tests/ui/test_template_manager_actions.py`

- [ ] **Step 1: Add failing tests for template catalog helpers**

```python
from zprompt_helper.ui.template_manager import split_template_groups
from zprompt_helper.templates.builtin import load_builtin_templates


def test_split_template_groups_separates_builtin_and_custom() -> None:
    built_in = next(template for template in load_builtin_templates() if template.name == "Cinematic")
    custom = built_in.model_copy(deep=True)
    custom.origin = "custom"

    groups = split_template_groups([built_in, custom])

    assert len(groups["built_in"]) == 1
    assert len(groups["custom"]) == 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python -m pytest tests/ui/test_template_manager_actions.py -v
```

Expected:

```text
E   ImportError: cannot import name 'split_template_groups'
```

- [ ] **Step 3: Implement the catalog grouping helper and new layout**

```python
def split_template_groups(templates):
    return {
        "built_in": [template for template in templates if template.origin == "built_in"],
        "custom": [template for template in templates if template.origin == "custom"],
    }
```

Layout rules:

- Show built-in templates as a card grid with description, block count, and `Create copy` CTA.
- Show custom templates in a list/detail layout instead of one long expander stack.
- Put import/export in a secondary action popover instead of top-level buttons.
- Wrap custom template editing in `st.form()` so typing into fields does not rerun the full page.

- [ ] **Step 4: Run the template manager tests**

Run:

```bash
python -m pytest tests/ui/test_template_manager_actions.py -v
```

Expected:

```text
all passed
```

- [ ] **Step 5: Run a manual browser check for the template manager**

Manual check:

- Built-in templates look like a browsable catalog.
- Creating a copy still persists the new custom template.
- Editing a custom template in the form still saves correctly.

- [ ] **Step 6: Commit**

```bash
git add src/zprompt_helper/ui/template_manager.py tests/ui/test_template_manager_actions.py
git commit -m "feat: redesign template manager"
```

### Task 6: Redesign Settings Into Grouped Forms

**Files:**
- Modify: `src/zprompt_helper/ui/settings_page.py`
- Modify: `tests/ui/test_settings_page_actions.py`

- [ ] **Step 1: Add failing tests for settings section metadata**

```python
from zprompt_helper.ui.settings_page import build_settings_sections


def test_build_settings_sections_returns_expected_groups() -> None:
    sections = build_settings_sections()
    assert [section["id"] for section in sections] == ["api", "model", "advanced"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python -m pytest tests/ui/test_settings_page_actions.py -v
```

Expected:

```text
E   ImportError: cannot import name 'build_settings_sections'
```

- [ ] **Step 3: Implement grouped forms and explicit validation feedback**

```python
def build_settings_sections() -> list[dict[str, str]]:
    return [
        {"id": "api", "label": "API Access"},
        {"id": "model", "label": "Model Defaults"},
        {"id": "advanced", "label": "Advanced Generation"},
    ]
```

Layout rules:

- Wrap save fields in one `st.form("settings-form")`.
- Separate API key, model defaults, and advanced generation controls into visual groups.
- Use a spinner when validating the key.
- Show transient success feedback after save and clear error feedback on failure.

- [ ] **Step 4: Run the settings tests**

Run:

```bash
python -m pytest tests/ui/test_settings_page_actions.py -v
```

Expected:

```text
all passed
```

- [ ] **Step 5: Run a manual browser check for settings**

Manual check:

- Saving settings still persists values.
- Validating the API key shows a loading state and a visible result.
- The page no longer reads like an ungrouped raw form.

- [ ] **Step 6: Commit**

```bash
git add src/zprompt_helper/ui/settings_page.py tests/ui/test_settings_page_actions.py
git commit -m "feat: redesign settings page"
```

### Task 7: Final Polish, Regression Pass, And Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/manual-acceptance-checklist.md`

- [ ] **Step 1: Update docs to reflect the redesigned UI**

Add:

- a short UI overview in `README.md`;
- the new page structure and verification notes;
- screenshots or screenshot placeholders once the redesign is implemented.

- [ ] **Step 2: Run the full automated test suite**

Run:

```bash
python -m pytest -v
```

Expected:

```text
all passed
```

- [ ] **Step 3: Run the browser acceptance pass**

Run:

```bash
streamlit run app.py
```

Manual check:

- All three sections use the same visual language.
- Workbench actions still behave correctly.
- Clipboard copy still works in the live app.
- Template switching still preserves separate drafts.
- No obvious layout breakage appears on a narrow window width.

- [ ] **Step 4: Run packaging verification**

Run:

```bash
python -m pip install --dry-run .
```

Expected:

```text
Successfully built or resolved z-prompt-helper
```

- [ ] **Step 5: Commit**

```bash
git add README.md docs/manual-acceptance-checklist.md
git commit -m "docs: update ui redesign guidance"
```

## Suggested Execution Order

1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 5
6. Task 6
7. Task 7

This order gives the project a visible shell first, then the workbench, then the supporting screens. It also keeps the highest-risk stateful screen (`Workbench`) behind an established theme and adapter layer instead of mixing visual experiments directly into action logic.

## Self-Review

- Spec coverage check: the plan covers navigation shell, workbench layout, history placement, settings grouping, template manager redesign, visual system, feedback, loading states, and regression verification.
- Placeholder scan: no unresolved placeholder markers or dangling file references remain.
- Type consistency check: page ids use `workbench`, `template_manager`, and `settings` consistently across shell tasks.
