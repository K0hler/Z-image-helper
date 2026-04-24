from pathlib import Path


ROOT = Path(__file__).resolve().parent

from zprompt_helper.storage.paths import ProjectPaths
from zprompt_helper.storage.template_store import TemplateStore
from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.template_manager import render_template_manager
from zprompt_helper.ui.workbench import render_workbench


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Z-Prompt-Helper", layout="wide")
    paths = ProjectPaths.from_root(ROOT)
    built_in_templates = load_builtin_templates()
    custom_templates = TemplateStore(paths).load_all()
    page = st.sidebar.radio("Раздел", options=["Workbench", "Template Manager"])

    if page == "Workbench":
        templates = [*built_in_templates, *custom_templates]
        render_workbench(
            {
                "template_names": [template.name for template in templates],
                "paths": paths,
            }
        )
    else:
        render_template_manager(custom_templates, built_in_templates)


if __name__ == "__main__":
    main()
