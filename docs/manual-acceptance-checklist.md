# Manual Acceptance Checklist

Use this checklist after installing dependencies in a fresh virtual environment.

## Environment

- [ ] Create a Python 3.12+ virtual environment.
- [ ] Run `python -m pip install -r requirements.txt`.
- [ ] Run `python -m pytest -v` and confirm all tests pass.
- [ ] Start the app with `streamlit run app.py`.

## Settings

- [ ] Open the **Settings** page.
- [ ] Enter an OpenRouter API key and save settings.
- [ ] Confirm `data/settings.json` does not contain the API key.
- [ ] Use **Проверить ключ** and confirm the app reports a successful connection.
- [ ] Leave the model field blank and confirm validation still sends a request.
- [ ] Enter a model name and confirm validation still works.

## Workbench

- [ ] Open **Workbench**.
- [ ] Select each built-in template and confirm block editors render.
- [ ] Enter a short idea and generate blocks.
- [ ] Lock one block, regenerate, and confirm the locked value is preserved.
- [ ] Edit a block manually and rebuild the final prompt.
- [ ] Confirm empty block values do not leave duplicate comma separators.
- [ ] Copy or prepare the final prompt from the UI.
- [ ] Confirm generated or rebuilt prompts are appended to history.

## Template Manager

- [ ] Open **Template Manager**.
- [ ] Create a copy of a built-in template.
- [ ] Confirm a custom template file appears under `data/templates/`.
- [ ] Edit a custom template name, system prompt, and formula.
- [ ] Save the template and confirm the changes persist after app reload.
- [ ] Try an invalid formula and confirm the app shows an error instead of saving it.

## History

- [ ] Confirm history entries are shown latest first.
- [ ] Delete one history entry and confirm it disappears after rerun.
- [ ] Clear history and confirm history files are removed.
- [ ] Import or manually add a history entry with a naive timestamp and confirm sorting still works.

## Persistence

- [ ] Stop and restart Streamlit.
- [ ] Confirm non-secret settings, custom templates, and history persist.
- [ ] Confirm the API key is still available through the OS keyring.

