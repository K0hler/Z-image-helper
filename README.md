# Z-Prompt-Helper

Local Streamlit workbench for building structured English prompts for Z-Image Turbo and similar image models.

The app provides built-in prompt templates, editable custom templates, OpenRouter-backed block generation, prompt history, and OS-backed API key storage through `keyring`.

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

