# Z-Prompt-Helper

Local Streamlit workbench for building structured English prompts for Z-Image Turbo and similar image models.

The app provides built-in prompt templates, editable custom templates, OpenRouter-backed block generation, prompt history, and OS-backed API key storage through `keyring`.

## UI Overview

The redesigned app uses a shared page shell with three sections:

- `Workbench` is now a two-column studio with native block editors on the left and prompt output, actions, and history on the right.
- `Template Manager` separates the built-in catalog from custom-template editing so cloning and maintenance no longer compete in one long widget stack.
- `Settings` groups API access, model defaults, and advanced generation controls into clearer surfaces and a single save form.

The visual system is intentionally light and editorial: warm neutral surfaces, copper accenting, `Manrope` for UI text, and `IBM Plex Mono` for prompt/code areas.

## Requirements

- Python 3.12 or newer
- Windows, macOS, or Linux with an available `keyring` backend
- OpenRouter API key for generation

## Setup

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` installs this project in editable mode. Runtime dependencies are declared in `pyproject.toml`.

## Run

```powershell
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal, usually `http://localhost:8501`.

## Basic Workflow

1. Open **Settings** and save your OpenRouter API key.
2. Optionally set a model name, temperature, top-p, and max token limit.
3. Open **Workbench**, select a template, enter a short idea, edit or lock blocks, and generate a prompt.
4. Review the final prompt and history entries.
5. Open **Template Manager** to copy built-in templates and edit custom templates.

## Verification Notes

- Targeted UI regression coverage lives under `tests/ui/`.
- The redesigned shell and layout helpers are covered by `tests/ui/test_theme.py`, `tests/ui/test_shadcn.py`, `tests/ui/test_page_frame.py`, and `tests/ui/test_workbench_layout.py`.
- Manual smoke verification should confirm section switching, two-column workbench layout, history visibility inside the workbench, grouped settings, and template catalog/edit flows.

## Data Storage

- Non-secret settings: `data/settings.json`
- Custom templates: `data/templates/*.json`
- Prompt history: `data/history/YYYY-MM-DD.json`
- API key: OS secret store via `keyring`

The `data/` directory is intentionally ignored by Git.

## Tests

```powershell
python -m pytest -v
```

