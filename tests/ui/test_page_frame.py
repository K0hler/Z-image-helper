from zprompt_helper.ui.page_frame import PAGE_SPECS, build_page_shell_state, normalize_page_id


def test_normalize_page_id_defaults_to_workbench() -> None:
    assert normalize_page_id(None) == "workbench"
    assert normalize_page_id("unknown") == "workbench"


def test_page_specs_cover_all_sections() -> None:
    assert set(PAGE_SPECS) == {"workbench", "template_manager", "settings"}


def test_build_page_shell_state_keeps_page_metadata_and_theme_in_sync() -> None:
    state = build_page_shell_state("settings", "dark")

    assert state.page_id == "settings"
    assert state.theme_mode == "dark"
    assert state.spec.label == "Settings"
