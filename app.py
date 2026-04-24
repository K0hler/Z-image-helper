from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent

from zprompt_helper.secrets.secret_store import KeyringSecretStore
from zprompt_helper.services.settings_service import SettingsService
from zprompt_helper.storage.history_store import HistoryStore
from zprompt_helper.storage.paths import ProjectPaths
from zprompt_helper.storage.settings_store import SettingsStore
from zprompt_helper.storage.template_store import TemplateStore
from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.history_panel import render_history_panel
from zprompt_helper.ui.settings_page import render_settings_page
from zprompt_helper.ui.template_manager import render_template_manager
from zprompt_helper.ui.workbench import render_workbench


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Z-Prompt-Helper", layout="wide")
    paths = ProjectPaths.from_root(ROOT)
    settings_service = SettingsService(SettingsStore(paths), KeyringSecretStore())
    history_entries = HistoryStore(paths).export_all()
    built_in_templates = load_builtin_templates()
    custom_templates = TemplateStore(paths).load_all()
    page = st.sidebar.radio("Раздел", options=["Workbench", "Template Manager", "Settings"])

    if page == "Workbench":
        templates = [*built_in_templates, *custom_templates]
        render_workbench(
            {
                "template_names": [template.name for template in templates],
                "paths": paths,
            }
        )
        render_history_panel(history_entries)
    elif page == "Template Manager":
        render_template_manager(custom_templates, built_in_templates)
    else:
        settings_vm = asdict(settings_service.load())
        render_settings_page(settings_vm)


if __name__ == "__main__":
    main()
