# Repository Guidelines

## Project Structure & Module Organization
`app.py` is the Streamlit entrypoint. Application code lives in `src/zprompt_helper/` and is split by responsibility: `ui/` for Streamlit views, `workbench/` for session state, `generation/` and `openrouter/` for model calls, `storage/` for local JSON persistence, `services/` for orchestration, and `secrets/` for keyring access. Built-in template assets live in `src/zprompt_helper/assets/`. Tests mirror the package layout under `tests/`. Runtime data stays in `data/` (`history/`, `templates/`, `settings.json`) and should remain untracked.

## Build, Test, and Development Commands
Create an environment and install dev dependencies:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
Run the app locally with `streamlit run app.py`. Run the full test suite with `python -m pytest -v`. For coverage on core logic changes, use `python -m pytest --cov=src/zprompt_helper --cov-report=term-missing`.

## Coding Style & Naming Conventions
Target Python 3.12+ and keep imports, type hints, and small focused classes consistent with the existing codebase. Use 4-space indentation, `snake_case` for functions, variables, and modules, and `PascalCase` for classes. Keep UI actions thin and move storage, API, and prompt-generation rules into package modules instead of `app.py`. Follow existing JSON naming and date-based history files like `data/history/2026-04-24.json`.

## Testing Guidelines
Use `pytest` for all tests. Place tests in the matching domain folder, for example `tests/storage/test_history_store.py` or `tests/ui/test_workbench_actions.py`. Name files `test_*.py` and prefer one behavior per test. When changing OpenRouter integration, storage, or UI actions, add or update targeted tests before merging.

## Commit & Pull Request Guidelines
Recent history uses short conventional subjects such as `fix: wire streamlit actions to services` and `chore: add requirements file`. Keep that format: `<type>: <imperative summary>`, with `fix` and `chore` as the current baseline. PRs should explain the user-visible change, list verification commands run, and include screenshots for Streamlit UI changes. Link the relevant issue or plan doc when the change traces back to `docs/superpowers/`.

## Security & Configuration Tips
Do not commit API keys or generated local data. Secrets belong in the OS keyring via `zprompt_helper/secrets/secret_store.py`; non-secret settings stay in `data/settings.json`.
