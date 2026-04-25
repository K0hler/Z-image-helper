from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent

from zprompt_helper.secrets.secret_store import KeyringSecretStore
from zprompt_helper.generation.service import GenerationService
from zprompt_helper.openrouter.client import OpenRouterClient
from zprompt_helper.services.settings_service import SettingsService
from zprompt_helper.storage.history_store import HistoryStore
from zprompt_helper.storage.paths import ProjectPaths
from zprompt_helper.storage.settings_store import SettingsStore
from zprompt_helper.storage.template_store import TemplateStore
from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.page_frame import normalize_page_id, render_page_shell
from zprompt_helper.ui.settings_page import render_settings_page
from zprompt_helper.ui.template_manager import render_template_manager
from zprompt_helper.ui.theme import apply_theme
from zprompt_helper.ui.workbench import render_workbench


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Z-Prompt-Helper", layout="wide")
    paths = ProjectPaths.from_root(ROOT)
    settings_service = SettingsService(SettingsStore(paths), KeyringSecretStore())
    settings_vm = asdict(settings_service.load())
    st.session_state.setdefault("theme_mode", settings_vm.get("theme_mode", "light"))
    page, theme_mode = render_page_shell(
        normalize_page_id(st.session_state.get("active_page")),
        st.session_state.get("theme_mode"),
        settings_service=settings_service,
    )
    apply_theme(theme_mode)
    history_store = HistoryStore(paths)
    history_entries = history_store.export_all()
    built_in_templates = load_builtin_templates()
    template_store = TemplateStore(paths)
    custom_templates = template_store.load_all()

    if page == "workbench":
        templates = [*built_in_templates, *custom_templates]
        render_workbench(
            {
                "templates": templates,
                "settings_service": settings_service,
                "generation_factory": lambda api_key: GenerationService(OpenRouterClient(api_key)),
                "history_store": history_store,
                "history_entries": history_entries,
                "paths": paths,
            }
        )
    elif page == "template_manager":
        render_template_manager(custom_templates, built_in_templates, template_store)
    else:
        settings_vm = asdict(settings_service.load())
        render_settings_page(settings_vm, settings_service=settings_service)


if __name__ == "__main__":
    main()
