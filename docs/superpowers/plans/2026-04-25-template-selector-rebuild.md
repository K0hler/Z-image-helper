# Template Selector Rebuild Plan

## Goal

Replace the current workbench template selector with a new implementation that does not depend on fragile cross-browser CSS overrides for Streamlit/BaseWeb `selectbox` internals.

## Why The Current Approach Should Be Replaced

The current template selector is visually unstable because it relies on styling nested BaseWeb layers inside Streamlit's native `selectbox`. The recent iterations showed the same pattern:

- the closed control can be styled in one browser and regress in another;
- the dropdown menu inherits extra wrapper borders and surfaces that are hard to target reliably;
- Chrome and Firefox render the popover shell and scrollbar differently;
- small visual defects require increasingly specific CSS rather than a better component boundary.

This is a bad maintenance tradeoff. The selector should be rebuilt as a dedicated UI surface instead of continuing to patch the native dropdown.

## Recommended Direction

Build a custom "template chooser" for the workbench header and remove the native `st.selectbox` from that area.

Recommended implementation:

1. Show the current template as a compact trigger surface in the header.
2. Open a controlled chooser panel when the user clicks the trigger.
3. Render template options as a vertical list of custom buttons/cards.
4. Persist the selected template through the existing `selected_template_id` and workbench session flow.
5. Keep the rest of the workbench state logic unchanged.

## Preferred UX

### Closed State

- One compact trigger row.
- Template name on the left.
- Small chevron on the right.
- Same surface language as the workbench header.
- No browser-native scrollbar, popover border, or hidden BaseWeb layers.

### Open State

- A custom dropdown panel or popover anchored under the trigger.
- Dark and light modes controlled only by our own tokens.
- Each template option rendered as a full-width row button.
- Hover and selected states designed explicitly.
- Optional built-in/custom grouping can be added later, but not required in the first pass.

## Technical Direction

### Option A: Native Streamlit Composition

Use `st.popover()` plus a list of `st.button()` or styled button rows.

Pros:

- minimal risk;
- no new dependency;
- easier to wire into current session state;
- avoids BaseWeb `selectbox` internals completely.

Cons:

- less flexible than a true custom component.

### Option B: Small Custom Component

Build a tiny component for a trigger + menu selector.

Pros:

- full visual control;
- easiest path to pixel-consistent behavior.

Cons:

- more implementation overhead than needed for tomorrow's first pass.

### Recommendation

Start with Option A. It is the fastest path to a stable cross-browser result and removes the root problem immediately.

## State Contract To Preserve

The rebuild must keep the existing behavior intact:

- selection still writes to `st.session_state["selected_template_id"]`;
- template switching still restores per-template drafts;
- `EditorSession` activation still flows through the existing workbench logic;
- no direct writes to widget state after widget instantiation in the same render pass;
- no regression in generate, regenerate, rebuild, clear, lock, unlock, or copy flows.

## Files Expected To Change

- `src/zprompt_helper/ui/workbench_panels.py`
- `src/zprompt_helper/ui/theme.py`
- `tests/ui/test_workbench_actions.py`
- `tests/ui/test_workbench_layout.py`

Potentially:

- `src/zprompt_helper/ui/shadcn.py`

Only if a shared trigger/list helper is worth extracting.

## Acceptance Criteria

- The workbench no longer uses the native `selectbox` for template selection.
- The closed selector looks intentional in both dark and light themes.
- The opened chooser has no stray white border, no browser-specific popover artifact, and no visible scrollbar mismatch.
- Template switching still restores separate drafts correctly.
- Existing workbench tests remain green, with focused additions for the new selector behavior.
- Manual verification passes in both Chrome and Firefox.

## Suggested Implementation Order

1. Add a small helper that renders the custom trigger and option list.
2. Replace the header `selectbox` with the new chooser.
3. Bind selection to the existing session state key.
4. Remove now-unneeded `selectbox`-specific CSS overrides from the theme.
5. Run targeted workbench tests.
6. Manually verify dark/light behavior in Chrome and Firefox.

## Explicit Non-Goals For The First Pass

- redesigning the entire workbench header;
- adding search inside the selector;
- adding icons or template previews;
- rebuilding the template manager page.

## Tomorrow Start Point

Open this file first, then implement the selector replacement in `workbench_panels.py` before touching any more theme CSS.
