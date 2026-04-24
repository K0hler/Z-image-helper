from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from zprompt_helper.storage.paths import ProjectPaths
from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.workbench import render_workbench


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Z-Prompt-Helper", layout="wide")
    paths = ProjectPaths.from_root(ROOT)
    templates = load_builtin_templates()
    render_workbench(
        {
            "template_names": [template.name for template in templates],
            "paths": paths,
        }
    )


if __name__ == "__main__":
    main()
