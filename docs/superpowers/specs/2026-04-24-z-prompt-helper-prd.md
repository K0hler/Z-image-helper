# Z-Prompt-Helper PRD

## Document Control

- Product: `Z-Prompt-Helper`
- Document type: `Product Requirements Document`
- Version: `v1.0 draft for implementation planning`
- Last updated: `2026-04-24`
- Status: `Approved for planning`

## 1. Product Summary

Z-Prompt-Helper is a local, open source prompt workbench for users who create image prompts for Z-Image Turbo. The product reduces prompt authoring from a manual, error-prone writing task into a structured workflow driven by reusable templates, assisted block generation, and local editing.

The application runs locally as a `Python + Streamlit` app and uses `OpenRouter` for LLM-powered block generation. It does not include accounts, cloud sync, or multi-user collaboration. The product focus for `v1` is a fast, editor-first workflow for generating, refining, and copying final prompts in English, while letting users start from a short idea in Russian or English.

## 2. Problem Statement

Z-Image Turbo works best with long, structured prompts and does not rely on negative prompts as a primary control mechanism. Users currently have to assemble prompts manually from pieces such as subject, scene, composition, lighting, style, details, and constraints. That process is slow, inconsistent, and difficult to scale across styles or repeated usage.

Users need a local tool that:

- gives them strong built-in prompt templates;
- fills template blocks from a short idea using an LLM;
- keeps the workflow understandable and editable;
- avoids cloud lock-in and unnecessary infrastructure;
- supports repeatable, copy-ready prompt output.

## 3. Goals And Non-Goals

### 3.1 Goals

- Reduce the time required to produce a usable Z-Image Turbo prompt from minutes to seconds.
- Improve prompt consistency by generating from structured template blocks instead of ad hoc freeform writing.
- Support both beginners and advanced users through strong built-in templates and editable custom copies.
- Keep the app local-first, portable, and easy to run.
- Make the final output copy-ready for direct use in Z-Image Turbo.

### 3.2 Success Metrics

- Median time from opening the app to copying a prompt.
- Number of successful prompt generations.
- Ratio of generated prompts that are copied by the user.
- Frequency of manual block edits after generation.
- Frequency of reuse of custom templates.

### 3.3 Non-Goals For v1

- No user accounts.
- No cloud sync or shared workspaces.
- No server-side storage.
- No direct integration with Z-Image Turbo image generation.
- No batch prompt generation.
- No arbitrary new block types outside the standard block catalog.

## 4. Target Users

### 4.1 Primary Users

- Freelancers creating prompts for image generation work.
- Artists and designers iterating on prompt structures.
- AI power users who want a reusable local prompt workbench.

### 4.2 Secondary Users

- Beginners who want help understanding prompt structure.
- Researchers or experimenters comparing prompt styles and outputs.

## 5. Product Principles

- `Editor-first`: the main work happens on one screen without forcing a wizard flow.
- `Structured over magical`: prompt generation must be predictable and schema-driven, not dependent on fragile parsing.
- `Local-first`: user data stays on the local machine unless explicitly sent to OpenRouter during generation.
- `Built-in strong defaults`: the app ships with opinionated templates that work immediately.
- `Safe customization`: users can customize copies of templates without mutating the built-in baseline.

## 6. Scope Overview

### 6.1 v1 Scope

`v1` includes:

- a local `Streamlit` application;
- 7 built-in templates;
- custom templates created as editable copies of built-in templates;
- one-shot generation for all active blocks;
- targeted regeneration for a single block;
- block locking;
- final prompt auto-assembly in English;
- direct editing of blocks and final prompt;
- local history storage by date;
- separate import/export for templates and history;
- local settings for model and generation parameters;
- API key storage via the OS secret store.

### 6.2 Post-MVP

Post-MVP may include:

- arbitrary new block types outside the standard block catalog;
- richer history rotation if one day file becomes too large;
- presets for models and generation settings;
- batch prompt generation;
- multiple providers beyond OpenRouter;
- branding, theming, and advanced design polish;
- analytics and prompt quality scoring;
- collaborative or cloud features.

## 7. Built-In Templates

The app ships with 7 immutable built-in templates. Users may use them directly or create editable copies.

### 7.1 Built-In Template Set

1. `Universal`
2. `Cinematic`
3. `Photorealism`
4. `Art / Illustration`
5. `Character`
6. `Scenes / Environment`
7. `Text In Image`

### 7.2 Template Status Rules

- Built-in templates are read-only.
- Users cannot edit a built-in template directly.
- Users can create a custom copy of a built-in template.
- Custom copies can be renamed and modified.

## 8. User Scenarios

### 8.1 Quick Start

The user opens the app, selects `Universal`, enters a short idea such as "steampunk city with an airship", clicks `Generate`, reviews the generated blocks, adjusts one or two fields, and copies the final prompt into Z-Image Turbo.

### 8.2 Controlled Iteration

The user generates a prompt, locks `Style` and `Lighting`, then regenerates only the remaining unlocked fields to explore alternative subject or scene variations without losing the locked decisions.

### 8.3 Block-Level Fix

The user likes the prompt except for `Composition`. They regenerate only that block while preserving the current state of all other blocks.

### 8.4 Advanced Template Reuse

The user creates a copy of `Cinematic`, renames fields, changes block order, updates the assembly formula, edits the template-level system prompt, and adds block-specific instructions for repeated use.

### 8.5 Settings On First Run

The user enters the OpenRouter API key once, stores it in the OS secret store, selects a default model and generation parameters, validates the connection, and does not need to re-enter the key on every launch.

## 9. Information Architecture And UX

The application is organized around three main areas:

- `Workbench`
- `Template Manager`
- `Settings`

### 9.1 Workbench

The Workbench is the default landing screen and the primary surface for day-to-day use. It contains:

- template selector;
- short idea input;
- primary actions: `Generate`, `Regenerate Unlocked`, `Copy Prompt`;
- block editor for the active template;
- final prompt editor;
- recent history section.

### 9.2 Template Manager

The Template Manager contains:

- list of built-in and custom templates;
- create-copy action for built-in templates;
- custom template editing;
- template import and export actions.

### 9.3 Settings

The Settings screen contains:

- OpenRouter API key setup and validation;
- model selection;
- generation parameters such as `temperature`, `top_p`, and token limit;
- local app preferences that are not secrets.

### 9.4 Core UX States

- `Empty state`: template selected, no generated content yet.
- `Generating state`: loader is shown, conflicting actions are disabled.
- `Editable result state`: blocks and final prompt are editable.
- `Error state`: the app shows a clear error and next step.

## 10. Functional Requirements

### 10.1 Template Selection And Editing

- The user can select any built-in or custom template.
- The user can create a custom template by copying a built-in template.
- The user can edit only custom templates.
- The user can reorder active blocks in a custom template.
- The user can rename active blocks in a custom template.
- The user can enable or disable standard blocks in a custom template.
- The user can edit the final prompt assembly formula in a custom template.
- The user can edit a template-level system prompt in a custom template.
- The user can edit block-level instructions in a custom template.

### 10.2 Generation

- The user enters a short idea in Russian or English.
- The app generates final prompt content in English by default.
- Main generation fills all active unlocked blocks in one request.
- Block-level regeneration updates only the selected block.
- Locked blocks are never overwritten during full regeneration.
- The app uses the current form state as context for regeneration.

### 10.3 Block Editing

- Each active block is rendered as a text field.
- Each block supports manual editing.
- Each block supports a `Lock` toggle.
- Each block supports targeted regeneration.

### 10.4 Final Prompt

- The final prompt is assembled automatically from block values using the template formula.
- The user can manually edit the final prompt text.
- Any later block edit or successful regeneration rebuilds the final prompt and may overwrite manual prompt edits.
- The user can copy the final prompt to the clipboard in one action.

### 10.5 History

- The app stores history locally by date.
- History stores only the final prompt plus minimal system metadata required for rendering and deletion.
- The user can view recent history entries.
- The user can copy a history entry.
- The user can delete a single history entry.
- The user can clear history.

### 10.6 Import And Export

- Template import/export is handled through a dedicated templates JSON file.
- History import/export is handled through a separate history JSON file.
- Imported files are validated before being written to local storage.
- API keys are never included in exports.

### 10.7 Settings And Connectivity

- The user can enter the OpenRouter API key once.
- The app stores the API key in the OS secret store, not in project-local JSON files.
- The user can choose the default model.
- The user can set generation parameters.
- The user can validate API connectivity from the Settings screen.

## 11. Standard Block Catalog

`v1` uses a standard block catalog. Custom templates can reorder, rename, enable, and disable blocks from this catalog, but cannot invent new block types outside it.

Expected standard blocks include:

- `Subject`
- `Scene`
- `Composition`
- `Lighting`
- `Style`
- `Details`
- `Constraints`

The final implementation may define additional standard blocks if needed for the `Text In Image` template, but the catalog must remain explicit and versioned.

## 12. Template Data Model

Each template definition should support the following conceptual fields:

- `id`
- `name`
- `description`
- `origin` (`built_in` or `custom`)
- `created_at`
- `updated_at`
- `active_blocks`
- `block_order`
- `block_labels`
- `assembly_formula`
- `template_system_prompt`
- `block_instructions`

### 12.1 Built-In Templates

- Stored as app assets.
- Read-only at runtime.

### 12.2 Custom Templates

- Stored as local JSON files.
- Created by copying built-in templates.
- Editable by the user.

## 13. Generation Contract With The LLM

The product uses a strict, schema-first generation contract.

### 13.1 Request Inputs

Each generation request must include:

- the app-level system prompt;
- the template-level system prompt;
- the short user idea;
- the active block schema;
- the block-specific instructions;
- current block values, if present;
- the set of locked blocks;
- the selected model and generation settings.

### 13.2 Response Contract

- The LLM must return valid JSON for the current block schema.
- The app must validate the JSON before applying it to the UI.
- If the response is invalid, the app performs one automatic retry with a stricter format reminder.
- If the retry also fails, the app shows a clear error and does not use heuristic text parsing.

### 13.3 Structured Output Strategy

The app-level contract is strict JSON output. Implementation should prefer OpenRouter structured output features such as `response_format` with `json_schema` when the selected model supports it. If the chosen model does not support structured outputs, the app still enforces the same JSON contract through prompt design plus local validation and retry behavior.

### 13.4 Regeneration Modes

- `Generate`: fill all active unlocked blocks in one request.
- `Regenerate Unlocked`: refill only unlocked blocks.
- `Regenerate Block`: refill only one selected block while preserving the rest of the current state.

## 14. Storage Model

The application stores non-secret files next to the app in the project workspace.

### 14.1 Expected Local Structure

```text
data/
  settings.json
  templates/
    *.json
  history/
    YYYY-MM-DD.json
```

### 14.2 History File Strategy

- One history JSON file per date.
- Example: `data/history/2026-04-24.json`
- This date-based sharding is the `v1` file-size control strategy.
- `v1` does not require additional within-day sharding unless proven necessary later.

### 14.3 Secret Storage

- The OpenRouter API key is not stored in `settings.json`.
- The OpenRouter API key is stored in the OS secret store.
- Exported files must never contain the API key.

## 15. Security And Privacy Requirements

- The app is local-first and single-user.
- The app does not require accounts.
- The app does not implement cloud sync.
- User input is sent only to OpenRouter during generation.
- API keys must never be written to plain-text local project files.
- Logs must never include the API key.
- Debug logging should avoid storing full prompt content by default.

## 16. Non-Functional Requirements

### 16.1 Technology

- Backend/application layer: `Python`
- UI layer: `Streamlit`
- LLM gateway: `OpenRouter`

### 16.2 Performance

- Local UI actions should feel immediate.
- Generation should always show an explicit loading state.
- Failed requests must resolve into a visible error state, not a broken form.

### 16.3 Reliability

- Invalid model output must not corrupt the current editor state.
- A failed generation request must leave the previous valid state intact.
- Import validation must prevent malformed JSON from entering storage.

### 16.4 Usability

- The interface should remain minimal and scannable.
- Core actions should be visible without deep navigation.
- The copy action should be obvious and low-friction.

### 16.5 Localization

- UI language for `v1`: Russian.
- Final prompt output language by default: English.
- User idea input may be Russian or English.

### 16.6 Portability

- The app must run locally with `streamlit run app.py`.
- The app should work without requiring a hosted backend.

## 17. Error Handling

The app must distinguish between at least these error classes:

- invalid or missing API key;
- network error;
- rate limit or quota error;
- unsupported model or unsupported structured output mode;
- invalid JSON returned by the model;
- local storage read/write error;
- import validation failure.

User-facing errors should be short and actionable. Technical details may be written to local debug logs when safe to do so.

## 18. Acceptance Criteria For v1

`v1` is ready for implementation completion when all of the following are true:

### 18.1 Templates

- All 7 built-in templates are available.
- Built-in templates are read-only.
- The user can create and edit custom copies.

### 18.2 Generation

- Main generation fills the active schema in one request.
- Invalid model output triggers one retry and then a visible error.
- Locked fields remain unchanged during full regeneration.
- Single-block regeneration updates only the targeted block.

### 18.3 Prompt Assembly

- Final prompt is assembled automatically in English.
- Copy-to-clipboard works from the Workbench.
- Final prompt is rebuilt after block changes, even if the user had manually edited it before.

### 18.4 History

- Final prompts are written to the current date file.
- Users can copy, delete, and clear history entries.
- History export and import work independently from template export and import.

### 18.5 Settings

- The API key can be entered once and reused across launches.
- The API key is stored in the OS secret store.
- Model and generation parameters are configurable in the UI.
- Connection validation is available.

## 19. Open Questions For Implementation Planning

These are not product-scope blockers, but they should be resolved in the implementation plan:

- Which Python library should be used for cross-platform OS secret storage.
- How built-in templates should be packaged: JSON assets, Python constants, or hybrid asset loading.
- Whether history import should merge by generated ID, by timestamp, or by exact prompt text deduplication.
- Which OpenRouter-compatible models should be recommended as defaults for `v1`.
- Whether `Text In Image` needs a small extension of the standard block catalog or can stay within the core catalog.

## 20. References

- User draft: `C:\Users\user\Downloads\Шаблоны для Z-Image Turbo.docx`
- Template source: `C:\Users\user\Desktop\Шаблоны.txt`
- OpenRouter official API documentation: chat completions, authentication, and structured outputs
